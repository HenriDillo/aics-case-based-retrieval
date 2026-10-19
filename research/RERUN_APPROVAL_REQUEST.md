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

Proposed available-field rule: represent the existing household score as per-field contributions c_j using its existing coefficients. Let a_j be each field’s fixed attainable contribution range (maximum minus minimum); treat the two sub-category terms as one field with their combined range. Let O contain only known, interpretable inputs. Compute S = (sum over O of c_j) × (sum over all fields of a_j)/(sum over O of a_j). This leaves complete-record scores unchanged while omitting unknown terms from both the sum and the available-range denominator. A fully unknown score is undefined and must stop generation for a documented resolution; do not silently substitute zero. Genuine No, zero income, zero workers, and applicable empty selections remain observed values under the existing schema; N/A must retain its documented field-specific meaning.

This normalization is a proposed methodological choice, not stated in the supplied brief or already approved. It assumes observed contributions can represent the unobserved portion; it may amplify extreme incomplete-record scores. Please approve this exact proposal or specify a replacement before implementation. It does not establish that missingness is ignorable. Preserve income thresholds, contribution coefficients, noise construction, rounding, floors, ceilings and cost assumptions. Recalibrate the corrected household score once on each existing case base and reuse its calibration for the corresponding reviewed cases. Preserve the existing intake records, type mix and seeds.

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
