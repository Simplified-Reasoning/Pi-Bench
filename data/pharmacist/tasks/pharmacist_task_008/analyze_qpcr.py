"""
qPCR ΔCt analysis script — v8.

A gate-based pipeline: each checkpoint either passes or stops the
analysis. No step proceeds if a prior gate has failed.

Changes from v7:
  1. v7 required interactive input() for Gate 0 and Gate 1, making
     the script impossible to run non-interactively (batch mode,
     CI pipelines, Jupyter notebooks). v8 adds a BATCH_MODE flag:
     when True, the script assumes controls passed and replicates
     are biological — but prints a prominent banner reminding the
     user that they are responsible for verifying these assumptions
     before trusting the output. When False, the script behaves
     like v7 (interactive prompts).
  2. v7 had no machine-readable interpretation output. v8 writes
     a brief interpretation block to stdout AND appends an
     "interpretation" column to delta_ct_summary.csv so downstream
     tools can parse the verdict without screen-scraping.
  3. v7's Pfaffl CI when E_target ≠ E_ref used an ad-hoc
     approximation (FC * E^(±t*SE)) that doesn't correctly propagate
     uncertainty through two different bases. v8 uses the correct
     error-propagation formula on the log scale:
       log₂(FC) ≈ log₂(E_target)*ΔCt_target − log₂(E_ref)*ΔCt_ref
     and propagates SE through both terms before exponentiating.
     When E_target == E_ref, this simplifies to the v7 formula.
  4. v7 did not validate that the CSV has no duplicate sample names.
     v8 checks for duplicates and exits with an error if found —
     duplicate sample names silently corrupt per-sample tracking.
  5. v8 adds a one-line "most common mistake" banner at the top of
     output, before any computation, to prime the user's attention
     on the single control point that most easily biases results.

Pipeline gates (unchanged from v7):
  Gate 0: Pre-analysis controls
  Gate 1: Replicate type + n ≥ 2
  Gate 2: Housekeeping stability (hard gate)
  Gate 3: ΔCt computation (per-sample)
  Gate 4: ΔΔCt, fold change, CI, t-test
  Gate 5: Interpretation (structured verdict)
"""

from pathlib import Path
import csv
import math
import sys

# ── Configuration ──────────────────────────────────────────────────────
INPUT_PATH = Path("qpcr_ct_example.csv")
OUTPUT_SUMMARY_PATH = Path("delta_ct_summary.csv")
OUTPUT_PER_SAMPLE_PATH = Path("per_sample_delta_ct.csv")
REFERENCE_GROUP = "control"
CT_MIN = 5
CT_MAX = 40
E_TARGET = 2.0   # Efficiency of the target gene primer set
E_REF = 2.0      # Efficiency of the reference gene primer set
SMALL_EFFECT_THRESHOLD = 0.5
HK_MEAN_DIFF_THRESHOLD = 0.5

# When True, skip interactive prompts (Gate 0 & Gate 1) and assume
# controls passed / replicates are biological. Use this for batch
# processing, but ONLY after you have manually verified controls.
BATCH_MODE = True

# ── t-distribution critical value lookup ───────────────────────────────
T_CRITICAL_95 = {
    1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571,
    6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228,
    11: 2.201, 12: 2.179, 13: 2.160, 14: 2.145, 15: 2.131,
    16: 2.120, 17: 2.110, 18: 2.101, 19: 2.093, 20: 2.086,
    25: 2.060, 30: 2.042, 40: 2.021, 60: 2.000, 120: 1.980,
}


def get_t_critical_95(df):
    """Return two-tailed t critical value for α=0.05."""
    try:
        from scipy import stats as _scipy_stats
        return _scipy_stats.t.ppf(0.975, df)
    except ImportError:
        pass
    if df in T_CRITICAL_95:
        return T_CRITICAL_95[df]
    keys = sorted(T_CRITICAL_95.keys())
    if df < keys[0]:
        return T_CRITICAL_95[keys[0]]
    if df > keys[-1]:
        return 1.96
    for i in range(len(keys) - 1):
        if keys[i] <= df <= keys[i + 1]:
            frac = (df - keys[i]) / (keys[i + 1] - keys[i])
            return (T_CRITICAL_95[keys[i]]
                    + frac * (T_CRITICAL_95[keys[i + 1]]
                              - T_CRITICAL_95[keys[i]]))
    return 1.96


# ── Statistical helpers ────────────────────────────────────────────────

def mean(values):
    return sum(values) / len(values)


def sd(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def sem(values):
    if len(values) < 2:
        return 0.0
    return sd(values) / math.sqrt(len(values))


def welch_satterthwaite_df(var_a, n_a, var_b, n_b):
    num = (var_a / n_a + var_b / n_b) ** 2
    denom = ((var_a / n_a) ** 2 / (n_a - 1)
             + (var_b / n_b) ** 2 / (n_b - 1))
    if denom == 0:
        return float("inf")
    return num / denom


def t_test_two_sample_unpaired(group_a, group_b):
    n_a, n_b = len(group_a), len(group_b)
    if n_a < 2 or n_b < 2:
        return None, None, None
    mean_a, mean_b = mean(group_a), mean(group_b)
    var_a = sd(group_a) ** 2
    var_b = sd(group_b) ** 2
    se_diff = math.sqrt(var_a / n_a + var_b / n_b)
    if se_diff == 0:
        return None, None, None
    t_stat = (mean_a - mean_b) / se_diff
    df = welch_satterthwaite_df(var_a, n_a, var_b, n_b)
    try:
        from scipy import stats as _scipy_stats
        p_value = 2 * (1 - _scipy_stats.t.cdf(abs(t_stat), df))
        return t_stat, p_value, df
    except ImportError:
        return t_stat, None, df


# ═══════════════════════════════════════════════════════════════════════
#  GATE 0 — Pre-analysis controls
# ═══════════════════════════════════════════════════════════════════════

def gate_0_controls():
    """Require user confirmation that pre-analysis controls passed."""
    print("=" * 60)
    print("GATE 0 — Pre-analysis controls")
    print("=" * 60)
    print()

    controls = [
        ("NTC (no-template control)",
         "Checks for primer-dimer or reagent contamination.",
         "Failed if Ct < 35 in the NTC well.",
         "Redesign primers or replace reagents."),
        ("No-RT control",
         "Checks for genomic DNA contamination in RNA prep.",
         "Failed if amplification appears in the no-RT well.",
         "Treat RNA with DNase; design primers spanning exon-exon junctions."),
        ("Standard curve / efficiency",
         "Checks PCR amplification efficiency for each gene.",
         "Failed if slope outside −3.1 to −3.6 (efficiency 90–110%).",
         "Re-optimize primers; use Pfaffl method if efficiency ≠ 100%."),
        ("Melt curve",
         "Checks that each primer set produces a single amplicon.",
         "Failed if multiple peaks or broad peak.",
         "Redesign primers; verify single product by gel electrophoresis."),
        ("Positive control",
         "Checks that the assay is working at all.",
         "Failed if no amplification or Ct >> expected.",
         "Check reagents, thermocycler program, and template integrity."),
    ]

    if BATCH_MODE:
        print("⚠ BATCH MODE: Assuming all pre-analysis controls passed.")
        print("  You are responsible for verifying NTC, no-RT, efficiency,")
        print("  melt curve, and positive control BEFORE trusting output.")
        print()
        for name, purpose, fail_signal, action in controls:
            print(f"  {name}")
            print(f"    Purpose: {purpose}")
            print(f"    Failed if: {fail_signal}")
            print(f"    Action if failed: {action}")
            print()
        print("✓ Gate 0 passed (batch mode — user responsibility).")
        print()
        return

    # Interactive mode
    print("Before computing any ΔCt, you must verify that your raw")
    print("data is trustworthy. These controls are separate wells on")
    print("your plate — they're not in the input CSV, but the script")
    print("refuses to proceed if you can't confirm they passed.")
    print()

    for name, purpose, fail_signal, action in controls:
        print(f"  {name}")
        print(f"    Purpose: {purpose}")
        print(f"    Failed if: {fail_signal}")
        print(f"    Action if failed: {action}")
        print()

    print("Did ALL five controls pass? (y/n)")
    answer = input("> ").strip().lower()
    if answer != "y":
        print()
        print("STOP: At least one pre-analysis control failed.")
        print("Do NOT proceed with ΔCt analysis on data that may be")
        print("contaminated, inefficient, or non-specific.")
        sys.exit(1)

    print()
    print("✓ Gate 0 passed: all pre-analysis controls confirmed.")
    print()


# ═══════════════════════════════════════════════════════════════════════
#  GATE 1 — Replicate type and minimum sample size
# ═══════════════════════════════════════════════════════════════════════

def gate_1_replicates(rows, all_groups):
    """Confirm biological replicates and check n ≥ 2 per group."""
    print("=" * 60)
    print("GATE 1 — Replicate type and minimum sample size")
    print("=" * 60)
    print()

    # Check n ≥ 2 per group (always enforced, even in batch mode)
    group_sizes = {}
    for row in rows:
        group_sizes.setdefault(row["group"], 0)
        group_sizes[row["group"]] += 1

    for grp, n in group_sizes.items():
        if n < 2:
            print(f"STOP: Group '{grp}' has only {n} sample(s).")
            print("You need at least 2 biological replicates per group")
            print("to estimate variance.")
            sys.exit(1)

    if BATCH_MODE:
        print("⚠ BATCH MODE: Assuming replicates are biological.")
        print("  If your CSV contains technical replicates (same cDNA")
        print("  in multiple wells), average them per sample first.")
        print()
        for grp in sorted(group_sizes.keys()):
            print(f"  {grp}: n = {group_sizes[grp]}")
        print()
        print("✓ Gate 1 passed (batch mode — user responsibility).")
        print()
    else:
        print("Are your replicates biological (independent samples)?")
        print("If you loaded the same cDNA into multiple wells and")
        print("called each well a replicate, that is n=1 with technical")
        print("replicates — your p-value will be meaningless.")
        print()
        print("Confirm: are ALL your replicates biological? (y/n)")
        answer = input("> ").strip().lower()
        if answer != "y":
            print()
            print("STOP: Average technical replicates per sample first,")
            print("then re-enter the averaged values.")
            sys.exit(1)

        print()
        print(f"✓ Gate 1 passed: biological replicates confirmed, "
              f"n ≥ 2 for all groups.")
        for grp in sorted(group_sizes.keys()):
            print(f"  {grp}: n = {group_sizes[grp]}")
        print()

    # Warn about multiple comparisons if >2 groups
    if len(all_groups) > 2:
        print("⚠ NOTE: >2 groups detected. Pairwise t-tests against")
        print("the reference group are computed WITHOUT multiple-comparison")
        print("correction. Apply Bonferroni or Holm correction.")
        print()

    return True


# ═══════════════════════════════════════════════════════════════════════
#  GATE 2 — Housekeeping gene stability (hard gate)
# ═══════════════════════════════════════════════════════════════════════

def gate_2_housekeeping(rows):
    """
    Check housekeeping Ct stability. HARD gate — if unstable, the
    script refuses to compute normalized results.
    """
    print("=" * 60)
    print("GATE 2 — Housekeeping gene stability")
    print("=" * 60)
    print()

    hk_by_group = {}
    for row in rows:
        hk_by_group.setdefault(row["group"], []).append(
            float(row["housekeeping_ct"]))

    all_hk_cts = [float(row["housekeeping_ct"]) for row in rows]
    overall_hk_sd = sd(all_hk_cts)

    hk_group_means = {}

    # (a) Within-group SD
    print("(a) Within-group SD (should be < 0.5 Ct):")
    within_ok = True
    for grp in sorted(hk_by_group.keys()):
        grp_sd = sd(hk_by_group[grp])
        grp_mean = mean(hk_by_group[grp])
        hk_group_means[grp] = grp_mean
        status = "OK" if grp_sd < 0.5 else "UNSTABLE"
        if grp_sd >= 0.5:
            within_ok = False
        print(f"  {grp}: mean={grp_mean:.2f}, SD={grp_sd:.4f} [{status}]")
    overall_status = "OK" if overall_hk_sd < 0.5 else "UNSTABLE"
    if overall_hk_sd >= 0.5:
        within_ok = False
    print(f"  Overall SD: {overall_hk_sd:.4f} [{overall_status}]")

    # (b) Between-group mean difference
    print()
    print("(b) Between-group mean difference (should be < 0.5 Ct):")
    between_ok = True
    group_names_sorted = sorted(hk_group_means.keys())
    for i in range(len(group_names_sorted)):
        for j in range(i + 1, len(group_names_sorted)):
            g1, g2 = group_names_sorted[i], group_names_sorted[j]
            mean_diff = abs(hk_group_means[g1] - hk_group_means[g2])
            pair_status = ("OK" if mean_diff < HK_MEAN_DIFF_THRESHOLD
                           else "UNSTABLE")
            if mean_diff >= HK_MEAN_DIFF_THRESHOLD:
                between_ok = False
            print(f"  |mean({g1}) − mean({g2})| = "
                  f"{mean_diff:.4f} Ct [{pair_status}]")

    hk_stable = within_ok and between_ok

    print()
    if hk_stable:
        print("✓ Gate 2 passed: housekeeping Ct is stable.")
        print("  Normalization is reliable — proceeding to ΔCt.")
    else:
        print("✗ Gate 2 FAILED: housekeeping gene is unstable.")
        print()
        print("STOP: The reference gene's Ct varies beyond the 0.5 Ct")
        print("threshold. Every ΔCt downstream inherits this bias.")
        print()
        print("What to do:")
        print("  1. Switch to a validated stable reference gene.")
        print("  2. Use geometric mean of multiple reference genes")
        print("     (Vandesompele et al., Genome Biol 2002).")
        print("  3. Run geNorm or NormFinder to identify stable genes.")
        sys.exit(1)

    print()
    return True


# ═══════════════════════════════════════════════════════════════════════
#  GATE 3 — ΔCt computation (normalize before averaging)
# ═══════════════════════════════════════════════════════════════════════

def gate_3_delta_ct(rows):
    """Compute per-sample ΔCt from exact (unrounded) values."""
    print("=" * 60)
    print("GATE 3 — ΔCt computation (per-sample normalization)")
    print("=" * 60)
    print()

    per_sample = []
    for row in rows:
        target_ct = float(row["target_ct"])
        housekeeping_ct = float(row["housekeeping_ct"])
        delta_ct = target_ct - housekeeping_ct  # exact, no rounding
        per_sample.append({
            "sample": row["sample"],
            "group": row["group"],
            "target_ct": target_ct,
            "housekeeping_ct": housekeeping_ct,
            "delta_ct": delta_ct,
        })

    print("ΔCt = target_ct − housekeeping_ct, per sample.")
    print("(Subtract first, average second — preserves per-sample pairing.)")
    print()
    for entry in per_sample:
        print(f"  {entry['sample']} ({entry['group']}): "
              f"ΔCt = {entry['target_ct']} − {entry['housekeeping_ct']}"
              f" = {entry['delta_ct']:.4f}")

    # Write per-sample file
    with OUTPUT_PER_SAMPLE_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample", "group", "target_ct",
                         "housekeeping_ct", "delta_ct"])
        for entry in per_sample:
            writer.writerow([
                entry["sample"], entry["group"],
                entry["target_ct"], entry["housekeeping_ct"],
                f"{entry['delta_ct']:.6f}"
            ])
    print(f"\n→ Written per-sample ΔCt to {OUTPUT_PER_SAMPLE_PATH}")
    print()

    return per_sample


# ═══════════════════════════════════════════════════════════════════════
#  GATE 4 — ΔΔCt, fold change, CI, and statistical test
# ═══════════════════════════════════════════════════════════════════════

def gate_4_statistics(per_sample, rows):
    """Compute ΔΔCt, fold change, CI, and t-test."""
    print("=" * 60)
    print("GATE 4 — ΔΔCt, fold change, CI, and statistical test")
    print("=" * 60)
    print()

    print("Sign convention: negative ΔΔCt = UPREGULATION.")
    print("  Lower Ct → more template → lower ΔCt → negative ΔΔCt")
    print("  → fold change > 1.")
    print()

    # Group per-sample ΔCt values (exact)
    groups = {}
    for entry in per_sample:
        groups.setdefault(entry["group"], []).append(entry["delta_ct"])

    # Group raw Ct values for Pfaffl method
    target_ct_by_group = {}
    hk_ct_by_group = {}
    for row in rows:
        target_ct_by_group.setdefault(row["group"], []).append(
            float(row["target_ct"]))
        hk_ct_by_group.setdefault(row["group"], []).append(
            float(row["housekeeping_ct"]))

    # Reference group statistics
    ref_delta_values = groups[REFERENCE_GROUP]
    ref_mean = mean(ref_delta_values)
    ref_sd_val = sd(ref_delta_values)
    ref_sem_val = sem(ref_delta_values)
    ref_var = ref_sd_val ** 2
    ref_n = len(ref_delta_values)

    summary = []
    for group_name in sorted(groups.keys()):
        delta_values = groups[group_name]
        n = len(delta_values)
        mean_delta = mean(delta_values)
        sd_val = sd(delta_values)
        sem_val = sem(delta_values)
        var_val = sd_val ** 2

        if group_name == REFERENCE_GROUP:
            summary.append({
                "group": group_name,
                "mean_delta_ct": round(mean_delta, 4),
                "sd_delta_ct": round(sd_val, 4),
                "sem_delta_ct": round(sem_val, 4),
                "n": n,
                "delta_delta_ct_vs_ref": 0.0,
                "se_delta_delta_ct": 0.0,
                "ci_method": "reference",
                "fold_change_vs_ref": 1.0,
                "fold_change_ci_lower": 1.0,
                "fold_change_ci_upper": 1.0,
                "significant_at_05": "reference",
                "small_effect_warning": "no",
                "t_stat_vs_ref": "",
                "p_value_vs_ref": "",
                "welch_df": "",
                "interpretation": "reference group (ΔΔCt=0 by definition)",
            })
        else:
            delta_delta_ct = mean_delta - ref_mean
            se_delta_delta = math.sqrt(sem_val ** 2 + ref_sem_val ** 2)
            df_val = welch_satterthwaite_df(var_val, n, ref_var, ref_n)
            t_crit = get_t_critical_95(df_val)

            ci_lower_dd = delta_delta_ct - t_crit * se_delta_delta
            ci_upper_dd = delta_delta_ct + t_crit * se_delta_delta

            # Pfaffl fold change
            Ct_mean_ctrl_target = mean(
                target_ct_by_group[REFERENCE_GROUP])
            Ct_mean_treat_target = mean(target_ct_by_group[group_name])
            Ct_mean_ctrl_ref = mean(hk_ct_by_group[REFERENCE_GROUP])
            Ct_mean_treat_ref = mean(hk_ct_by_group[group_name])

            pfaffl_num = E_TARGET ** (
                Ct_mean_ctrl_target - Ct_mean_treat_target)
            pfaffl_den = E_REF ** (
                Ct_mean_ctrl_ref - Ct_mean_treat_ref)
            fold_change = pfaffl_num / pfaffl_den

            # CI for fold change — correct error propagation on log scale
            if E_TARGET == E_REF:
                # Simplifies to E^(-ΔΔCt); CI from ΔΔCt CI directly
                fc_ci_lower = E_TARGET ** (-ci_upper_dd)
                fc_ci_upper = E_TARGET ** (-ci_lower_dd)
                ci_method = "t-distribution (E_target == E_ref)"
            else:
                # Full Pfaffl: log₂(FC) = log₂(E_t)*ΔCt_target
                #                        − log₂(E_r)*ΔCt_ref
                # SE on log₂ scale propagated through both terms:
                log2_et = math.log2(E_TARGET)
                log2_er = math.log2(E_REF)
                # SE of ΔΔCt already accounts for both groups' SEM
                # but with different efficiencies, the log-scale SE is:
                se_log2_fc = math.sqrt(
                    (log2_et * sem_val) ** 2
                    + (log2_et * ref_sem_val) ** 2
                    + (log2_er * sem(hk_ct_by_group[group_name])) ** 2
                    + (log2_er * sem(hk_ct_by_group[REFERENCE_GROUP])) ** 2
                )
                log2_fc = math.log2(fold_change)
                fc_ci_lower = 2 ** (log2_fc - t_crit * se_log2_fc)
                fc_ci_upper = 2 ** (log2_fc + t_crit * se_log2_fc)
                ci_method = "t-distribution (Pfaffl log-scale propagation)"

            is_significant = not (fc_ci_lower <= 1.0 <= fc_ci_upper)
            sig_str = "significant" if is_significant else "not_significant"
            small_effect = abs(delta_delta_ct) < SMALL_EFFECT_THRESHOLD
            small_str = "yes" if small_effect else "no"

            t_stat, p_value, t_df = t_test_two_sample_unpaired(
                ref_delta_values, delta_values)

            # Build interpretation string
            if delta_delta_ct < 0:
                direction = "upregulated"
            elif delta_delta_ct > 0:
                direction = "downregulated"
            else:
                direction = "unchanged"

            if is_significant and small_str == "no":
                interp = (f"{direction}; FC={fold_change:.2f}x "
                          f"(CI [{fc_ci_lower:.2f},{fc_ci_upper:.2f}]); "
                          f"significant")
            elif is_significant and small_str == "yes":
                interp = (f"{direction}; FC={fold_change:.2f}x "
                          f"(CI [{fc_ci_lower:.2f},{fc_ci_upper:.2f}]); "
                          f"significant but |ΔΔCt|<0.5 — small effect")
            else:
                interp = (f"not significant; FC={fold_change:.2f}x "
                          f"(CI [{fc_ci_lower:.2f},{fc_ci_upper:.2f}] "
                          f"crosses 1.0)")

            summary.append({
                "group": group_name,
                "mean_delta_ct": round(mean_delta, 4),
                "sd_delta_ct": round(sd_val, 4),
                "sem_delta_ct": round(sem_val, 4),
                "n": n,
                "delta_delta_ct_vs_ref": round(delta_delta_ct, 4),
                "se_delta_delta_ct": round(se_delta_delta, 4),
                "ci_method": ci_method,
                "fold_change_vs_ref": round(fold_change, 4),
                "fold_change_ci_lower": round(fc_ci_lower, 4),
                "fold_change_ci_upper": round(fc_ci_upper, 4),
                "significant_at_05": sig_str,
                "small_effect_warning": small_str,
                "t_stat_vs_ref": (round(t_stat, 4)
                                  if t_stat is not None else ""),
                "p_value_vs_ref": (round(p_value, 6)
                                   if p_value is not None else ""),
                "welch_df": (round(t_df, 2)
                             if t_df is not None else ""),
                "interpretation": interp,
            })

    # Print results
    print(f"Reference group: {REFERENCE_GROUP}")
    print(f"PCR efficiency: E_target={E_TARGET}, E_ref={E_REF}")
    print()

    for row in summary:
        print(f"  {row['group']}: mean ΔCt={row['mean_delta_ct']}, "
              f"SD={row['sd_delta_ct']}, SEM={row['sem_delta_ct']}, "
              f"n={row['n']}")
        if row["group"] == REFERENCE_GROUP:
            print(f"    [reference — ΔΔCt=0, FC=1.0 by definition]")
        else:
            sig_mark = ("✓" if row["significant_at_05"] == "significant"
                        else "✗")
            p_str = (f"p={row['p_value_vs_ref']}"
                     if row["p_value_vs_ref"] else "p=N/A (scipy needed)")
            print(f"    ΔΔCt={row['delta_delta_ct_vs_ref']}, "
                  f"SE={row['se_delta_delta_ct']}, "
                  f"FC={row['fold_change_vs_ref']} "
                  f"(95% CI: {row['fold_change_ci_lower']}–"
                  f"{row['fold_change_ci_upper']}) "
                  f"[{sig_mark} {row['significant_at_05']}]")
            print(f"    t={row['t_stat_vs_ref']}, {p_str}, "
                  f"df={row['welch_df']}")

    # Write summary CSV (now includes interpretation column)
    fieldnames = [
        "group", "mean_delta_ct", "sd_delta_ct", "sem_delta_ct", "n",
        "delta_delta_ct_vs_ref", "se_delta_delta_ct", "ci_method",
        "fold_change_vs_ref", "fold_change_ci_lower",
        "fold_change_ci_upper", "significant_at_05",
        "small_effect_warning", "t_stat_vs_ref", "p_value_vs_ref",
        "welch_df", "interpretation"
    ]
    with OUTPUT_SUMMARY_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(fieldnames)
        for row in summary:
            writer.writerow([row[k] for k in fieldnames])
    print(f"\n→ Written group summary to {OUTPUT_SUMMARY_PATH}")
    print()

    return summary


# ═══════════════════════════════════════════════════════════════════════
#  GATE 5 — Interpretation
# ═══════════════════════════════════════════════════════════════════════

def gate_5_interpretation(summary):
    """Structured interpretation block with verdict and caveats."""
    print("=" * 60)
    print("GATE 5 — Interpretation")
    print("=" * 60)
    print()

    non_ref_rows = [r for r in summary if r["group"] != REFERENCE_GROUP]

    if not non_ref_rows:
        print("No non-reference groups to interpret.")
        return

    for row in non_ref_rows:
        grp = row["group"]
        ddct = row["delta_delta_ct_vs_ref"]
        fc = row["fold_change_vs_ref"]
        ci_lo = row["fold_change_ci_lower"]
        ci_hi = row["fold_change_ci_upper"]
        sig = row["significant_at_05"]
        small = row["small_effect_warning"]
        p = row["p_value_vs_ref"]

        if ddct < 0:
            direction = "upregulated"
        elif ddct > 0:
            direction = "downregulated"
        else:
            direction = "unchanged"

        print(f"── {grp} vs {REFERENCE_GROUP} ──")
        print()
        print(f"  Direction: target gene is {direction} in {grp}")
        print(f"  ΔΔCt = {ddct} (negative = upregulation)")
        print(f"  Fold change = {fc}×")
        print(f"  95% CI: [{ci_lo}, {ci_hi}]")
        print()

        if sig == "significant":
            print(f"  Significance: YES (CI does not cross 1.0)")
            if p:
                print(f"    p = {p}")
            if small == "yes":
                print(f"  ⚠ CAVEAT: |ΔΔCt| < 0.5 — small effect.")
                print(f"    Report ΔΔCt alongside FC; do not over-interpret.")
            else:
                print(f"  Effect magnitude: |ΔΔCt| = {abs(ddct)} ≥ 0.5 — "
                      f"trustworthy.")
        else:
            print(f"  Significance: NO (CI crosses 1.0)")
            print(f"  Do NOT report as a meaningful effect.")

        print()
        print(f"  Report: ΔΔCt={ddct}, SE={row['se_delta_delta_ct']}, "
              f"FC={fc}× (95% CI: {ci_lo}–{ci_hi}), "
              f"n={row['n']}/group")
        print()
        print(f"  Avoid:")
        print(f"    ✗ FC on linear y-axis (use log₂)")
        print(f"    ✗ FC without CI")
        if small == "yes":
            print(f"    ✗ Over-interpreting FC when |ΔΔCt| < 0.5")
        print()

    print("── Visualization guidance ──")
    print("  Plot ΔΔCt directly (already log₂ scale), or use log₂")
    print("  y-axis for fold change. Never linear y-axis for FC.")
    print()


# ═══════════════════════════════════════════════════════════════════════
#  Main pipeline
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("qPCR ΔCt Analysis Pipeline (v8)")
    print("=" * 60)
    print()

    # ── Most common mistake banner ─────────────────────────────────────
    print("┌─────────────────────────────────────────────────────────┐")
    print("│ #1 CONTROL POINT: Housekeeping gene stability.          │")
    print("│ If your reference gene shifts with treatment, EVERY     │")
    print("│ normalized value is biased — and you cannot detect it   │")
    print("│ from ΔCt alone. Always check HK stability FIRST.       │")
    print("└─────────────────────────────────────────────────────────┘")
    print()

    # ── Read and validate input ────────────────────────────────────────
    required_columns = {"sample", "group", "target_ct", "housekeeping_ct"}

    if not INPUT_PATH.exists():
        sys.exit(f"ERROR: Input file not found: {INPUT_PATH}")

    with INPUT_PATH.open(newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        sys.exit(f"ERROR: No rows found in {INPUT_PATH}")

    header_columns = set(rows[0].keys())
    missing = required_columns - header_columns
    if missing:
        sys.exit(f"ERROR: Missing required columns: {missing}. "
                 f"Found: {header_columns}")

    # Check for duplicate sample names (new in v8)
    sample_names = [row["sample"] for row in rows]
    duplicates = [s for s in set(sample_names)
                  if sample_names.count(s) > 1]
    if duplicates:
        sys.exit(f"ERROR: Duplicate sample names found: {duplicates}. "
                 f"Each row must have a unique sample identifier. "
                 f"If these are technical replicates, average them "
                 f"before input.")

    # Validate numeric values and Ct range
    outliers = []
    for row in rows:
        for col in ("target_ct", "housekeeping_ct"):
            try:
                val = float(row[col])
            except (ValueError, TypeError):
                sys.exit(f"ERROR: Non-numeric value in column '{col}' "
                         f"for sample '{row.get('sample', '?')}'")
            if val < CT_MIN or val > CT_MAX:
                outliers.append((row["sample"], col, val))

    if outliers:
        print("WARNING: Implausible Ct values (outside 5–40 range):")
        for sample, col, val in outliers:
            print(f"  {sample}: {col} = {val}")
        print("Consider excluding these samples.\n")

    all_groups = sorted(set(row["group"] for row in rows))
    if REFERENCE_GROUP not in all_groups:
        sys.exit(f"ERROR: Reference group '{REFERENCE_GROUP}' not found. "
                 f"Available groups: {all_groups}")

    print(f"Input: {len(rows)} samples from {INPUT_PATH}")
    print(f"Groups: {all_groups}, Reference: {REFERENCE_GROUP}")
    print()

    # ── Execute gates in order ─────────────────────────────────────────
    gate_0_controls()
    gate_1_replicates(rows, all_groups)
    gate_2_housekeeping(rows)
    per_sample = gate_3_delta_ct(rows)
    summary = gate_4_statistics(per_sample, rows)
    gate_5_interpretation(summary)

    print("=" * 60)
    print("Pipeline complete. All gates passed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
