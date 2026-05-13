# German Credit Raw Data Schema

Source URL:
- https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data

Local raw file:
- `german.data`

The local file is the original whitespace-delimited Statlog German Credit data file without a header row.

Column order:
1. checking_status
2. duration
3. credit_history
4. purpose
5. credit_amount
6. savings_status
7. employment
8. installment_commitment
9. personal_status
10. other_parties
11. residence_since
12. property_magnitude
13. age
14. other_payment_plans
15. housing
16. existing_credits
17. job
18. num_dependents
19. own_telephone
20. foreign_worker
21. target

Target coding for this task:
- `target = 1` means good credit.
- `target = 2` means bad credit.
- For validation metrics, define `bad = 1` when `target = 2`, otherwise `bad = 0`.

Dataset background to verify from the public UCI page:
- 1,000 rows.
- 20 input attributes plus the target label.
- This is a benchmark dataset, not evidence by itself that a production applicant population is represented.
