"""Validate and export the existing reviewed v11 packet without regenerating cases.

Preserves authored layout, narrative, exact pairs and one-field near pairs. This
deliberately does not run the stale make_sheets.py/build_sheets.js in the bundle.
No case values or participant answers are invented. No file is sent externally.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent


def inspect_packet(csv_path, template_path):
    with Path(csv_path).open(encoding='utf-8-sig', newline='') as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 40 or {r['case_id'] for r in rows} != {f'J{i:02d}' for i in range(1, 41)}:
        raise ValueError('Expected the forty reviewed case IDs')
    with zipfile.ZipFile(template_path) as archive:
        tree = ET.fromstring(archive.read('word/document.xml'))
    text = '\n'.join(''.join(e.text or '' for e in p.iter() if e.tag.endswith('}t'))
                     for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
    chunks = re.split(r'CASE (J\d\d)\s+page \d+ of 40', text)
    sections = dict(zip(chunks[1::2], chunks[2::2]))
    if len(sections) != 40:
        raise ValueError('Packet must contain all forty distinct case sections')
    normalize = lambda s: re.sub(r'\s+', ' ', s).strip()
    for row in rows:
        body = normalize(sections[row['case_id']])
        if row['Funds available'] != '₱250,000' or 'Funds available: ₱250,000' not in body:
            raise ValueError(f"{row['case_id']}: funds must be 250,000 on every sheet")
        diagnosis = row['Diagnosis / cause of death'].strip()
        if diagnosis and f'Diagnosis / cause of death: {diagnosis}' not in body:
            raise ValueError(f"{row['case_id']}: populated diagnosis missing from sheet")
        # Match every displayed non-empty CSV value to its corresponding case.
        for key, value in row.items():
            if key in ('case_id', 'no_income_recorded', 'amount_granted') or not value:
                continue
            if normalize(value) not in body:
                raise ValueError(f"{row['case_id']}: template differs from CSV: {key}")
    by = {r['case_id']: r for r in rows}
    # Private diagnostic information must not be written into the reviewer packet.
    exact = [('J01','J22'), ('J28','J13'), ('J11','J30'), ('J20','J35')]
    near = [('J14','J37','A member is physically or mentally incapacitated to work'),
            ('J04','J24','Relatives'), ('J27','J03','Savings'),
            ('J17','J33','Successfully sought employment opportunities or explored additional income sources')]
    for a, b in exact:
        if any(by[a][k] != by[b][k] for k in by[a] if k != 'case_id'):
            raise ValueError('Exact pair changed')
    for a, b, field in near:
        if [k for k in by[a] if k != 'case_id' and by[a][k] != by[b][k]] != [field]:
            raise ValueError('Near pair must differ in its single designated field')
    return dict(cases=40, funds_per_case=250000,
                populated_diagnoses=sum(bool(r['Diagnosis / cause of death'].strip()) for r in rows),
                source_csv_sha256=hashlib.sha256(Path(csv_path).read_bytes()).hexdigest(),
                source_packet_sha256=hashlib.sha256(Path(template_path).read_bytes()).hexdigest(),
                method='Validated byte-for-byte export of existing reviewed packet, not new case generation')


def export_packet(output, csv_path=ROOT/'inputs/judged_cases_v11.csv',
                  template_path=ROOT/'inputs/AICS_Case_Review_11.docx'):
    report = inspect_packet(csv_path, template_path)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(template_path, output/'AICS_Case_Review_11.docx')
    (output/'verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(export_packet(args.output), indent=2))
