# qPCR Analysis Workflow — v8

> **The single easiest way to get wrong qPCR results:** an unstable housekeeping gene. If your reference gene's expression shifts with treatment, every normalized value inherits a systematic bias — and nothing downstream can detect or correct it. That's why this pipeline checks housekeeping stability *before* computing any ΔCt.

---

## How the pipeline works

The script runs six gates in order. Each gate either passes or stops the analysis. No step proceeds if a prior gate has failed. The point is to prevent the most common failure mode: computing precise numbers on bad data and then reporting them as if they were trustworthy.

The gates follow the order you'd actually encounter when processing a qPCR experiment:

| Gate | Question it answers | If the answer is bad |
|------|--------------------|-----------------------|
| 0 | Were my plate controls clean? | Stop — data may be contaminated or non-specific |
| 1 | Are my replicates real (biological), and do I have enough? | Stop — statistics would be meaningless |
| 2 | Is my housekeeping gene stable across groups? | Stop — every normalized value would be biased |
| 3 | What is each sample's ΔCt? | Computation step (per-sample normalization) |
| 4 | How big is the difference between groups, and can I trust it? | Computation step (ΔΔCt, fold change, CI, t-test) |
| 5 | What does this mean in plain language? | Output step (structured verdict) |

---

## Gate 0 — Were my plate controls clean?

Before touching any Ct numbers, you need to know whether the data is trustworthy at all. The script checks five controls. These are separate wells on your plate — they're not in the input CSV, but the pipeline refuses to proceed unless you confirm they passed.

**What each control catches, in the order you'd notice problems:**

1. **NTC (no-template control)** — You ran a well with primers but no template. If it amplified (Ct < 35), something is contaminated: primer-dimers, reagent carryover, or aerosol contamination. Fix: redesign primers or replace reagents.

2. **No-RT control** — You ran a well with RNA but skipped reverse transcription. If it amplified, your RNA prep contains genomic DNA, and your "mRNA" signal is partly DNA. Fix: DNase treatment, or design primers that span an exon-exon junction so genomic DNA can't amplify.

3. **Standard curve / efficiency** — You ran a dilution series for each primer set. The slope of log(dilution) vs Ct should be between −3.1 and −3.6, corresponding to 90–110% amplification efficiency. Outside that range, your Ct values don't scale linearly with template amount, and the 2^(−ΔΔCt) formula breaks down. Fix: re-optimize primers. If efficiency is measurably different from 100% but reproducible, the Pfaffl method (used in Gate 4) can compensate.

4. **Melt curve** — After amplification, you ramped the temperature and watched fluorescence drop. A single sharp peak means one product; multiple peaks or a broad shoulder means your primers are amplifying more than one thing. Fix: redesign primers, confirm by gel electrophoresis.

5. **Positive control** — You ran a well with a known template that should amplify. If it didn't (or Ct was far higher than expected), the assay itself isn't working — bad reagents, wrong thermocycler program, or degraded template.

**Batch mode:** When `BATCH_MODE = True`, the script assumes all five passed and prints a reminder that you're responsible for having checked. When `False`, it prompts interactively and stops if you say any control failed.

---

## Gate 1 — Are my replicates real, and do I have enough?

Now the script looks at the CSV and counts how many samples are in each group.

**Why this matters before any computation:** If your three "replicates" are actually the same cDNA pipetted into three wells, you have n=1 with technical replicates. The SD you'd compute reflects pipetting noise, not biological variability. Your p-value would be meaningless — it would tell you "the pipetting was consistent," not "the treatment had an effect."

The script enforces two things:

1. **n ≥ 2 per group** (always, even in batch mode). With n=1, SD=0, SEM=0, and the confidence interval has zero width. That doesn't mean "no uncertainty" — it means "cannot estimate uncertainty."

2. **Confirmation that replicates are biological** (interactive mode) or a banner reminder (batch mode).

For the example data:
- control: n = 3 ✓
- treatment: n = 3 ✓

If >2 groups are present, the script also warns that pairwise t-tests are computed without multiple-comparison correction — you'd need Bonferroni or Holm on top.

---

## Gate 2 — Is my housekeeping gene stable?

This is a **hard gate**: if the housekeeping gene is unstable, the script refuses to compute any normalized results. The reason is simple — ΔCt is defined as (target Ct − housekeeping Ct), so if the housekeeping Ct shifts between groups, every ΔCt inherits that shift as a systematic bias. And unlike random noise, systematic bias doesn't average out with more replicates.

The script checks two things, in order:

**(a) Within-group SD (threshold: < 0.5 Ct).** This catches a noisy reference gene — high replicate-to-replicate variation within the same condition. For the example data:

| Group | HK mean Ct | HK SD | Verdict |
|-------|-----------|-------|---------|
| control | 18.10 | 0.10 | OK — low noise |
| treatment | 18.10 | 0.10 | OK — low noise |
| Overall | 18.10 | 0.09 | OK |

**(b) Between-group mean difference (threshold: < 0.5 Ct).** This catches the more dangerous problem: the treatment itself shifting the housekeeping gene. Within-group SD can be small while the group means are different — that's a stable-looking gene that's actually treatment-responsive.

| Comparison | |mean difference| | Verdict |
|-----------|-------------------|---------|
| control vs treatment | 0.00 Ct | OK — treatment didn't shift HK |

Both checks pass → normalization is reliable → proceed to ΔCt.

**If Gate 2 fails:** Don't just pick a different threshold. The data is telling you this gene isn't a valid normalizer for this experiment. Options: (1) switch to a validated stable reference gene, (2) use the geometric mean of multiple reference genes (Vandesompele et al., Genome Biol 2002), or (3) run geNorm or NormFinder to identify which of your candidate genes is most stable.

---

## Gate 3 — Compute each sample's ΔCt

Now the script computes the first real number: **ΔCt = target Ct − housekeeping Ct**, for each sample individually.

The key decision here is **subtract first, average second** (not the other way around). Why? Each sample's target and housekeeping Ct were measured from the same cDNA. That pairing is informative — if one sample had slightly more template loaded, both its target and housekeeping Ct shift together, and the subtraction cancels the loading difference. If you average raw Ct across samples first and then subtract, you lose that per-sample pairing, and the result is biased whenever housekeeping Ct varies across replicates.

For the example data:

| Sample | Group | Target Ct | HK Ct | ΔCt (= target − HK) |
|--------|-------|-----------|-------|---------------------|
| Ctrl_1 | control | 24.8 | 18.1 | 6.70 |
| Ctrl_2 | control | 25.0 | 18.0 | 7.00 |
| Ctrl_3 | control | 24.7 | 18.2 | 6.50 |
| Treat_1 | treatment | 22.9 | 18.1 | 4.80 |
| Treat_2 | treatment | 23.1 | 18.0 | 5.10 |
| Treat_3 | treatment | 22.8 | 18.2 | 4.60 |

Notice that the treatment samples have lower ΔCt (4.6–5.1) than control (6.5–7.0). Lower ΔCt means the target gene's Ct is closer to the housekeeping gene's Ct, which means there's relatively more target mRNA. That's the first hint of upregulation — but we haven't quantified it or tested it yet.

The script stores these values at full precision internally and rounds only at CSV output, to avoid rounding errors propagating into the statistics.

**Output:** `per_sample_delta_ct.csv`

---

## Gate 4 — How big is the difference, and can I trust it?

This is where the per-sample ΔCt values get aggregated into a group comparison. The gate proceeds in four sub-steps, each building on the previous one.

### Step 4a — Summarize each group

First, compute the mean, SD, and SEM of ΔCt within each group:

| Group | Mean ΔCt | SD | SEM | n |
|-------|----------|----|-----|---|
| control | 6.7333 | 0.2517 | 0.1453 | 3 |
| treatment | 4.8333 | 0.2517 | 0.1453 | 3 |

The treatment group's mean ΔCt is about 1.9 units lower than control. But how confident are we in that difference?

### Step 4b — Compute ΔΔCt (the difference of differences)

ΔΔCt = mean ΔCt(treatment) − mean ΔCt(control) = 4.8333 − 6.7333 = **−1.9000**

**Sign convention:** Negative ΔΔCt means the target gene is *upregulated* in the treatment group. The logic chain: treatment has lower target Ct → more target mRNA → lower ΔCt → negative ΔΔCt → fold change > 1. Quick sanity check: if ΔΔCt is negative, fold change must be > 1.

### Step 4c — Convert to fold change

ΔΔCt is on a log₂ scale (because each PCR cycle doubles the product). To get a fold change that's easier to interpret:

- **When both primer sets have ~100% efficiency** (E_target = E_ref = 2.0, the standard assumption): FC = 2^(−ΔΔCt) = 2^(1.9) = **3.73×**. The target gene has ~3.7 times more mRNA in treatment than control.

- **When efficiencies differ** (e.g., E_target = 1.95, E_ref = 2.05 — measured from your standard curves in Gate 0): the script uses the Pfaffl formula, which accounts for each gene's actual doubling rate:

  FC = E_target^(Ct_ctrl_target − Ct_treat_target) / E_ref^(Ct_ctrl_ref − Ct_treat_ref)

  For the example data with E=2.0 for both, this gives the same 3.73×.

### Step 4d — Confidence interval and significance test

A fold change without a confidence interval is just a point estimate — it tells you the best guess but not how uncertain that guess is. The script builds the CI in three steps:

1. **SE of ΔΔCt.** Since ΔΔCt is the difference of two group means, its standard error combines both groups' SEMs: SE(ΔΔCt) = √(SEM_treatment² + SEM_control²) = √(0.1453² + 0.1453²) = **0.2055**

2. **Degrees of freedom and critical value.** With only n=3 per group, the normal approximation (z = 1.96) would understate uncertainty by about 42%. The script uses the t-distribution with Welch-Satterthwaite degrees of freedom, which accounts for small sample sizes and potentially unequal variances:
   - df = 4.0 (Welch-Satterthwaite)
   - t critical (two-tailed, α=0.05) = 2.776

3. **CI on the ΔΔCt scale, then convert to fold change.**
   - 95% CI for ΔΔCt: −1.9 ± 2.776 × 0.2055 = **[−2.47, −1.33]**
   - Convert each bound: FC = 2^(−ΔΔCt), so CI for FC = [2^1.33, 2^2.47] = **[2.51, 5.54]**

   When E_target ≠ E_ref, the CI conversion is more involved: the script propagates uncertainty on the log₂ scale through both efficiency terms separately, then exponentiates. When E_target = E_ref, this simplifies to the formula above.

**Significance decision:** The fold-change CI [2.51, 5.54] does not cross 1.0, so the difference is **significant at α = 0.05**. The Welch t-test gives t = 9.25, df = 4.0 (p-value requires scipy; if unavailable, the CI-based decision still holds).

**Effect size check:** |ΔΔCt| = 1.9, which is well above the 0.5 threshold. A ΔΔCt of 0.3 might be "statistically significant" with enough replicates but biologically trivial — the script flags any |ΔΔCt| < 0.5 as a small-effect warning.

**Reference group:** ΔΔCt = 0, SE = 0, FC = 1.0, CI = [1.0, 1.0] by definition. (An earlier version of the script computed a non-zero SE for the reference group by comparing it to itself — that was a bug fixed in v4.)

**Output:** `delta_ct_summary.csv` (now includes an `interpretation` column with a machine-readable one-line verdict per group).

---

## Gate 5 — What does this mean?

The final gate translates the numbers into a structured verdict. For the example data:

```
treatment vs control:
  Direction:    target gene is upregulated in treatment
  ΔΔCt:        −1.9 (negative = upregulation)
  Fold change:  3.73×
  95% CI:       [2.51, 5.54]
  Significant:  YES — CI does not cross 1.0
  Effect size:  |ΔΔCt| = 1.9 ≥ 0.5 — trustworthy magnitude

  How to report:
    ΔΔCt = −1.9, SE = 0.2055, FC = 3.73× (95% CI: 2.51–5.54), n = 3/group

  What to avoid:
    ✗ Plotting fold change on a linear y-axis (use log₂ — ΔΔCt is already log₂)
    ✗ Reporting fold change without a confidence interval
```

The `interpretation` column in `delta_ct_summary.csv` contains a condensed version:
`"upregulated; FC=3.73x (CI [2.51,5.54]); significant"`

---

## Common mistakes the pipeline catches

These are ordered by the gate that catches them, which is also roughly the order in which they'd corrupt your results (earliest = most damaging):

| Gate | Mistake | How the script handles it |
|------|---------|--------------------------|
| Input | Duplicate sample names | Hard exit with error message |
| 0 | Skipping NTC / no-RT / efficiency / melt / positive controls | Requires confirmation or batch-mode banner |
| 1 | Treating technical replicates as biological | Requires confirmation or batch-mode banner |
| 1 | n < 2 per group (can't estimate variance) | Hard exit |
| 1 | >2 groups without multiple-comparison correction | Warning printed |
| 2 | Housekeeping gene noisy within groups (SD ≥ 0.5) | Hard exit |
| 2 | Housekeeping gene shifted between groups (mean diff ≥ 0.5) | Hard exit |
| 3 | Averaging raw Ct across samples before subtracting (loses pairing) | Script always computes per-sample ΔCt first |
| 3 | Rounding ΔCt before statistics (propagates rounding error) | Exact values internally, round only at output |
| 4 | Using z = 1.96 for CI with small n | Uses t-distribution with Welch df |
| 4 | Using 2^(−ΔΔCt) when primer efficiencies differ | Full Pfaffl formula with log-scale CI propagation |
| 4 | Computing non-zero SE/CI for the reference group | Hardcoded to SE=0, FC=1.0, CI=[1,1] |
| 5 | Over-interpreting a small |ΔΔCt| (< 0.5) as biologically meaningful | Flagged with warning |
| 5 | Reporting fold change without CI or on a linear y-axis | Interpretation block says "avoid" |

---

## Running the script

```bash
# Default: batch mode (no interactive prompts)
python analyze_qpcr.py

# To require interactive confirmation of controls and replicate type:
# Edit the script and set BATCH_MODE = False
```

**Configuration** (top of `analyze_qpcr.py`):

| Variable | Default | What it controls |
|----------|---------|-----------------|
| `INPUT_PATH` | `qpcr_ct_example.csv` | Input CSV file |
| `REFERENCE_GROUP` | `"control"` | Which group is the baseline for ΔΔCt |
| `E_TARGET` | `2.0` | Target gene primer efficiency (from standard curve) |
| `E_REF` | `2.0` | Reference gene primer efficiency |
| `BATCH_MODE` | `True` | Skip interactive prompts (Gates 0 & 1) |
| `SMALL_EFFECT_THRESHOLD` | `0.5` | |ΔΔCt| below this triggers a warning |
| `HK_MEAN_DIFF_THRESHOLD` | `0.5` | Between-group HK mean diff above this fails Gate 2 |

**Output files:**

| File | Contents |
|------|----------|
| `per_sample_delta_ct.csv` | One row per sample: sample, group, target Ct, HK Ct, ΔCt |
| `delta_ct_summary.csv` | One row per group: mean ΔCt, SD, SEM, n, ΔΔCt, SE, fold change, CI, significance, interpretation |

---

## Version history

| Version | What changed |
|---------|-------------|
| v1 | Original flawed draft |
| v2 | Added t-test, Pfaffl, CI, validation, file output |
| v3 | Added Welch's t-test; **bug**: non-zero SE for reference group |
| v4 | Fixed reference-group bug; added HK check; **bug**: z=1.96 CI |
| v5 | Fixed z→t CI; full Pfaffl; **bug**: rounded ΔCt before stats |
| v6 | Fixed rounding; n<2 guard; **gap**: controls only in doc; HK instability was warning not gate; no interpretation |
| v7 | Gate-based pipeline with hard gates; added Gate 0 (controls), Gate 1 (replicates), Gate 2 (HK hard gate), Gate 5 (interpretation) |
| v8 | Batch mode; machine-readable interpretation column; correct Pfaffl CI propagation on log₂ scale; duplicate sample name check; narrative-order workflow doc |
