"""Reporting-only additions from the 19 October brief; never fit or retrieve."""
import json
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
STUDY=ROOT/'research/generated/completed-study-v1'

def revise(md):
    if '### Medical error diagnosis' in md:
        return md
    rows=json.loads((STUDY/'reviewed-results.json').read_text())['p50']['plain']['events']
    rows=[r for r in rows if r['assistance_type']!='Transportation']
    medical=[r for r in rows if r['assistance_type']=='Medical']
    other=[r for r in rows if r['assistance_type']!='Medical']
    assert len(rows)==36 and len(medical)==14 and len(other)==22
    mae=mean(r['error'] for r in other); base=mean(r['baseline_error'] for r in other)
    share=100*sum(r['error'] for r in medical)/sum(r['error'] for r in rows)
    evidence=json.loads((STUDY/'weight-evidence.json').read_text())
    gains=[v['mean_scaled_improvement'] for v in evidence.values()]
    spread=max(gains)-min(gains); sd=mean(v['noise_floor_sd'] for v in evidence.values())
    diagnosis=f'''
### Medical error diagnosis

Medical assistance accounts for 14 of 36 cases (38.9%) but **{share:.1f}% of total retrieval absolute error**. Its retrieval MAE is ₱3,251.16 against ₱1,222.94 for the purpose baseline, a −165.85% reduction. Medical is the source of the aggregate failure: the remaining 22 cases have retrieval MAE **₱{mae:,.2f}** against **₱{base:,.2f}**, a **{100*(base-mae)/base:.2f}% reduction**.

| Diagnostic subset | Cases | Retrieval MAE ₱ | Purpose-baseline MAE ₱ | Reduction % |
| --- | --- | --- | --- | --- |
| All non-transport cases — fixed main test | 36 | 1,903.82 | 1,333.76 | −42.74 |
| Medical | 14 | 3,251.16 | 1,222.94 | −165.85 |
| Non-medical non-transport — post-result diagnosis | 22 | {mae:,.2f} | {base:,.2f} | {100*(base-mae)/base:.2f} |

The 22-case subset exceeds 20% descriptively; it is not a replacement success test and does not change the failed 36-case conclusion. Cash relief and education individually remain below their baselines. The diagnosis concerns the aggregate concentration of error, not a claim that every non-medical type passes.

| Assistance type | Purpose and base share or direct amount |
| --- | --- |
| Medical | Hospital bill .2075; dialysis .3556; chemotherapy .3556; assistive device .3556; medicines .8046; laboratory .9052 |
| Funeral | Funeral expenses and cadaver transfer: .2903 each |
| Educational | Allowance, school fees and school supplies: .6105 each |
| Food assistance | Single purpose, food subsidy: direct base ₱3,857.14 |
| Cash relief | Single purpose, other needs: direct base ₱4,400.00 |
| Transportation | Both purposes: 1.0000; exact cost with no household adjustment |

Medical is the only type with different purpose-specific base shares, spanning .2075–.9052. The baseline is conditioned on purpose, while retrieval pools by type and gives purpose one of 39 equal nominal weights (1/39, about 2.6%; the effective share depends on the available-field denominator). A medicines query can therefore retrieve hospital-bill cases with a much lower base share. This is the mechanism supported by the error concentration and the known rule; the existing comparisons do not isolate its causal contribution from every other generator limitation.

The separate case-base experiment corroborates the role of purpose: its mean learned weight is 2.9797, compared with 1.5750 for the next field. At p = .50, medical's applicant-averaged reduction changes from −340.42% under equal weights to −20.36% under learned weights, the largest type-specific improvement. These are case-base results, not the 14 reviewed-case results above.

'''
    md=md.replace('## 4.7 Five-fold',diagnosis+'## 4.7 Five-fold')
    flat=f'''### Gain across household-signal levels

The thirty-set scaled gains are .023033, .022640, .023645 and .025527 at p = 0, .25, .50 and .75. Their spread is **{spread:.6f}**, smaller than the mean replicate SD of **{sd:.6f}**. The gain is descriptively flat rather than showing a clear increase with household signal. This range-to-SD comparison is a descriptive diagnostic, not a formal trend or equivalence test. Together with improvement at p = 0 and the weight-mass results below, it identifies purpose recovery without detectable household-pattern recovery at any tested signal level under this implementation and evidence. It does not prove that no household information could be recovered by any method.

'''
    md=md.replace('## 4.8 Weight recovery',flat+'## 4.8 Weight recovery')
    old='Equal weights allocate 74.36% of total weight to the 29 nominal rule fields and 71.79% to the 28 household-score fields. At p = .50, learned household-only mass is 71.61%. Thus the increase in total rule-field mass largely reflects purpose rather than an increase in household-field mass. This descriptive result does not establish strong household-pattern recovery.'
    new='''### Household weight mass did not increase

| p = .50 household-only diagnostic | Weight mass |
| --- | --- |
| Equal weights on the 28 household-score fields | **71.79%** |
| Learned weights on the same fields | **71.61%** |
| Change | **−0.18 percentage points** |

Equal weights allocate 74.36% to all 29 nominal rule fields including purpose. The larger learned rule-field mass is driven chiefly by purpose, not increased household mass. Household-only mass is also below the equal-weight share at the other three signal levels in the table. **The weight search recovers purpose and does not detectably recover the household pattern at any tested signal level.** This is a finding about the present search and diagnostics; aggregate weight mass alone cannot rule out every redistribution among household fields.'''
    assert old in md
    md=md.replace(old,new)
    md=md.replace('## 4.3 Data composition', 'The purpose-baseline MAE also rose from ₱923.49 in the provisional run to ₱1,333.76 in the reconciled run (44.43%); reconciliation changed the generated outcomes and calibration used by the comparator, so this is a change of run definition, not an improvement measured against a fixed baseline.\n\n## 4.3 Data composition')
    md=md.replace('Six-month income bands are retained', 'The flattened mix cuts against the study’s interpretation: medical represents 51.0% of generated events versus 70.6% in the supplied published comparator. Because medical has the largest error and baseline deficit, a more medical-heavy mix would worsen the pooled result if the observed within-type errors held fixed. This is a composition sensitivity interpretation, not an estimate from a representative population or a newly generated sample.\n\nSix-month income bands are retained')
    limitation='''### Unknown-value defects and the decision required before a rerun

The amount rule treats some unknowns as absence or zero, whereas Gower omits fields missing in either record. Unknown emergency fund, savings and insurance values can therefore attract absence points, and an unreadable employed-member count can be treated as zero workers. Unknown six-month income returns zero band points, the same numeric contribution as the highest income band: this affects 52 primary-base events. This mismatch can encode amount variation that retrieval cannot compare as an observed household attribute.

The proposed correction is to omit unknown contributions with an explicitly agreed available-field aggregation rule. Simply replacing the missing-income return with zero or skipping an addition to an unnormalised sum would leave that income contribution numerically unchanged; the aggregation and recalibration must be specified before approval. No corrected amounts or new comparisons are included here.

The 19 October brief requires Ma’am Grace’s dated written agreement before correcting the data and rerunning the original same-type test, or running the proposed same-purpose test. The proposed change would revise rules eight and eleven in Section 3.2.2 so numeric ranges use the revised eligible pool. The ≥20% criterion, Section 3.2.4.2 evidence standard, seeds, k, search budget, weights procedure, bands and noise remain fixed. Both corrected-data tests must be reported, alongside the retained prior runs, whether they pass or fail. Same-purpose pools also have thin medical subgroups: assistive device n = 14, chemotherapy n = 18 and dialysis n = 19 before exclusions. Approval has not been supplied and neither comparison has been run.

'''
    md=md.replace('## Appendix 4A',limitation+'## Appendix 4A')
    md=md.replace('https://github.com/HenriDillo/aics-triage-system.git','https://github.com/HenriDillo/aics-case-based-retrieval.git')
    md=md.replace('This draft stops\nat Chapter 4. It does not alter the approved Chapters 1–3 or claim team approval\nof implementation details added where the paper was incomplete.', 'This draft stops\nat Chapter 4. A separate manuscript copy fills only the six environment blanks in\nSection 3.2.4.3; the approved retrieval specification is unchanged. No team approval\nof additional implementation choices is claimed.')
    md=md.replace('Draft for research-team review · 19 October 2026','Draft for research-team review · revised from the 19 October 2026 brief; existing results only')
    diagnostic=dict(medical_cases=len(medical),medical_error_share_percent=share,nonmedical_cases=len(other),nonmedical_mae=mae,nonmedical_baseline=base,nonmedical_reduction=100*(base-mae)/base,gain_spread=spread,mean_replicate_sd=sd,new_experiment_run=False)
    (STUDY/'brief-diagnostics.json').write_text(json.dumps(diagnostic,indent=2))
    return md
