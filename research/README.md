# Synthetic cost and amount pipeline verification

**Audit status, 19 October 2026: provisional implementation, not certified as the
final v25 study pipeline.** The checks below establish internal consistency, not
approval of changes to the supplied amount rule. See `ALIGNMENT_AUDIT.md` for
confirmed departures, unspecified choices and unfinished requirements. Preserve
existing outputs; resolve those items before further study experiments.

Prepared 19 October 2026. Pipeline revision `v26-preparation-1`; the supplied manuscript remains v25. This is an implementation extension with documented assumptions, not a claim of new adviser approval.

The pipeline generated four conditions for 1,000 case-base events across 844 applicant IDs and the 40 reviewed test sheets: 4,160 generated amounts in total. The original bundle and original app case-base CSV remain unchanged.

## What was reconciled

| Item | Resolution |
| --- | --- |
| Missing laboratory share | 0.9052 from 5,250 / 5,800 in the Region XI row of Table 29. |
| Missing dialysis and chemotherapy shares | 0.3556 for each, using the published combined row of 8,228.57 / 23,142.86. Applying a combined row separately is an explicit assumption. |
| Conflicting assistive-device ceiling | Retained the current amount-rule ceiling of 150,000 rather than the older figures module's assumed 10,000. This is a study convention, not a current-policy assertion. |
| Cost distribution unspecified | Uniform intervals from 0.5 to 1.5 times each published benchmark; choices fixed before generation. Costs rounded to 50 pesos. |
| Educational purpose costs | All three purposes use the 11,700 tuition benchmark, as a proxy assumption consistent with the approved share's tuition denominator. It is not evidence that allowances and supplies cost the same as tuition. |
| No Region XI device/transport cost benchmark | Assumed ranges: devices 10,000–40,000; transportation 1,000–10,000. No benchmark-pass claim is made for these. |
| Repeated events overwritten by applicant ID | Calculate household scores for each event independently. |
| Unknown answers previously treated as No or zero in parts of the amount rule | Unknown fields contribute no points. Explicit No and recorded zero retain their stated effects. No source values are imputed. |
| Grant could exceed cost after floor/rounding | Round within the feasible floor/ceiling/cost interval. Reject impossible inputs instead of violating a constraint. |
| Calibration saved from only 40 cases | Recalculated on all 1,000 prepared case-base events and reused for both datasets. |
| Different schemas produced different noise payloads | Normalize the same 39 matching fields and assistance type before hashing; exclude identifiers, dates and outcomes. Cost and condition are explicit inputs to the amount seed. |

The last normalization change intentionally versions the generated noise: these outputs, including p00, are not byte-compatible with the old forty-case amount files. Old outputs were not overwritten. Within this pipeline p00 is invariant to household calibration; no retrieval evaluation was used to select a seed.

## Published source

DSWD PDPB (2022), Process Evaluation of AICS, Table 29 on printed page 41; Table 31 continued on page 42; Tables 32–34 on page 42. The PDF's page images were checked against the extracted table text. The published cost may include payments by other payers, while this study treats cost as the outstanding balance, so the comparison is approximate as the manuscript states.

[Official report download](https://pdpb.dswd.gov.ph/download/process-evaluation-of-aics/?wpdmdl=4603)

## Consistency repair

244 events had a Wage Earner sub-category while both worker counts were explicitly zero. The prepared outputs remove only those contradictory wage labels. Worker counts, income values, income bands, purpose, type, IDs and dates are unchanged. Other sub-category labels are preserved. An emptied set becomes explicit not applicable rather than unknown. Every change is listed in `consistency_changes.json`.

Ten additional wage-labelled events cannot be checked because worker counts are missing. They are flagged and retained. None of the forty reviewed cases needed a wage-label repair. Their documented costs are preserved exactly as printed, using the outstanding balance when a hospital bill contains two amounts.

## Cost checks

No cost range required the allowed one-time adjustment. No shares were adjusted.

| Group | Published mean cost | Generated mean cost | Difference |
| --- | ---: | ---: | ---: |
| Hospital bill | 147,375.00 | 150,927.42 | +2.41% |
| Funeral | 45,230.74 | 46,048.33 | +1.81% |
| Medicines | 7,831.71 | 7,949.84 | +1.51% |
| Laboratory | 5,800.00 | 6,040.52 | +4.15% |
| Educational | 11,700.00 | 11,261.25 | -3.75% |
| Chemotherapy | 23,142.86 | 21,652.78 | -6.44% |
| Dialysis | 23,142.86 | 24,555.26 | +6.10% |

## Validation results

- 63 tests pass, including the full existing API/retrieval suite and 15 pipeline tests.
- Two complete builds produced identical output file hashes.
- All four exact pairs have identical normalized inputs and equal amounts at every condition.
- Each near pair differs in exactly its designated matching field. Amount differences are reported; no seed was changed to obtain a desired direction.
- Every amount is a multiple of 50, respects the applicable floor and ceiling, and never exceeds documented cost.
- Transportation equals ticket cost exactly at all four conditions.
- Food and cash relief have no documented cost; their amounts are generated directly.
- Calibration: n=1,000 events, mean household score=3.01185, population SD=1.4580867866831522.
- Case-base income bands: 529 below food threshold, 148 between thresholds, 271 at/above poverty threshold, 52 unknown.
- Reviewed-case income bands remain 26 / 7 / 7.
- Source hashes verified unchanged; generated CSVs reloaded without changing normalized values.

The nominal p setting controls the latent household/noise mixture before floors, caps and rounding. It is not a claim that observed peso variance has exactly that explained proportion.

## Reproduce

Run from `C:\Users\henri\Documents\Code Files\aics-triage-system`:

```powershell
.\.venv\Scripts\python.exe -m research.build_dataset --output research/generated/reproduction
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```

Choose a new output directory each time; the command refuses to overwrite a prior run. No retrieval or statistical comparison runs as part of this command.

## Files and what to use

- `case_base_p00.csv`, `case_base_p25.csv`, `case_base_p50.csv`, `case_base_p75.csv`: prepared case base with costs and generated outcomes.
- `judged_p00.csv`, `judged_p25.csv`, `judged_p50.csv`, `judged_p75.csv`: reviewed cases with existing costs and new outcomes under shared calibration.
- `calibration.json`, `manifest.json`: scale, seeds, source/code/output hashes and counts.
- `cost_checks.json`: benchmark checks and any range correction (none in this run).
- `consistency_changes.json`: exact field-change log and unverifiable cases.
- `validation.json`: constraint and pair checks plus per-purpose means and aggregate shares.
- `diagnostics_p*.json`: event-specific scores, realized shares and binding constraints; research-only, never matching features.

The running app still reads the preserved intake-only case base. This milestone produces the research datasets; it does not silently switch the app or start evaluation. The next evaluation must use matching p conditions for case base and held-out cases and must exclude applicant events and applicable pair partners.

## Checklist before using these in Chapter 4

- [ ] Retain this reconciliation note with the project; incorporate the new assumptions and implementation corrections in the methodology before comparing methods.
- [ ] Treat the 10 unverifiable wage labels and 52 missing incomes as reported data limitations.
- [ ] Use one matching condition for both files; p50 is the preselected main condition.
- [ ] Keep identifiers and diagnostics out of distance calculations.
- [ ] Report generated versus published means and shares without describing their agreement as validation of real social-worker behavior.
- [ ] Keep pair information and all project materials private to the team.
- [ ] Run the purpose baseline and leakage checks next; no accuracy or 20% improvement claim has been made.


## Completion update — 19 October 2026

The earlier status below is historical. The completed reconciled implementation, full experiments, and Chapter 4 draft are documented in RUNBOOK.md and chapter-4-draft.md. The main test failed; its result is preserved. Implementation choices are not adviser approval, and new external feedback remains outstanding. Work stops at the Chapter 4 draft.
