# Clinical Study Breakdown

**Study:** Yanai et al., "Phase II study of sequential S-1 and cyclophosphamide therapy in patients with metastatic breast cancer," *BMC Cancer* (2020) 20:1068. DOI: 10.1186/s12885-020-07550-5.

---

## Workflow

### Study Design
| Aspect | Detail | Source |
|---|---|---|
| **Phase** | Phase II | Title; Methods (p.2) |
| **Design** | Single-arm, open-label, single-center, prospective | Methods (p.2) |
| **Population** | 36 patients with metastatic breast cancer (MBC) | Results (p.3) |
| **Setting** | Gunma University, Japan | Methods (p.2) |
| **Enrollment period** | November 2007 – December 2018 (11 years) | Methods (p.2); Results (p.3) |
| **Trial Registration** | JRCTs031180296 (registered 2 December 2019 — retrospective) | Abstract (p.1) |
| **Sample size rationale** | ~40 patients estimated, **without statistical powering** | Methods (p.2): "without any calculations based on statistical assumptions" |

> The study was designed around ORR as the primary endpoint but was **not statistically powered**. The sample size of ~40 was estimated from prior phase I/II experience, not from a formal power calculation. The authors themselves note this was "a small, open-label, single center trial with no formal hypothesis testing" (Conclusions, p.8).

### Treatment Regimen
| Step | Drug | Dose | Schedule | Source |
|---|---|---|---|---|
| 1 | S-1 (tegafur/gimeracil/oxonate) | 80 mg/m²/day | Oral, 2×/day, 14 consecutive days | Methods (p.2); ref 18 (Horiguchi et al., 2013) |
| 2 | Cyclophosphamide (CPA) | 100 mg/m²/day | Oral, 2×/day, 14 consecutive days | Methods (p.2); ref 18 |
| 3 | Repeat cycle | — | 4-week cycle (S-1 2 wk → CPA 2 wk) | Methods (p.2) |
| 4 | Continue until | — | PD (RECIST), unmanageable toxicity, or withdrawal | Methods (p.2–3) |

**Rationale (from Background, p.1–2):** Both S-1 and CPA are orally administered, individually active in MBC, and have manageable toxicity profiles. The sequential oral regimen aims to maintain efficacy while preserving quality of life compared to IV taxane/anthracycline regimens, which cause alopecia, neuropathy, edema, and significant myelosuppression. A prior phase I study (Horiguchi et al., *Gan To Kagaku Ryoho* 2013; ref 18) established the recommended doses. The SELECT BC phase III trial (Takashima et al., *Lancet Oncol* 2016; ref 4) showed S-1 noninferior to taxane for OS as first-line MBC treatment and superior for HRQOL.

### Endpoints
| Type | Measure | Definition | Source |
|---|---|---|---|
| **Primary** | Overall Response Rate (ORR) | Proportion of CR + PR per RECIST (confirmed ≥4 weeks) | Methods (p.3) |
| **Secondary** | Overall Survival (OS) | Time from enrollment to death | Methods (p.3) |
| **Secondary** | Progression-Free Survival (PFS) | Time from enrollment to progression or death | Methods (p.3) |
| **Secondary** | Clinical Benefit Rate (CBR) | Proportion of CR + PR + SD continuing >4 weeks (28 days) | Methods (p.3) |
| **Secondary** | Safety | Adverse events per CTCAE v3.0/v4.0 | Methods (p.3) |

> **Primary vs. secondary distinction is essential — and determines what counts as the study's answer.**
>
> The study was designed around a single question: *does this oral regimen shrink tumors at a clinically meaningful rate?* That question is answered by ORR — a proportion measured at discrete RECIST assessments. PFS and OS are secondary time-to-event measures estimated via Kaplan-Meier; they describe *how long* benefit lasts, not *whether* the regimen produces tumor responses. A Kaplan-Meier curve cannot substitute for ORR in evaluating whether the study met its primary goal.
>
> **Why this matters in practice:** If a reader looks only at the survival figures (Figures 1–2), they see median PFS = 9.5 months and subgroup curves — but they never see the primary endpoint at all. The ORR (33.3%) and CBR (66.7%) exist only in the Results text. A reader who equates "the survival curve" with "the study result" has silently replaced the study's design logic with a different question the study was not powered or structured to answer as its main objective.

### Limitations (from study text and design)
- Small sample (n = 36); no formal statistical powering or hypothesis testing (Methods p.2; Conclusions p.8)
- Single-center, single-arm — no comparative efficacy claim possible
- Retrospective trial registration (Dec 2019 for a study running since Nov 2007)
- 11-year enrollment period introduces temporal heterogeneity in standards of care
- Subgroup analyses are exploratory and underpowered (especially triple-negative, n = 7)
- CTCAE grading changed from v3.0 to v4.0 mid-trial via protocol amendment (Methods p.3)

---

## Results

### Tumor Response (Primary Endpoint)
| Response | Count | Percentage | Source |
|---|---|---|---|
| Complete Response (CR) | 0 | 0% | Results (p.3) |
| Partial Response (PR) | 12 | 33.3% | Results (p.3) |
| Stable Disease (SD) | 12 | 33.3% | Results (p.3) |
| Progressive Disease (PD) | 11 | ~30.6%* | Results (p.3); Abstract says 30.1% |
| Non-evaluable (NE) | 1 | — | Results (p.3) |
| **ORR (CR + PR)** | **12/36** | **33.3%** | Results (p.3) |
| **CBR (CR + PR + SD >4 wk)** | **24/36** | **66.7%** | Results (p.3) |

> **Paper internal inconsistency in PD percentage:** The Results text (p.3) lists PD as "11 (33.3%)" while the Abstract (p.1) lists PD as "11 (30.1%)." Neither is correct: 11/36 = 30.56%. The Abstract's 30.1% is closer but still slightly off; the Results text's 33.3% appears to be a copy error from the PR and SD rows. One patient was non-evaluable for response, so the evaluable denominator could be 35 (11/35 = 31.4%), but the paper uses 36 as the denominator for ORR and CBR, so the intended PD percentage is ~30.6%.

> **This table comes entirely from study text (Results, p.3). No survival figure depicts tumor response.** The primary endpoint is invisible in any Kaplan-Meier plot.

### Did the Study Meet Its Primary Endpoint?

The study did not pre-specify a target ORR threshold (e.g., "success if ORR ≥ X%"). The observed ORR of 33.3% is therefore evaluated by the authors through external comparison, not against an internal benchmark:

| Comparator | ORR | Source |
|---|---|---|
| **This study (S-1 + CPA)** | **33.3%** | Results (p.3) |
| Capecitabine + CPA (Tanaka et al.) | 35.6% | Discussion (p.6); ref 15 |
| Capecitabine + CPA (Yoshimoto et al.) | 30.3% | Discussion (p.6); ref 16 |
| S-1 monotherapy (prior phase II) | 41.7% | Background (p.2); ref 8 |
| S-1 in SELECT BC (phase III, 1L MBC) | — (noninferior to taxane for OS) | Background (p.2); ref 4 |

The authors call their ORR "consistent" with the capecitabine+CPA studies (Discussion, p.6). They do not claim superiority or inferiority to any comparator — the single-arm design makes such claims impossible. The CBR of 66.7% is described as "good disease control" (Conclusions, p.8).

> **Design-logic chain (what the study actually argues):**
> 1. Background: oral regimens preserve QOL; S-1 and CPA are individually active in MBC → *rationale for combining them sequentially*
> 2. Phase I (ref 18): established safe doses → *justification for phase II dosing*
> 3. Primary endpoint (ORR = 33.3%): tumors shrank in one-third of patients → *consistent with similar oral regimens*
> 4. Secondary endpoints (PFS, OS, safety): the responses translated into 9.5-month median PFS and 20.2-month median OS with manageable toxicity → *supporting evidence that responses are durable and the regimen is tolerable*
> 5. Conclusion: "feasible new treatment option" warranting further study → *not a claim of superiority*
>
> Steps 3–4 are sequential in the study's logic: ORR answers the primary question first, then PFS/OS describe how long those responses last. Reading the survival figures without first anchoring on the ORR result inverts this chain.

### Survival (Secondary Endpoints)

**Full cohort:**
| Measure | Value | 95% CI | Source |
|---|---|---|---|
| Median PFS | 9.5 months | 7.8–12.6 | Study text (p.3) + Figure 1a (PDF p.4) |
| Median OS | 20.2 months | 15.0–25.4 | Study text (p.3) + Figure 1b (PDF p.4) |

> Figure 1 is embedded in the PDF (page 4) but has **no separate image file** in the task directory. The medians and CIs are stated in both the Results text and the figure legend; the figure confirms the Kaplan-Meier curve shape but the exact numerical values come from the text.

**Subgroup PFS (exploratory — from Figure 2 legend text, p.7, and figure image `figure_2_survival_curves.png`):**

| Subgroup Comparison | Median PFS (Group A) | Median PFS (Group B) | p-value | Significant? | Source |
|---|---|---|---|---|---|
| Metastatic recurrent (n=26) vs. de-novo (n=10) | 11.0 mo (95%CI: 8.1–13.9) | 4.0 mo (95%CI: 2.0–6.0) | **0.007** | **Yes** | Fig 2a legend + image |
| No prior chemo (n=22) vs. after chemo (n=14) | 9.5 mo (95%CI: 6.5–12.5) | 10.5 mo (95%CI: 6.1–13.9) | 0.784 | No | Fig 2b legend + image |
| Visceral (n=23) vs. non-visceral (n=13) | 10.0 mo (95%CI: 7.1–12.9) | 5.0 mo (95%CI: 1.2–8.8) | 0.254 | No | Fig 2c legend + image |
| Luminal (n=29) vs. triple-negative (n=7) | 9.0 mo (95%CI: 6.4–11.6) | 10.0 mo (95%CI: 4.1–15.9) | 0.609 | No | Fig 2d image OCR |

> **Paper inconsistency in Figure 2d legend (p.7):** The legend text says "the median PFS was 10.0 months (95%CI: 4.1–15.9 months) in patients **without** triple negative breast cancer." But "without triple negative" = luminal (n=29), which the same legend gives as 9.0 months (95%CI: 6.4–11.6). These two values with different CIs cannot both describe the same group. The figure image OCR labels the 10.0-month curve as "Triple negative (n=7)," suggesting the legend text's "without" is a typo for "with" (or simply "triple negative"). The figure image labels are used here as the more direct source; the legend text inconsistency is noted.

> **Paper inconsistency in "after chemotherapy" median PFS:** The Figure 2b legend text (p.7) states 10.5 months (95%CI: 6.1–13.9). The figure image OCR reads "10.0." The legend text is the authoritative published source and is used here.

> **Counterintuitive direction in visceral vs. non-visceral PFS:** Patients with visceral metastasis had longer median PFS (10.0 mo) than those with non-visceral metastasis (5.0 mo) — opposite to the usual expectation that visceral disease carries worse prognosis. The difference is not significant (p = 0.254), and the small sample sizes (n=23 vs. n=13) with wide CIs that overlap substantially make this direction unreliable. The paper does not comment on this counterintuitive finding.

### Subgroup Confound for the Only Significant Finding
The de-novo vs. recurrent comparison (p = 0.007) is confounded by subtype imbalance (Table 2a, p.5):
- All 10 de-novo patients were luminal (100%); 0 were triple-negative
- 7 of 26 recurrent patients were triple-negative (26.9%); 19 were luminal (73.1%)
- Subtype difference between groups: p = 0.079 (borderline non-significant)

The shorter PFS in de-novo patients may reflect the fact that de-novo disease has no prior treatment exposure (including no prior endocrine therapy for the luminal cases), or it may be confounded by the absence of triple-negative cases in the de-novo group (TN tumors in the recurrent group might respond differently to oral fluoropyrimidine-based therapy). The authors state "the reason for this is unclear" (Discussion, p.6).

### Safety
| Adverse Event | All Grade | Grade 3/4 | Source |
|---|---|---|---|
| Leukopenia | 7 (19.4%) | 5 (13.9%) | Table 3 (p.8) |
| Anemia | 1 (2.8%) | 1 (2.8%) | Table 3 (p.8) |
| Thrombocytopenia | 3 (8.3%) | 1 (2.8%) | Table 3 (p.8) |
| Fatigue | 3 (8.3%) | 0 | Table 3 (p.8) |
| Nasolacrimal duct obstruction | 1 (2.8%) | 0 | Table 3 (p.8) |
| Sepsis | 1 (2.8%) | 1 (2.8%) | Table 3 (p.8) |

- Dose reductions due to AEs: 12 patients (33.3%) — Results text (p.4)
- Treatment discontinuation (sepsis): 1 patient (2.8%) — Results text (p.4)
- **No treatment-related mortality** — Results text (p.4)

> **Paper internal inconsistency in leukopenia reporting:** The Results text (p.4) states "Five (13.9%) patients had grade 3 leukopenia, but no patients had grade 4 hematologic toxicity. Grade 3/4 adverse events included leukopenia in 7 patients each (19.4%)." Table 3 (p.8) lists leukopenia All Grade = 7 (19.4%), Grade 3/4 = 5 (13.9%). The most consistent reading: 7 patients had leukopenia of any grade (19.4%), of which 5 had grade 3 (13.9%) and none had grade 4. The text's sentence beginning "Grade 3/4 adverse events included leukopenia in 7 patients each (19.4%)" is misleadingly phrased — the 7 (19.4%) figure is the all-grade count, not the grade 3/4 count. Table 3 is the more structured source and is used here.

> **CTCAE version change:** Adverse events were graded per CTCAE v3.0 initially, then switched to v4.0 mid-trial via protocol amendment (Methods, p.3). This means grade thresholds may not be uniform across all patients, which complicates safety comparisons.

> **Absence of common taxane/anthracycline toxicities:** The Discussion (p.6) explicitly states: "Adverse events such as hair loss, peripheral neuropathy, gastrointestinal toxicity and edema — which are commonly observed in patients with taxane or anthracycline regimens — were not observed in our study." This is a direct claim of zero incidence for these specific AEs, not merely an inference from Table 3's limited listing. Table 3 lists only 6 AE categories, but the Discussion text provides the explicit confirmation that the draft previously lacked.

---

## Figure Evidence: What Each Image Shows and Does Not Show

### Figure 1 — Overall Cohort Kaplan-Meier Curves (Yanai et al.)

**Location:** Embedded in `clinical_study_source.pdf` page 4. **No separate image file in the task directory.**

| Panel | Measure | Median | 95% CI | What it shows | What it does NOT show |
|---|---|---|---|---|---|
| (a) | PFS, all 36 patients | 9.5 mo | 7.8–12.6 | Time-to-progression distribution for the full cohort | ORR, CBR, safety, subgroups, control comparison |
| (b) | OS, all 36 patients | 20.2 mo | 15.0–25.4 | Time-to-death distribution for the full cohort | Same as above; also does not show PFS |

> Figure 1 establishes the cohort-level headline outcome. The numerical values come from the Results text (p.3) and the figure legend (p.4); the figure itself confirms the KM curve shape but the exact medians and CIs are stated in the text.

### Figure 2 — Subgroup PFS Analysis (Yanai et al.)

**Location:** `figure_2_survival_curves.png` in the task directory. This file **is** the paper's Figure 2.

| Panel | Comparison | Significant? | p-value | What it shows | What it does NOT show |
|---|---|---|---|---|---|
| (a) | De-novo vs. recurrent | **Yes** | 0.007 | Recurrent patients had significantly longer PFS | OS subgroups, ORR, safety, mechanism |
| (b) | No prior chemo vs. after chemo | No | 0.784 | Prior chemotherapy status does not affect PFS | Same as above |
| (c) | Visceral vs. non-visceral | No | 0.254 | Metastasis site does not significantly affect PFS (direction is counterintuitive: visceral > non-visceral) | Same as above |
| (d) | Luminal vs. TN | No | 0.609 | Subtype does not significantly affect PFS | Same as above |

> Figure 2 explores heterogeneity within the headline PFS established by Figure 1. Only panel (a) shows meaningful curve separation. The other three panels show overlapping curves consistent with their non-significant p-values.

> **Figure 2d legend inconsistency (see Results section above):** The paper's legend text assigns 10.0 months to "patients without triple negative breast cancer" (= luminal), but the same legend gives luminal as 9.0 months, and the figure image labels the 10.0-month curve as "Triple negative." The figure image labels are the more direct source.

### ⚠ `figure_2_overall_survival_km.jpg` — NOT from the Yanai et al. Study

**This image is from KEYNOTE-063**, a separate clinical trial comparing Pembrolizumab vs. Paclitaxel in patients with advanced gastric cancer. OCR confirms legend labels "Pembrolizumab" and "Paclitaxel" with 47 patients per arm — neither drug nor sample size matches the Yanai study (36 patients, S-1 + CPA). The task directory also contains `keynote_063_trial.pdf` (a JavaScript-gated web capture, not readable).

**This image must NOT be used as evidence for the Yanai et al. study.** It depicts overall survival from a different trial entirely. Any interpretation that treats this image as the Yanai cohort's OS curve is incorrect.

### How the Two Yanai Figures Relate to Each Other — and to the Primary Endpoint

**Neither figure depicts the primary endpoint (ORR).** The study's main result — that tumors shrank in 33.3% of patients — has no visual representation anywhere in the paper's figures. It exists only as a number in the Results text. Both figures live entirely within the secondary-endpoint layer.

#### What each figure answers

| | Figure 1 (PDF p.4; no separate file) | Figure 2 (`figure_2_survival_curves.png`) |
|---|---|---|
| **Question** | How did the full 36-patient cohort do on PFS and OS? | Did any subgroup have meaningfully different PFS? |
| **Panels** | (a) PFS, all patients; (b) OS, all patients | (a) de-novo vs. recurrent; (b) prior chemo; (c) visceral; (d) subtype |
| **Measure** | PFS *and* OS | PFS only — no OS subgroup analysis exists |
| **Result** | Median PFS = 9.5 mo; Median OS = 20.2 mo | Only panel (a) significant (p = 0.007); panels (b–d) non-significant |
| **Role in the study** | Establishes the aggregate secondary headline | Partitions that headline to look for heterogeneity |

#### How the numbers talk to each other

Figure 1a's overall median PFS of 9.5 months is a **weighted composite** of the subgroups shown in Figure 2. The decomposition makes the aggregate interpretable:

| Subgroup (Fig 2 panel) | n | Median PFS | Relative to overall 9.5 mo | Direction |
|---|---|---|---|---|
| Recurrent (2a) | 26 | 11.0 mo | +1.5 mo above | Pulls overall up |
| De-novo (2a) | 10 | 4.0 mo | −5.5 mo below | Pulls overall down |
| No prior chemo (2b) | 22 | 9.5 mo | Equal | Neutral |
| After chemo (2b) | 14 | 10.5 mo | +1.0 mo above | Slight upward pull |
| Visceral (2c) | 23 | 10.0 mo | +0.5 mo above | Slight upward pull |
| Non-visceral (2c) | 13 | 5.0 mo | −4.5 mo below | Pulls overall down |
| Luminal (2d) | 29 | 9.0 mo | −0.5 mo below | Near-neutral |
| Triple-negative (2d) | 7 | 10.0 mo | +0.5 mo above | Slight upward pull |

> **Reading this table:** The overall 9.5-month median is not simply the average of subgroup medians — it is the median of the pooled Kaplan-Meier curve. But the subgroup medians show *where the aggregate comes from*. The de-novo group (n=10, median 4.0 mo) is the strongest downward pull; the recurrent group (n=26, median 11.0 mo) dominates the aggregate because it is 2.6× larger. This is why Figure 2a's separation is the only significant finding — the gap is 7.0 months and the larger group's weight drives the overall.

#### What Figure 2 reveals that Figure 1 hides — and vice versa

- **Figure 1 hides subgroup heterogeneity.** The smooth aggregate PFS curve (9.5 mo) conceals the fact that de-novo patients progressed at a median of 4.0 months — less than half the headline number. A reader who sees only Figure 1 would assume the 9.5-month median applies roughly uniformly.
- **Figure 2 hides the OS dimension.** All four Figure 2 panels show PFS only. The study never reports subgroup OS curves. A reader who sees only Figure 2 knows nothing about overall survival — neither the aggregate 20.2-month median (Figure 1b) nor whether the de-novo/recurrent PFS split persists in OS.
- **Figure 2 hides the aggregate benchmark.** The subgroup medians (11.0, 4.0, 9.5, 10.5, 10.0, 5.0, 9.0, 10.0 months) are only interpretable relative to Figure 1a's 9.5-month overall. Without that anchor, a reader cannot tell whether "10.0 months for visceral" is good or bad for this regimen.
- **Neither figure shows the primary endpoint.** ORR = 33.3% and CBR = 66.7% exist only in text. The figures show *how long* responses lasted, not *whether* tumors shrank.

#### What Figure 2 raises that the text partially answers

Figure 2a's significant finding (de-novo PFS = 4.0 mo vs. recurrent PFS = 11.0 mo) raises an obvious question: *why?* The figures alone cannot answer this. The text provides partial answers:
- **Subtype confound (Table 2a, p.5):** All 10 de-novo patients were luminal; 7/26 recurrent patients were triple-negative (p = 0.079). But Figure 2d shows luminal vs. TN PFS is non-significant (p = 0.609), so subtype alone doesn't explain the gap.
- **Prior endocrine therapy confound (Table 2a, p.5):** 100% of de-novo patients had prior endocrine therapy vs. 61.5% of recurrent patients (p = 0.021). This is the only statistically significant baseline imbalance between the two groups.
- **Authors' own assessment (Discussion, p.6):** "The mechanism is unknown." They recommend further study in larger cohorts.

This means Figure 2a's most visually striking result — the wide curve separation — is also the most confounded. The figure shows a real PFS difference, but the *reason* for that difference requires reading the text's Table 2a and Discussion, not just the curves.

#### The study's argument chain across both figures

```
ORR = 33.3% (text only)          ← Primary endpoint: "Did tumors shrink?"
        │
        ▼
Figure 1a: PFS = 9.5 mo          ← Secondary: "How long before progression?"
Figure 1b: OS = 20.2 mo          ← Secondary: "How long did patients survive?"
        │
        ▼
Figure 2a: recurrent 11.0 mo     ← Exploratory: "Who did better on PFS?"
           vs. de-novo 4.0 mo       (only significant subgroup split)
Figure 2b–d: non-significant     ← Exploratory: "Any other PFS differences?"
                                    (no — prior chemo, site, subtype don't matter)
        │
        ▼
Table 2a + Discussion text       ← Confound analysis: "Why the de-novo gap?"
                                    (subtype imbalance + prior endocrine therapy;
                                     mechanism unknown)
```

Entering at Figure 2 without first anchoring on ORR and Figure 1 inverts this chain. Entering at `figure_2_overall_survival_km.jpg` is worse — that image is from a different trial entirely (see warning above).

---

## Interpretation

### What the Study Set Out to Measure vs. What the Figures Show

| Layer | Question | Answer | Source | In a figure? |
|---|---|---|---|---|
| **Design logic** | Why this regimen? | Oral, QOL-preserving alternative to IV taxane/anthracycline | Background (p.1–2) | No |
| **Primary endpoint** | Did the regimen shrink tumors? | ORR = 33.3%, CBR = 66.7% — "consistent" with similar oral regimens | Results text (p.3); Discussion (p.6) | **No — invisible in all figures** |
| **Secondary (time-to-event)** | How long before half the cohort progressed? | Median PFS = 9.5 mo | Results text + Figure 1a | Yes (Fig 1a) |
| **Secondary (time-to-event)** | How long did half the cohort survive? | Median OS = 20.2 mo | Results text + Figure 1b | Yes (Fig 1b) |
| **Secondary (exploratory)** | Which subgroup had significantly different PFS? | De-novo vs. recurrent (p = 0.007) | Results text + Figure 2a | Yes (Fig 2a) |
| **Secondary (exploratory)** | Was PFS different by prior chemo, site, or subtype? | No (p = 0.784, 0.254, 0.609) | Results text + Figure 2b–d | Yes (Fig 2b–d) |
| **Secondary (safety)** | Was the regimen tolerable? | Manageable toxicity, no treatment-related death, no alopecia/neuropathy/GI toxicity | Results text + Table 3; Discussion (p.6) | **No — invisible in all figures** |
| **Design limitation** | Is the regimen better than standard care? | **Cannot be determined** — no control arm | Study design | N/A |

> **Reading order matters.** The table above is ordered by the study's own logic: design rationale → primary endpoint → secondary endpoints → limitations. A reader who enters through Figure 2 (subgroup PFS) is starting at layer 5 of an 8-layer chain. The primary endpoint (layer 2) and the tolerability rationale (layers 1 and 7) — which together form the study's core argument — are entirely text-based and invisible in any figure.

### Key Takeaways

1. **The primary endpoint (ORR) is invisible in every figure the study provides.** The study's design logic runs: oral regimen rationale → ORR as primary measure of tumor shrinkage → PFS/OS as secondary measures of response durability. Figures 1 and 2 depict only the secondary layer (PFS, OS). A reader who treats a survival curve as "the study result" has silently replaced the primary question ("did tumors shrink?") with a secondary question ("how long before progression?") that the study was not designed or powered to answer as its main objective. The ORR of 33.3% and CBR of 66.7% — the actual primary result — exist only in the Results text (p.3).

2. **The two Yanai figures are complementary layers of the same secondary endpoint, not interchangeable views.** Figure 1 gives the aggregate PFS (9.5 mo) and OS (20.2 mo) for all 36 patients. Figure 2 decomposes the PFS aggregate into four subgroup comparisons — only one of which (de-novo vs. recurrent, p = 0.007) is significant. The subgroup medians are only interpretable relative to Figure 1's overall: the recurrent group's 11.0 months is 1.5 months above the aggregate; the de-novo group's 4.0 months is 5.5 months below it. Figure 2 also reveals what Figure 1 hides (the de-novo patients progressed at less than half the headline rate) and hides what Figure 1 shows (OS — no subgroup OS analysis exists). Neither figure alone represents the study, and neither touches the primary endpoint (ORR = 33.3%, text only). See the figure-relationship section for the full numerical decomposition and argument chain.

3. **The only significant subgroup finding** is that patients with metastatic recurrent disease had longer PFS (11.0 mo) than de-novo metastatic patients (4.0 mo, p = 0.007). This finding is confounded by subtype imbalance: all 10 de-novo patients were luminal (100%), while 7 of 26 recurrent patients were triple-negative (26.9%, subtype p = 0.079). The authors state "the reason for this is unclear" (Discussion, p.6). With only 10 de-novo and 7 TN patients, this finding is exploratory and not generalizable.

4. **The visceral vs. non-visceral PFS direction is counterintuitive.** Patients with visceral metastasis had longer median PFS (10.0 mo) than non-visceral (5.0 mo), opposite to the usual expectation. The difference is not significant (p = 0.254), and the wide overlapping CIs make this direction unreliable. The paper does not comment on this.

5. **The regimen's main advantage** is its oral, well-tolerated profile. The Background and Discussion emphasize that S-1+CPA avoids alopecia, neuropathy, edema, and significant GI toxicity typical of taxane/anthracycline regimens. The Discussion (p.6) explicitly states these AEs "were not observed in our study" — this is a direct zero-incidence claim, not merely an inference from Table 3's limited listing. This tolerability advantage is entirely absent from the survival figures but central to the study's rationale.

6. **`figure_2_overall_survival_km.jpg` is from KEYNOTE-063 and must not be interpreted as Yanai et al.'s data.** It shows Pembrolizumab vs. Paclitaxel OS in 47-patient arms — a different trial, different drugs, different sample size, different disease setting. It has no relevance to the S-1/CPA cohort of 36 MBC patients.

7. **The paper contains multiple internal inconsistencies** that affect data reliability:
   - PD percentage: Abstract (p.1) says "11 (30.1%)" while Results text (p.3) says "11 (33.3%)" — neither matches 11/36 = 30.56%
   - Figure 2d legend assigns 10.0 months to "patients without triple negative breast cancer" (= luminal), but the same legend gives luminal as 9.0 months, and the figure image labels 10.0 as the TN curve
   - Leukopenia: text says "Grade 3/4 adverse events included leukopenia in 7 patients each (19.4%)" but Table 3 says Grade 3/4 = 5 (13.9%)
   - CTCAE grading changed mid-trial (v3.0 → v4.0), making grade thresholds non-uniform across patients

8. **No individualized treatment advice can be derived from this breakdown.** The study is a small, single-arm, unpowered phase II trial with no control arm and no formal hypothesis testing. Its results inform whether further controlled study is warranted, not whether any specific patient should receive this regimen.

### One-Line Takeaway
Sequential oral S-1 followed by CPA was designed to test tumor response rate (primary endpoint: ORR = 33.3%, from text only) in 36 MBC patients; the secondary survival data (PFS 9.5 mo, OS 20.2 mo, shown in Figures 1–2) describe how long responses lasted but do not substitute for the primary result, and the single-arm design with no formal hypothesis testing means further controlled study is needed before any comparative efficacy claim.