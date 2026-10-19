"""Validated study intake and display-only response contracts."""
from datetime import date
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator
from .catalog import SECTIONS

DEFINITIONS = {f['key']: f for s in SECTIONS for f in s['fields']}
Money = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Count = Annotated[int, Field(ge=0)]
Text = Annotated[str, Field(min_length=1, max_length=500)]

class IntakeValidation(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)

    @field_validator('*', mode='before', check_fields=False)
    @classmethod
    def normalize_and_validate(cls, value, info):
        definition = DEFINITIONS.get(info.field_name)
        if not definition:
            return value
        if isinstance(value, str):
            value = value.strip()
            if not value:
                value = None
        if value is None:
            if not definition['optional']:
                raise ValueError('Select an assistance type.')
            return None
        if definition['kind'] in ('money', 'count') and isinstance(value, bool):
            raise ValueError('Enter a number, not a yes/no answer.')
        if definition['kind'] == 'select' and value not in definition['options']:
            raise ValueError('Select a listed option.')
        if definition['kind'] == 'boolean' and not isinstance(value, bool):
            raise ValueError('Use Yes, No, or Not recorded.')
        if definition['kind'] == 'multi':
            if not isinstance(value, list) or any(v not in definition['options'] for v in value):
                raise ValueError('Select only listed options.')
            if len(set(value)) != len(value):
                raise ValueError('Do not repeat a selection.')
        if info.field_name == 'date_received':
            try:
                date.fromisoformat(value)
            except (TypeError, ValueError):
                raise ValueError('Use YYYY-MM-DD.')
        return value

fields = {}
for key, definition in DEFINITIONS.items():
    kind = definition['kind']
    annotation = (Money if kind == 'money' else Count if kind == 'count'
                  else bool if kind == 'boolean' else list[str] if kind == 'multi' else Text)
    fields[key] = (annotation | None, None) if definition['optional'] else (annotation, ...)
CaseInput = create_model('CaseInput', __base__=IntakeValidation, **fields)

class ComparisonRow(BaseModel):
    key: str
    label: str
    current: str
    past: str
    status: Literal['same', 'different', 'not_recorded']

class ComparisonSection(BaseModel):
    id: str
    title: str
    rows: list[ComparisonRow]

class RetrievedCase(CaseInput):
    matched_fields: list[str]
    explanation_context: str
    comparison: list[ComparisonSection] = Field(default_factory=list)

class SampleCase(BaseModel):
    id: str
    label: str
    case: CaseInput
