# Dataset contract

`mock_cases.csv` contains exactly 30 invented, de-identified closed records (five per assistance type). No row represents a real person, office decision, or official policy ceiling. Requested amounts include deliberately large outliers. Granted amounts vary within each type; these are illustrative figures, not guidance.

There is one column per field in `backend/models.py` / `backend/catalog.py`. Multi-select columns contain JSON arrays inside standard CSV quoting. Boolean columns use `true`/`false`. Money columns contain nonnegative numeric pesos without symbols or separators; presentation adds `₱` and thousands separators. Optional text can be blank. Income breakdown components and the recorded total cover the previous six months; combined family income and family expenses are monthly. `provided_type`, `provided_purpose`, `amount_granted`, and `fund_source` describe the closed outcome and are populated in every historical row.

The application loads the CSV once per process at startup, validates it, and keeps it in a pandas DataFrame. It performs no writes, imports, exports, backups, persistence of intakes, or logging of request bodies. Use a single application worker for the study. The only committed CSV is this synthetic fixture.

Later, set `AICS_CSV_PATH` to the authorized location of the study CSV (matching this schema), without copying it into this repository. Replace the marked function in `backend/retrieval.py` before switching datasets. Do not regenerate, commit, or distribute the real data. The repository does not configure a deployment or make claims about NDA compliance.
