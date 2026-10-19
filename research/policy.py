"""Frozen generation choices, recorded before running outcome comparisons.

Source: DSWD PDPB (2022), Process Evaluation of AICS, printed pp. 41-42,
Tables 29, 31, 32 and 33. Figures transcribed and visually verified 2026-10-19.
This is a synthetic research rule, not current benefit policy or advice.
"""
VERSION = 'v26-preparation-1'
SOURCE_URL = 'https://pdpb.dswd.gov.ph/download/process-evaluation-of-aics/?wpdmdl=4603'
AMOUNT_SEED = 20261014
COST_SEED = 20261019
SETTINGS = (0.0, 0.25, 0.5, 0.75)
LOG_SD = 0.25
ROUND_TO = 50

# purpose: type, base share, published mean cost (None if unavailable), ceiling
# Existing shares retain the approved four-decimal values. New laboratory share
# is round(5250 / 5800, 4); dialysis/chemo use the shared T29 row, 8228.57/23142.86.
SHARES = {
    'Hospital bill': ('Medical', .2075, 147375.00, 150000),
    'Medicines': ('Medical', .8046, 7831.71, 10000),
    'Laboratory': ('Medical', .9052, 5800.00, 10000),
    'Dialysis': ('Medical', .3556, 23142.86, 150000),
    'Chemotherapy': ('Medical', .3556, 23142.86, 150000),
    # Keep current amount_rule_v2 ceiling; older dswd_figures.py's 10000 is stale.
    'Assistive device': ('Medical', .3556, None, 150000),
    'Funeral expenses': ('Funeral', .2903, 45230.74, 25000),
    'Cadaver transfer': ('Funeral', .2903, 45230.74, 25000),
    'Allowance': ('Educational', .6105, 11700.00, None),
    'School fees': ('Educational', .6105, 11700.00, None),
    'School supplies': ('Educational', .6105, 11700.00, None),
    'Transportation to home province': ('Transportation', 1., None, None),
    'Transportation for medical treatment': ('Transportation', 1., None, None),
}
DIRECT = {'Food subsidy': ('Food Assistance', 3857.14, None),
          'Other needs': ('Cash Relief Assistance', 4400.00, 10000)}
FLOORS = {'Medical': 1000, 'Funeral': 5000, 'Educational': 500,
          'Food Assistance': 1000, 'Cash Relief Assistance': 1000}

# ASSUMED: uniform spread, not estimated from recipients. Fixed before generation.
# Published means anchor intervals at 0.5x to 1.5x the reference mean. Educational
# purposes use the tuition benchmark as the approved rule does (proxy assumption).
# Assistive and transportation ranges have no Region XI cost benchmark.
COST_RANGES = {p: ((.5 * mean, 1.5 * mean) if mean else
                   (10000, 40000) if p == 'Assistive device' else (1000, 10000))
               for p, (_, _, mean, _) in SHARES.items()}
EXACT_PAIRS = (('J01','J22'), ('J28','J13'), ('J11','J30'), ('J20','J35'))
NEAR_PAIRS = (('J14','J37','vuln_member_incapacitated'),
              ('J04','J24','support_relatives'), ('J27','J03','savings'),
              ('J17','J33','selfhelp_sought_income'))
