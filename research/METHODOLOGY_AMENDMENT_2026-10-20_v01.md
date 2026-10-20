# Methodology amendments recorded after the fixed test

The current source is Manuscript Chapters 1–3 v27, dated 20 October 2026. Its DOCX is preserved unchanged. This note records the amendments actually used in the new offline comparisons; it must not be presented as the original approved plan.

The pool amendment and the missing-value correction were decided after the fixed main test had been run and had failed. Both the original type-pool result and the amended purpose-pool result are reported, and the original result is not withdrawn.

## Pool definition and reference statistics

Retain the original type-pool experiment as a historical result and rerun it on corrected outcomes. For the separately labelled amended comparison, an eligible reference must match both the query’s assistance type and its intake purpose. Keep applicant and documented pair-partner exclusions unchanged. Estimate numeric ranges, field constants and any applicable fuzzy quartiles only from that eligible reference pool. The purpose written beside the outcome is never used as an independent matching feature.

This affects the pool and range descriptions in Section 3.2.2 rule eight, the training and held-out reference pools in rule eleven, and the formal definition of C in Section 3.3. Under the amended comparison, C comprises events with matching assistance type and intake purpose. The 39-field schema, asymmetric shared-absence treatment, missing comparison masks, Jaccard terms and outcome exclusion remain unchanged. Within a purpose pool, purpose is constant and therefore inactive in the distance.

## Synthetic household score

For each of the existing 28 household-rule fields, retain its contribution tᵢ and fixed bounds [lᵢ, uᵢ]. Let L be the sum of all lower bounds and A the sum of all contribution ranges. Use:

S = L + A × Σ observed (tᵢ − lᵢ) / Σ observed (uᵢ − lᵢ).

Unknown fields enter neither observed sum. Explicit No, zero and a recorded empty sub-category remain observed. The combined sub-category contribution has one availability mask and range [0, 1.3]. Keep income’s existing thresholds and its single 0, 0.5 or 1 contribution. Stop on an all-unknown record. Complete raw scores are unchanged, but recalibration can change their standardized scores and amounts. Recalibrate once on each existing 1,000-event base and reuse its calibration for the forty fixed cases.

## Fixed settings and an execution limit

Keep p50 main, k5, equal weights for the fixed test, plain money, categorical duration, the same intake records and missingness, amounts/noise seeds, cost bounds, grant rounding, folds, optimizer seeds, 200-evaluation budget, shared 39-weight procedure, four signal conditions and the original evidence criteria. Earlier transformation selection is not repeated on corrected outcomes. Neither the original failure nor a failed corrected test may be reclassified using a different k or criterion.

One purpose-pool replication is infeasible: seed 51024 fold 0 has only four eligible assistive-device references after exclusion. The full thirty-set weight-evidence standard is unavailable. The primary comparison and the other 29 replications are reported, with no replacement seed, omitted query, reduced k or 29-set noise-floor substitution. See the dated feasibility addendum for the input-only discovery and explicit handling.

## Participation and scope

Use v27’s statement that no social worker answered case sheets or used the prototype in the study. No UAT or SUS was conducted. Historical consultation is not participation or approval of these amendments. Do not restore a commitment to return to CIS. Chapter 5 belongs to Rygan; this note does not draft that chapter or its recommendations.
