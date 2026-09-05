"""
Explanation layer.

For the prototype (no trained model yet), `explain_placeholder()` just
reshapes PlaceholderScorer's hand-written contributions into a format the
UI can chart, so the layout/interaction of "show me why" is demonstrable now.

TODO once model.py's train_xgboost() produces a real model:
  - use shap.TreeExplainer(model) on the trained XGBoost model
  - return real SHAP values per feature, per case
  - keep the return shape compatible with what app.py expects below, so
    the UI code barely has to change
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def explain_placeholder(contributions: Dict[str, float]) -> List[Tuple[str, float]]:
    """Sort placeholder contributions largest-first for display."""
    return sorted(contributions.items(), key=lambda kv: abs(kv[1]), reverse=True)


def explain_shap(model, feature_row):
    """Real SHAP explanation. TODO once a trained XGBoost model exists."""
    raise NotImplementedError(
        "Wire up shap.TreeExplainer here once train_xgboost() is implemented."
    )
