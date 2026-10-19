"""
Generate the intake side of the AICS case base.

What this produces: 1,000 assistance events with every GIS Section I to VIII
field plus the header fields, and an EMPTY amount_granted column.

The amount is deliberately left empty.  It comes later, from the pattern fitted
to the judged sample (Part 7 and Part 9 of the dataset design).  We may invent
the applicants.  We may not invent the amounts.

Run:  python generate_intake.py
Out:  ../data/synthetic/v1_intake.csv
      ../data/synthetic/v1_manifest.json

Importable: make_event() is used by make_sheets.py to build the judged sample.
"""

import csv
import json
import random
import pathlib
from datetime import date, timedelta

import dswd_figures as F

OUT_DIR = pathlib.Path(__file__).resolve().parent.parent / "data" / "synthetic"
GENERATOR_VERSION = "1.0"

# ==========================================================================
# Vocabularies.  Printed options come from the GIS; weights are ASSUMED.
# ==========================================================================

# Section VIII target sectors, all seven printed options.
SECTORS = {
    "FHONA": 0.58,   # Family Heads and Other Needy Adults - the catch-all
    "SC":    0.15,   # Senior Citizen
    "WEDC":  0.10,   # Women in Especially Difficult Circumstances
    "PWD":   0.08,
    "CNSP":  0.04,   # Children in Need of Special Protection
    "YNSP":  0.04,   # Youth in Need of Special Protection
    "PLHIV": 0.01,
}  # ASSUMED weights

# Section VIII sub-categories, all thirteen printed options.  Henri's audit
# flagged that five were missing from the starter generator (Street Dwellers,
# KIA/WIA, Stateless Person, Asylum Seekers, Refugees); all five are here.
SUBCAT_NON_INCOME = {
    "Solo Parent":                    0.14,
    "Indigenous People":              0.07,
    "4Ps Beneficiary":                0.18,
    "Street Dwellers":                0.012,
    "KIA/WIA":                        0.006,
    "Stateless Person":               0.003,
    "Asylum Seekers":                 0.003,
    "Refugees":                       0.003,
    "Recovering Person Who Used Drugs": 0.008,
    "Others":                         0.02,
}  # ASSUMED weights

# Section VIII disability types, all ten printed options.  The audit flagged
# that Speech Impairment and Mental Disability were missing; both are here, and
# Mental Disability is kept distinct from Psychosocial and Intellectual.
DISABILITIES = {
    "Physical Disability":     0.26,
    "Visual Disability":       0.15,
    "Deaf/Hard-of-hearing":    0.11,
    "Intellectual Disability": 0.10,
    "Psychosocial Disability": 0.09,
    "Mental Disability":       0.08,
    "Cancer":                  0.08,
    "Learning Disability":     0.06,
    "Speech Impairment":       0.05,
    "Rare Disease":            0.02,
}  # ASSUMED weights

# Purposes per assistance type.  Medical uses the real sub-type mix from the
# Process Evaluation, Table 13.  The rest are ASSUMED and need question 3.
PURPOSES = {
    "Medical":         F.MEDICAL_PURPOSE_MIX,
    "Funeral":          {"Funeral expenses": 0.88, "Cadaver transfer": 0.12},
    "Educational":       {"School fees": 0.45, "School supplies": 0.30,
                        "Allowance": 0.25},
    "Food Assistance":            {"Food subsidy": 1.0},
    "Cash Relief Assistance": {"Other needs": 1.0},
    "Transportation":  {"Transportation to home province": 0.62,
                        "Transportation for medical treatment": 0.38},
}

# Shown on the form only for funeral cases.  Excluded from matching, but it has
# to be consistent or DSWD will notice, and it makes the judged-sample sheets
# readable.
CAUSES_OF_DEATH = ["Cardiac arrest", "Stroke", "Cancer", "Pneumonia",
                   "Kidney failure", "Tuberculosis", "Dengue",
                   "Vehicular accident"]  # ASSUMED - free text on the real form

OCCUPATIONS = ["Construction worker", "Driver", "Factory worker", "Farmer",
               "Fisherfolk", "Househelp", "Office staff", "Vendor",
               "Security guard", "None"]  # ASSUMED - question 4

ILLNESS_DURATIONS = ["Recently diagnosed (3 months and below)",
                     "Three months to a year",
                     "Chronic, lifelong"]

HEALTH_PURPOSES = set(F.MEDICAL_PURPOSE_MIX) | {"Transportation for medical treatment"}

NA = "not_applicable"
YES, NO = "Yes", "No"


# ==========================================================================
# Small helpers
# ==========================================================================

def weighted(rng, table):
    """Pick one key from {key: weight}."""
    keys = list(table)
    return rng.choices(keys, weights=[table[k] for k in keys], k=1)[0]

def yn(rng, p):
    """Yes with probability p, otherwise No.  Never blank - an unticked box on
    the GIS means No, per the working assumption behind question 1."""
    return YES if rng.random() < p else NO

def peso(x, to=50):
    return int(round(x / to) * to)

def skewed_income(rng, scale):
    """AICS applicants are poor.  A long left-heavy tail with a thin right one."""
    v = rng.lognormvariate(0, 0.75) * scale
    return peso(min(v, scale * 3))

# AICS is crisis intervention, so the caseload is poor by definition.  Without
# a ceiling the component sums produce households on six figures a month, which
# would never reach a CIS queue.  Anything above this is scaled back in
# proportion so the mix of sources is kept.
HOUSEHOLD_INCOME_CEILING = 35_000        # ASSUMED - confirm against the extract

# 4Ps is targeted at households below the poverty threshold, so a 4Ps
# beneficiary earning well above it is not a real record.
FOURPS_INCOME_CEILING = 15_000           # ASSUMED - near the PSA poverty threshold


# ==========================================================================
# The generation chain.  Order matters: each step uses what came before.
# ==========================================================================

def pick_sectors(rng):
    """One sector usually, two sometimes.  Step 2."""
    first = weighted(rng, SECTORS)
    out = [first]
    if rng.random() < 0.12:  # ASSUMED - question 7 (is multi-select allowed?)
        second = weighted(rng, {k: v for k, v in SECTORS.items() if k != first})
        out.append(second)
    return out


def pick_disability(rng, sectors):
    """Structural: blank unless PWD is among the sectors.  Step 3."""
    if "PWD" not in sectors:
        return [NA]
    out = [weighted(rng, DISABILITIES)]
    if rng.random() < 0.08:  # a person may have more than one
        other = weighted(rng, {k: v for k, v in DISABILITIES.items() if k != out[0]})
        out.append(other)
    return out


def pick_employment(rng, sectors):
    """Step 4.  Senior citizens and PWDs are much less likely to be working."""
    if "SC" in sectors:
        p_any = 0.18
    elif "PWD" in sectors:
        p_any = 0.30
    else:
        p_any = 0.62                                     # ASSUMED
    if rng.random() > p_any:
        return 0, (1 if rng.random() < 0.22 else 0)      # may still do seasonal work
    employed = rng.choices([1, 2, 3], weights=[0.74, 0.22, 0.04])[0]
    seasonal = rng.choices([0, 1, 2], weights=[0.72, 0.24, 0.04])[0]
    return employed, seasonal


def pick_income(rng, employed, seasonal, sectors, subcats):
    """Step 5.  Monthly figures per source.  Each one is zero unless its own
    condition holds, which is what the checkbox beside it on the form means."""
    inc = dict.fromkeys(
        ["salaries_wages", "entrepreneurial", "cash_assistance_domestic",
         "cash_assistance_abroad", "government_transfers", "pension", "other"], 0)

    if employed:
        inc["salaries_wages"] = skewed_income(rng, 7_000 * employed)
    if seasonal:
        inc["salaries_wages"] += skewed_income(rng, 2_500 * seasonal)

    if rng.random() < 0.26:
        inc["entrepreneurial"] = skewed_income(rng, 4_000)       # sari-sari, vending
    if rng.random() < 0.34:
        inc["cash_assistance_domestic"] = peso(rng.uniform(200, 3_000))
    if rng.random() < 0.05:
        inc["cash_assistance_abroad"] = peso(rng.uniform(2_000, 15_000))
    if "4Ps Beneficiary" in subcats:
        inc["government_transfers"] = peso(rng.uniform(1_400, 3_200))
    elif rng.random() < 0.04:
        inc["government_transfers"] = peso(rng.uniform(500, 2_000))  # ASSUMED
    if "SC" in sectors and rng.random() < 0.46:
        inc["pension"] = peso(rng.uniform(1_000, 9_000))         # SSS/GSIS/social
    if rng.random() < 0.09:
        inc["other"] = peso(rng.uniform(200, 2_500))

    total = sum(inc.values())
    if total > HOUSEHOLD_INCOME_CEILING:
        # Round each component DOWN, so rounding cannot push the sum back over
        # the ceiling it was just scaled under.
        k = HOUSEHOLD_INCOME_CEILING / total
        inc = {s: int(v * k // 50) * 50 for s, v in inc.items()}
    return inc


def income_subcategory(monthly_total):
    """The three income-linked sub-categories are decided BY the income, not
    sampled next to it.  Sampling them independently is how you end up with a
    'No Regular Income' household earning 25,000."""
    if monthly_total <= 0:
        return "No Regular Income"
    if monthly_total < F.MIN_WAGE_MONTHLY:
        return "Below Minimum Wage Earner"
    if monthly_total <= F.MIN_WAGE_MONTHLY * 1.08:
        return "Minimum Wage Earner"
    return None


def pick_crisis(rng, atype, purpose):
    """Step 8.  Conditioned on why they came."""
    c = {k: NO for k in ["hospitalization", "death_of_member", "catastrophic_event",
                         "disablement", "loss_of_livelihood", "others"]}
    if atype == "Funeral":
        c["death_of_member"] = YES                       # hard rule
        c["hospitalization"] = yn(rng, 0.55)
        c["loss_of_livelihood"] = yn(rng, 0.30)
    elif atype == "Medical":
        c["hospitalization"] = yn(rng, 0.62 if purpose in
                                  ("Hospital bill", "Dialysis", "Chemotherapy") else 0.22)
        c["disablement"] = yn(rng, 0.14)
        c["loss_of_livelihood"] = yn(rng, 0.28)
    else:
        c["loss_of_livelihood"] = yn(rng, 0.42)
        c["catastrophic_event"] = yn(rng, 0.10)
        c["hospitalization"] = yn(rng, 0.08)
    if rng.random() < 0.06:
        c["others"] = YES
    any_crisis = any(v == YES for v in c.values())
    return c, (YES if any_crisis else NO)


def build(rng, atype, purpose=None, caseno=None, eventno=None):
    """Make one assistance event.  Returns a dict of columns."""
    r = {}

    # --- 1. why they came --------------------------------------------------
    purpose = purpose or weighted(rng, PURPOSES[atype])
    r["assistance_type_granted"] = atype
    r["purpose_of_assistance"] = purpose

    # --- 2 and 3. sectors, sub-categories, disability ----------------------
    sectors = pick_sectors(rng)
    subcats = [k for k in SUBCAT_NON_INCOME if rng.random() < SUBCAT_NON_INCOME[k]]
    disabilities = pick_disability(rng, sectors)

    # --- 4 and 5. employment and income ------------------------------------
    employed, seasonal = pick_employment(rng, sectors)
    inc = pick_income(rng, employed, seasonal, sectors, subcats)
    monthly = sum(inc.values())

    # 4Ps reaches the poorest households.  If the sampled income landed above
    # the programme's reach, this household would not be a beneficiary, so the
    # sub-category goes and so does the transfer that depended on it.  Sampling
    # the two independently is how you get a 4Ps household on 25,000 a month.
    if "4Ps Beneficiary" in subcats and monthly > FOURPS_INCOME_CEILING:
        subcats.remove("4Ps Beneficiary")
        inc["government_transfers"] = 0
        monthly = sum(inc.values())

    band = income_subcategory(monthly)
    if band:
        subcats.append(band)
    if not subcats:
        subcats = [NA]

    # --- 6. the two income questions ---------------------------------------
    # Section I asks combined family income; Section VIII asks total income in
    # the past six months.  Different questions, asked at different points, so
    # they do NOT line up exactly.  Henri's starter file had total = sum x 6 on
    # all 694 complete rows, which is the kind of exact identity DSWD would spot.
    r["combined_family_income"] = peso(
        min(monthly * rng.uniform(0.86, 1.14), HOUSEHOLD_INCOME_CEILING), 100)
    r["total_income_past_6_months"] = peso(monthly * 6 * rng.uniform(0.82, 1.18), 100)

    # --- 7. expenses and buffers -------------------------------------------
    # Expenses often exceed income.  That is frequently the crisis.
    r["monthly_expenses"] = peso(max(1_200, monthly * rng.uniform(0.70, 1.45)), 100)
    rich = monthly > F.MIN_WAGE_MONTHLY
    r["insurance_coverage"] = yn(rng, 0.30 if rich else 0.10)
    r["savings"] = yn(rng, 0.26 if rich else 0.07)
    r["emergency_fund"] = yn(rng, 0.18 if rich else 0.05)

    # --- 8 and 9. crisis, illness ------------------------------------------
    crisis, any_crisis = pick_crisis(rng, atype, purpose)
    r["crisis_last_3_months"] = any_crisis
    for k, v in crisis.items():
        r["crisis_" + k] = v

    health = purpose in HEALTH_PURPOSES
    r["illness_duration"] = (weighted(rng, {
        ILLNESS_DURATIONS[0]: 0.34, ILLNESS_DURATIONS[1]: 0.24,
        ILLNESS_DURATIONS[2]: 0.42}) if health else NA)

    # --- 10. cause of death, funeral only ----------------------------------
    r["diagnosis_cause_of_death"] = (rng.choice(CAUSES_OF_DEATH)
                                     if atype == "Funeral" else NA)

    # --- 11. who else is helping -------------------------------------------
    r["support_family"]    = yn(rng, 0.52)
    r["support_relatives"] = yn(rng, 0.44)
    r["support_friends"]   = yn(rng, 0.21)
    r["support_employer"]  = yn(rng, 0.11 if employed else 0.01)
    r["support_church"]    = yn(rng, 0.15)

    # --- 12. external resources already accessed ---------------------------
    r["ext_philhealth"] = yn(rng, 0.70 if health else 0.46)
    r["ext_health_card"] = yn(rng, 0.09)
    r["ext_guarantee_letter_other_agency"] = yn(rng, 0.22 if health else 0.06)
    r["ext_mss_discount"] = yn(rng, 0.26 if health else 0.04)
    r["ext_senior_citizen_discount"] = YES if ("SC" in sectors and rng.random() < 0.82) else NO
    r["ext_pwd_discount"] = YES if ("PWD" in sectors and rng.random() < 0.78) else NO

    # --- 13. vulnerability markers -----------------------------------------
    r["vuln_elderly_child_pwd_pregnant"] = (
        YES if ({"SC", "PWD", "CNSP", "YNSP"} & set(sectors)) else yn(rng, 0.44))
    r["vuln_member_incapacitated"] = yn(rng, 0.62 if "PWD" in sectors else 0.14)
    # A household with nobody working and no income from any source cannot
    # answer No here.  A social worker reading the sheet would stop on that.
    if not employed and not seasonal and monthly == 0:
        r["vuln_unstable_employment"] = YES
    else:
        r["vuln_unstable_employment"] = yn(rng, 0.30 if employed else 0.78)

    # --- 14. self-help efforts ---------------------------------------------
    r["selfhelp_sought_income"] = yn(rng, 0.48)
    r["selfhelp_reached_agencies"] = yn(rng, 0.33)

    # --- 15. header and administrative -------------------------------------
    r["employed_members"] = employed
    r["seasonal_members"] = seasonal
    # Someone running a sari-sari store has an occupation even though nobody in
    # the household is formally employed, so business income has to show here.
    if employed:
        r["occupation"] = rng.choice(OCCUPATIONS[:-1])
    elif inc["entrepreneurial"] > 0:
        r["occupation"] = "Vendor"
    else:
        r["occupation"] = "None"
    r["target_sector"] = "|".join(sectors)
    r["sub_category"] = "|".join(sorted(set(subcats)))
    r["disability_type"] = "|".join(disabilities)
    for k, v in inc.items():
        r["income_" + k] = v

    r["program"] = "AICS"
    r["client_type"] = "Returning" if (eventno or 1) > 1 else (
        "Returning" if rng.random() < 0.28 else "New")
    r["service_setting"] = weighted(rng, {"Onsite": 0.74, "Malasakit": 0.18,
                                          "Offsite": 0.08})  # ASSUMED
    r["referral_type"] = weighted(rng, {"Walk-in": 0.81, "Referral": 0.19})  # ASSUMED
    # Guarantee letters go to service providers, so they cluster on hospital
    # bills; outright cash is used for 10,000 and below.  [PE p.17]
    r["mode_of_assistance"] = ("Guarantee Letter"
                               if purpose in ("Hospital bill", "Dialysis", "Chemotherapy")
                               and rng.random() < 0.66 else "Outright Cash")
    r["fund_source"] = weighted(rng, {"Regular Funds": 0.90,
                                      "Quick Response Fund": 0.10})  # ASSUMED

    # --- the outcome, left empty on purpose --------------------------------
    r["amount_granted"] = ""

    r["case_id"] = caseno
    r["event_id"] = eventno
    return r


# ==========================================================================
# Unknowns.  Separate pass, so structural blanks written above are untouched.
# ==========================================================================

MONEY_COLS = ["combined_family_income", "monthly_expenses",
              "total_income_past_6_months"]
# target_sector is never blank: it is how the case is classified, so it is
# filled before anything else on the form and it drives the structural blanks
# in Section VIII.  Everything else can be unknown.
NEVER_BLANK = {"case_id", "event_id", "control_no", "date_received", "program",
               "assistance_type_granted", "purpose_of_assistance",
               "amount_granted", "fund_source", "target_sector", "client_type"}

def inject_unknowns(rng, row):
    """A truly unknown value is an EMPTY cell.  'not_applicable' and 'No' are
    both real answers and are never overwritten here."""
    for col, val in list(row.items()):
        if col in NEVER_BLANK or val == NA or val == "":
            continue
        rate = F.UNKNOWN_RATE_MONEY if col in MONEY_COLS else F.UNKNOWN_RATE_OTHER
        if rng.random() < rate:
            row[col] = ""
    return row


# ==========================================================================
# Main
# ==========================================================================

COLUMNS = [
    "case_id", "event_id", "control_no", "date_received", "program",
    "client_type", "service_setting", "referral_type",
    "purpose_of_assistance", "diagnosis_cause_of_death", "mode_of_assistance",
    "occupation",
    "employed_members", "seasonal_members", "combined_family_income",
    "insurance_coverage", "savings",
    "monthly_expenses", "emergency_fund",
    "illness_duration", "crisis_last_3_months", "crisis_hospitalization",
    "crisis_death_of_member", "crisis_catastrophic_event", "crisis_disablement",
    "crisis_loss_of_livelihood", "crisis_others",
    "support_family", "support_relatives", "support_friends",
    "support_employer", "support_church",
    "ext_philhealth", "ext_health_card", "ext_guarantee_letter_other_agency",
    "ext_mss_discount", "ext_senior_citizen_discount", "ext_pwd_discount",
    "selfhelp_sought_income", "selfhelp_reached_agencies",
    "vuln_elderly_child_pwd_pregnant", "vuln_member_incapacitated",
    "vuln_unstable_employment",
    "target_sector", "sub_category", "disability_type",
    "income_salaries_wages", "income_entrepreneurial",
    "income_cash_assistance_domestic", "income_cash_assistance_abroad",
    "income_government_transfers", "income_pension", "income_other",
    "total_income_past_6_months",
    "assistance_type_granted", "amount_granted", "fund_source",
]


def random_weekday(rng, start, end):
    d = start + timedelta(days=rng.randrange((end - start).days + 1))
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return min(d, end)


def main():
    rng = random.Random(F.RANDOM_SEED)
    start = date.fromisoformat(F.WINDOW_START)
    end = date.fromisoformat(F.WINDOW_END)

    # Build the pool of assistance types to the stratified counts, then shuffle
    # so applicants with several events get a realistic mixture.
    pool = []
    for atype, n in F.TYPE_COUNTS.items():
        pool += [atype] * n
    rng.shuffle(pool)

    rows, case_no, i = [], 0, 0
    while i < len(pool):
        case_no += 1
        n_events = rng.choices(list(F.EVENTS_PER_APPLICANT),
                               weights=list(F.EVENTS_PER_APPLICANT.values()))[0]
        n_events = min(n_events, len(pool) - i)
        # Event dates are drawn as a sequence, not independently, so that a
        # returning applicant's later visits never fall before their earlier
        # ones and never land on the same day. Drawing each date on its own
        # produced both, and neither is a thing a real record set contains.
        gaps = [rng.randint(60, 150) for _ in range(n_events - 1)]
        span = (end - start).days
        offset = rng.randrange(max(1, span - sum(gaps)))
        dates, cur = [], start + timedelta(days=offset)
        for g in [0] + gaps:
            cur += timedelta(days=g)
            d = cur
            while d.weekday() >= 5:
                d += timedelta(days=1)
            dates.append(min(d, end))

        for e in range(1, n_events + 1):
            row = build(rng, pool[i], caseno=f"C{case_no:05d}", eventno=e)
            # A repeat visit happens later, and is re-interviewed, so the
            # record is close to but not identical with the first.
            row["date_received"] = dates[e - 1].isoformat()
            row["control_no"] = f"DC-{case_no:05d}-{e}"
            rows.append(inject_unknowns(rng, row))
            i += 1

    rows.sort(key=lambda r: (r["date_received"], r["control_no"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "v1_intake.csv"
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)

    manifest = {
        "generator_version": GENERATOR_VERSION,
        "generated_on": date.today().isoformat(),
        "seed": F.RANDOM_SEED,
        "n_events": len(rows),
        "n_applicants": case_no,
        "window": [F.WINDOW_START, F.WINDOW_END],
        "type_counts_generated": F.TYPE_COUNTS,
        "type_mix_real_dswd": F.TYPE_MIX_REAL,
        "amount_granted": "EMPTY BY DESIGN - comes from the judged sample",
        "note": ("Type mix deliberately flattened so every assistance type has "
                 "enough cases to retrieve five neighbours. DSWD's real mix is "
                 "recorded above for comparison. See Part 8 of the dataset design."),
    }
    (OUT_DIR / "v1_manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"wrote {out}  ({len(rows)} events, {case_no} applicants)")
    print(f"wrote {OUT_DIR / 'v1_manifest.json'}")


if __name__ == "__main__":
    main()
