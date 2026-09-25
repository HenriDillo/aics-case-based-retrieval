"""One read-only CSV, loaded once per application process into pandas."""

import json
import os
from pathlib import Path
import pandas as pd
from .catalog import SECTIONS
from .models import CaseInput

_cases: pd.DataFrame | None = None
DEFAULT_CSV = Path(__file__).parent / "data" / "mock_cases.csv"


def load_cases() -> None:
    global _cases
    if _cases is not None:
        return
    path = Path(os.environ.get("AICS_CSV_PATH", str(DEFAULT_CSV)))
    frame = pd.read_csv(path, keep_default_na=False, dtype=str)
    definitions = [f for s in SECTIONS for f in s["fields"]]
    if set(frame.columns) != {f["key"] for f in definitions}:
        raise ValueError("CSV columns do not match the documented GIS schema.")
    for f in definitions:
        if f["kind"] == "multi":
            frame[f["key"]] = frame[f["key"]].map(json.loads)
    records = [CaseInput.model_validate(row).model_dump() for row in frame.to_dict(orient="records")]
    if not records or len({r["control_number"] for r in records}) != len(records):
        raise ValueError("CSV must contain cases with unique control numbers.")
    if any(r["amount_granted"] is None for r in records):
        raise ValueError("Past cases must be closed records with assistance provided.")
    _cases = pd.DataFrame(records, dtype=object)


def get_cases() -> pd.DataFrame:
    """Return the shared DataFrame. Consumers must not modify it."""
    if _cases is None:
        raise RuntimeError("The case CSV has not been loaded at startup.")
    return _cases

