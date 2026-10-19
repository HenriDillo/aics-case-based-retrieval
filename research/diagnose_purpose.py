"""Post-result diagnostic only; does not change or retune the retrieval method."""
import hashlib
import json
from pathlib import Path
from statistics import mean, median

from backend.study_loader import load_study_csv
from backend.study_retrieval import retrieve


def diagnose(root):
    generated = root/'research/generated'
    evaluation = generated/'evaluation-v1'
    original_hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in evaluation.iterdir() if p.is_file()}
    base = load_study_csv(generated/'v26/case_base_p50.csv').records
    judged = load_study_csv(generated/'v26/judged_p50.csv').records
    lookup = {(r.applicant_id, r.event_id): r for r in base}
    queries = {r.applicant_id: r for r in judged}
    results = {}
    for split in ('reviewed', 'leave_one_applicant_out'):
        rows = json.loads((evaluation/f'p50_{split}_events.json').read_text())
        medical = []
        for row in rows:
            if row['assistance_type'] != 'Medical':
                continue
            neighbors = [lookup[tuple(n)] for n in row['neighbors']]
            shares = [r.values['amount_granted']/r.values['documented_cost'] for r in neighbors]
            mismatch = sum(r.values['purpose_of_assistance'] != row['purpose'] for r in neighbors)
            medical.append(dict(**row, mismatched_neighbors=mismatch,
                                neighbor_details=[dict(applicant_id=r.applicant_id,
                                    event_id=r.event_id, purpose=r.values['purpose_of_assistance'],
                                    amount=r.values['amount_granted'], cost=r.values['documented_cost'],
                                    share=s) for r, s in zip(neighbors, shares)],
                                median_share=median(shares)))
        nontransport = [r for r in rows if r['assistance_type'] != 'Transportation']
        gap = sum(r['error']-r['baseline_error'] for r in nontransport)
        groups = {}
        for label, group in [('all_medical', medical),
                             ('any_mismatch', [r for r in medical if r['mismatched_neighbors']]),
                             ('all_same_purpose', [r for r in medical if not r['mismatched_neighbors']])]:
            groups[label] = dict(n=len(group),
                retrieval_mae=mean(r['error'] for r in group) if group else None,
                baseline_mae=mean(r['baseline_error'] for r in group) if group else None,
                total_excess_error=sum(r['error']-r['baseline_error'] for r in group))
        results[split] = dict(groups=groups, nontransport_total_excess_error=gap,
                              cases=medical)
    reviewed = results['reviewed']
    worst = sorted(reviewed['cases'], key=lambda r: r['error']-r['baseline_error'], reverse=True)[:3]
    for row in worst:
        query = queries[row['applicant_id']]
        ranked = retrieve(query, base, k=len(base), exclude_applicant_ids=row['excluded_applicants'])
        same = [(i+1, m) for i, m in enumerate(ranked.matches)
                if m.record.values['purpose_of_assistance'] == row['purpose']]
        row['same_purpose_available'] = len(same)
        row['first_same_purpose_rank'] = same[0][0]
        row['first_same_purpose_distance'] = same[0][1].distance
        row['first_same_purpose_id'] = same[0][1].record.applicant_id
        row['selected_distances'] = [m.distance for m in ranked.matches[:5]]
        assert [(m.record.applicant_id, m.record.event_id) for m in ranked.matches[:5]] == [tuple(n) for n in row['neighbors']]
        assert all('purpose_of_assistance' in m.field_scores for m in ranked.matches[:5])
        row['purpose_weight_fraction_selected'] = [1/len(m.field_scores) for m in ranked.matches[:5]]
    assert original_hashes == {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in evaluation.iterdir() if p.is_file()}
    results['evaluation_files_unchanged'] = True
    return results


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    result = diagnose(root)
    destination = root/'research/generated/purpose-diagnostic-v1'
    destination.mkdir(exist_ok=False)
    (destination/'diagnostic.json').write_text(json.dumps(result, indent=2)+'\n')
    for split in ('reviewed', 'leave_one_applicant_out'):
        print(split, json.dumps(result[split]['groups']))
    for r in sorted(result['reviewed']['cases'], key=lambda r: r['error']-r['baseline_error'], reverse=True)[:3]:
        print(r['applicant_id'], r['same_purpose_available'], r['first_same_purpose_rank'], r['median_share'], r['purpose_weight_fraction_selected'])
