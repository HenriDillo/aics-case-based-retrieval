# data/

This folder is intentionally empty in git (see `.gitignore`).

Once DSWD Field Office XI delivers the historical, de-identified AICS/GIS
applicant records described in the Research Brief (GF-004), place the raw
file here as:

```
data/raw/aics_applicants.csv   (or .xlsx, whatever format DSWD sends)
```

Do **not** commit the real file to GitHub — it must stay restricted-access
per the Data Privacy Notice and Consent Form (GF-014) and the Data Privacy
Act of 2012 (RA 10173). `.gitignore` already excludes `data/raw/` and
`data/processed/`.

Henri: this is the folder your preprocessing script (`src/preprocessing.py`)
should read from.
