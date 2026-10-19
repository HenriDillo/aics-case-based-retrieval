"""Create printable HTML sheets from approved CSVs; never invent new reviewed cases.

python -m research.make_sheets --input research/inputs/judged_cases_v11.csv --output packet.html
The reviewed DOCX remains available unchanged through research.sheets.
"""
import argparse
from html import escape
import json
from pathlib import Path
from backend.study_loader import load_study_csv
from backend.study_schema import PRINTED_TO_CANONICAL
from research.reconciled import printed


def render(input_path, output):
    records=load_study_csv(input_path).records
    parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><title>AICS synthetic case review sheets</title>
<style>body{font:12px Arial,sans-serif;color:#111;margin:24px auto;max-width:850px}h1{font-size:24px}h2{font-size:18px;margin:0 0 10px}h3{font-size:13px;margin:12px 0 4px}p{line-height:1.45}table{border-collapse:collapse;width:100%;table-layout:fixed}td{border-bottom:1px solid #ddd;padding:4px 6px;vertical-align:top;overflow-wrap:anywhere}td:first-child{width:67%}.answer{border:1px solid #999;height:50px;margin-top:12px;padding:8px}.sheet{break-before:page;margin-top:30px}.page{break-before:page}.cover{min-height:300px}@page{size:A4;margin:16mm}@media print{body{margin:0;max-width:none;font-size:10px}.sheet{margin-top:0}td{padding:3px 5px}h3{margin-top:8px}.toolbar{display:none}}</style>
<main><section class="cover"><h1>AICS synthetic case review sheets</h1>
<p>These are constructed research records, not real clients. The supplied forty-case inputs are preserved. Every case assumes ₱250,000 available funds. Generated grants are omitted from these sheets so they do not suggest a decision.</p>
<p>Please review field ranges, the mix of assistance types, the plausibility of the proposed amount spread in the accompanying summary, and any implausible combinations. No reviewer response or endorsement is assumed.</p>
<p class="toolbar">Use the browser Print command to save or print this packet. Each case has two pages, with the intake sections in order.</p></section>''']
    labels=list(PRINTED_TO_CANONICAL)
    # Section boundaries follow the printed GIS, with Section VIII on page two.
    groups=[('Request',labels[1:9]),('I Income and financial resources',labels[9:15]),
            ('II Budget and expenses',labels[15:17]),('III Severity of the crisis',labels[17:25]),
            ('IV Availability of support systems',labels[25:30]),
            ('V External resources tapped by the family',labels[30:36]),
            ('VI Self help and client efforts',labels[36:38]),
            ('VII Vulnerability and risk factors',labels[38:41]),
            ('VIII Target sector and income',labels[41:-1])]
    for record in records:
        row=printed(record);row['Funds available']='₱250,000'
        title=escape(record.applicant_id+(f' event {record.event_id}' if record.event_id else ''))
        parts.append(f'<section class="sheet" data-case="{title}"><h2>Case {title}</h2>')
        for index,(heading,keys) in enumerate(groups):
            if index==5: parts.append(f'</section><section class="page"><h2>Case {title} continued</h2>')
            parts.append(f'<h3>{heading}</h3><table>')
            for key in keys:
                if key=='Diagnosis / cause of death' and not row.get(key,'').strip(): continue
                value=row.get(key,'') or '(not recorded)'
                label='No income recorded' if key=='no_income_recorded' else key
                parts.append(f'<tr><td>{escape(label)}</td><td>{escape(str(value))}</td></tr>')
            parts.append('</table>')
        parts.append('<div class="answer">Reviewer comments on missing information or implausible combinations</div></section>')
    parts.append('</main></html>')
    output=Path(output)
    if output.exists(): raise ValueError('Choose a new output path')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text('\n'.join(parts),encoding='utf-8')
    return dict(cases=len(records),funds_per_case=250000,format='printable HTML; reviewed DOCX not replaced')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();print(json.dumps(render(args.input,args.output)))
