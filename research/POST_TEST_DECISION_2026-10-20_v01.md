# Post-test decision and fixed rerun specification

Recorded 20 October 2026, 20:13:53 PHT (UTC+08:00), before generating corrected outcomes or running either new comparison.

Henri explicitly instructed: “Decision made, we're not asking Ma'am Grace first. Go ahead with the correction and both reruns.” This supersedes the earlier instruction to wait. No prior dated agreement from Ma'am Grace is claimed.

The required disclosure is retained verbatim:

> The pool amendment and the missing-value correction were decided after the fixed main test had been run and had failed. Both the original type-pool result and the amended purpose-pool result are reported, and the original result is not withdrawn.

## Changes authorized

1. Apply the previously documented shifted bounded-contribution missing-value correction. For field contribution t_i with fixed bounds l_i and u_i, c_i = t_i − l_i, a_i = u_i − l_i, L = Σ all l_i, A = Σ all a_i. Use S = L + A × Σ observed c_i / Σ observed a_i. Stop on zero observed range. Explicit No, zero and recorded empty/not-applicable sub-category remain observed; unknown fields are excluded. Preserve all 28 rule fields and coefficients. Income's single contribution retains 0, 0.5, 1.0 bands and its existing thresholds. The sub-category terms share one availability mask and range [0, 1.3]. Recalibrate once on each existing corrected case base and reuse that calibration for its forty test cases.
2. Run the original same-type comparison on corrected outcomes first, then the amended same-purpose-and-type comparison. In the latter, reference-only ranges, constants and fuzzy quartiles (where applicable) use the same eligible purpose pool. Applicant and paired-partner exclusions remain fixed. No fallbacks or silent dropped queries.

## Factors held fixed

- Existing intake records, missingness, costs, type mix, frozen forty cases and pair mappings.
- All existing amount/noise seeds, calibration convention, total log spread, condition values p = 0, .25, .50, .75, main p = .50, rounding, floors and ceilings.
- k = 5; selected plain money scaling and categorical duration. Do not reopen the earlier transformation selection after seeing new results.
- Shared 39 nonnegative weights summing to 39, five applicant folds, original fold/optimizer seeds, fixed 200-evaluation search budget, scaled applicant-averaged objective.
- Existing primary base and thirty weight-replication inputs, with their existing master seeds 51001–51030. Correct each existing input rather than generating a new intake sample.
- Thirty-set noise floor and the original applicant-paired Wilcoxon evidence criterion. Both pool configurations receive the same fixed procedure.
- Fixed main-test criterion: at least 20% pooled peso MAE reduction on the 36 non-transport test cases against the same-purpose baseline. Transportation remains separate.
- The prototype remains equal-weight case retrieval. Experimental amended pools or learned weights are not silently deployed to it.

The earlier scaling-selection results remain historical; those comparisons are not rerun or used to choose new settings. State this limitation rather than implying they were validated again on corrected outcomes.

## Required execution order

1. First check all four frozen twin pairs on the existing data. This passed for every existing condition before correction.
2. Implement the correction, generate corrected outcomes into a new directory, and immediately run the vendor `check_pairs` plus full input-equality checks for J01/J22, J13/J28, J11/J30 and J20/J35. Both pairs with missing rule inputs receive special attention. Check all four conditions, every corrected input set, and record-order invariance. Stop on any failure before any retrieval evaluation or fitting.
3. Freeze the corrected code hash and record passed pair checks. Run corrected original type-pool evaluation first.
4. Run corrected amended purpose-pool evaluation second. Preserve complete event errors, seeds, folds and traces for both.
5. Report both results whatever they show, alongside the failed pre-correction fixed test and earlier provisional results. Make no prospective-approval or preregistration claim for these new amendments.

## Manuscript and Chapter 5

Use Manuscript Chapters 1–3 v27 dated 20 October 2026 as the current source. It removes the social-worker answer conditionals in Sections 3.2.1 and 3.4 and the Chapter 1 commitment to return to CIS. No social worker participates in the study, and there is no UAT or SUS. Historical packet-review statements in v27 are not evidence of social-worker participation or new feedback on these runs.

Henri assigns Chapter 5 to Rygan and explicitly directs that its recommendations must not include a commitment to return to CIS. Sending that message is authorized, but a confirmed recipient address or messaging destination is still needed.
