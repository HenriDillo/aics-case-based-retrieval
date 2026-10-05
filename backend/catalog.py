"""GIS presentation metadata shared by the form and server-side comparison.

The browser renders these definitions; it does not define matching rules.
Amounts are entered, never estimated or aggregated by this application.
"""

TYPES = ["medical", "burial", "transportation", "educational", "food", "cash relief"]
CRISES = ["hospitalization", "death of a family member", "catastrophic event", "disablement", "loss of livelihood", "others"]
SUPPORT = ["family", "relatives", "friends", "employer", "church or community organization"]
RESOURCES = ["PhilHealth", "health card", "guarantee letter from another agency", "MSS discount", "senior citizen discount", "PWD discount", "others", "not applicable"]
VULNERABILITIES = ["elderly in the household", "child in need in the household", "PWD in the household", "pregnant person in the household", "a member physically or mentally incapacitated to work", "inability to secure stable employment"]
SUBCATEGORIES = ["solo parent", "indigenous people", "street dweller", "4Ps beneficiary", "minimum wage earner", "below minimum wage earner", "no regular income", "others"]
ILLNESS = ["recently diagnosed (3 months or below)", "3 months to a year", "chronic / lifelong", "not applicable"]
MODES = ["outright cash", "guarantee letter", "material assistance", "psychological support", "referral"]
SECTORS = ["FHONA", "WEDC", "PWD", "CNSP", "SC", "YNSP", "PLHIV"]
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]


def field(key, label, kind="text", options=None, optional=False, hint=None):
    return {"key": key, "label": label, "kind": kind, "options": options or [], "optional": optional, "hint": hint}


SECTIONS = [
    {"id": "intake", "title": "Intake details", "fields": [
        field("intake_month", "Month of intake", "select", MONTHS),
        field("intake_year", "Year of intake", "year"),
        field("control_number", "Control number"),
        field("client_status", "Client status", "select", ["new", "returning"]),
        field("entry_method", "Entry method", "select", ["walk-in", "referral"]),
        field("assistance_type", "Type of assistance sought", "select", TYPES),
        field("purpose", "Purpose of assistance"),
        field("mode_of_assistance", "Mode of assistance", "select", MODES),
    ]},
    {"id": "income", "title": "I. Income and Financial Resources", "fields": [
        field("family_members_employed", "Number of family members employed", "count"),
        field("seasonal_employees", "Number who are seasonal employees", "count"),
        field("combined_family_income", "Combined family income", "money", hint="Monthly household income."),
        field("insurance_coverage", "Insurance coverage", "boolean"),
        field("savings", "Savings", "boolean"),
    ]},
    {"id": "expenses", "title": "II. Budget and Expenses", "fields": [
        field("monthly_family_expenses", "Monthly family expenses", "money"),
        field("emergency_fund", "Availability of emergency fund", "boolean"),
    ]},
    {"id": "crisis", "title": "III. Severity of the Crisis", "fields": [
        field("illness_duration", "How long the patient has suffered from the illness", "select", ILLNESS),
        field("recent_crisis", "Any crisis in the past 3 months", "boolean"),
        field("crises", "Crises experienced", "multi", CRISES),
        field("crisis_other", "Other crisis details", optional=True),
    ]},
    {"id": "support", "title": "IV. Availability of Support Systems", "fields": [
        field("support_systems", "Available support systems", "multi", SUPPORT),
    ]},
    {"id": "resources", "title": "V. External Resources Tapped", "fields": [
        field("external_resources", "External resources tapped", "multi", RESOURCES),
        field("external_resources_other", "Other external resource details", optional=True),
    ]},
    {"id": "efforts", "title": "VI. Self Help and Client Efforts", "fields": [
        field("sought_employment", "Successfully sought employment or additional income", "boolean"),
        field("sought_help", "Successfully reached out to organizations or agencies for help", "boolean"),
    ]},
    {"id": "vulnerability", "title": "VII. Vulnerability and Risk Factors", "fields": [
        field("vulnerabilities", "Vulnerability and risk factors", "multi", VULNERABILITIES),
    ]},
    {"id": "sector", "title": "VIII. Client Sector", "fields": [
        field("target_sector", "Target sector", "select", SECTORS),
        field("sub_categories", "Sub-category", "multi", SUBCATEGORIES),
        field("sub_category_other", "Other sub-category details", optional=True),
        field("disability_type", "Type of disability, if applicable", optional=True),
        field("salaries_wages", "Salaries and wages", "money"),
        field("entrepreneurial_income", "Entrepreneurial income", "money"),
        field("domestic_cash_assistance", "Cash assistance from domestic sources", "money"),
        field("abroad_cash_assistance", "Cash assistance from abroad", "money"),
        field("government_transfers", "Government transfers (such as 4Ps)", "money"),
        field("pension", "Pension", "money"),
        field("other_income", "Other income", "money"),
        field("total_income_six_months", "Total income in the past 6 months", "money", hint="Recorded intake figure; enter manually."),
    ]},
    {"id": "provided", "title": "Assistance provided", "description": "Optional for a new intake. Complete this section only if assistance has already been recorded. These fields are never suggested by the system.", "fields": [
        field("provided_type", "Type of assistance provided", "select", TYPES, optional=True),
        field("provided_purpose", "Purpose of assistance provided", optional=True),
        field("amount_granted", "Amount granted", "money", optional=True),
        field("fund_source", "Fund source", optional=True),
    ]},
]


def empty_intake():
    return {
        f["key"]: ([] if f["kind"] == "multi" else None if f["kind"] == "boolean" else "")
        for section in SECTIONS for f in section["fields"]
    }

