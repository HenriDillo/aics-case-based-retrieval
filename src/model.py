"""
Priority-scoring model.

Two things live here:

1. PlaceholderScorer — a transparent, hand-written rule-of-thumb scorer with
   NO trained model behind it. It exists only so the Streamlit prototype
   (app.py) has something to call end-to-end before real data exists. Its
   weights are made up for demo purposes and must NOT be cited as a result
   or used for any real prioritization decision.

2. train_xgboost() — a stub for the real model, to be implemented once
   preprocessing.py is filled in against the actual dataset.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Dict

from src.schema import ApplicantRecord


class PlaceholderScorer:
    """
    Rule-based stand-in for the trained XGBoost model.
    Produces a 0-100 score and per-feature "contributions" so the UI can
    demonstrate the score + explanation layout before SHAP is wired up.

    NOT a validated model. Weights are illustrative only.
    """

    # illustrative weights only — not derived from any real data
    URGENCY_WEIGHTS = {
        "None reported": 0,
        "Ongoing medical emergency": 40,
        "Recent death in household": 30,
        "Displacement / calamity-affected": 35,
        "No income for 30+ days": 20,
    }

    def score(self, applicant: ApplicantRecord) -> Dict[str, float]:
        contributions: Dict[str, float] = {}

        contributions["urgency_indicator"] = self.URGENCY_WEIGHTS.get(
            applicant.urgency_indicator, 0
        )

        # lower income -> higher contribution, capped
        income_component = max(0.0, 25 - (applicant.monthly_household_income_php / 1000))
        contributions["monthly_household_income_php"] = round(min(income_component, 25), 1)

        contributions["dependents_count"] = round(min(applicant.dependents_count * 3, 15), 1)

        contributions["household_size"] = round(min(applicant.household_size * 1.5, 10), 1)

        contributions["employment_status"] = (
            10 if applicant.employment_status == "Unemployed" else 0
        )

        contributions["has_prior_aics_assistance"] = (
            -5 if applicant.has_prior_aics_assistance else 5
        )

        contributions["days_since_application"] = round(
            min(applicant.days_since_application * 0.2, 5), 1
        )

        total = sum(contributions.values())
        total = max(0.0, min(100.0, total))

        return {"score": round(total, 1), "contributions": contributions}

    @staticmethod
    def tier(score: float) -> str:
        if score >= 70:
            return "Critical"
        if score >= 45:
            return "High"
        if score >= 20:
            return "Medium"
        return "Low"


def train_xgboost(X_train, y_train):
    """
    Train the real XGBoost priority-scoring model on SMOTE-balanced data.

    TODO once preprocessing.py is implemented:
      - import xgboost as xgb
      - fit an XGBClassifier (or ranker, depending on how "priority" is framed)
      - evaluate with precision/recall/F1/AUC per the Research Brief's
        specific objectives
      - persist with e.g. joblib for app.py to load
    """
    raise NotImplementedError(
        "Implement after preprocessing.py produces real train/test splits."
    )
