# Equal-weight study retrieval

`study_retrieval.py` operates on records from `study_loader.py`. It is a standalone engine, now used by the application through study_adapter.py
and retrieval.py. Distances remain internal to the backend. The default is five
events, equal field weights, plain numeric range scaling and categorical duration.

## Run

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m backend.study_retrieval 'C:\Users\henri\Downloads\aics-v25-for-henri\aics-v25\data\synthetic\v1_intake.csv' 'C:\Users\henri\Downloads\aics-v25-for-henri\aics-v25\data\judged\judged_cases_as_printed_v11.csv' J01
```

The CLI prints IDs, context, recorded amounts and diagnostic counts. Amounts and
case-base documented costs are currently null because the source intake CSV does
not contain populated amounts or costs. They are not estimated by retrieval.

## Rules and boundaries

- Compare the 39-field allowlist only. Assistance type selects a candidate pool;
  no other outcome is used in distance. The study assumes sought and granted type
  coincide. The future API adapter must use the requested type for a new query.
- Remove the query applicant and every event belonging to them before deriving
  ranges, removing constants or scoring candidates.
- Extra `exclude_applicant_ids` remove pair partners or training-fold applicants
  from both reference statistics and candidates. For a fold fit, pass its training
  subset only or explicitly exclude the other fold. Fold assignment and pair-key
  loading are caller responsibilities; this module does not perform experiments.
- Numeric ranges and constant-field detection use eligible same-type records only.
  Fewer than two distinct known values means a field is inactive. Missingness does
  not create a second category. Out-of-range numeric scores are clamped to zero.
- Unknown values are excluded pair by pair; remaining fields have equal weight.
  Shared No in crisis-list and vulnerability fields is excluded. Shared No in
  support, resource and standalone yes/no fields counts as a match.
- Multi-select fields use Jaccard similarity. Two explicit empty sets match.
  Illness duration is categorical, including the explicit not-applicable value.
- Pairs without comparable active fields are excluded and counted. A result can
  contain fewer than five cases; there is no cross-type or undefined-score fallback.
- Ties use applicant ID then event ID lexicographically, independent of row order.
  This is a deterministic implementation choice fixed before outcome evaluation.
- Distances and field scores exist internally for research diagnostics. The engine
  is exposed through a display-only API adapter and does not recommend an amount. Returned records
  are copies, so display changes cannot mutate the case base.

## Section V evidence and remaining limitation

The supplied `generator/generate_intake.py` explicitly generates each external
resource with `yn(...)` or YES/NO, then `inject_unknowns` writes empty strings for
unknown answers. Its docstring also distinguishes empty unknowns from recorded No.
The printed CSV contains explicit Yes/No labels and `(not recorded)` markers.

For these synthetic CSVs, the loader's recorded semantics therefore apply: No is
False and a missing marker is None. An entirely unknown Section V contributes no
fields; a partial unknown excludes only that field. An all-No section retains its
recorded absences. This does not infer that a paper N/A box was ticked. The loader's
179 case-base and 11 printed all-No warnings remain provenance cautions, not
reasons to overwrite recorded No answers. Real form import needs an explicit
section-response/N/A indicator and must map an unanswered section to all None.

## Verification performed

- Full backend suite: See the latest full backend test run for the current count; the suite includes 14 retrieval tests.
- Hand-calculated Gower result, shared absences, Jaccard, unknown denominators,
  constants, clamping, exclusion-before-range calculation, deterministic ties,
  unchanged rankings after outcome edits, and input/output mutation checks.
- All 40 printed cases queried against the 1,000-record base: each returned five
  same-type cases. A real repeat applicant was also tested for event exclusion.
- Source CSV hashes stayed unchanged. No amount evaluation, scaling selection or weight fitting was performed.
  Frontend integration is documented in the main README.
