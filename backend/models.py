"""Validated, de-identified intake and API response contracts."""

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from .catalog import SECTIONS

Money = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Count = Annotated[int, Field(ge=0)]
Text = Annotated[str, Field(min_length=1, max_length=500)]


class CaseInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    intake_month: str
    intake_year: Annotated[int, Field(ge=1900, le=9999)]
    control_number: Annotated[str, Field(min_length=1, max_length=80)]
    client_status: str
    entry_method: str
    assistance_type: str
    purpose: Text
    mode_of_assistance: str
    amount_requested: Money  # Deliberately no policy ceiling.
    family_members_employed: Count
    seasonal_employees: Count
    combined_family_income: Money
    insurance_coverage: bool
    savings: bool
    monthly_family_expenses: Money
    emergency_fund: bool
    illness_duration: str
    recent_crisis: bool
    crises: list[str]
    crisis_other: str | None = None
    support_systems: list[str]
    external_resources: list[str]
    external_resources_other: str | None = None
    sought_employment: bool
    sought_help: bool
    vulnerabilities: list[str]
    target_sector: str
    sub_categories: list[str]
    sub_category_other: str | None = None
    disability_type: str | None = None
    salaries_wages: Money
    entrepreneurial_income: Money
    domestic_cash_assistance: Money
    abroad_cash_assistance: Money
    government_transfers: Money
    pension: Money
    other_income: Money
    total_income_six_months: Money
    provided_type: str | None = None
    provided_purpose: Text | None = None
    amount_granted: Money | None = None
    fund_source: Text | None = None

    @field_validator("*", mode="before")
    @classmethod
    def validate_choice(cls, value, info):
        definition = next((f for s in SECTIONS for f in s["fields"] if f["key"] == info.field_name), None)
        if definition and definition["optional"] and value == "":
            return None
        if definition and definition["kind"] == "select" and value is not None:
            if value not in definition["options"]:
                raise ValueError("Select one of the listed options.")
        if definition and definition["kind"] == "multi":
            if not isinstance(value, list) or any(item not in definition["options"] for item in value):
                raise ValueError("Choose only the listed options.")
            if len(value) != len(set(value)):
                raise ValueError("Do not repeat a selection.")
        return value

    @model_validator(mode="after")
    def validate_record(self):
        if "not applicable" in self.external_resources and len(self.external_resources) > 1:
            raise ValueError("External resources: choose 'not applicable' on its own.")
        if not self.recent_crisis and self.crises:
            raise ValueError("Crises experienced: clear the selections or mark a crisis in the past 3 months as Yes.")
        if self.recent_crisis and not self.crises:
            raise ValueError("Crises experienced: select at least one crisis when the answer is Yes.")
        outcome = [self.provided_type, self.provided_purpose, self.amount_granted, self.fund_source]
        if any(v is not None for v in outcome) and not all(v is not None for v in outcome):
            raise ValueError("Assistance provided: fill all four fields, or leave all four blank for a new intake.")
        return self


class ComparisonRow(BaseModel):
    key: str
    label: str
    current: str
    past: str
    status: Literal["same", "different", "not_recorded"]


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

