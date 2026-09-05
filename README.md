# AICS Priority Scoring & Triage — Prototype

An Explainable AI-Driven Priority Scoring and Triage System for DSWD AICS
Applicants in Davao City using XGBoost and SHAP.

Thesis team: Alexzander Rojan Payot, Henri James Dillo, Rygan Carl Rocamora
(BS Computer Science, Ateneo de Davao University). Adviser: Dr. Oneil B.
Victoriano.

## Current status (as of this scaffold)

DSWD Field Office XI has approved the data request, but the real historical
AICS/GIS dataset has **not yet been delivered**. Per team decision, this repo
does **not** use a synthetic/fabricated dataset — instead:

- The Streamlit UI (`app.py`) is fully wired up and runnable end-to-end.
- The "model" behind it (`src/model.py: PlaceholderScorer`) is a hand-written,
  transparent rule-of-thumb scorer — **not a trained model**. It exists only
  to demonstrate the workflow (intake → score → explanation → social worker
  review) before real data exists.
- `src/preprocessing.py`, `src/model.py: train_xgboost()`, and
  `src/explain.py: explain_shap()` are stubs that raise `NotImplementedError`
  until the real dataset arrives.

**Do not** present the placeholder score/tier as a real result in the thesis
— it's a UI scaffold, not a finding.

## Project layout

```
app.py                  Streamlit entry point (run this)
src/
  schema.py             Applicant intake fields (placeholder — see file docstring)
  preprocessing.py      STUB: cleaning, encoding, SMOTE (owner: Henri)
  model.py              PlaceholderScorer (working) + train_xgboost() (STUB)
  explain.py            Placeholder explanation chart + explain_shap() (STUB)
data/                   Real dataset goes here once received — gitignored
notebooks/              For EDA / experimentation once data arrives
tests/                  For unit tests once real logic exists
```

## Run it locally

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

This opens the app at `http://localhost:8501`.

## Once the real DSWD dataset arrives

1. Drop the raw file into `data/raw/` (see `data/README.md` — never commit it).
2. Implement `src/preprocessing.py` (Henri's part): load → clean/de-identify →
   encode → SMOTE → train/test split.
3. Implement `src/model.py: train_xgboost()` and evaluate against the
   Research Brief's specific objectives (Accuracy, Precision, Recall,
   F1, AUC).
4. Implement `src/explain.py: explain_shap()` using `shap.TreeExplainer`
   on the trained model.
5. Swap `app.py`'s call from `PlaceholderScorer` / `explain_placeholder`
   to the real model + `explain_shap` — the UI layout needs little to no
   change since the return shapes were kept compatible on purpose.
6. Remove the "prototype notice" banner once the real model is in place.

## Pushing this to your GitHub repo

This was built outside of git. To push it into your existing empty repo:

```bash
cd aics-triage-prototype
git init
git add .
git commit -m "Scaffold AICS triage prototype (Streamlit UI, placeholder scorer)"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main
```

## On using Streamlit for the thesis's "Operational Framework"

Streamlit is a reasonable, defensible choice to name as the prototype/
implementation stack for this thesis: it's Python-native, so it plugs
directly into the XGBoost + SHAP work with no separate API/frontend layer,
and it's a very common choice for academic ML decision-support prototypes
built for a UAT-style evaluation with a small group of users.

Worth being explicit about in the Operational Framework write-up, though:
Streamlit reruns the whole script on each interaction, has no built-in
authentication/role separation, and isn't typically what an agency would
run in actual production for many concurrent users. For a thesis prototype
evaluated by a handful of social workers, none of that is disqualifying —
but it's worth framing Streamlit as the **prototype/evaluation
implementation**, with a short note that a production deployment (if DSWD
ever adopted this beyond the thesis) would likely move to a proper backend
(e.g., FastAPI) behind authentication. That distinction (prototype stack vs.
recommended production architecture) is a normal and expected thing to state
in a thesis, not a weakness.
