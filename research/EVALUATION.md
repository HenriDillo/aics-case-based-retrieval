# Fixed equal-weight evaluation

**Audit status, 19 October 2026:** the existing failed run describes the provisional
`v26-preparation-1` datasets, not a certified final v25 experiment. The aggregation
and holdout rules below are implemented, but the generation choices require
reconciliation. See `ALIGNMENT_AUDIT.md`. Preserve the failure and original outputs.

Run from the repository root:

```powershell
.venv/Scripts/python.exe -m research.evaluate --input research/generated/v26 --output research/generated/evaluation-v1
```

The output directory must not exist. The evaluator records the protocol before calculating results, hashes input CSVs, and never imports the synthetic amount generator or reads its household-score diagnostics. No weights, seeds, distance settings, purpose filters, or thresholds are selected from these results.

For each of the four amount conditions, every one of the 1,000 case-base events is queried after excluding all events of its applicant. There are 844 applicants. Ranges and constant-field removal use only eligible same-type reference records. The 40 reviewed sheets are evaluated separately against the case base; they are never inserted into it. The explicit exact/near partner map also excludes partners if they are ever present in the reference pool.

Five neighbors are required. Cost-bearing predictions use the median of the neighbors' actual recorded grant/cost ratios times the query's own cost. Food and cash use median grants. Predictions are not rounded or clipped to the generation schedule: the manuscript's specified aggregation is evaluated directly. These predictions are research diagnostics, never recommendations in the app.

The baseline uses all same-type, same-purpose reference events under the same applicant exclusions. It does not filter on household features. Missing costs, empty baselines, or fewer than five defined neighbors cause an explicit error instead of silently dropping queries.

Reports contain per-type event-level peso MAE and scaled MAE, plus per-applicant averages for later paired comparisons. Scaled widths are 149,000 for hospital/other medical, 10,000 for medicines/laboratory, 20,000 for funeral, 4,500 for education, 2,000 for food, and 9,000 for cash. Transportation has no scaled error and is excluded from pooled main results. Negative reduction means retrieval is worse than the purpose baseline. A zero-error baseline has undefined percentage reduction.

The prespecified main test uses p50, the 36 non-transportation reviewed cases, pooled **peso** MAE, and at least a 20% reduction. It does not use scaled errors, applicant averages, or a subset chosen after seeing results. The p00 control and other conditions are descriptive checks. A local improvement in p00 warrants inspection; a single finite sample does not by itself prove leakage.

This run evaluates equal weights, plain scaling and categorical duration only. It does not constitute the manuscript's 30-seed challenger comparisons, scaling selection, learned-weight evaluation, or statistical evidence about real applicants. A failure must remain a failure in reporting; subsequent work must not retune this held-out test into a claimed success.

The generation manifest's `amount_evaluation_run: false` describes its earlier generation stage. It is preserved; the evaluation has its own outputs and provenance.
