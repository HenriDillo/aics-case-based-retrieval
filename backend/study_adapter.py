"""Boundary between JSON form values and canonical study records."""
from .catalog import empty_intake
from .models import CaseInput
from .study_loader import StudyRecord
from .study_schema import MULTI_FIELDS, NOT_APPLICABLE


def to_study(case):
    values = dict(case)
    for key in MULTI_FIELDS:
        values[key] = None if case.get(key) is None else frozenset(case[key])
    values['assistance_type_granted'] = case['assistance_type']
    # An ID is optional for a genuinely new intake. The sentinel is never stored.
    identity = case.get('case_id') or '__new_intake__'
    return StudyRecord('api', 0, identity, case.get('event_id'), values, {})


def to_display(record):
    result = empty_intake()
    for key in result:
        value = record.values.get(key)
        result[key] = sorted(value) if isinstance(value, frozenset) else value
    result.update(case_id=record.applicant_id, event_id=record.event_id,
                  assistance_type=record.values['assistance_type_granted'],
                  provided_type=record.values['assistance_type_granted'],
                  provided_purpose=record.values['purpose_of_assistance'])
    if result.get('documented_cost') == NOT_APPLICABLE:
        result['documented_cost'] = None
    return CaseInput.model_validate(result).model_dump()
