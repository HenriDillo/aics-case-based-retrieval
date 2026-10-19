"""Six study examples; original IDs retained to exclude their own household."""
from .catalog import TYPES
from .data_store import get_cases
from .study_adapter import to_display

def sample_cases():
    samples = []
    for index, assistance in enumerate(TYPES):
        record = next((r for r in get_cases() if r.values['assistance_type_granted'] == assistance), None)
        if record is None:
            continue
        case = to_display(record)
        for field in ['provided_type','provided_purpose','amount_granted','fund_source']:
            case[field] = None
        samples.append(dict(id=f'sample-{index+1}', label=f'{assistance} · sample intake', case=case))
    return samples
