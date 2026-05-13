# Huadong Operating Loan PD Model Gray-Release Performance Review Memo (Internal Monitoring Summary)

> Scope: Pre-investment-committee discussion draft; not a formal sign-off document.  
> Observation window: 2025-04-01 to 2025-05-15 gray-release monitoring period.  
> Note: Since full 12-month bad-outcome labels have not yet been fully observed, some risk assessments rely on early risk proxy indicators.

---

## A. Current Deployment Setup

- Current Champion: A5
- Shadow Challenger: A3
- Replay Baseline: A1
- Current default thresholding: S2 for regular industries; high-volatility industries have not yet been switched separately, but the approval committee has requested an assessment of whether a more conservative setup is needed.

Additional notes:
- A5 entered gray release on 2025-04-01;
- A3 remains in shadow mode for apples-to-apples comparison;
- A1 is retained as a linear replay baseline, mainly for explainability and governance reference.

---

## B. Route Definitions at a Glance

- A1: Binning + Logistic Regression (WOE / GLM binary classification)
- A3: Boosted-tree route based on histogram splitting and leaf-wise growth
- A5: Classic gradient-boosted-tree route, implemented in engineering with `booster=gbtree` and `objective=binary:logistic`

---

## C. Overall Monitoring Results (Gray-Release Window Summary)

During the gray-release window, a total of 32,400 loan-application samples were included. Under unified sample definitions, unified proxy labels, and unified feature snapshot timing, the monitoring team obtained the following results:

| Route | Current Role | AUC | KS | Brier | Overall PSI | Relative Training Time | Per-Case Local Explanation Latency |
|---|---|---:|---:|---:|---:|---:|---:|
| A5 | Champion | 0.796 | 0.401 | 0.053 | 0.16 | 2.3 | 4.8 sec |
| A3 | Challenger | 0.791 | 0.395 | 0.054 | 0.14 | 1.7 | 4.1 sec |
| A1 | Replay Baseline | 0.742 | 0.316 | 0.061 | 0.09 | 1.0 | 0.2 sec |

Internal discussion excerpts:
- The business side believes A5 provides the best segmentation effect and more room for risk-based pricing;
- The approval side reports that A5's single-case explanations are generally usable, but complex cases still require manual second-pass translation;
- The governance side believes A5 is still acceptable at present, but its explanation cost and drift-monitoring pressure are both higher than A1's.

---

## D. Industry-Segment Observations

### D1. Regular-Industry Samples

| Route | AUC | KS | PSI | Notes |
|---|---:|---:|---:|---|
| A5 | 0.804 | 0.409 | 0.13 | Best performance, drift under control |
| A3 | 0.798 | 0.401 | 0.12 | Slightly weaker than A5, but relatively stable |
| A1 | 0.748 | 0.321 | 0.08 | Best interpretability, but insufficient discrimination |

### D2. High-Volatility Industry Samples (foreign-trade chains, parts of commodity-linked chains, regional construction materials)

| Route | AUC | KS | PSI | Notes |
|---|---:|---:|---:|---|
| A5 | 0.772 | 0.382 | 0.21 | Discrimination still acceptable, but drift has crossed the internal attention line |
| A3 | 0.776 | 0.386 | 0.17 | Slightly better than A5 and more stable |
| A1 | 0.731 | 0.301 | 0.10 | Too conservative and insufficiently discriminative |

Monitoring notes:
- In high-volatility industries, A5's PSI has reached 0.21, exceeding the monitoring team's internal attention line of 0.20;
- A3 is more stable in this segment overall, so the approval committee explicitly requested that it be included in the conservative-plan discussion.

---

## E. Threshold-Plan Simulation (Under the Current Champion Setup)

Without changing the existing front-end rules, the monitoring and strategy teams produced the following lightweight threshold simulation:

| Threshold Plan | Approval Rate | Manual Review Share | Early Risk Proxy Rate | Risk-Adjusted Return (Estimated) | Notes |
|---|---:|---:|---:|---:|---|
| S2 (baseline) | 54.9% | 22.8% | 3.9% | +7.1% | Balanced for regular industries |
| S3 (conservative) | 48.1% | 24.7% | 3.2% | +6.7% | More stable for high-volatility industries |

Additional notes:
- The business side prefers to keep S2 as the default configuration for regular industries;
- For high-volatility industries, if A5 is retained, it should at least be paired with S3;
- There is also a view that directly switching to A3+S3 in high-volatility industries would make governance communication easier.

---

## F. Governance and Engineering Constraints

- The monthly full rerun window still needs to stay within 2 hours;
- Model governance requires quarterly auditable replay capability;
- Average per-case local explanation latency is about 4.8 seconds for A5, 4.1 seconds for A3, and 0.2 seconds for A1;
- In manual-review samples, about 7.6% of A5 cases require supplemental second-pass explanations;
- Relationship-network features have an "inconsistent information freshness" issue in some high-volatility industries;
- If upstream field-definition changes are not synchronized in time, latent performance degradation in tree models is usually harder to detect early than in A1.

---

## G. Monitoring Team's Recommended Switching Triggers (Discussion Draft)

If any of the following occurs, a Champion/Challenger review should be initiated:

1. Overall PSI >= 0.20 and does not fall back for two consecutive months;
2. A5's AUC drops below 0.790;
3. A5's KS drops below 0.390;
4. Per-case local explanation latency exceeds 5 seconds and the explanation-exception rate exceeds 8%;
5. High-volatility-industry PSI >= 0.22 and the manual-review pool simultaneously expands abnormally.

---

## H. Current Discussion Leaning

- Regular industries: continue using A5 as the Champion, preferably paired with S2;
- High-volatility industries: if the investment committee prioritizes stability and governance communication cost, A3+S3 can be considered as the conservative plan;
- A1 should not return to the primary route, but should continue to be retained as an explainability and audit reference baseline.

---

## I. Risk Reminders

- The current observation window is still short, and part of the risk assessment relies on early risk proxies rather than complete 12-month bad-outcome performance;
- Although A5 performs better overall, its drift pressure is more visible in high-volatility industries;
- The information-freshness issue in relationship-network features may cause inconsistent segment stability across industries;
- If overall AUC is overemphasized while single-case explanation burden and governance pressure are ignored, subsequent approval communication cost may be underestimated.

---

## J. Questions Ready for Direct Discussion in the Meeting

1. Should regular industries continue to use A5+S2 as the default setup?
2. For high-volatility industries, should the team use A5+S3 or switch directly to A3+S3?
3. Should the Champion/Challenger switching thresholds in Section G be formalized into the monthly monitoring mechanism?
