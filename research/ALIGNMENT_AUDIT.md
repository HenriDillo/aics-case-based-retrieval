# Alignment audit against the supplied AICS v25 folder

19 October 2026. Verdict: the baseline retrieval implementation substantially follows
the manuscript; the amount-generation extension is provisional, and the full research
workflow is incomplete. Passing software tests does not establish complete alignment.

Authority: manuscript v25 takes precedence under the current Context for Astra.
HENRI_START_HERE and Amount_Rule_Spec_v3 identify the current handoff and amount code.
Old comments and scripts outside SUPERSEDED are not automatically authoritative when
they conflict with the current manuscript. This audit changes documentation only;
it does not alter the amount rule, regenerate data, or replace the failed result.

## Confirmed alignment in the implemented baseline

| Requirement and source | Local evidence | Assessment |
| --- | --- | --- |
| 39 matching fields; Table 3.1 and Start Here 2.1 | backend/study_schema.py MATCHING_FIELDS | Present; costs, amounts, income-source lines and other context-only fields excluded. |
| Same-type retrieval, five neighbors; 3.2.1 and 1.5 | backend/study_retrieval.py; research/evaluate.py | Present. No hard same-purpose restriction added. |
| Unknown vs No vs N/A; Jaccard; shared-absence rules; 3.2.2 | study_loader.py and study_retrieval.py | Present for these CSVs. Section V paper N/A checkbox is absent in source schema; paper-form provenance cannot be reconstructed. |
| Eligible-pool ranges, constants, clamping, undefined pairs; 3.2.2 | study_retrieval.py | Present, before distance calculation. |
| All events of held-out applicant; Start Here 2.3 | retrieve and evaluate_case | Present. Reviewed pair map is applied by evaluator. |
| Actual median shares times query cost; direct median for food/cash; 1.5 | research/evaluate.py predict | Present. Query outcome does not steer retrieval. |
| Purpose baseline and 36-case p50 fixed 20% test; 1.5 | evaluate.py | Present. The run failed; failure retained. |
| Four conditions; per-type peso and scaled errors; 3.2.4 | evaluation-v1 outputs | Present for the provisional dataset and equal-weight baseline only. |
| Equal-weight local read-only prototype; 3.3 | data_store.py, retrieval.py, frontend results | Present. Default case base still lacks amounts and costs, so the prototype is not finished. |
| Income bands and direct/transport distinction; Amount Spec 2–4 | research/amounts.py and policy.py | Published thresholds retained; transportation exact cost, no food/cash cost. |
| Shared case-base calibration; Start Here 1 | amounts.calibrate; build_dataset | Uses 1,000 events and reuses calibration. This is explicitly required, unlike the supplied provisional n=40 calibration. |

Tests rerun during this audit: **67 passed**. One non-failing Starlette/httpx
deprecation warning. No new performance experiment was run. Review of code and
existing tests does not certify every possible input or the unimplemented experiments.

## Confirmed departures and unresolved implementation choices

### A1. Missing-answer scoring changed

The supplied amount_rule_v2.py counts an unknown emergency-fund/savings/insurance
answer as absence, and an unreadable employed count as zero. Local household_score
instead gives those unknowns no points. The manuscript's no-imputation rule is a
distance rule; it does not by itself authorize rewriting the amount generator.

Using identical normalized input values, this changes raw scores for **75 of 1,000
base events and 2 of 40 reviewed cases**. This comparison isolates the score logic,
before costs, noise or calibration. Resolve explicitly whether the source behavior
must be preserved or corrected and documented; do not silently choose another policy.

### A2. Noise construction changed

The source seeds from a sorted printed-field payload, excluding IDs/dates/outcomes,
using the first 16 hex digits of SHA-256. The local code uses canonical matching
fields plus type, cost, domain and condition, JSON serialization, and the entire
digest. Both are deterministic and exclude IDs, but they do not produce the same
random draws. Cross-schema normalization does not require changing every part of
the seed algorithm.

Against the supplied forty-case amount CSVs, local grants differ in **36/40 at p00,
35/40 at p25, 32/40 at p50 and 32/40 at p75**. At nonzero p, these are combined
pipeline differences, not an attribution solely to the seed. At p00 the household
score/calibration term is zero, so the seed change is especially material. The
handoff's byte-identical p00 statement concerns adding the income term to the
earlier rule, not a mandate that every future dataset equal that old file; nevertheless
our new outputs must not be represented as reproducing the supplied amount files.

Resolve a single cross-schema seed contract while preserving the approved source
behavior wherever possible. Do not pick a seed contract based on which result wins.

### A3. Cost choices are not specified numerically by the folder

The manuscript explicitly delegates generation of costs from researcher-set ranges
and specifies the 20% benchmark check with one adjustment. Therefore adding costs
is required, not itself a violation. But the local uniform 0.5–1.5 benchmark range,
device 10,000–40,000 interval, transport 1,000–10,000 interval, cost seed 20261019,
and tuition proxy for all education purposes are local choices, not quoted instructions.
Under Henri's request to flag unspecified details, these require clarification before
further use. The earlier run's choices were recorded before evaluation; do not tune
them now to improve the failed result.

### A4. Missing medical-purpose parameters were filled locally

The base CSV contains laboratory, dialysis and chemotherapy events, but the supplied
current amount-rule table lacks those keys. Local policy added shares 0.9052, 0.3556
and 0.3556 and matching caps, using a separately checked publication. This is a
documented completion of an incomplete source table, not an exact implementation
of its existing table. Resolve the parameter table before further generation.
Device ceiling 150,000 follows the current amount script; the older figures helper
contains a conflicting 10,000 assumption. Do not silently alternate between them.

### A5. Wage-label repair is a chosen remedy, not the requested validator fix

The folder requests an employed-plus-seasonal >=1 validation rule for wage-earner
labels. Local repair_wage_labels removes contradictory labels from **244 events**,
leaving incomes and worker counts unchanged; ten other events are unverifiable.
The requirement to detect contradictions does not specify this remedy. The original
generator still needs the requested consistency rule and an agreed generation fix.
Do not describe the local repair as completing both original generator tasks.

### A6. Rounding and repeated-event handling

Local generation computes one score per event, avoiding the source dictionary's
overwriting of repeated applicants. This follows the manuscript's event definition
and should be retained as an explicit bug fix. Local rounding also enforces both the
cost ceiling and the 50-peso grid and rejects infeasible costs. The manuscript requires
these constraints; the exact rejection/grid procedure is an implementation choice,
not an additional scientific result. Keep these separate from unapproved changes to
the household coefficients or seed definition.

### A7. Additional diagnostic is not a new retrieval method

diagnose_purpose.py is post-result descriptive analysis. It did not change eligibility,
weights or outcomes. Its suggested hard purpose restriction is outside the current
methodology and is not part of the remaining implementation plan. Do not turn its
observational groups into a causal claim or tune against the forty inspected cases.

## Unfinished requirements, not evidence of a wrong baseline

| Required work | Current state / next action |
| --- | --- |
| Money scaling and duration on a separate set; 3.2.2 rule 10 | Not implemented. Plain/categorical are baseline settings, not selected winners. |
| Fully specified fuzzy similarity | Quartiles are specified; membership shape, pairwise formula and coincident-quartile handling need clarification. |
| Five-fold shared weight search; 3.2.2 rule 11, 3.2.3 | Not implemented. Objective and pools specified; optimizer, budget and stopping choices need clarification. |
| Thirty-set noise floor plus applicant-paired Wilcoxon; 3.2.4 | Not implemented. Exact randomization plan and statistical handling across sets must be fixed before comparisons. |
| Field recovery, reference-weight gap and convergence; 3.2.4 | Not implemented. Generation coefficients must remain outside normal retrieval/fitting. Reference benchmark is explicitly permitted for evaluation only. |
| Retrieval count sensitivity | Not implemented; tested count list unspecified. Five remains fixed for failure test and search. |
| Requested generator validator and sheet fixes | No local full sheet-generation workflow implementing them. Need wage validation, constant 250,000 funds, populated diagnosis display and preservation of the v11 one-field pairs. |
| Final displayed reference amounts/costs | App still uses intake-only CSV; expected final output is incomplete. Do not connect provisional data merely to make it look finished. |
| Compared-field counts in saved evaluation | Engine has per-pair field_scores, but evaluate.py does not persist their counts. active_fields is not equivalent because pair missingness/shared absences differ. Add before final reporting. |
| DSWD benchmark report | Raw summaries exist, but final side-by-side direct food/cash published mean comparisons and full Chapter 4 presentation remain incomplete. |
| Runtime/memory reporting | Required repeated-run medians and full weight-search timing are unfinished. |
| Environment and reproducibility | Requirements files use version ranges rather than the manuscript's exact versions; hardware/library snapshot and six manuscript placeholders unfinished. Remote URL exists locally, but hosted repository privacy was not verified in this audit. No push was made. |
| Minimal example | README has run/retrieval guidance but not the required small fixed-seed generation plus five-case command example. |
| DSWD review and Chapter 4 | No response should be invented; do not claim submission, approval or completed Chapter 4. |

## Corrections completed by this audit

- Replaced stale README statements that the already-existing pipeline/evaluator are
  still wholly unbuilt.
- Marked research generation and evaluation documentation as provisional.
- Kept the original folder, executable algorithms, generated CSVs and raw evaluation
  files unchanged. No new dataset or challenger experiment was created.
- Preserved the failed result as an outcome of this pipeline version, not a final
  certified v25 result and not a pass.

## Reconciliation order

1. Resolve A1–A5 against the manuscript/current rule; record any source ambiguities
   explicitly with the research team. Do not choose based on performance.
2. Implement the agreed contract in a versioned correction and the specifically
   requested generator/sheet fixes. Preserve earlier datasets/results as history.
3. Complete missing descriptive reporting and reproducibility details.
4. Set the unspecified scaling/search/statistical implementation details before
   running comparisons, then follow the manuscript's separate-set -> fixed settings
   -> case-base weight evaluation sequence.

No new methodological choice is made by this audit. The user's instruction to
flag unspecified details, rather than assume approval, governs the unresolved items.

## Subsequent reporting progress — 19 October 2026

After this audit, the user requested completion and then explicitly requested
methodological choices for review before comparisons. The historical findings
above remain; this note updates the implementation status without replacing them.

- Added read-only wage validation; source findings are 244 contradictions and
  10 unverifiable events. No additional source repair was applied.
- Added checked, byte-for-byte export of the existing 40-case reviewed DOCX.
  This is not completion of the full new-case sheet generator.
- Added per-neighbor compared-field counts to future evaluation output and saved
  a supplement for all 1,040 existing queries, verifying identical neighbors in
  all four conditions and unchanged original evaluation files.
- Recorded exact installed packages, hardware/OS, repeated retrieval times,
  backend import/load working set, missingness, and benchmark comparisons in
  `generated/report-supplement-v2`. Full search runtime remains unavailable.
- Backend verification now passes 72 tests. Added exact Python requirements lock.
- Prepared `METHOD_CHOICES_FOR_REVIEW.md`. These choices have not been approved
  or used in challenger experiments. A1–A5 remain unresolved. The source bundle
  and earlier failed result remain unchanged.


## Completion update — 19 October 2026

The earlier status below is historical. The completed reconciled implementation, full experiments, and Chapter 4 draft are documented in RUNBOOK.md and chapter-4-draft.md. The main test failed; its result is preserved. Implementation choices are not adviser approval, and new external feedback remains outstanding. Work stops at the Chapter 4 draft.
