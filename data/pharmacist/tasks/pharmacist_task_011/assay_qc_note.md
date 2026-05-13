# Assay QC Note — CCK-8 Dose-Exploration Round 1 → Round 2

---

## Main Risk

**Replicate imbalance at the high-dose end compounds with systematic edge-row exposure across the entire dataset.**

1. **Singleton high-dose points.** 3 µM (B11, n = 1) and 10 µM (B12, n = 1) have no variance estimate. These two concentrations bracket the estimated IC₅₀ (~4.5 µM) and define the curve's inflection zone. Any IC₅₀ derived from them is a point estimate with no confidence interval. [Layout+CSV]

2. **All data in edge rows.** The entire Round 1 dataset occupies only rows A–B (the two top-edge rows of the 96-well plate), where evaporation and temperature gradients are strongest. The blanks at A1–A2 / B1–B2 (CV 2.09%) show no gross artifact, but they sit at the same edge and cannot serve as an interior reference to detect a row-wide systematic shift. Row-A-vs-row-B comparison shows a consistent −0.005 OD offset for UT and DMSO (row B lower), which is within noise but cannot be distinguished from a mild gradient because there is no interior-row comparator. [Layout+CSV]

3. **Outer-column dose placement.** 0.3 µM occupies A11–A12 (outer-edge columns); 3 µM sits at B11; 10 µM at B12. Edge evaporation preferentially elevates OD in peripheral wells, which would inflate apparent viability at 0.3 µM and reduce confidence in the 3 µM and 10 µM singletons. [Layout]

4. **10 µM near the positive-control floor.** The 10 µM singleton (BC OD 0.236) sits only 0.027 OD above the Pos BC mean (0.209) — 3.4% of the blank-corrected assay window, or 3.15 Pos-SDs apart. With proper replicates and normal biological variance, these distributions could overlap, meaning the apparent near-complete kill at 10 µM may be statistically indistinguishable from the positive-control floor. [CSV]

5. **Prior-draft blank-correction omission (now fixed).** The standard CCK-8 formula is Viability (%) = (OD_sample − OD_blank) / (OD_DMSO − OD_blank) × 100. An earlier draft omitted blank subtraction, inflating all viability values. Corrected values shift meaningfully at the high-dose end: 10 µM drops from 35.8% (uncorrected) to 29.3% (blank-corrected); IC₅₀ shifts from ~5.5 µM to ~4.5 µM. [CSV]

**Net assessment:** The dose–response trend is real (monotonic decline, Z′ = 0.93, solvent gap only 3.0%), but the IC₅₀ estimate rests on two unreplicated edge-position singletons. Round 2 must confirm the 1–10 µM zone with n ≥ 3 in interior wells before any curve fitting is credible. [Brief+Layout+CSV]

---

## Dose Interpretation Table

All values blank-corrected (Blank mean = 0.082 OD, n = 4, CV = 2.09%). Viability normalized to DMSO BC mean (0.806 OD, n = 4, CV = 0.68%).

| Dose | Evidence Weight | Observed Signal | Action | Source |
|------|----------------|-----------------|--------|--------|
| 0.1 µM | Moderate — n = 2, row A cols 9–10 (near-edge) | BC OD 0.775; viability 96.2% (SD 0.97%); reduction 3.8% | Retain as upper-plateau anchor; carry into Round 2 at n = 3 in interior wells | [Brief+Layout+CSV] |
| 0.3 µM | Moderate, edge-flagged — n = 2, row A cols 11–12 (outer edge) | BC OD 0.726; viability 90.1% (SD 0.61%); reduction 9.9% | First detectable step-down; outer-column position may inflate OD → true reduction possibly larger; replicate in interior | [Brief+Layout+CSV] |
| 1 µM | Moderate — n = 2, row B cols 9–10 (near-edge) | BC OD 0.653; viability 81.1% (SD 1.58%); reduction 18.9% | Most informative duplicated point; marks curve steepening; within-pair CV acceptable | [Brief+Layout+CSV] |
| 3 µM | Low — singleton n = 1, B11 (near-edge col 11) | BC OD 0.489; viability 60.7%; reduction 39.3% | No variance estimate; do not weight equally in curve fitting; must replicate at n ≥ 3 | [Brief+Layout+CSV] |
| 10 µM | Low — singleton n = 1, B12 (outer-edge col 12); 0.027 OD above Pos floor | BC OD 0.236; viability 29.3%; reduction 70.7%; 3.15 Pos-SDs above Pos mean | May overlap Pos floor with replicates; confirm separability before using as curve anchor | [Brief+Layout+CSV] |

**Controls summary:**

| Group | n | BC Mean OD | CV | Wells | Note |
|-------|---|-----------|-----|-------|------|
| Blank | 4 | — (raw 0.082) | 2.09% | A1–A2, B1–B2 | Acceptable |
| UT | 4 | 0.830 | 1.01% | A3–A4, B3–B4 | — |
| DMSO | 4 | 0.806 | 0.68% | A5–A6, B5–B6 | Normalization denominator |
| Pos | 4 | 0.209 | 4.14% | A7–A8, B7–B8 | Highest CV; still acceptable |

- **Solvent effect:** UT-vs-DMSO gap = 3.01% — within the 5% threshold. DMSO at 0.1% is not confounding. [CSV]
- **Z′ factor:** 0.93 — excellent (threshold ≥ 0.5). [CSV]
- **IC₅₀ estimate:** ~4.5 µM by log-linear interpolation between 3 µM (60.7%) and 10 µM (29.3%). Treat as provisional — both anchor points are singletons. [CSV]

---

## Refine Range

**Round 2 concentrations:** 0.1, 0.3, 1, 2, 3, 5, 7, 10 µM — 8 doses × n = 3 = 24 dose wells.

- 0.1 and 0.3 µM: retained as upper-plateau anchors (Round 1 confirmed minimal effect). [Brief+CSV]
- 2, 5, 7 µM: new points that densify the 1–10 µM inflection zone where the IC₅₀ sits. [CSV]
- 1, 3, 10 µM: carried forward for direct Round 1 → Round 2 comparison. [Brief+CSV]

If Round 2 shows 10 µM is inseparable from Pos (see First Optimization Variable), extend to 15 and 20 µM in Round 3. [CSV]

---

## Round 2 Executable Workflow

### Step 1 — Seed cells (Day 0, afternoon)

1. Trypsinize MDA-MB-231 cells at ~80% confluence. Count with hemocytometer or automated counter.
2. Adjust to 5 × 10⁴ cells/mL in complete medium (DMEM + 10% FBS + 1% pen-strep).
3. Pipette **100 µL cell suspension** (= 5,000 cells) into every well that will contain cells (see plate map below). Use a multichannel pipette, column by column, to minimize seeding time variation.
4. Pipette **200 µL complete medium** (no cells) into blank wells (C9, C10, F9, F10 for interior blanks; A1, A2, A11, A12 for edge sentinels).
5. Leave rows B and H, and columns 1–2 / 11–12 (except designated blanks) empty — fill with **200 µL sterile PBS** to serve as an evaporation moat.
6. Incubate overnight (37 °C, 5% CO₂, humidified) for attachment.

### Step 2 — Prepare dosing solutions (Day 1, morning)

**Stock:** 10 mM formulation A in DMSO (store at −20 °C; thaw at RT, vortex briefly).

**Intermediate A (1 mM):** 100 µL stock + 900 µL complete medium. Vortex. DMSO = 10%.

**Intermediate B (100 µM):** 100 µL Intermediate A + 900 µL complete medium. Vortex. DMSO = 1%.

**2× working solutions** (prepare 500 µL each in labelled tubes):

| Final conc. | 2× conc. | Source | Intermediate (µL) | Medium (µL) | DMSO in well |
|-------------|----------|--------|-------------------|-------------|-------------|
| 0.1 µM | 0.2 µM | Inter B (100 µM) | 1.0 | 499.0 | 0.001% |
| 0.3 µM | 0.6 µM | Inter B (100 µM) | 3.0 | 497.0 | 0.003% |
| 1 µM | 2 µM | Inter A (1 mM) | 1.0 | 499.0 | 0.010% |
| 2 µM | 4 µM | Inter A (1 mM) | 2.0 | 498.0 | 0.020% |
| 3 µM | 6 µM | Inter A (1 mM) | 3.0 | 497.0 | 0.030% |
| 5 µM | 10 µM | Inter A (1 mM) | 5.0 | 495.0 | 0.050% |
| 7 µM | 14 µM | Inter A (1 mM) | 7.0 | 493.0 | 0.070% |
| 10 µM | 20 µM | Inter A (1 mM) | 10.0 | 490.0 | 0.100% |

**DMSO vehicle control (2×, 0.2% DMSO):** 1 µL pure DMSO + 499 µL medium. This matches the highest DMSO load (10 µM well = 0.1%).

**UT control:** plain complete medium (no DMSO).

**Positive control:** prepare at 2× in medium. (Use the same agent and concentration as Round 1 — record identity and lot number.)

### Step 3 — Treat cells (Day 1, morning)

1. Remove plate from incubator. Check cells under microscope — confirm attachment and ~30–40% confluence.
2. **Do not aspirate** the existing 100 µL medium. Add 100 µL of each 2× working solution directly on top (final volume = 200 µL/well, final concentration = 1×). This avoids cell loss from aspiration.
3. Dose in this order to minimize cross-contamination: Blanks (skip — already filled) → UT → DMSO → lowest dose → … → highest dose → Pos.
4. Return plate to incubator. Start 24 h timer.

### Step 4 — Round 2 plate map

```
        Col1   Col2   Col3   Col4   Col5   Col6   Col7   Col8   Col9   Col10  Col11  Col12
Row A   Blk-E  Blk-E   —      —      —      —      —      —      —      —    Blk-E  Blk-E
Row B   [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]
Row C    —      —      UT     UT    DMSO   DMSO    Pos    Pos   Blk-I  Blk-I   —      —
Row D    —      —     0.1    0.3     1      2      3      5      7      10     —      —
Row E    —      —     0.1    0.3     1      2      3      5      7      10     —      —
Row F    —      —     0.1    0.3     1      2      3      5      7      10     —      —
Row G    —      —      UT     UT    DMSO   DMSO    Pos    Pos   Blk-I  Blk-I   —      —
Row H   [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]  [PBS]
```

- **Blk-E** = edge-sentinel blanks (medium only, no cells) — compare outer vs inner to detect evaporation.
- **Blk-I** = interior blanks (medium only, no cells) — used for blank correction.
- **[PBS]** = sterile PBS moat (no cells, no medium) — evaporation buffer.
- **—** = empty well.
- Dose labels are final concentrations in µM.
- Controls are split into two spatial blocks (row C upper-interior, row G lower-interior) to detect plate-wide gradients.
- All dose replicates (rows D–F) are in the plate interior (rows 4–6 of 8, cols 3–10 of 12).

**Well counts:** UT = 4, DMSO = 4, Pos = 4, Blk-I = 4, Blk-E = 4, dose = 24. Total seeded = 36. Total filled = 44 + PBS moat.

### Step 5 — CCK-8 readout (Day 2, morning, 24 h post-treatment)

1. Prepare CCK-8 reagent: warm to RT (protect from light). Calculate volume: 44 wells × 10 µL = 440 µL + 20% dead volume = 530 µL.
2. Add **10 µL CCK-8 reagent** to every well containing medium (including blanks). Do not add to PBS moat wells.
3. Incubate **1–2 h** at 37 °C (protect from light). Check color development at 1 h — if DMSO wells are pale orange, extend to 2 h; if deep orange, read at 1 h.
4. Read absorbance at **450 nm** (reference wavelength 650 nm if available). Record incubation time.
5. Export raw OD values as CSV with well ID, group label, and OD450.

### Step 6 — QC gate (before any viability calculation)

Run these checks in order. If any fails, stop and follow the action column.

| # | Check | Pass criterion | Action if fail |
|---|-------|---------------|----------------|
| 1 | Blank-I CV | ≤ 5% | Inspect plate for contamination or bubbles; rerun if systematic |
| 2 | Edge blank drift | \|mean(Blk-E) − mean(Blk-I)\| ≤ 0.010 OD | Edge evaporation confirmed; do not pool Round 1 edge-row data; use Round 2 interior data only |
| 3 | Z′ factor (DMSO vs Pos, blank-corrected) | ≥ 0.5 | Assay window too noisy; rerun with fresh cells and humidity check |
| 4 | UT-vs-DMSO gap | ≤ 5% | Solvent toxicity; reduce DMSO or re-match vehicle |
| 5 | Control block gradient | \|mean(row C controls) − mean(row G controls)\| ≤ 0.015 OD per group | Plate-wide gradient detected; flag but proceed if Z′ still passes |
| 6 | 10 µM vs Pos separability | Gap ≥ 2 Pos-SDs (both n ≥ 3) | See First Optimization Variable below |

### Step 7 — Calculate viability and compare rounds

**Blank correction:** Subtract mean(Blk-I) from all cell-containing wells. (Do not use Blk-E for correction — they are sentinels only.)

**Viability:** Viability (%) = (OD_sample − OD_blank) / (OD_DMSO − OD_blank) × 100.

**Round 1 → Round 2 comparison at shared doses (0.1, 0.3, 1 µM):**

| Metric | Threshold | Interpretation |
|--------|-----------|----------------|
| Relative shift per dose | ≤ 10% | Rounds are consistent; may pool for curve fitting |
| Relative shift per dose | > 10% | Systematic inter-round difference; use Round 2 only |

**Round 1 singletons (3, 10 µM):**

| Metric | Threshold | Interpretation |
|--------|-----------|----------------|
| Round 2 mean within ± 15% of Round 1 singleton | Yes | Round 1 value was in the right ballpark; note but do not pool |
| Round 2 mean outside ± 15% | — | Expected given n = 1 + edge position; discard Round 1 values entirely |

**IC₅₀ fitting (only after QC gate passes):**
- Fit 4-parameter logistic (Hill equation) on 8 doses × n = 3 using Round 2 data.
- Report IC₅₀ with 95% CI.
- Compare to Round 1 provisional estimate (~4.5 µM).
- If 10 µM is not separable from Pos, constrain the curve bottom to Pos BC mean and note the constraint.

---

## Rerun Trigger

| # | Condition | Threshold | Decision |
|---|-----------|-----------|----------|
| 1 | Blank OD drift | Mean > 0.10 OD or CV > 5% | Full rerun — plate-level instability |
| 2 | Z′ factor | < 0.5 | Full rerun — assay window too noisy |
| 3 | UT-vs-DMSO gap | > 5% | Full rerun — solvent confounding |
| 4 | Edge blank drift | \|Blk-E − Blk-I\| > 0.010 OD | Confirms Round 1 edge artifact; discard Round 1 singletons; use Round 2 as authoritative |
| 5 | Inter-round drift, shared doses | > 10% relative | Do not pool rounds; use Round 2 standalone |
| 6 | Inter-round drift, singleton doses | > 15% relative | Discard Round 1 singleton values |
| 7 | 10 µM not separable from Pos | Gap < 2 Pos-SDs | Redefine floor as Pos; refit curve with constrained bottom; add 15/20 µM in Round 3 |

**Decision after trigger fires:**
- Triggers 1–3: full plate rerun with fresh cells and incubator humidity check.
- Trigger 4: Round 1 edge data unreliable — use Round 2 as sole dataset.
- Triggers 5–6: do not pool rounds; report Round 2 independently.
- Trigger 7: proceed with curve fitting using DMSO→Pos window; add 15/20 µM in Round 3 to find a true bottom.

---

## First Optimization Variable

**Confirm whether 10 µM is statistically separable from the positive-control floor.**

This single comparison determines whether the dose–response curve has a true bottom anchor or an ambiguous floor — and must precede any IC₅₀ curve fitting.

Current state: the 10 µM singleton (BC OD 0.236) sits 0.027 OD above Pos (BC mean 0.209), which is 3.15 Pos-SDs — nominally separable, but based on n = 1 vs n = 4 with no within-group variance at 10 µM. A single outlier replicate could collapse this gap. [CSV]

**Round 2 decision rule (10 µM n = 3 vs Pos n = 4, both blank-corrected):**

| Outcome | Criterion | Action |
|---------|-----------|--------|
| Clearly separable | Gap ≥ 3 Pos-SDs and p < 0.05 (Welch's t-test) | 10 µM is a valid bottom anchor; fit 4PL across 0.1–10 µM |
| Marginally separable | 2–3 Pos-SDs or p = 0.05–0.10 | Flag 10 µM as near-floor; fit curve but report IC₅₀ with wide CI; consider 15 µM in Round 3 |
| Not separable | < 2 Pos-SDs or p > 0.10 | Redefine floor as Pos BC mean; constrain curve bottom; fit 0.1–7 µM only; add 15/20 µM in Round 3 |

Until this is resolved, the IC₅₀ estimate of ~4.5 µM carries unquantified uncertainty in its lower asymptote. No confirmatory experiment or dense-spacing refinement should proceed before this variable is locked down.
