# Proposed implementation choices — awaiting review

Prepared 19 October 2026 for Henri. These are proposals, not instructions found in
the manuscript and not evidence that the adviser has approved a change. No fuzzy,
duration-selection, or learned-weight comparison has been run using them.

The v25 manuscript, especially Sections 3.2.2–3.2.4, determines the experiment.
It specifies quartile breakpoints, the fitting objective, five applicant folds,
thirty generated sets, and the two evidence tests. It does not completely specify
the algorithms below. Review these choices before implementing or comparing them.

## 1. Fuzzy money comparison

**Recommendation: three overlapping memberships, with linear transitions.**
This gives a precise meaning to the paper's low, middle, and high money levels
without introducing income thresholds from the amount-generating rule.

For each money field, calculate q1, q2, q3 at probabilities .25, .50, .75 from
known numeric values in the eligible, same-type reference records. Use linear
quantile interpolation: index (n−1)p, interpolating between adjacent sorted values.
Exclude the query applicant and, during fitting, the entire held-out fold.

For q1 < q2 < q3, define the membership vector M(x) = (low, middle, high):

| Value | Membership vector |
| --- | --- |
| x ≤ q1 | (1, 0, 0) |
| q1 < x < q2 | ((q2−x)/(q2−q1), (x−q1)/(q2−q1), 0) |
| x = q2 | (0, 1, 0) |
| q2 < x < q3 | (0, (q3−x)/(q3−q2), (x−q2)/(q3−q2)) |
| x ≥ q3 | (0, 0, 1) |

The field similarity is **1 − 0.5 × sum(abs(M(x) − M(y)))**. Identical
memberships score one; completely separated memberships score zero. The score
enters the existing Gower calculation exactly where a money-field score enters.

If adjacent quartiles coincide but the reference field is not constant, use
plain range similarity for that field/query and record a fallback count. Remove
constant fields under the paper's existing rule. Unknowns remain excluded;
recorded not-applicable values retain the existing categorical handling.

Tradeoff: this is transparent and reproducible, but saturation beyond the outer
quartiles deliberately makes very low values equivalent to each other and very
high values equivalent to each other. It is one defensible interpretation, not
the only fuzzy formula the manuscript could mean. A team-supplied formula would
replace this proposal before experiments, not after seeing its results.

## 2. Weight optimizer and fixed search budget

**Recommendation: seeded pairwise weight-transfer search, 200 objective
evaluations per fold, including the starting equal-weight vector.**

1. Start from all 39 weights equal to one. Use the paper's applicant-averaged,
   scaled absolute-error objective on the other four folds, with applicant-level
   leave-one-out retrieval inside that fitting pool. Use five neighbors.
2. At each of the next 199 evaluations, uniformly choose an ordered pair of
   distinct field indices. Transfer a fraction of the donor's current weight to
   the recipient. Cycle through fractions 0.25, 0.50, and 1.00. If the selected
   donor is zero, sample another positive donor. All fields remain eligible to
   receive weight, including fields currently at zero.
3. Keep a candidate only when its objective is strictly lower than the incumbent
   by more than 1e-12. Keep the incumbent on a tie. This preserves nonnegative
   weights summing to 39 and allows zero weights without using rule coefficients.
4. Save every candidate objective, incumbent objective, candidate weights, seed,
   and evaluation number. Stop at the fixed budget, even after a long plateau.
   This is a bounded heuristic; do not call the resulting weights optimal.
5. Evaluate held-out applicants using all other case-base applicants as references,
   exactly as the paper specifies. Use the identical reference pool for equal
   weights. Never fit on the held-out fold or on the forty reviewed cases.

Use deterministic distance ties ordered by applicant ID and event ID, matching
the baseline's existing behavior. Exclude undefined pairs and count them. As a
proposed safeguard, reject a candidate with infinite objective if any fitting
query cannot obtain five defined neighbors; never improve a score by dropping
that query. Report an unavailable evaluation if the baseline itself lacks five.

Tradeoff: 200 evaluations bounds computation and is easy to audit, but a greedy
search may miss better weight vectors. This limitation must appear in the report.
Do not increase the budget because a result is disappointing. Benchmark one
complete five-fold run after approval; if a resource-driven protocol amendment
is needed, document it before launching the thirty-set comparisons.

## 3. Remaining experimental conventions

These additional choices make the proposed protocol runnable; they also require
review because the paper does not settle every detail.

| Item | Proposed convention |
| --- | --- |
| Separate selection data | Generate a new 1,000-event set using the same reconciled generator and repeat-applicant mechanism. Never use the forty reviewed cases for selection. |
| Selection order | Compare money transformations with equal weights and categorical duration; then compare duration treatments with equal weights under the selected money treatment. Freeze both before weight fitting. |
| Seed registry | Selection primary master seed 41000, selection replicates 41001–41030; weight replicates 51001–51030. Retain the supplied case base as the primary weight set. Preserve the earlier provisional run separately. |
| Seed derivation | SHA-256 of UTF-8 `aics-v25-review-1\|MASTER\|DOMAIN\|INDEX`, with the backslashes omitted; first 16 hexadecimal digits interpreted as an unsigned integer. Domains `intake`, `cost`, `fold`, `optimizer`; index 0 except optimizer index 1–5 for folds. Freeze the per-record amount-noise contract separately under the generator reconciliation below. |
| Fold assignment | Sort applicant IDs, shuffle with the registered fold seed, then assign round-robin to five folds. All events for an applicant stay together. Persist the complete assignment. |
| Thirty-set evidence | Paired baseline-minus-challenger mean errors per generated set; sample standard deviation (denominator 29) of the 30 gaps is the noise floor. Require mean gap strictly greater than that SD. Report peso and scaled gaps; propose scaled applicant errors for the selection criterion, matching the fitting objective. |
| Wilcoxon | Use paired applicant errors from the designated primary set, not a pooled stack of repeated synthetic applicants across 30 sets. Two-sided signed-rank test; discard zero differences; average ranks for tied absolute differences; asymptotic tie-corrected calculation without continuity correction. All-zero differences give p=1. Use scaled applicant errors for this proposed test and report the paired peso difference alongside it. |
| Multiplicity | Require p < .025 for each money challenger; p < .05 for duration and learned weights. Also require the noise-floor test. If both money challengers pass, choose the lower primary-set scaled error; an exact tie keeps log, declared here before comparison. |
| Condition for selecting settings | Propose p=.50 for money/duration selection. Report fixed settings and weight comparisons separately at all four p conditions; no selection of a favorable condition for the main failure test. |
| Retrieval-count sensitivity | k = 3, 5, 7, 10 as descriptive sensitivity, with selected settings and learned weights held fixed. No retuning per k. Main failure test and search remain k=5. |
| Repeated full-run timing | Three runs with identical inputs/seeds; report median wall time. Retain one result set, verify repeated results match, and do not treat timing repetitions as independent evidence. |

The supplied main failure criterion remains unchanged: p=.50, k=5, pooled peso
MAE on the 36 non-transport reviewed cases, at least 20% reduction against the
same-purpose baseline. Transportation is reported separately. The proposals
above cannot replace that criterion or turn the preserved failed run into a pass.

## 4. Generator reconciliation is a separate prerequisite

Approval of the fuzzy formula and optimizer alone does **not** approve the earlier
provisional generator choices. `ALIGNMENT_AUDIT.md`, A1–A5, remains the record:

- The local missing-value score behavior differs from the supplied amount code.
- The local normalized seed payload differs from the supplied noise contract.
- Numeric cost ranges, educational proxies, and device/transport ranges were
  implementation assumptions, not numeric ranges supplied by the paper.
- Three missing medical-purpose parameters were extended locally; the combined
  dialysis/chemotherapy source row does not independently establish both values.
- Removing contradictory wage labels was a chosen repair, not the specified
  validation rule. The read-only validator now flags the original contradictions.

Recommendation: restore supplied amount-score semantics and source-compatible
noise as the compatibility baseline, with golden tests against all supplied
forty-case outputs. Where the current written rule conflicts with executable
source, list the exact conflict before choosing either. Keep the per-event score
bug fix, explicit cost constraints, and current written device ceiling separate
from coefficient changes. Review a concrete generator contract before new data
are produced; do not silently adopt the earlier provisional choices.

No result-dependent adjustment, new purpose restriction, inferred reviewer
approval, or replacement of the reviewed cases is proposed.

## Review decision

Henri can approve or revise sections 1–3 as implementation proposals. These are
not claims of research-team approval; methodological additions should be reflected
in the written protocol before comparisons. Section 4 must also be resolved before
any new scientific comparison is run. This document deliberately does not claim
that the full study or Chapters 4–5 are complete.
