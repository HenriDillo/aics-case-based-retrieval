"""Saved synthetic intake examples; nothing is written to disk."""

from copy import deepcopy
from .data_store import get_cases


def sample_cases() -> list[dict]:
    result = []
    labels = ["Medical · senior citizen", "Burial · family crisis", "Transportation · return journey", "Educational · school expenses", "Food · disrupted livelihood", "Cash relief · household recovery"]
    frame = get_cases()
    for i, label in enumerate(labels):
        row = deepcopy(frame.iloc[i * 5].to_dict())
        row.update(control_number=f"SAMPLE-NEW-{i + 1:03d}", intake_month="September", intake_year=2026)
        for field in ["provided_type", "provided_purpose", "amount_granted", "fund_source"]:
            row[field] = None
        result.append({"id": f"sample-{i + 1}", "label": label, "case": row})
    return result

