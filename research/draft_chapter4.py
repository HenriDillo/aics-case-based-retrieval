"""Draft Chapter 4 from completed, checked result artifacts; no placeholder results."""
import argparse
from collections import Counter,defaultdict
import csv
import hashlib
import json
from pathlib import Path
from statistics import mean,median
import subprocess
import sys
from time import perf_counter

from backend.study_loader import load_study_csv
from backend.study_retrieval import retrieve
from research.amounts import income_band
from research.report_completion import environment
from research.run_experiments import ROOT,STUDY,GENERATED,TAGS
from research.build_dataset import write_json
from research.policy import SHARES,DIRECT
from research.vendor.dswd_figures import TYPE_MIX_REAL


def read(path):return json.loads(path.read_text(encoding='utf-8'))
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+
                     ['| '+' | '.join(str(v) for v in row)+' |' for row in rows])
def num(x,d=2):return 'N/A' if x is None else f'{x:,.{d}f}'
def pvalue(x):return f'{x:.3g}'


def applicant_summary(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['applicant_id']].append(r)
    error=mean(mean(r['error'] for r in v) for v in groups.values())
    baseline=mean(mean(r['baseline_error'] for r in v) for v in groups.values())
    scaled=[mean(r['scaled_error'] for r in v if r['scaled_error'] is not None)
            for v in groups.values() if any(r['scaled_error'] is not None for r in v)]
    return dict(applicants=len(groups),events=len(rows),mae=error,baseline=baseline,
                scaled=mean(scaled) if scaled else None,reduction=100*(baseline-error)/baseline if baseline else None)


def measure():
    env=environment()
    privacy_path = STUDY/'repository-privacy.json'
    if privacy_path.exists():
        privacy = read(privacy_path)
        if privacy.get('verified') and privacy.get('private'):
            env['repository_privacy'] = 'Verified private through authenticated hosting-provider API; no push performed'
    base=load_study_csv(ROOT/'backend/data/study_complete.csv').records
    judged=load_study_csv(GENERATED/'reconciled-primary/judged_p50.csv').records
    times=[]
    for typ in sorted({r.values['assistance_type_granted'] for r in judged}):
        query=next(r for r in judged if r.values['assistance_type_granted']==typ)
        for _ in range(3):retrieve(query,base)
        runs=[]
        for _ in range(11):
            start=perf_counter();retrieve(query,base);runs.append((perf_counter()-start)*1000)
        times.append(dict(type=typ,query=query.applicant_id,runs_ms=runs,median_ms=median(runs)))
    command='from backend.main import app; from backend.data_store import load_cases; from research.report_completion import working_set_bytes; load_cases(); print(working_set_bytes())'
    memory=[int(subprocess.check_output([sys.executable,'-c',command],cwd=ROOT,text=True).strip()) for _ in range(5)]
    write_json(STUDY/'environment-final.json',env)
    perf=dict(retrieval=times,backend_working_set_bytes=memory,median_working_set_bytes=median(memory),
        memory_scope='Fresh process after app import and loading default CSV; not peak or HTTP-load measurement',
        full_evaluation=read(STUDY/'full-runtime.json'))
    write_json(STUDY/'performance-final.json',perf)
    return env,perf


def draft(output):
    output.mkdir(parents=True,exist_ok=True)
    primary=read(STUDY/'weights/primary/results.json')
    settings=read(STUDY/'selected-settings.json');evidence=read(STUDY/'weight-evidence.json')
    reviewed=read(STUDY/'reviewed-results.json');definitions=read(STUDY/'reporting-definitions.json')
    main=reviewed['p50']['selected']['summary']['non_transport']
    manifest=read(GENERATED/'reconciled-primary/manifest.json')
    costs=read(GENERATED/'reconciled-primary/cost_checks.json')
    validation=read(GENERATED/'reconciled-primary/validation.json')
    base=load_study_csv(GENERATED/'reconciled-primary/case_base_p50.csv').records
    judged=load_study_csv(GENERATED/'reconciled-primary/judged_p50.csv').records
    # Every promised replicate, fold, condition and fixed budget must exist.
    for directory in ['primary']+[str(s) for s in range(51001,51031)]:
        r=read(STUDY/f'weights/{directory}/results.json')
        for tag in TAGS:
            assert len(r[tag]['learned']['events'])==1000
            assert len(r[tag]['folds'])==5
            assert len(evidence[tag]['gaps'])==30
            for fold in range(5):
                trace=read(STUDY/f'weights/{directory}/{tag}-fold-{fold}-trace.json')
                assert len(trace)==200
                assert all(a['incumbent']>=b['incumbent'] for a,b in zip(trace,trace[1:]))
                w=r[tag]['folds'][fold]['weights']
                assert min(w.values())>=0 and abs(sum(w.values())-39)<1e-9
    env,perf=measure()
    type_counts=Counter(r.values['assistance_type_granted'] for r in base)
    bands=Counter(income_band(r.values['total_income_past_6_months'])[0] for r in base)
    judged_bands=Counter(income_band(r.values['total_income_past_6_months'])[0] for r in judged)
    pieces=[f'''# Chapter 4
# Results and discussion

Draft for research-team review · 19 October 2026

## 4.1 Scope and principal finding

This chapter reports the completed synthetic-data experiments for the AICS case
reference prototype. The fixed main test **failed**. On the 36 non-transport
reviewed cases at p = .50 and five retrieved neighbors, equal-weight retrieval
had mean absolute error (MAE) of **₱{num(main['mae'])}**, compared with
**₱{num(main['baseline_mae'])}** for the same-purpose baseline. The resulting
reduction was **{num(main['reduction_percent'])}%**, rather than the required
reduction of at least 20%. The maximum MAE compatible with that criterion was
₱{num(.8*main['baseline_mae'])}. These results do not establish that the proposed
retrieval method works on this dataset under the study's stated success criterion.

The separate weight-learning experiment improved over equal weights under its
specified tests. That finding addresses a different comparison and does not
replace the failed main test. In particular, improvement also appeared in the
no-household-signal control. It cannot, by itself, establish recovery of household
structure or usefulness in real benefit decisions.

All records and grants in these experiments are synthetic. The forty reviewed
intake sheets are fixed test cases; their evaluated grants were generated by the
written rule, not supplied here as new social-worker judgments. This draft stops
at Chapter 4. It does not alter the approved Chapters 1–3 or claim team approval
of implementation details added where the paper was incomplete.

## 4.2 Implementation and provenance

The comparison uses the 39 fields specified in the manuscript, same-type reference
pools, applicant-level exclusion, reference-only numeric ranges and constants,
Jaccard scores for multi-select fields, and the specified treatment of unknowns,
not-applicable values and shared absences. All events of a held-out applicant are
excluded. The reviewed cases are never inserted into the case base; the evaluator
also applies their documented partner exclusions. The prototype displays five
past cases using equal weights and does not output a prediction or applicant score.

The reconciled implementation restores the supplied amount-code scoring semantics
and sorted-payload noise algorithm. Compatibility tests reproduce all 160 supplied
forty-case amounts with the supplied calibration. The study run instead uses the
required calibration from the 1,000-event case base and reuses it for the forty
test cases. Per-event scoring avoids the source script's repeated-applicant
overwrite. Cost and rounding constraints are enforced explicitly.

Researcher-selected cost ranges were retained from the earlier preparation, not
changed in response to its failed result. They use uniform intervals from 0.5 to
1.5 times available cost benchmarks; device and transport ranges remain declared
assumptions. Educational costs use a tuition proxy. Laboratory uses the published
ratio .9052; dialysis and chemotherapy each use .3556 from their combined source
row. These completions and proxies must remain disclosed in the methodology.

The existing base had 244 wage-label contradictions. The reconciled copy removes
the contradictory labels without changing incomes or worker counts. New generated
sets enforce that consistency before inserting unknown values. Ten original-base
events remain unverifiable because worker counts are missing; they are flagged,
not presented as validated. Unknown values are still excluded from Gower. The
source amount rule's distinct missing-score semantics are preserved and are a
limitation of the synthetic mechanism.

The earlier provisional run is retained separately: its main-test retrieval MAE
was ₱1,930.18 against ₱923.49, a −109.01% reduction. The reconciled run is a distinct
version justified by source compatibility, not a replacement advertised as success.

## 4.3 Data composition and published benchmarks

The primary base contains 1,000 events from 844 applicant IDs. The published-mix
column below is the comparator recorded in the supplied figures module (Table 12);
the synthetic mix was deliberately flattened. It is not a sampled Davao City
population distribution. Rounded published percentages sum to approximately 100%.
''']
    pieces.append(table(['Assistance type','Generated events','Generated %','Bundle published comparator %'],
        [[t,n,num(n/10,1),num(TYPE_MIX_REAL[t]*100,1)] for t,n in sorted(type_counts.items())]))
    pieces.append('\nSix-month income bands are retained as generated, without balancing them to improve detectability.\n')
    pieces.append(table(['Income band','Base events','Reviewed cases'],[[label,bands.get(key,0),judged_bands.get(key,0)] for key,label in
        [('below_food','Below food threshold'),('food_to_poverty','Food to poverty threshold'),('at_or_above_poverty','At or above poverty threshold'),('missing','Unknown')]]))
    pieces.append('\nThe cost checks below compare generated means with the historical published anchors, not current benefit policy. No post-result cost adjustment was made.\n')
    pieces.append(table(['Group','Published mean cost ₱','Generated mean cost ₱','Difference %','Within 20%'],[
        [r['group'],num(r['published_mean_cost']),num(r['final_mean']),num(100*r['relative_difference']),str(r['within_20_percent'])] for r in costs['checks']]))
    pieces.append('\nThe following p = .50 summaries compare aggregate generated shares (total grants divided by total costs) with the declared share bases. Food and cash relief instead compare mean amounts in pesos. Shares are not mean individual ratios. The borrowed device share and exact transport share are assumptions, not Region XI estimates.\n')
    pieces.append(table(['Purpose','n','Generated share or mean ₱','Rule base share or mean ₱'],[
        [r['purpose'],r['n'],num(r['aggregate_share'] if r['aggregate_share'] is not None else r['mean_amount'],4 if r['aggregate_share'] is not None else 2),
         num(r['rule_base'],4 if r['aggregate_share'] is not None else 2)] for r in validation['p50']['case_base_summary']]))
    pieces.append('''
The published amounts and costs were reported for a historical population and may
include payments by other sources. Here documented cost is the outstanding need.
Agreement of selected summary means therefore supports a limited plausibility
check, not population validity or proof of realistic joint relationships.

## 4.4 Missingness and effective comparisons

Unknown entries are not imputed into the distance. Explicit No and not-applicable
values follow the manuscript's separate rules. The primary base has the following
unknown counts among matching fields; rates use 1,000 events as the denominator.
''')
    pieces.append(table(['Matching field','Unknown events','Unknown %'],[[f,n,num(n/10,1)] for f,n in manifest['missingness']['unknown_matching_values'].items()]))
    available=[n for r in primary['p50']['equal']['events'] for n in r['neighbor_compared_field_counts']]
    positive=[n for r in primary['p50']['learned']['events'] for n in r['neighbor_positive_weight_compared_field_counts']]
    undefined=sum(r['undefined_pairs'] for r in primary['p50']['equal']['events'])
    pieces.append(f'''
At p = .50, the equal-weight retrieved pairs compared between {min(available)} and
{max(available)} fields (median {median(available):g}). Learned-weight retrieved
pairs had between {min(positive)} and {max(positive)} comparable fields with positive
weight (median {median(positive):g}). The equal-weight primary run counted
{undefined} undefined eligible pairs. The machine-readable results retain each
neighbor's count; available-field counts and positive-weight counts are distinguished.

The source schema lacks the separate Section V not-applicable tick, so all-No
resource rows cannot independently establish whether that tick was recorded.
The supplied explicit No values are retained with a provenance warning. This
cannot be repaired by inferring an unrecorded answer.

## 4.5 Separate-set selection of money and duration treatments

A separate primary set used master seed 41000; thirty new sets used 41001–41030.
All selection comparisons used equal weights and p = .50. Money transformations
were compared first, then duration under the selected money treatment. The
criterion used applicant-averaged scaled absolute errors, with transportation
excluded because it has no scaled width and its grant is exactly its ticket cost.
The noise floor was the sample SD of the thirty paired mean gaps. Each challenger
also had to pass the primary-set two-sided Wilcoxon test, with α = .025 for money
and α = .05 for duration. Applicants, not a pooled stack of replicated IDs, were
the paired units. All-zero differences would give p = 1.
''')
    tests=[('Log versus plain',settings['money_evidence']['log']),('Fuzzy versus plain',settings['money_evidence']['fuzzy']),('Rank versus categorical duration',settings['duration_evidence'])]
    pieces.append(table(['Comparison','Mean scaled improvement','Noise-floor SD','Wilcoxon p','Passes both'],[
        [name,num(t['mean_scaled_improvement'],6),num(t['noise_floor_sd'],6),pvalue(t['wilcoxon']['p']),str(t['passes'])] for name,t in tests]))
    pieces.append(f'\nThe retained settings are **{settings["money"]} money scaling** and **{settings["duration"]} duration**. Failure to pass is not proof of equivalent methods; it means the preregistered implementation criterion did not justify replacing the baseline.\n')
    fuzzy=read(STUDY/'selection/money-41000.json')['fuzzy']['events']
    qrows=[]
    for typ in sorted({r['assistance_type'] for r in fuzzy}):
        qs=[r['quartiles'].get('total_income_past_6_months') for r in fuzzy if r['assistance_type']==typ]
        qs=[q for q in qs if q]
        q=[median(a[i] for a in qs) for i in range(3)]
        qrows.append([typ,*[num(v) for v in q],num(100*(q[1]-55161.5)/55161.5),num(100*(q[2]-78803.5)/78803.5)])
    pieces.append('\nFor transparency, these are medians of the query-specific reference-pool income quartiles on the separate primary set. Each actual query used its own eligible pool. The signed percentage differences compare Q2 with the food edge and Q3 with the poverty edge.\n')
    pieces.append(table(['Type','Q1 ₱','Q2 ₱','Q3 ₱','Q2–food edge %','Q3–poverty edge %'],qrows))
    pieces.append('''
Fuzzy membership used linear low/middle/high memberships anchored at these
quartiles, with similarity equal to one minus half their L1 distance. Coincident
quartiles triggered a recorded plain-range fallback. These are explicitly
documented implementation choices, not formulas supplied verbatim in the paper.

## 4.6 Fixed reviewed-case test

For cost-bearing cases, retrieval combines the five recorded grant-to-cost ratios
by their median and applies it to the query's own cost. Direct food/cash amounts
are combined by their median. The baseline uses the same-purpose eligible pool
with the same exclusions. The following p = .50 results are descriptive by type;
the success criterion is the pooled 36-case peso comparison, not a type-specific
or scaled-error substitute.
''')
    pieces.append(table(['Type','Cases','Retrieval MAE ₱','Purpose-baseline MAE ₱','Reduction %','Scaled MAE'],[
        [typ,r['n'],num(r['mae']),num(r['baseline_mae']),num(r['reduction_percent']),num(r['scaled_mae'],6)]
        for typ,r in reviewed['p50']['selected']['summary']['by_type'].items()]))
    pieces.append('\nThe four transportation cases have zero error by construction. They are reported separately and do not count toward the main test. Plain and selected settings coincide in this run. Results across all conditions are:\n')
    pieces.append(table(['Household condition','36-case MAE ₱','Purpose-baseline MAE ₱','Reduction %'],[
        [tag,num(reviewed[tag]['selected']['summary']['non_transport']['mae']),num(reviewed[tag]['selected']['summary']['non_transport']['baseline_mae']),num(reviewed[tag]['selected']['summary']['non_transport']['reduction_percent'])] for tag in TAGS]))
    pieces.append('''
## 4.7 Five-fold learned weights and thirty-set evidence

Applicant IDs were assigned to five fixed folds. Each fold's shared 39 weights
were fitted only on the other four folds, using applicant leave-one-out retrieval
inside that training pool and 200 objective evaluations. All weights were
nonnegative and summed to 39. Held-out applicants retrieved from all other
case-base applicants, including other applicants assigned to their test fold;
the equal-weight comparator used that identical reference pool. Settings selected
on the separate set were held fixed. No reviewed case selected weights or budget.

Thirty weight replicates used master seeds 51001–51030. The same two-part evidence
criterion was applied with α = .05 per specified condition. The paired test used
the primary case-base applicants. The following peso MAEs first average the
non-transport event errors within each applicant, then average applicants; scaled
errors similarly average each event's error divided by its prescribed band width.
This differs from an event-weighted pooled MAE when applicants have repeat visits.
''')
    case_rows=[]
    for tag in TAGS:
        eq=applicant_summary([r for r in primary[tag]['equal']['events'] if r['scaled_error'] is not None])
        learned=applicant_summary([r for r in primary[tag]['learned']['events'] if r['scaled_error'] is not None])
        t=evidence[tag]
        case_rows.append([tag,num(eq['mae']),num(learned['mae']),num(eq['mae']-learned['mae']),num(eq['baseline']),num(t['mean_scaled_improvement'],6),num(t['noise_floor_sd'],6),pvalue(t['wilcoxon']['p']),str(t['passes'])])
    pieces.append(table(['Condition','Equal MAE ₱','Learned MAE ₱','Paired mean peso gain','Purpose baseline ₱','30-set scaled gain','SD','Wilcoxon p','Passes'],case_rows))
    pieces.append('''
All four implemented signed-rank calculations were independently cross-checked
against SciPy 1.17.1 using the same two-sided asymptotic, tie-corrected convention.
SciPy was used for verification, not as a hidden optimizer dependency. The
condition-wise tests follow the stated protocol; no additional family-wide claim
across all conditions or descriptive k values is asserted.

The p = 0 improvement over equal weights is especially important for interpretation.
Purpose still determines base shares in that control, while household adjustment
is disabled. Learned weights can improve by emphasizing purpose and suppressing
irrelevant variation. Therefore this comparison alone cannot show that the search
recovered the household relationship. The purpose baseline remains the relevant
no-household comparison; the primary pooled learned peso error remains above it.
Any small subgroup fluctuation below that baseline is not, on its own, proof of
leakage or of a real household effect.

## 4.8 Weight recovery and reference gap

The written household score uses 28 matching fields. Purpose also determines the
base share, so the amount-rule reference includes 29 matching fields. It assigns
equal positive weight to those 29 and zero to the other matching fields. Cost is
not a matching field and cannot enter this reference. This is a fixed nominal
rule-field diagnostic across conditions; p = 0 disables the household term.
Both purpose-inclusive and household-only weight masses are shown to avoid
mistaking purpose recovery for household recovery. The reference is not a proven
optimum. A negative learned-minus-reference gap is possible and is not an error.
''')
    pieces.append(table(['Condition','Mean rule-field weight %','Mean household-only weight %','Mean zero-rule fields in top 10','Learned scaled error','Reference scaled error','Learned minus reference'],[
        [tag,num(100*mean(f['rule_weight_fraction'] for f in primary[tag]['folds'])),num(100*mean(f['household_rule_weight_fraction'] for f in primary[tag]['folds'])),num(mean(len(f['zero_rule_fields_in_top_ten']) for f in primary[tag]['folds'])),num(primary[tag]['learned']['objective'],6),num(primary[tag]['reference']['objective'],6),num(primary[tag]['reference_gap'],6)] for tag in TAGS]))
    pieces.append(f'\nEqual weights allocate {100*29/39:.2f}% of total weight to the 29 nominal rule fields and {100*28/39:.2f}% to the 28 household-score fields. At p = .50, learned household-only mass is {100*mean(f["household_rule_weight_fraction"] for f in primary["p50"]["folds"]):.2f}%. Thus the increase in total rule-field mass largely reflects purpose rather than an increase in household-field mass. This descriptive result does not establish strong household-pattern recovery.\n')
    weights={f:mean(fold['weights'][f] for fold in primary['p50']['folds']) for f in primary['p50']['folds'][0]['weights']}
    pieces.append('\nLargest mean weights at p = .50 (all 39 weights and every candidate trace are retained in the evidence archive):\n')
    pieces.append(table(['Field','Mean weight','In nominal amount rule'],[[f,num(w,4),str(f in definitions['all_amount_rule_matching_fields'])] for f,w in sorted(weights.items(),key=lambda x:-x[1])[:10]]))
    convergence=[]
    for fold in range(5):
        tr=read(STUDY/f'weights/primary/p50-fold-{fold}-trace.json')
        convergence.append([fold+1,num(tr[0]['incumbent'],6),num(tr[-1]['incumbent'],6),max(x['evaluation'] for x in tr if x['accepted']),sum(x['accepted'] for x in tr)-1])
    pieces.append('\nEach search stopped at its fixed budget, not a claim of convergence to an optimum. The trace reports the incumbent after each candidate evaluation.\n')
    pieces.append(table(['Fold','Initial scaled objective','Final scaled objective','Last accepted evaluation','Accepted moves'],convergence))
    pieces.append('''
## 4.9 Sensitivity to the number of retrieved cases

The following applicant-averaged scaled errors vary k while keeping the selected
settings and learned weights fixed. They are descriptive, with no retuning and
no additional superiority claim. The main test and fitting objective remain k=5.
''')
    sensitivity=read(STUDY/'k-sensitivity.json')
    pieces.append(table(['Condition','k','Equal scaled MAE','Learned scaled MAE'],[[tag,k,num(sensitivity[tag][str(k)]['equal']['objective'],6),num(sensitivity[tag][str(k)]['learned']['objective'],6)] for tag in TAGS for k in (3,5,7,10)]))
    pieces.append('''
## 4.10 Computational performance and reproducibility

Retrieval timing used three warmups and eleven timed calls for one fixed reviewed
query per assistance type, starting from the complete 1,000-event reference set.
These are function timings, not end-to-end network latency or a population-wide
latency estimate. Memory is the process working set after importing the backend
and loading the default CSV, measured in five fresh processes, not peak memory.
''')
    pieces.append(table(['Type','Query','Median retrieval ms'],[[r['type'],r['query'],num(r['median_ms'],3)] for r in perf['retrieval']]))
    pieces.append(f'''
Median backend working set was {num(perf['median_working_set_bytes']/2**20)} MiB.
The full five-fold, four-condition weight evaluation had median runtime
{num(perf['full_evaluation']['median_seconds'])} seconds across three deterministic
repetitions ({', '.join(num(v) for v in perf['full_evaluation']['runs_seconds'])}
seconds). The repeated learned outcomes and weights were identical. This time
includes distance construction, search, held-out evaluation and trace writes;
it excludes the thirty replicate runs, input generation, final document drafting,
and the later reporting-only reference/count supplement.

The recorded machine used {env['hardware']['processor']},
{num(env['hardware']['ram_bytes']/2**30)} GiB reported physical memory,
{env['hardware']['os']} version {env['hardware']['os_version']}, and Python
{env['python']}. The tested frontend used React {env['frontend_versions']['react']}
and Vite {env['frontend_versions']['vite']}. Exact installed Python versions and
the frontend lock file accompany the run. The configured repository is
`{env['repository']}`; its private status was authenticated and verified on
19 October 2026. No external push or message was performed by this work.

## 4.11 Prototype and review status

The prototype loads the reconciled p = .50 synthetic reference CSV once, retrieves
five same-type cases using equal weights, and displays their circumstances,
documented costs and generated grants. Six-type browser checks covered retrieval,
numeric grant display, comparison navigation and mobile overflow. The production
frontend build passed. Software verification establishes implementation behavior;
it does not change the failed research success criterion.

The printable CSV-driven packet fixes funds at ₱250,000 and includes populated
diagnoses for every assistance type. All forty supplied reviewed cases and all
their nonempty displayed values were checked. The packet has two printable pages
per case; the original reviewed DOCX remains unchanged and available separately.
No private pair key is included in the reviewer packet.

No new DSWD response to this completed run or packet has been supplied or verified.
The earlier consultations described in Chapters 1–3 are not represented as approval
of these new results. The record therefore cannot claim that the new packet was
submitted, accepted, rejected, or ignored. The four review topics remain field
ranges, assistance-type mix, amount spread and implausible combinations. Actual
feedback can be added with its date and source when available.

## 4.12 Interpretation and limitations

The fixed reviewed-case test does not support the proposed retrieval method's
success on this generated data under its preregistered peso-error criterion.
Separately, learned weights improve over equal weights within the implemented
synthetic experiments. The control result and the large role of purpose limit
an interpretation based on household-pattern recovery. Statistical improvement
in scaled error is also distinct from passing the pooled peso test.

The data-generating mechanism includes assumed costs, a flattened type mix,
chosen missingness, historical income thresholds and a known amount rule. Its
source scoring treats some unknown inputs as absence or zero, while retrieval
does not impute them. These choices restrict external validity. The forty-case
test has small type-specific counts, so those rows should not be treated as
precise type-level estimates. The fixed greedy search budget is reproducible but
does not guarantee globally best weights. No result here estimates the accuracy,
fairness or operational usefulness of decisions on actual DSWD applicants.

The complete evidence retains all seeds, fold assignments, event predictions,
applicant errors, comparison counts, candidate traces and source hashes. Failed
results and unverified external feedback remain visible. The chapter is ready
for the research team's substantive review, not presented as an approved thesis
chapter or evidence of successful real-world deployment.

## Appendix 4A Per-type case-base errors

Each row first averages event errors within applicant and assistance type, then
averages those applicant errors. An applicant with events in more than one type
can appear in more than one row. Peso and scaled errors are both reported;
transportation has no defined scaled width. The purpose baseline uses the same
eligible pool and exclusions as retrieval.
''')
    appendix=[]
    for tag in TAGS:
        for method in ('equal','learned'):
            rows=primary[tag][method]['events']
            for typ in sorted(type_counts):
                s=applicant_summary([r for r in rows if r['assistance_type']==typ])
                appendix.append([tag,method,typ,s['applicants'],s['events'],num(s['mae']),num(s['baseline']),num(s['scaled'],6),num(s['reduction'])])
    pieces.append(table(['Condition','Method','Type','Applicants','Events','MAE ₱','Baseline ₱','Scaled MAE','Reduction %'],appendix))
    pieces.append('''
## Sources and evidence

- Manuscript Chapters 1–3 v25, supplied by the research team, especially Sections
  1.5 and 3.2.1–3.2.4 and Table 3.1.
- Context for Astra, 18 October 2026, and Amount Rule Specification v3, supplied
  in the AICS v25 handoff.
- DSWD PDPB (2022), Process Evaluation of AICS, historical cost/share benchmarks
  transcribed in the supplied code and checked source tables. Device and transport
  values are explicitly labelled assumptions, not additional published estimates.
- Reconciliation contract, method choices, generated-data manifests and the
  completed-study-v1 machine-readable results accompanying this draft.
''')
    (output/'chapter-4-draft.md').write_text('\n\n'.join(pieces)+'\n',encoding='utf-8')
    with (output/'chapter-4-per-type-results.csv').open('w',newline='',encoding='utf-8-sig') as stream:
        writer=csv.writer(stream);writer.writerow(['condition','method','type','applicants','events','mae_pesos','baseline_mae_pesos','scaled_mae','reduction_percent']);writer.writerows(appendix)
    write_json(output/'chapter-4-key-results.json',dict(main=main,selected_settings=settings,
        weight_evidence=evidence,environment=env,performance=perf,verified_weight_replicates=30,
        source='completed-study-v1',chapter_status='Draft for team review; external feedback not invented'))
    print('Chapter 4 draft and evidence tables written',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path)
    draft(parser.parse_args().output)
