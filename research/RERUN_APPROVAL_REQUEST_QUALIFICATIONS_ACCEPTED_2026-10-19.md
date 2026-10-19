# Request for a dated decision before any new experiment

Prepared 19 October 2026 for Ma’am Grace Tacadao. Draft for Henri and the research team to review and send; it has not been sent. Approval status: NOT RECEIVED.

Ma’am Grace,

Our fixed main test failed: at p = .50 and k = 5, the 36 non-transport reviewed cases had retrieval MAE of ₱1,903.82 against the same-purpose baseline’s ₱1,333.76 (−42.74% reduction). We will retain this result, the earlier provisional run, all seeds and all traces.

Medical accounts for 66.4% of retrieval absolute error. Its purposes have different base shares, while other types have uniform shares or one purpose. The baseline is given purpose explicitly; retrieval pools by type with purpose one of 39 equally weighted fields. The present comparison therefore combines purpose matching with household-pattern recovery. The separate weight search emphasizes purpose but does not detectably recover the household pattern at the tested signal levels.

We request your dated written agreement to two changes before producing any new comparison:

1. Correct the amount rule’s unknown-value handling. The present rule can score unknown resources as absent, unknown employed counts as zero and unknown income as zero points, numerically the same contribution as the highest income band. We propose excluding unknown fields from the household score and its available-field aggregation, with the exact rule below frozen first.
2. Amend rules eight and eleven of Section 3.2.2 for a separately labelled purpose-pool comparison. Eligible neighbors would have the same purpose and assistance type as the query, with the existing applicant and partner exclusions; numeric ranges and constants would use that same eligible pool. The purpose baseline would use exactly the same eligible reference pool. Purpose is available on the intake sheet in actual use.

The revised specification would separate household-pattern retrieval from purpose matching. It may still fail. Both corrected-data results will be reported, never only the better one. Thin primary medical pools are assistive device n = 14, chemotherapy n = 18 and dialysis n = 19 before exclusions.

## Exact unknown-value proposal for review

“Skip unknown” needs an aggregation definition: merely skipping an additive zero leaves the unknown-income score unchanged. No implementation of the correction or corrected amounts has been produced.

Revised proposal following the two-corrections brief: use shifted, bounded contributions before normalizing for observed fields. For an indicator x_i in [0, 1] with signed coefficient w_i, define c_i = w_i x_i − min(0, w_i). Then c_i lies in [0, |w_i|]. For the observed terms O, compute S = (Σ over O of c_i) × (Σ over all terms of |w_i|)/(Σ over O of |w_i|) + Σ over all terms of min(0, w_i). A complete record reproduces the original unshifted raw sum. Any record with no observed term of positive attainable range must stop generation rather than default to zero.

For the existing nonbinary income contribution, use its existing band points 0, 0.5 and 1.0 as x_i with unit coefficient. Expand counted supports, crises and discounts into their existing indicator contributions. The two sub-category indicators share the availability of their source field. More generally, for a field contribution t_i with fixed bounds l_i and u_i, use c_i = t_i − l_i and range a_i = u_i − l_i; the equivalent score is S = L + A × Σ observed c_i / Σ observed a_i, where L = Σ all l_i and A = Σ all a_i. Grouping multiple terms from one field must preserve their combined bounds and shared missingness; it must not treat an unknown sub-category as observed absence. Record the exact mapping and N/A interpretation before implementation. Genuine No, zero income, zero workers and applicable empty selections remain recorded values rather than unknowns.

This revision supersedes the earlier unshifted normalization proposal; neither proposal has been implemented in the generator or approved. The revised score is bounded between the full-score minimum and maximum, but boundedness does not guarantee movement toward the midpoint. For example, weights −1 and +1 with the negative-weight indicator observed as zero and the positive-weight indicator unknown give S = +1, the upper bound. Do not describe the method as automatically shrinking scores toward the middle. It assumes the observed normalized contributions can represent the missing portion and does not establish that missingness is ignorable.

Complete-record raw-score invariance does not imply unchanged generated amounts: recalibration after incomplete-record scores change can change the mean, standard deviation and standardized scores even for complete records. Recompute the calibration from each corrected case base once, then reuse it for its corresponding reviewed cases. Preserve income thresholds, contribution coefficients, noise construction, rounding, floors, ceilings, cost assumptions, intake records, type mix and seeds. Please approve this exact revised proposal or specify a replacement before implementation.

## Proposed rule wording

Rule eleven for the additional comparison: “A held-out case retrieves from every other eligible record with the same purpose of assistance and assistance type, excluding every event of that applicant and the required paired-case partner. The original same-assistance-type comparison is also retained and reported.”

Rule eight for that comparison: “Numeric ranges and constant-field exclusions are computed only from the query’s eligible same-purpose, same-type reference pool after exclusions, using the same reference-only rules as the original test.”

The 20% success criterion and Section 3.2.4.2 evidence standard remain unchanged. Do not change k, the search budget, the weights procedure, seeds, thresholds or noise in response to results. The prototype remains equal-weight case retrieval; neither experimental learned weights nor the amount rule configures its decisions.

## Sequence after written agreement

1. Save the original written agreement, date/time, approver, and exact approved specification and code/version reference. Agreement must precede any new generated amounts or comparison results.
2. Implement and unit-check only the approved correction, without selecting settings from new performance results. Freeze the implementation hash and any necessary implementation detail before evaluation.
3. Reuse the intake data and frozen seeds. Generate corrected outcomes and calibration as a new version. Preserve all previous datasets and drafts.
4. Rerun the original type-pool test on corrected data first.
5. Run the approved purpose-pool comparison second, including the same exclusions and evidence rules. Do not run previews before approval.
6. Report both new results and the retained earlier results, identifying the decision date, data version, changes and thin-pool limitations. Any further adjustment requires a new prospective decision, not tuning to pass.

## Decision record to be completed by the team

- Written agreement source: pending.
- Approver and role: pending.
- Decision date and time: pending.
- Exact unknown-value aggregation approved: pending.
- Pool/range wording approved: pending.
- Conditions or changes requested: pending.
- Specification version/hash approved: pending.

No reply or approval is inferred from this document being prepared. No new DSWD feedback is claimed. The private pair key remains within the team.

## Rationale and measured scope following the accepted-qualifications brief

The reason for the shifted rule is consistency in omitting unknown inputs and normalizing over available bounded components, rather than shrinkage toward the midpoint. This is analogous to Gower's available-field normalization. It is not literally the same calculation: Gower averages pairwise similarities using the fields available in both records; the proposed amount score aggregates contributions within one record over a different field set. This analogy is a methodological rationale, not a guarantee that every variation in the generated amount will be observable or recoverable through the distance. Missingness patterns, pairwise availability, income-band shapes and noise still constrain retrieval.

The proposed rule uses observed normalized contributions to represent the unavailable portion. Population-average imputation is not part of this proposal; it would introduce an assumed contribution beyond the record's observed inputs. Neither method is established as empirically superior by the present analysis.

Exact counts from the unchanged primary data: 463 events are complete across all 39 matching fields, and 537 are incomplete (772 unknown cells). Across the 28 household-rule fields, 545 events are complete and 455 are incomplete (606 unknown cells). The latter 455 is the relevant count of records with directly incomplete score inputs; it is not 537. Changes to calibration can also affect records with complete score inputs, without guaranteeing that every rounded or capped amount changes.

In the frozen reviewed source file, every case has an unrecorded non-outcome source entry: 287 cells across 21 columns. That broad count includes context and income-source columns. Only 18 of 40 cases have unknown matching fields, and 13 have unknown household-rule fields. The reviewed inputs remain frozen. The correction must handle the existing unknowns rather than remove missingness or regenerate the cases to make an experiment easier.

Any later corrected-data run must be recorded as a new approved data version with its recalibration and material missingness scope disclosed; preserve the present and all earlier runs and report both approved comparisons. Claude's agreement with these qualifications is not Ma'am Grace's dated written agreement. The experimental approval status remains pending.
