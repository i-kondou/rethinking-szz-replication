# Developer-Informed Oracle Verified (DIO-V)

- [dataset.json](dataset.json): 67 cases from 60 repositories; original labels are retained alongside revisions.
- Corrected: 907, 1381, 1728 and 3530. Unchanged: 63 cases.
- Excluded: nine ambiguous cases and 1121, 2557, 2911, which lack a single defensible replacement BIC. See [RQ3 evidence](../../analysis/rq3/README.md).
- From the package root, run `python3 -B analysis/dataset.py` to verify and rescore 1,005 saved answers without model calls.
