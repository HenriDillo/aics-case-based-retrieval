# Reproduce the completed AICS implementation

The original bundle and the earlier provisional failed run are preserved. Current
code uses the reconciled generator described in RECONCILIATION.md. Implementation
choices supplement unspecified details in the manuscript; they do not imply
adviser approval. The live prototype always uses equal weights.

## Environment and application

Use Python 3.12.10 and the exact backend/requirements-lock.txt snapshot. Frontend
versions are pinned by frontend/package-lock.json; the tested Node runtime is
24.19.0. From the repository root in PowerShell:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-lock.txt
.venv/Scripts/python.exe -m pytest backend/tests -q -p no:cacheprovider
.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, run `npm ci` then `npm run dev` in frontend/. The default
CSV is backend/data/study_complete.csv, the reconciled p=.50 synthetic base.
AICS_CSV_PATH can select another explicitly approved CSV. Loading is read-only
and cached once per backend process; restart the backend after changing the file.
The UI shows recorded generated grants and costs, not a suggested amount or score.

## Small fixed-seed example

This is a 100-event smoke fixture, not the dataset used in the thesis results.
The output folder must be new. Run from the repository root:

```powershell
.venv/Scripts/python.exe -m research.reconciled --master 61000 --count 100 --output research/generated/example-new
.venv/Scripts/python.exe -m backend.study_retrieval research/generated/example-new/case_base_p50.csv research/generated/example-new/judged_p50.csv J01 -k 5
```

Expected neighbor IDs in order are C00064/1, C00063/1, C00059/1, C00071/1 and
C00069/1. This verifies fixed-seed generation and retrieval without asserting
that the method is successful. Each output file carries generated amounts only.

## Full study

From a clean checkout with no generated runs, execute:

```powershell
.venv/Scripts/python.exe -m research.reconciled --output research/generated/reconciled-primary
.venv/Scripts/python.exe -m research.run_experiments --phase all
.venv/Scripts/python.exe -m research.finalize_diagnostics
```

The runner generates the separate selection primary set and thirty selection
replicates, fixes settings, evaluates five applicant folds for every condition,
then evaluates thirty weight replicates and repeats the primary evaluation for
timing. Replicate fitting uses three independent workers after sequential input
generation. It does not change seeds, folds, candidates or budgets. Completed
results are resumed, not silently replaced with another random run. Do not
change code between partial runs; move a failed partial run to a separately
named archive before restarting it. Keep manifests and hashes with results.

The reporting finalizer includes purpose among the amount-rule reference fields,
preserves the narrower household-only diagnostic, and records positive-weight
compared-field counts. It does not refit, retune, or alter any learned prediction.
The reference is not a proven optimum. The fixed main test is evaluated separately
on 36 non-transport reviewed cases. A failed main test remains a failure even if
learned weights improve against equal weights elsewhere.

## Validator and printable sheets

```powershell
.venv/Scripts/python.exe -m research.validate_intake backend/data/study_complete.csv
.venv/Scripts/python.exe -m research.make_sheets --input research/inputs/judged_cases_v11.csv --output research/generated/review-new.html
.venv/Scripts/python.exe -m research.sheets --output research/generated/review-docx-new
```

The first command checks observed wage contradictions and separately lists
unverifiable cases. The second generates printable sheets from CSV with constant
funds and populated diagnosis lines. It supports the synthetic schema as well as
the reviewed schema. Open the HTML in a browser and Print to PDF if needed.
The third validates and copies the unchanged reviewed DOCX; it does not generate
new reviewed cases or reveal the private pair key. Keep all paired-case diagnostics
private and out of packets sent for review.

## External review and version control

GitHub privacy was authenticated and verified as private on 19 October 2026.
No push or external message was performed. Keep the repository private and never
add real applicant data. Obtain actual team review of the report and methodological
addendum before submission. A new DSWD response cannot be manufactured by code;
record whether feedback was requested and received, with dates and evidence.

The current reports distinguish earlier feedback mentioned in the manuscript
from any response to this newly generated packet. No new response is evidenced.
