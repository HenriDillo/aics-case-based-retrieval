"""
Applicant intake schema for the AICS triage prototype.

IMPORTANT: DSWD has not yet delivered the real dataset or a data dictionary.
The fields below are PLACEHOLDERS, drafted from public knowledge of how the
Assistance to Individuals in Crisis Situations (AICS) program is generally
structured (crisis/assistance type, household economic indicators, urgency
signals) and from the Research Brief (GF-004). They exist so the prototype
UI and pipeline have something concrete to wire up against.

TODO (once the real dataset arrives): replace this file's field list and
value ranges with whatever DSWD's actual data dictionary specifies, and
re-check every downstream module (preprocessing.py, model.py, explain.py)
against the real column names.
"""

from dataclasses import dataclass, fields
from typing import Literal

ASSISTANCE_TYPES = [
    "Medical",
    "Burial",
    "Food/Cash",
    "Transportation",
    "Educational",
]

EMPLOYMENT_STATUS = [
    "Unemployed",
    "Informally employed",
    "Formally employed",
    "Retired/PWD/Senior - unable to work",
]

URGENCY_INDICATORS = [
    "None reported",
    "Ongoing medical emergency",
    "Recent death in household",
    "Displacement / calamity-affected",
    "No income for 30+ days",
]


@dataclass
class ApplicantRecord:
    """One applicant's intake features. Placeholder shape — see module docstring."""

    age: int
    household_size: int
    monthly_household_income_php: float
    dependents_count: int
    assistance_type: Literal[
        "Medical", "Burial", "Food/Cash", "Transportation", "Educational"
    ]
    employment_status: str
    urgency_indicator: str
    has_prior_aics_assistance: bool
    days_since_application: int

    @classmethod
    def field_names(cls):
        return [f.name for f in fields(cls)]
