"""Study field definitions shared by API validation and the intake form."""
from .study_schema import MATCHING_FIELDS, PRINTED_TO_CANONICAL, BOOLEAN_FIELDS, MULTI_FIELDS, NUMERIC_FIELDS

TYPES = ['Medical', 'Funeral', 'Transportation', 'Educational', 'Food Assistance', 'Cash Relief Assistance']
CHOICES = {'client_type': ['New', 'Returning'],
 'service_setting': ['Onsite', 'Malasakit', 'Offsite'],
 'referral_type': ['Walk-in', 'Referral'],
 'occupation': ['Construction worker',
                'Driver',
                'Factory worker',
                'Farmer',
                'Fisherfolk',
                'Househelp',
                'Office staff',
                'Vendor',
                'Security guard',
                'None'],
 'illness_duration': ['Recently diagnosed (3 months and below)',
                      'Three months to a year',
                      'Chronic, lifelong',
                      'not_applicable'],
 'target_sector': ['FHONA', 'SC', 'WEDC', 'PWD', 'CNSP', 'YNSP', 'PLHIV'],
 'sub_category': ['Solo Parent',
                  'Indigenous People',
                  '4Ps Beneficiary',
                  'Street Dwellers',
                  'KIA/WIA',
                  'Stateless Person',
                  'Asylum Seekers',
                  'Refugees',
                  'Recovering Person Who Used Drugs',
                  'Others',
                  'No Regular Income',
                  'Below Minimum Wage Earner',
                  'Minimum Wage Earner'],
 'disability_type': ['Physical Disability',
                     'Visual Disability',
                     'Deaf/Hard-of-hearing',
                     'Intellectual Disability',
                     'Psychosocial Disability',
                     'Mental Disability',
                     'Cancer',
                     'Learning Disability',
                     'Speech Impairment',
                     'Rare Disease'],
 'purpose_of_assistance': ['Allowance',
                           'Assistive device',
                           'Cadaver transfer',
                           'Chemotherapy',
                           'Dialysis',
                           'Food subsidy',
                           'Funeral expenses',
                           'Hospital bill',
                           'Laboratory',
                           'Medicines',
                           'Other needs',
                           'School fees',
                           'School supplies',
                           'Transportation for medical treatment',
                           'Transportation to home province']}

LABELS = {canonical: printed for printed, canonical in PRINTED_TO_CANONICAL.items()}
LABELS.update(employed_members='Employed household members', seasonal_members='Seasonal workers',
              service_setting='Service setting', occupation='Occupation',
              client_type='Client type', referral_type='Walk-in or referral',
              sub_category='Sub-category', illness_duration='Duration of illness')


def field(key, label=None, kind=None, options=None, optional=True):
    if kind is None:
        kind = ('boolean' if key in BOOLEAN_FIELDS else 'multi' if key in MULTI_FIELDS
                else 'count' if key in ('employed_members', 'seasonal_members')
                else 'money' if key in NUMERIC_FIELDS or key == 'documented_cost'
                else 'select' if key in CHOICES else 'text')
    return dict(key=key, label=label or LABELS.get(key, key.replace('_', ' ').capitalize()),
                kind=kind, options=options or CHOICES.get(key, []), optional=optional, hint=None)


SECTIONS = [
    dict(id='intake', title='Intake details', fields=[
        field('case_id', 'Applicant reference ID'),
        field('event_id', 'Event ID'), field('control_no', 'Control number'),
        field('date_received', 'Date received (YYYY-MM-DD)'),
        field('assistance_type', 'Type of assistance sought', 'select', TYPES, False),
        *[field(k) for k in MATCHING_FIELDS[:5] if k != 'occupation'],
    ]),
    dict(id='income', title='I. Income and financial resources', fields=[field(k) for k in ['occupation','employed_members','seasonal_members','combined_family_income','insurance_coverage','savings']]),
    dict(id='expenses', title='II. Budget and expenses', fields=[field(k) for k in ['monthly_expenses','emergency_fund']]),
    dict(id='crisis', title='III. Severity of the crisis', fields=[field(k) for k in MATCHING_FIELDS if k == 'illness_duration' or k.startswith('crisis_')]),
    dict(id='support', title='IV. Available support systems', fields=[field(k) for k in MATCHING_FIELDS if k.startswith('support_')]),
    dict(id='resources', title='V. External resources', description='Select Yes, No, or Not recorded for each resource. If the section was unanswered, leave every answer Not recorded. If none apply, explicitly select No for each resource.', fields=[field(k) for k in MATCHING_FIELDS if k.startswith('ext_')]),
    dict(id='efforts', title='VI. Self-help and client efforts', fields=[field(k) for k in MATCHING_FIELDS if k.startswith('selfhelp_')]),
    dict(id='vulnerability', title='VII. Vulnerability and risk factors', fields=[field(k) for k in MATCHING_FIELDS if k.startswith('vuln_')]),
    dict(id='sector', title='VIII. Client sector and income', fields=[field(k) for k in ['target_sector','sub_category','disability_type',*sorted(k for k in NUMERIC_FIELDS if k.startswith('income_')), 'total_income_past_6_months']]),
    dict(id='context', title='Supporting context', description='Context is displayed with cases and never used for similarity.', fields=[field('diagnosis_cause_of_death'),field('documented_cost'),field('mode_of_assistance')]),
    dict(id='provided', title='Assistance recorded', description='Leave blank for an undecided intake. Missing historical amounts remain unavailable.', fields=[field('provided_type','Type granted','select',TYPES),field('provided_purpose','Purpose granted'),field('amount_granted'),field('fund_source')]),
]


def empty_intake():
    return {f['key']: None for s in SECTIONS for f in s['fields']}
