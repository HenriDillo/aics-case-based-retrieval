"""
AICS Priority Scoring & Triage — Prototype UI

Status: UI/workflow demo only. There is no trained XGBoost model behind this
yet — see src/model.py's PlaceholderScorer docstring. This exists so the
team (and eventually DSWD social workers during UAT) can click through the
intended workflow — enter applicant info, get a score + explanation, social
worker reviews and decides — before the real dataset arrives.

Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""

import matplotlib.pyplot as plt
import streamlit as st

from src.explain import explain_placeholder
from src.model import PlaceholderScorer
from src.schema import ASSISTANCE_TYPES, EMPLOYMENT_STATUS, URGENCY_INDICATORS, ApplicantRecord

st.set_page_config(page_title="AICS Triage Prototype", page_icon="🩺", layout="centered")

st.title("AICS Priority Scoring & Triage — Prototype")

st.warning(
    "**Prototype notice:** This scorer is a hand-written placeholder, "
    "not a trained model. Real DSWD applicant data has not yet been received. "
    "Nothing shown here should be used for an actual prioritization decision. "
    "This screen exists to demonstrate the intended workflow and UI."
)

st.caption(
    "This system does not automate decisions. It is a decision-support tool — "
    "final approval of assistance remains with the DSWD social worker."
)

st.divider()
st.subheader("Applicant Intake")

col1, col2 = st.columns(2)
with col1:
    age = st.number_input("Age", min_value=0, max_value=120, value=35)
    household_size = st.number_input("Household size", min_value=1, max_value=30, value=4)
    dependents_count = st.number_input("Number of dependents", min_value=0, max_value=20, value=2)
    monthly_income = st.number_input(
        "Monthly household income (PHP)", min_value=0.0, value=8000.0, step=500.0
    )
with col2:
    assistance_type = st.selectbox("Assistance type requested", ASSISTANCE_TYPES)
    employment_status = st.selectbox("Employment status", EMPLOYMENT_STATUS)
    urgency_indicator = st.selectbox("Urgency indicator", URGENCY_INDICATORS)
    has_prior_assistance = st.checkbox("Received AICS assistance before?")
    days_since_application = st.number_input(
        "Days since application was filed", min_value=0, max_value=365, value=1
    )

if st.button("Calculate Priority Score", type="primary"):
    applicant = ApplicantRecord(
        age=int(age),
        household_size=int(household_size),
        monthly_household_income_php=float(monthly_income),
        dependents_count=int(dependents_count),
        assistance_type=assistance_type,
        employment_status=employment_status,
        urgency_indicator=urgency_indicator,
        has_prior_aics_assistance=bool(has_prior_assistance),
        days_since_application=int(days_since_application),
    )

    scorer = PlaceholderScorer()
    result = scorer.score(applicant)
    tier = scorer.tier(result["score"])

    st.divider()
    st.subheader("Result")

    tier_colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    c1, c2 = st.columns(2)
    c1.metric("Priority score", f"{result['score']} / 100")
    c2.metric("Priority tier", f"{tier_colors.get(tier, '')} {tier}")

    st.markdown("**Why this score? (placeholder explanation)**")
    ranked = explain_placeholder(result["contributions"])
    labels = [k for k, _ in ranked]
    values = [v for _, v in ranked]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    colors = ["#d64545" if v >= 0 else "#3d7dd6" for v in values]
    ax.barh(labels, values, color=colors)
    ax.set_xlabel("Contribution to score")
    ax.invert_yaxis()
    fig.tight_layout()
    st.pyplot(fig)

    st.caption(
        "Once the real dataset is available and an XGBoost model is trained, "
        "this chart will be replaced by actual SHAP values (src/explain.py: "
        "explain_shap)."
    )

    with st.expander("Raw applicant record"):
        st.json(applicant.__dict__)
