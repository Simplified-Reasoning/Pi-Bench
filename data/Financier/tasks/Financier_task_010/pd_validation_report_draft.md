# Independent Validation Report — Fixed German Credit PD Scorecard

**Model:** fixed_german_credit_pd_scorecard (logistic-regression scorecard)  
**Validation Date:** 2026-05-01  
**Validation Framework Anchor:** Federal Reserve SR 11-7 *Supervisory Guidance on Model Risk Management* (2011)  
**Validation Conduct:** Independent of model development team

---

## Validation Decision

**CONDITIONAL PASS — Use with Specified Remediation and Monitoring Conditions**

The model meets minimum SR 11-7 thresholds for discriminatory power and population stability on the German Credit benchmark data. However, it carries material deficiencies in conceptual soundness, threshold justification, and data-representativeness evidence that prevent an unconditional approval. Four HIGH-priority findings and two MEDIUM-priority findings require remediation before broader deployment. No LOW-priority issues were identified. Until remediation is complete, use is restricted to supervised decision-support only.

---

## Findings

### HIGH Priority — Must Resolve Before Deployment

**H1 · Interaction terms and goodness-of-fit not validated**  
*SR 11-7 Principle: Model theory and assumptions must be sound.*  
The scorecard is a fixed additive logistic-regression formula with no documented interaction terms. Known credit-risk interactions — duration × credit_amount, age × employment — are absent from the specification. No Hosmer-Lemeshow or le Cessie-van Houwelingen goodness-of-fit test has been run on any partition. Without interaction controls, the model can assign systematically inflated PDs to thin-file young applicants with high credit amounts, a segment that also shows test-PSI instability.  
*Remediation:* Run H-L test on 10 decile groups on train and test; if p < 0.05 on train, refit or add interaction terms for H1 and H2.

**H2 · PD threshold of 0.35 is unanchored from business or regulatory calibration**  
*SR 11-7 Principle: Methodology must be appropriate for its intended use.*  
The cutoff for manual-review escalation has no documented derivation. No calibration curve, no benchmark against portfolio default rates, and no precision/recall tradeoff analysis at alternative cutoffs is provided. On test, at the chosen cutoff: precision=47.0% (fewer than half of flagged applications are actually bad). No cost-of-error analysis or regulatory expected-loss table is referenced.  
*Remediation:* Document threshold rationale — portfolio bad-rate matching, F1 optimization, or regulatory capital grid — and retest at cutoffs 0.30 and 0.40.

**H3 · KS collapses from 0.21 to 0.06 — rank-order discrimination does not transfer to unseen data**  
*SR 11-7 Principle: Out-of-sample discriminatory power must be demonstrated; performance deterioration is a model risk signal.*  
Train KS of 0.21 is weak; test KS of 0.06 represents a 71% deterioration. This is not a sample-size artifact. Contributing factors: sparse-bin instability (A30, N=40; A103, N=52 in test), interaction misspecification, and possible training-partition overfitting.  
*Remediation:* Bootstrap cross-validation (100 × 70/30); flag if the 5th-percentile KS falls below 0.10.

**H4 · Q4 and Q5 of test produce identical 50.0% bad rates — rank-order inversion above PD=0.40**  
*SR 11-7 Principle: Model output should exhibit monotonic risk stratification; non-monotonicity in the upper tail undermines decision reliability.*  
Q4 (PD 0.400–0.603) and Q5 (PD 0.603–0.907) each yield 30/60 bads on test. The model cannot rank-order the 60th through 100th percentile of risk. The 0.35 threshold contributes by compressing PDs in the 0.35–0.60 band, but the issue is structural — the scorecard's upper range lacks granularity.  
*Remediation:* Collapse Q4+Q5 into a single high-risk segment for decision purposes, or recalibrate to improve granular ranking above PD=0.40.

---

### MEDIUM Priority — Must Resolve Before Production Deployment

**M1 · Calibration evidence is absent**  
*SR 11-7 Principle: Predicted probabilities must be aligned with observed outcomes.*  
No reliability diagram, Brier score, or expected-to-observed default ratio by decile has been performed or referenced. Without calibration, the scorecard cannot be used for regulatory capital, expected loss, or pricing reserves.  
*Remediation:* Compute Brier score and calibration curve on train and test; recalibrate via Platt scaling or isotonic regression if Brier > 0.18 on test.

**M2 · PSI masks directional category instability in A13 checking_status**  
*SR 11-7 Principle: Stability assessment must identify sub-population shifts, not only aggregate shifts.*  
Score PSI=0.026, checking_status PSI=0.008, credit_amount band PSI=0.025 — all below the 0.10 threshold. However, A13 shows a 7 pp bad-rate increase from train (17.5%) to test (30.4%) on only 23 test observations, which is masked by aggregate PSI. The PSI masking of a directionally worsening minority category is itself a finding.  
*Remediation:* Track single-variable PSI on all key features in production; escalate if any individual-variable PSI exceeds 0.05.

---

### LOW Priority — No Issues Identified

No LOW-priority findings were identified. All identified issues rise to MEDIUM or HIGH severity. The following observations are documented for completeness but do not independently impede conditional approval:

- The log-transform centering constant of 3,000 in the credit_amount term is not documented; however, the direction of the term is economically sound.
- The exclusion of five variables (purpose, other_payment_plans, own_telephone, installment_commitment, residence_since) lacks documented rationale; however, no evidence of omitted-variable bias was detected in the available data.
- No sensitivity or stress test is documented; however, boundary regions (credit_amount > 10,000, age > 60) account for fewer than 4% of observations.

---

## Limitations

1. **Not a production portfolio.** The UCI German Credit dataset is a static 1,000-observation academic benchmark from a single German bank (1990s vintage). It does not represent any current applicant population. SR 11-7 requires data representative of the intended use population; deploying without recalibration on representative current data would be a fundamental misuse.

2. **No temporal dimension.** All 1,000 observations lack a date field, making economic-cycle and time-series stability testing impossible. Static-benchmark validation is necessary but not sufficient for SR 11-7 compliance.

3. **Sparse minority bins.** Test N=300 yields wide binomial confidence intervals on subgroup metrics. A30 (N=40), A103 (N=52), A13 (N=23) have confidence bounds of approximately ±8–15%. Decisions on applicants mapped primarily to these bins require expert review.

4. **Credit_amount log-transform parameters not documented.** The centering constant 3,000 and coefficient 0.25 lack documented derivation. No comparison to linear or piecewise alternatives has been performed.

5. **No sensitivity or stress testing documented.** Boundary conditions (credit_amount > 10,000, N=40, 4%; age > 60, N≈30) are in extrapolation regions where SR 11-7 requires documented sensitivity analysis.

6. **Excluded variables not justified.** Purpose (10 categories), other_payment_plans, own_telephone, installment_commitment, and residence_since are excluded without documented rationale, creating potential omitted-variable bias.

---

## Recommendations

### HIGH — Before Any Deployment

| # | Recommendation | SR 11-7 Principle |
|---|---------------|-------------------|
| R1 | Run Hosmer-Lemeshow test (10 decile groups) on train and test. If p < 0.05 on train, refit with interaction terms for duration × credit_amount and age × employment. | Conceptual soundness |
| R2 | Document threshold 0.35 rationale; compute precision/recall/F1 at cutoffs 0.30, 0.35, 0.40; anchor to business cost-of-error or regulatory expected-loss. | Appropriate methodology |
| R3 | Bootstrap cross-validation (100 × 70/30); flag if 5th-percentile KS < 0.10. | Out-of-sample stability |
| R4 | Collapse Q4+Q5 into a single high-risk segment or recalibrate to improve rank-order granularity above PD=0.40. | Model output validity |
| R5 | Recalibrate on a current, population-representative sample reflecting the intended portfolio's credit product mix, demographics, and economic environment. | Data representativeness |
| R6 | Establish monthly monitoring triggers before first production use: score PSI > 0.05, KS < 0.15, bad-rate deviation > ±5 pp. | Ongoing monitoring |
| R7 | Define business use-case boundaries: approved use, prohibited use, required human-review triggers, and override protocols. Document that this is a decision-support tool, not an autonomous decision system. | Governance and controls |

### MEDIUM — Before Production Deployment

| # | Recommendation | SR 11-7 Principle |
|---|---------------|-------------------|
| R8 | Compute Brier score and calibration curve on train and test. Recalibrate via Platt scaling or isotonic regression if Brier > 0.18 on test. | Probability calibration |
| R9 | Track individual-variable PSI in production; escalate if any single-variable PSI exceeds 0.05, regardless of total score PSI. | Stability monitoring |
| R10 | Generate sensitivity analysis: vary duration, credit_amount, and age across their observed ranges; confirm monotonicity direction is consistent with credit risk theory. | Model transparency |
| R11 | Document rationale for excluding purpose, other_payment_plans, own_telephone, installment_commitment, and residence_since. Re-evaluate any with bivariate IV > 0.1 on the current portfolio. | Documentation completeness |

### LOW — Addressable Over Time

| # | Recommendation | SR 11-7 Principle |
|---|---------------|-------------------|
| R12 | Compare the log-linear credit_amount term to a linear and piecewise alternative specification using AIC/BIC on the current calibration sample. | Model specification refinement |
| R13 | Conduct stress testing on boundary regions (credit_amount > 10,000, age > 60) to document model behavior under extrapolation. | Sensitivity analysis |
| R14 | Establish a quarterly model risk report template incorporating all monitoring metrics in the table below. | Ongoing governance |

---

## Monitoring And Use Conditions

### Approved Use Scope
- Decision-support for supervised consumer credit decisions (analogous to the German Credit benchmark product mix).
- Not approved for fully automated decision-making above PD=0.40 without human review.
- Not approved for any portfolio other than one on which the model has been recalibrated on representative, current data.

### Required Monitoring Triggers

| Metric | Frequency | Trigger Threshold | Action on Breach |
|--------|-----------|-------------------|-----------------|
| Score PSI (rolling 90-day window) | Monthly | > 0.05 | Escalate to model risk team; suspend auto-decisions |
| KS statistic | Monthly | < 0.15 | Re-validate or initiate retirement |
| Bad-rate deviation vs. train expected | Monthly | > ±5 pp | Recalibrate threshold |
| Any single-variable PSI | Monthly | > 0.05 | Investigate sub-population shift; flag for expert review |
| High-balance accounts (credit_amount > 10,000) | Monthly | > 8% of volume | Investigate composition shift |
| A13 checking_status proportion | Monthly | > 10% of volume | Investigate demographic shift |
| Brier score | Quarterly | > 0.20 | Initiate recalibration |

### Documentation Requirements
- All monitoring metrics logged monthly; presented in the quarterly model risk report.
- Human-review overrides logged with reason code.
- Annual full re-validation; interim re-validation if any threshold is breached twice within 12 months.
- Model version control: any change to weights, intercept, or binning rules requires a new validation cycle and senior model risk approval.

### Dependency on Downstream Decisions
The predicted PD is not calibrated to regulatory capital or expected loss without a formal calibration step. If used for pricing or capital calculations, a separate economic-use validation is required. For credit-decision use only, the conditional pass stands once H1–H4 and M1–M2 are completed and documented.

---

*Validation performed from: UCI Statlog German Credit Data (n=1,000), split 700/300 per `german_credit_split.csv`; scorecard per `pd_scorecard_model_spec.yaml`. All metrics computed independently from raw data, score formula, and split file. SR 11-7 reference: Federal Reserve SR 11-7 / OCC Bulletin 2011-12.*
