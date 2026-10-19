"""Load one synthetic study CSV per process. Never write intake data."""
import os
from pathlib import Path
from .study_loader import load_study_csv

_cases = None
DEFAULT_CSV = Path(__file__).parent / 'data' / 'study_complete.csv'

def load_cases():
    global _cases
    if _cases is None:
        dataset = load_study_csv(Path(os.environ.get('AICS_CSV_PATH', DEFAULT_CSV)))
        if not dataset.records:
            raise ValueError('The study case base is empty')
        _cases = dataset.records

def get_cases():
    if _cases is None:
        raise RuntimeError('Case base has not been loaded')
    return _cases
