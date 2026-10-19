"""
Every number in the dataset that came from DSWD, in one place, each one cited.

Anything NOT in this file and NOT marked with its source is an assumption we made,
and in the generator it carries a `# ASSUMED` comment. Before the manuscript is
final there should be no `# ASSUMED` left on a number that affects a result.

Sources used here:

  [PE p.17]   DSWD Policy Development and Planning Bureau (2022).
              Process Evaluation of the Assistance to Individuals in Crisis
              Situation (AICS). Schedule of assistance, p. 17.
  [PE T12]    Same report, Table 12, Most Recent Type of AICS Availed by
              Respondents, p. 30. n = 473.
  [PE T13]    Same report, Table 13, Sub-types of Medical Assistance Most
              Recently Requested, p. 30. n = 334.
  [PE T32-34] Same report, Tables 32, 33 and 34, Cost vs. Amount Received,
              pp. 42. Region XI rows used where available.
  [MC15]      DSWD Memorandum Circular No. 15, s. 2022.
"""

# --------------------------------------------------------------------------
# 1. Schedule of assistance: floor and ceiling per type, in pesos.  [PE p.17]
# --------------------------------------------------------------------------
# Note on medical: the schedule caps out-patient medicines and laboratory at
# 10,000, but hospital bills and other medical expenses run to 150,000.  That
# is a fifteen-fold difference INSIDE one assistance type, and which bracket
# applies is decided by the purpose, not by the type.  So medical is keyed by
# purpose below rather than by a single range.  This is question 10 for DSWD.

LIMITS = {
    "Funeral":          (5_000, 25_000),    # funeral expenses / cadaver transfer
    "Food Assistance":            (1_000,  3_000),
    "Cash Relief Assistance": (1_000, 10_000),    # "cash for other needs"
    # Educational is bracketed by school level [PE p.17].  We do not have the
    # school level as a field, so we use the full span and record the gap.
    "Educational":       (  500,  5_000),
    # Transportation has no printed range in the Process Evaluation schedule.
    # The only figure is an average received of 5,375 nationally [PE T34].
    "Transportation":  (1_000, 10_000),    # ASSUMED - treated as cash-for-other-needs
}

EDUCATION_BRACKETS = {                     # [PE p.17]
    "Elementary":  (  500, 1_000),
    "High school": (1_000, 1_500),
    "College":     (2_000, 5_000),
}

MEDICAL_LIMITS_BY_PURPOSE = {              # [PE p.17]
    "Medicines":      (1_000,  10_000),    # out-patient
    "Laboratory":     (1_000,  10_000),    # out-patient
    "Hospital bill":  (1_000, 150_000),
    "Dialysis":       (1_000, 150_000),
    "Chemotherapy":   (1_000, 150_000),
    "Assistive device": (1_000, 10_000),   # ASSUMED - not separately scheduled
}

# Casualties during a calamity get a flat 10,000 per casualty, no case study
# report required.  [PE p.17]
CALAMITY_CASUALTY_FLAT = 10_000

# A social worker may recommend above the maximum if justified in a Social Case
# Study Report, validated by the CIU Head and approved by the Division Chief.
# [PE p.17]  So the ceiling is a soft one.  We keep a small share of cases above
# it, because the real records will contain them.
SHARE_ABOVE_CEILING = 0.02                 # ASSUMED

# --------------------------------------------------------------------------
# 2. Type mix.  [PE T12], n = 473, most recent assistance availed.
# --------------------------------------------------------------------------
TYPE_MIX_REAL = {
    "Medical":         0.706,
    "Funeral":          0.123,
    "Cash Relief Assistance": 0.083,
    "Educational":       0.040,
    "Food Assistance":            0.038,
    "Transportation":  0.011,
}

# What we actually generate.  Deliberately flattened: at n = 1,000 the real mix
# leaves Transportation with 11 cases, and you cannot retrieve five meaningful
# neighbours from eleven.  DSWD's real Davao City caseload over twelve months is
# large enough that 1.1 percent is still several hundred records, so this is an
# artefact of OUR size, not of the programme.  Chapter 3 states this plainly and
# prints TYPE_MIX_REAL next to it.
TYPE_COUNTS = {
    "Medical":         510,
    "Funeral":          150,
    "Cash Relief Assistance": 100,
    "Educational":        80,
    "Food Assistance":             80,
    "Transportation":   80,
}

# --------------------------------------------------------------------------
# 3. Medical sub-types.  [PE T13], n = 334, most recently requested.
# --------------------------------------------------------------------------
# These map onto purpose_of_assistance, which means the field that decides the
# medical bracket may already be in the extract.  Worth confirming (question 3).
MEDICAL_PURPOSE_MIX = {
    "Medicines":        0.605,
    "Hospital bill":    0.174,
    "Laboratory":       0.108,
    "Dialysis":         0.047,   # dialysis and chemotherapy reported together
    "Chemotherapy":     0.034,   #   at 8.1%; split here  # ASSUMED split
    "Assistive device": 0.032,   # ASSUMED - remainder
}

# --------------------------------------------------------------------------
# 4. Region XI average amounts actually received.  [PE T32-T34]
# --------------------------------------------------------------------------
# These anchor the CENTRE of each distribution.  They do NOT give the spread,
# and they say nothing about which applicant gets which amount.  The spread and
# the conditioning come from the judged sample (Part 7 of the design) and, if
# DSWD answers, from the per-type statistics request (Layer 3).
REGION_XI_MEAN_RECEIVED = {
    "Funeral":          13_129.63,   # [PE T32] against a stated need of 45,230.74
    "Educational":        7_142.86,   # [PE T32]
    "Food Assistance":             3_857.14,   # [PE T33]
    "Cash Relief Assistance":  4_400.00,   # [PE T33]
    # Transportation: no Region XI row; national average received 5,375 [PE T34]
    "Transportation":   5_375.00,   # national, not Region XI
    # Medical: no cost-vs-received table in the report.
}

NATIONAL_MEAN_RECEIVED = {
    "Funeral":          11_196.43,   # [PE T32]
    "Educational":        4_722.22,   # [PE T32]
    "Food Assistance":             2_882.35,   # [PE T33]
    "Cash Relief Assistance":  5_629.73,   # [PE T33]
    "Transportation":   5_375.00,   # [PE T34]
}

# --------------------------------------------------------------------------
# 5. Context figures, used for sanity rather than generation.
# --------------------------------------------------------------------------
CIS_CLIENTS_PER_DAY_FO11 = 250      # [PE p.39] Davao City CIS, average
AICS_FREQUENCY_LIMITS = {           # [PE p.17]
    "Medical":         "quarterly (maximum frequency per guidelines)",
    "Funeral":          "availment of one service excludes others in the category",
    "Educational":       "once per school year; college once per semester; max 3 children",
    "Food Assistance":            "as needed",
    "Cash Relief Assistance": "once every 6 months, maximum of 1 year",
}

# --------------------------------------------------------------------------
# 6. Our own assumptions that need a DSWD answer.  All marked ASSUMED.
# --------------------------------------------------------------------------
# Region XI daily minimum wage, non-agriculture, used only to place an applicant
# in the Minimum Wage Earner / Below Minimum Wage Earner sub-category.
MIN_WAGE_MONTHLY = 12_500           # ASSUMED - confirm current Region XI rate

EVENTS_PER_APPLICANT = {1: 0.85, 2: 0.12, 3: 0.03}   # ASSUMED - question 9

UNKNOWN_RATE_MONEY = 0.05           # ASSUMED - question 1 / real extract
UNKNOWN_RATE_OTHER = 0.02           # ASSUMED

WINDOW_START = "2025-08-01"         # matches the extract window DSWD confirmed
WINDOW_END   = "2026-08-31"

ROUND_AMOUNTS_TO = 500              # real grants are round numbers
RANDOM_SEED = 20261009
