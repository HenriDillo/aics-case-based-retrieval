# AICS Case Reference

A local research prototype for the AICS case-based reasoning study in Davao City.
The form now retrieves up to five same-type cases from the 1,000-event synthetic
study case base using equal-weight Gower similarity. The social worker retains
all decisions. No distances, scores, suggested amounts or amount summaries appear
in the interface.

## Current study status

The prototype now loads reconciled synthetic grants and documented costs.
Scaling/duration selection, five-fold weights, thirty-set comparisons, sensitivity,
recovery, convergence and repeated timing are complete. Plain scaling and categorical
duration were retained. The fixed main test failed: retrieval MAE 1,903.82 pesos
versus purpose-baseline MAE 1,333.76 pesos. Learned-weight improvements do not
replace that failure. Chapter 4 is a draft for team review, not an approval claim.

See `research/RUNBOOK.md` for the complete reproduction commands and the small
fixed-seed example. `research/RECONCILIATION.md` records implementation decisions;
`research/ALIGNMENT_AUDIT.md` preserves the earlier audit and its subsequent status.

## Run locally

The tested versions are Python 3.12.10 and Node.js 24.19.0. From the repository root, use two
PowerShell terminals:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

```powershell
npm.cmd ci --prefix frontend
npm.cmd run dev --prefix frontend
```

Open http://127.0.0.1:5173. The backend reads the bundled synthetic
`backend/data/study_complete.csv` once per process. An explicit `AICS_CSV_PATH` can
select another compatible study CSV; restart the backend after changing it.
Only generated data may be used in this private project. There are no writes to
the source CSV, no database and no browser persistence of intakes.

## Try the actual retrieval

1. Choose a sample and click **Load sample**. Samples retain their source IDs so
   the corresponding applicant and all their events are excluded from retrieval.
2. Review or edit the intake. Only the assistance type is required. Leave unknown
   answers blank, distinguish No from Not recorded, and use the response-state
   selector on multi-select fields to distinguish unknown from recorded none.
3. Click **Find similar cases**. Up to five same-type records are returned. A query
   with no comparable data returns no cases, rather than invented matches.
4. Click **Compare case** and use Previous/Next to inspect the recorded fields.
5. Return to **Edit intake**. Any edit invalidates the old results; search again.

For a returning applicant, use their existing Applicant reference ID. A matching
control number also excludes that applicant's events. A new intake can leave IDs
blank. The system cannot infer household identity from similar field values.

## Schema and matching

The API and form use the study's canonical field names. This replaces the old
mock-only API contract. Occupation and service setting are included; target sector,
sub-category and disability type are multi-select. The three study vulnerability
flags and individual Yes/No/Not recorded resource fields are preserved.

The 39-field allowlist in `study_schema.py` controls matching. Mode of assistance,
combined income, source-specific income, diagnosis, costs and outcomes remain
context only. The requested-amount input was removed because it is not a v25
study field. The chosen assistance type groups candidates and is not a distance
feature. For the synthetic data, sought and granted types coincide by design.

`study_retrieval.py` removes excluded applicants before fitting ranges and removing
constant fields. It uses plain numeric ranges, categorical illness duration,
Jaccard multi-select similarity and the manuscript's shared-absence rules.
`retrieval.py` returns actual case fields plus truthful exact-match examples;
those examples describe only part of the full field comparison.

Section V: explicit No in these generated CSVs means recorded absence; blanks
mean unknown. An entirely unanswered section contributes nothing. The source does
not preserve a paper N/A tick, so actual paper-form import needs a separate
response-state indicator. See `backend/STUDY_RETRIEVAL.md` for detailed rules.

## Components

- `backend/catalog.py`, `models.py`: common form definitions and API validation.
- `backend/study_schema.py`, `study_loader.py`: schema and read-only normalization.
- `backend/data_store.py`: one in-memory study case base.
- `backend/study_adapter.py`: JSON and normalized-record conversion.
- `backend/study_retrieval.py`: independently testable Gower engine.
- `backend/retrieval.py`: application retrieval and explanation boundary.
- `backend/comparison.py`: display-only field comparison, including missing values.
- `frontend/src/components`: intake, results and comparison screens.

## Verification

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
npm.cmd run build --prefix frontend
npm.cmd audit --prefix frontend
```

Tests cover normalization, hand-calculated similarity, applicant exclusion,
reference-range isolation, outcome independence, all six API sample flows,
validation, missing values, one-time loading, no mutation and response boundaries.
Browser verification additionally covers sample loading, search, comparison,
editing, multiple sectors, all six assistance types and desktop/mobile layouts.

Passing software checks does not establish research success or accuracy against
the purpose baseline. Both the original provisional failure and the reconciled
failure are retained. No real recipient data or real decision validation is claimed.

## Historical provisional preparation

For reproducibility of the existing provisional implementation only, the four
research datasets and their audit files can be built with the command below.
For current experiments use `research.reconciled` and the runbook instead.

```powershell
.\.venv\Scripts\python.exe -m research.build_dataset --output research/generated/new-run
```

Use a new output directory. See `research/README.md` for source figures, explicitly
assumed ranges, consistency repairs, the updated missing-value policy and the
shared 1,000-event calibration. These historical outputs remain separate from the
reconciled p=.50 data now explicitly configured in the application.

## Reporting additions — 19 October 2026

The proposed methods were implemented after Henri asked to complete the remaining
work. Team/adviser review remains distinct from authorization to implement code.

The tested Python environment is recorded in `backend/requirements-lock.txt`.
For a fresh Python 3.12 environment, install with
`python -m pip install -r backend/requirements-lock.txt`.
This is an exact snapshot of the tested environment, not a claim that a fresh
installation has been independently tested.

Run from the repository root:

```powershell
python -m research.validate_intake backend/data/study_intake.csv
python -m research.sheets --output research/generated/review-packet-new
python -m research.report_completion --output research/generated/report-supplement-new
python -m pytest backend/tests -q -p no:cacheprovider
```

The validator reports source contradictions without repairing data and returns
nonzero when violations exist. The packet command verifies and copies the existing
reviewed DOCX; use `research.make_sheets` for CSV-driven printable HTML. Output directories
must not already exist. The supplement reads the preserved `evaluation-v1` and
provisional `v26` data and verifies that old evaluation files are unchanged.
