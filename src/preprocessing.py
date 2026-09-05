"""
Preprocessing pipeline — STUB.

Owner (per team split): Henri.

This module is intentionally unimplemented. Per the team's decision to wait
for the real DSWD dataset rather than build against a synthetic one, there is
no cleaning/encoding/SMOTE logic here yet.

Once data/raw/<file> exists (see data/README.md), this file should:
  1. load_raw()        -> read the DSWD file (csv/xlsx) into a DataFrame
  2. clean()           -> handle missing values, fix dtypes, de-identify
                          any residual PII, validate against schema.py
  3. encode_features() -> one-hot / ordinal encode categorical fields
  4. balance_classes()  -> apply SMOTE (imbalanced-learn) to the training
                          split only, on the high-vulnerability minority class
  5. train_test_split_data() -> stratified split, saved for model.py

Keep every function's input/output as plain pandas DataFrames / Series so
model.py and any notebook can call them without re-implementing logic.
"""

from __future__ import annotations

import pandas as pd


def load_raw(path: str) -> pd.DataFrame:
    """Load the raw DSWD file. TODO: implement once the real file/format is known."""
    raise NotImplementedError(
        "Waiting on the real DSWD dataset. See data/README.md. "
        "Implement this once the file and its columns are confirmed."
    )


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """De-identify, fix dtypes, handle missing values. TODO once data arrives."""
    raise NotImplementedError


def encode_features(df: pd.DataFrame) -> pd.DataFrame:
    """Encode categorical fields (see schema.py) for model input. TODO."""
    raise NotImplementedError


def balance_classes(X_train: pd.DataFrame, y_train: pd.Series):
    """Apply SMOTE to the training split only. TODO."""
    raise NotImplementedError


def train_test_split_data(df: pd.DataFrame, target_col: str, test_size: float = 0.2):
    """Stratified train/test split. TODO."""
    raise NotImplementedError
