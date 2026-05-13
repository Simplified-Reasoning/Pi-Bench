# East China Business Operating Loan PD Project: Development Working Draft (Excerpt, Internal Circulation Draft)

> Note: This document is a consolidated working draft circulated among the modeling team, strategy team, and model governance team. It is not an external-facing presentation deck.
> Definitions and metrics may differ across stages; individual indicators are subject to the finally signed-off version.

---

## A. Project Background and Practical Constraints (Excerpt)

- The business line has multiple objectives:
  - Credit approval access must control bad debt;
  - Existing customers require dynamic credit limit management;
  - The pricing team wants finer segmentation;
  - The approval team requires case-level traceability.

- Technical constraints and organizational constraints are equally important:
  - Monthly full recalculation window < 2 hours;
  - Must be compatible with the existing rules engine (there are inconsistencies between legacy system field names and new data warehouse field names);
  - The model governance team requires “quarterly auditable replay.”

- Definition notes (current version):
  - Label: A sample is considered bad if any of the following occurs within 12 months: “90+ days past due / write-off / judicial enforcement”;
  - Sample: Corporate business operating loan applicants; after removing samples with conflicting definitions, approximately 180,000 records remain;
  - Positive sample rate is around 7%, with large differences across industries.

---

## B. Data Definition Conflicts and Repair Records (Simplified Log)

### B1. Conflict List

1. `invoice_peak_cnt_6m` has different definitions in the risk-control ODS and the business analytics warehouse (one is based on calendar months, the other on billing-cycle months).  
2. `related_party_trade_ratio` showed a sudden shift before and after 2024Q2; initial investigation suggests it was caused by a change in upstream ETL join logic.  
3. `post_loan_collection_tag` was once mixed into the feature snapshot, creating a label leakage risk (already removed).  

### B2. Handling Actions

- Unified the “latest available time” principle: no feature may be later than application date T+1;
- Added a feature availability audit script (sampling and checking field timestamps);
- Applied “dual-threshold” exclusion to high-missingness and high-drift fields: missing rate >75% or PSI >0.25 in the most recent two quarters leads to direct exclusion.

### B3. Trace Records

- Modeling version: `credit_pd_r3_candidate_pack`  
- Data snapshot: `snapshot_2025_02_15`  
- Audit script version: `feature_audit_v0.9.6`

---

## C. Candidate Routes (Not Final Conclusions, Only Experimental Trajectory)

The modeling team once ran five routes in parallel, with the following internal code names:

- Route A1: Traditional linear approach (binning followed by generalized linear binary classification)
- Route A2: Bagging tree approach (multi-tree voting, relatively robust)
- Route A3: Boosted tree approach based on histogram splitting and leaf-wise growth
- Route A4: Ordered boosting approach friendly to categorical variables
- Route A5: Classic gradient boosted tree approach (called TB-420 by the engineering team)

> Note: Route names are internal code names and do not correspond to any external communication terminology.

---

## D. Experimental Records (Excerpt, Including Repeated Trials)

### D1. First Unified Rerun (2025-02-03)

| Route | AUC | KS | Brier | Relative Training Time |
|---|---:|---:|---:|---:|
| A1 | 0.741 | 0.317 | 0.061 | 1.0 |
| A2 | 0.779 | 0.370 | 0.056 | 2.5 |
| A3 | 0.811 | 0.420 | 0.051 | 1.8 |
| A4 | 0.807 | 0.413 | 0.052 | 2.1 |
| A5 | 0.818 | 0.435 | 0.049 | 2.4 |

Excerpt from meeting notes:
- Strategy team: A1 is interpretation-friendly, but its discriminatory power is relatively weak;
- Approval line: A3/A5 provide better segmentation and can reduce the manual review pool;
- Model governance: A5 needs supplementary “parameter-behavior mapping explanations”; otherwise, audit Q and A pressure will be high.

### D2. OOT Back-Test (2025Q1 Sample)

| Route | OOT AUC | OOT KS | Overall PSI | Notes |
|---|---:|---:|---:|---|
| A1 | 0.731 | 0.301 | 0.10 | Stable, but the performance ceiling is obvious |
| A3 | 0.798 | 0.401 | 0.17 | Good performance, but drift needs monitoring |
| A5 | 0.802 | 0.408 | 0.18 | Slightly better than A3, with drift close to warning level |

Supplement: A2/A4 were not included in the main comparison in this OOT round due to limited resource windows; historical results are retained for now.

---

## E. Technical Note for Route A5 (For Governance Review)

The following is excerpted from the training script parameter snippet (not complete):

```python
params = {
    "booster": "gbtree",
    "objective": "binary:logistic",
    "eval_metric": ["auc", "logloss"],
    "eta": 0.05,
    "max_depth": 5,
    "min_child_weight": 20,
    "subsample": 0.80,
    "colsample_bytree": 0.70,
    "gamma": 0.20,
    "reg_alpha": 0.10,
    "reg_lambda": 1.50,
    "seed": 2025,
}
```

Explanation summary written by the modeling team for the governance team:
- This route is an additive model that “adds weak learners round by round”;
- Each newly added tree fits the gradient direction of the current loss function; business colleagues may understand this as “continuously correcting the previous round’s errors”;
- The final output can be directly interpreted as default probability after logistic mapping.

---

## F. Strategy Simulation (Approval Perspective, Not Equivalent to Final Decision)

Under the same pre-existing rule conditions, if the current preferred candidate route is adopted:

| Threshold Scheme | Pass Rate | Expected Bad Debt Rate | Manual Review Share | Risk-Adjusted Return (Estimate) |
|---|---:|---:|---:|---:|
| Scheme S1 (Growth-Oriented) | 61.2% | 4.8% | 18.4% | +6.1% |
| Scheme S2 (Baseline) | 54.7% | 3.9% | 22.6% | +7.4% |
| Scheme S3 (Conservative) | 47.9% | 3.2% | 25.1% | +6.8% |

Verbal comments from the Approval Committee (not signed):
- Regular industries should first use S2;
- For highly volatile industries, try raising the threshold under S3;
- Keep a challenger model so that switching is possible when the economic cycle changes.

---

## G. Interpretability and Business Consistency (Internal Debate Points)

### G1. Positive Conclusions
- The direction of important features is generally consistent with human expert judgment:
  - Increased concentration among core customers -> higher risk
  - Longer collection cycle -> higher risk
  - Larger invoice-tax deviation -> higher risk

### G2. Points of Dispute
- The approval team wants “more intuitive single-case rejection reasons”;
- The modeling team believes local explanations are usable, but the cost is significantly higher than that of the linear baseline;
- The governance team requires supplementary explanation of the linkage between “feature stability and threshold drift.”

---

## H. Open Issues (As of This Draft)

1. If external demand contracts after 2025Q2, should the current threshold be tightened in advance?
2. Relationship-network features have an “inconsistent information freshness” issue in some industries, which may lead to segmentation errors.  
3. It has not yet been finally signed off whether A3 or A1 should be retained as the main backup challenger route.

---

## I. Risk List (For Investment Committee Q and A Preparation)

- Overfitting risk: The parameter space is relatively large, and excessive pursuit of AUC may harm generalization;
- Drift risk: PSI is already close to the warning threshold, so monthly changes need to be monitored;
- Interpretability risk: For single-case approval communication, tree models are more complex to explain than linear approaches;
- Data governance risk: If changes in field definitions are not synchronized with governance, hidden performance degradation may occur.

---

## J. Appendix: Definition Notes for Routes A1/A2/A3/A4 (Summary)

- A1 (Linear Binning Route):
  - Advantages: Direct interpretation and low governance cost;
  - Disadvantages: Limited ability to express nonlinearity and high-order interactions.

- A2 (Bagging Tree Route):
  - Advantages: Relatively strong noise resistance;
  - Disadvantages: Probability calibration and ranking performance are usually weaker than mainstream boosted tree routes.

- A3 (Leaf-Wise Boosting Route):
  - Advantages: High training efficiency and stable performance on large samples;
  - Disadvantages: Parameters are strongly coupled with the data distribution, so drift monitoring is required.

- A4 (Ordered Boosting Route):
  - Advantages: Friendly mechanism for handling categorical variables;
  - Disadvantages: Training time and resource usage are not advantageous in the current environment.

- A5 (Current Preferred Candidate):
  - See the technical note and simulation results for Route A5 above.

---

## K. Current Stage Conclusion (Internal Use Only)

At present, the team is more inclined to move A5 into gray release as the Champion, with A3 as the main challenger;  
however, whether it will officially become the “production default” depends on model governance sign-off and the Q2 data back-test results.