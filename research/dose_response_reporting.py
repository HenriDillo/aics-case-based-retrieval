"""Read Appendix 4A across conditions; reporting only, no experiments."""

HEADING='### Retrieval error across household-signal levels'

def add_dose_response(md):
    if HEADING in md:
        return md
    appendix=md.split('## Appendix 4A',1)[1]
    lookup={}
    for line in appendix.splitlines():
        cells=[c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells)==9 and cells[0] in ('p00','p25','p50','p75'):
            lookup[(cells[1],cells[2],cells[0])]=cells[8]
    types=[('Cash Relief Assistance','Cash relief'),('Educational','Educational'),('Food Assistance','Food'),('Funeral','Funeral'),('Medical','Medical')]
    conditions=('p00','p25','p50','p75')
    tables=[]
    for method,label in [('equal','Equal weights'),('learned','Learned weights')]:
        rows=[]
        for key,name in types:
            values=[float(lookup[(method,key,tag)].replace(',','')) for tag in conditions]
            trend='Yes' if all(a<b for a,b in zip(values,values[1:])) else 'No'
            rows.append('| '+name+' | '+' | '.join(f'{v:+.2f}' for v in values)+' | '+trend+' |')
        tables.append('**'+label+' — reduction against the matching purpose baseline (%)**\n\n| Assistance type | p00 | p25 | p50 | p75 | Strictly increasing |\n| --- | --- | --- | --- | --- | --- |\n'+'\n'.join(rows))
    section=HEADING+'''

Appendix 4A also supports an ordered comparison across the four planted household-signal conditions. The following figures are case-base results: errors are first averaged within applicant and assistance type across the 1,000 events, then across applicants in that type. They are distinct from the fixed 36 reviewed-case test. Each percentage uses its own condition-specific purpose baseline, which changes because the generated amounts change with the condition. Transportation is excluded here because its error is zero by construction.

'''+tables[0]+'''

For each of the four non-medical types, the equal-weight reduction increases at every step as the household share of variation rises from 0% to 75%. All four trail their purpose baseline at p00, where there is no household signal, and all four exceed it at p75. This dose-response pattern is consistent with retrieval responding to planted household information where the medical purpose-share mismatch is absent. Medical remains far below its baseline throughout; its equal-weight sequence is non-monotonic, rather than literally constant or evidence of statistical equivalence.

'''+tables[1]+'''

Under learned weights, medical improves monotonically from −35.11% at p00 through −27.08% and −20.36% to +2.21% at p75. This is consistent with emphasizing purpose reducing an obstacle to observing household-signal response. It does not isolate the effect of purpose from all other learned-weight changes. Food and funeral also increase monotonically. Cash relief and education dip at p25, so the learned-weight results must not be described as monotonic for every type.

These findings are compatible with Section 4.8. The weight search minimizes an applicant-averaged scaled-error objective across the whole case base and assigns its largest mean weight to purpose. Medical dominates the unscaled peso error under equal weights, but that alone does not establish its influence on the scaled optimization objective. The observed weights and error changes support purpose as a major lever used by the search. They do not demonstrate additional household-pattern recovery by the search. Retrieval can nevertheless respond to household signal through fields already included under equal weights, as the non-medical ordered comparisons show. What the search emphasizes and what retrieval responds to are different findings.

There are only four points per type. This is a descriptive pattern, not a formal trend test; no statistical significance, fitted trend line or causal proof is claimed. These comparisons do not isolate the mechanism from the generator's other limitations. The main condition remains p = .50, fixed before evaluation. The better p75 results do not justify choosing a different main condition. The fixed reviewed-case test still failed at −42.74%, as Section 4.1 reports; this case-base analysis explains aspects of that result and does not overturn or replace it. It supports a household-signal response in the four non-medical types and a purpose-confusion explanation for medical that remains to be isolated in an approved comparison.

'''
    marker='## 4.7 Five-fold'
    assert md.count(marker)==1
    return md.replace(marker,section+marker)
