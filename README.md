# AICS Case Reference

**An Explainable Case-Based Reasoning System for AICS Assistance Decision Support in Davao City** — a BS Computer Science thesis prototype for Ateneo de Davao University.

This application shows closed assistance records as precedent. The social worker decides the assistance amount. It contains no scores, visible ranks, similarity percentages, urgency ordering, estimated grants, recommended ranges, or amount summaries. The retrieved records and their field explanations are the explanation.

## Run locally

Requirements: Python **3.11+** and Node.js **22.12+** with npm. Run both terminals from the repository root unless a command changes directories. Both servers bind to the local computer only.

### Terminal 1 — FastAPI

Windows PowerShell (activation is not required):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

macOS / Linux:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

API documentation: <http://127.0.0.1:8000/docs>. Use one worker: each process loads the CSV once. `--reload` is optional for development with synthetic data; a reload starts a new process and reads the CSV again.

### Terminal 2 — React / Vite

Windows PowerShell:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

macOS / Linux: use `npm ci` and `npm run dev` instead. Open **<http://127.0.0.1:5173>**. Vite forwards `/api` to FastAPI on port 8000, so no separate CORS configuration is needed. Keep both terminals running; Ctrl+C stops each server.

To verify the production build:

```powershell
cd frontend
npm.cmd run build
npm.cmd run preview
```

Preview is served on <http://127.0.0.1:4173> and also requires FastAPI. This repository is a local prototype, not a production deployment configuration.

## Try the workflow

1. On **New case**, choose **Medical · senior citizen**, then **Load sample**. Six saved samples cover the six assistance types. Loading a sample replaces the current draft.
2. Review or edit the GIS sections, in their original order. Checkbox groups can be empty. Income breakdown values refer to the past six months. The total is manually recorded, never computed by the application.
3. Leave **Assistance provided** blank for an undecided intake. If an outcome already exists, all four fields can be entered together. The system never fills them from retrieved cases.
4. Choose **Find similar cases**. Eight fixed mock records appear, with prominent month/year, requested and granted amounts, and backend-written field explanations. There is no ordering control or visible position number.
5. Choose **Compare case** to see every field alongside the intake in GIS order. **Same** marks equal field values; missing fields are not marked as matches. Previous/next moves through the returned records.
6. **Edit intake** preserves your draft. Changing any field invalidates old results. A browser refresh clears the intake; nothing is saved to browser storage or a database.

**Stub limitation:** retrieval deliberately ignores the submitted intake and always returns the same fixed cases. Its handwritten explanations describe matches against the saved medical sample only. This limitation is visible in the interface. The comparison table independently compares the actual submitted intake on the backend; its equal/different field markers remain accurate after edits or when using another sample. No real retrieval or machine learning is implemented.

## Repository structure

```text
.
├── README.md
├── .gitignore
├── backend/
│   ├── __init__.py
│   ├── main.py                 # Startup and API routes
│   ├── models.py               # Intake and response validation
│   ├── catalog.py              # GIS field order, labels, options
│   ├── data_store.py           # One in-memory pandas DataFrame
│   ├── retrieval.py            # Replace only retrieve_similar_cases later
│   ├── comparison.py           # Server-side field equality and formatting
│   ├── samples.py              # Six synthetic sample intakes
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── data/
│   │   ├── mock_cases.csv      # 30 synthetic closed cases, 42 columns
│   │   └── README.md          # CSV format and data handling
│   └── tests/
│       └── test_api.py
└── frontend/
    ├── package.json
    ├── package-lock.json
    ├── index.html
    ├── vite.config.js
    ├── public/
    │   └── favicon.svg
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js
        ├── styles.css
        └── components/
            ├── Field.jsx
            ├── IntakeForm.jsx
            ├── Results.jsx
            └── Comparison.jsx
```

## Retrieval replacement boundary

**Replace only `retrieve_similar_cases` in [`backend/retrieval.py`](backend/retrieval.py).** Keep this exact signature:

```python
def retrieve_similar_cases(new_case: dict, k: int = 8) -> list[dict]:
    ...
```

`new_case` is a validated dictionary of the GIS fields. Use `get_cases()` for the already-loaded pandas DataFrame, treating it as read-only. Return up to `k` complete case dictionaries, each with these additional fields:

```python
{
    # All fields from a closed CSV record, including the assistance outcome.
    "matched_fields": [
        "Same assistance type: medical",
        "Both in the SC client sector",
        "Combined family income within ₱800",
    ],
    "explanation_context": "These field explanations refer to the submitted intake.",
}
```

The endpoint adds the field-by-field comparison. The browser simply renders the response, including `matched_fields` verbatim. In the future, keep any Gower distances internal to this function; never return them, turn them into match percentages, or use them to propose assistance amounts. Generate truthful field explanations for the actual intake. Do not use outcome fields (granted amount, provided type/purpose, fund source) as intake features; they may be blank and are the historical outcomes being inspected.

Changing this function requires no API or frontend changes. A contract test swaps in a replacement function to verify that boundary. Dataset location is separately configurable using `AICS_CSV_PATH`; see [`backend/data/README.md`](backend/data/README.md). The real CSV must match the documented schema. Changing the data location is not part of retrieval implementation.

## API

| Endpoint | Request | Response |
| --- | --- | --- |
| `GET /api/sample-cases` | None | Array of `{id, label, case}` synthetic intakes |
| `POST /api/similar-cases` | A `case` object | Array of full past records, `matched_fields`, `explanation_context`, and `comparison` |
| `GET /api/form-schema` | None | Ordered GIS sections and an empty intake for the form |

Amounts use JSON numbers or validated numeric input strings, without currency symbols. Rendered amounts use `₱` and thousands separators. Requested amounts have **no policy upper limit**. Negative or non-finite amounts are invalid. The schema rejects unknown fields (including names or scores). Standard finite numeric representation applies; no application monetary ceiling is imposed.

For an executable example in PowerShell:

```powershell
$samples = Invoke-RestMethod http://127.0.0.1:8000/api/sample-cases
$payload = $samples[0].case | ConvertTo-Json -Depth 8
Invoke-RestMethod http://127.0.0.1:8000/api/similar-cases -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($payload))
```

## Checks

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest backend/tests -q
cd frontend
npm.cmd run build
```

Tests cover the 30-record dataset, one-time CSV loading, all six samples, fixed retrieval, response contracts, very large requests, invalid input, absence of unrequested response fields, correct comparison after edits, no mutations, empty results, and the retrieval replacement boundary.

## Data and scope

All records, control numbers, purposes, and fund sources are invented. The five grants within each assistance type differ, and requests include large outliers. They are not an assertion of current DSWD policy ceilings. No official eligibility or ceiling rules are encoded.

No name field, database, CSV-writing endpoint, browser persistence, dataset export, ML model, or external service is present. The application loads one CSV into memory at startup using FastAPI's [lifespan mechanism](https://fastapi.tiangolo.com/advanced/events/). React/Vite handles presentation and input state only; field validation, retrieval, and comparisons live in Python. The Vite setup follows the official [getting started documentation](https://vite.dev/guide/).
