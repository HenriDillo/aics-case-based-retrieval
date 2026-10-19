"""Application retrieval. Internal similarity values never leave this boundary."""
from .catalog import LABELS
from .comparison import display
from .data_store import get_cases
from .study_adapter import to_display, to_study
from .study_retrieval import retrieve
from .study_schema import NUMERIC_FIELDS


def retrieve_similar_cases(new_case: dict, k: int = 5) -> list[dict]:
    if k <= 0:
        return []
    query = to_study(new_case)
    records = get_cases()
    # A known control number also identifies the household when the applicant
    # reference was left blank. Do not rely on UI users entering both identifiers.
    excluded = {r.applicant_id for r in records
                if new_case.get('control_no') and r.values.get('control_no') == new_case['control_no']}
    result = retrieve(query, records, k, exclude_applicant_ids=excluded)
    output = []
    for match in result.matches:
        case = to_display(match.record)
        explanations = [f"Same assistance type: {case['assistance_type']}."]
        # Describe only actual active field matches; never shared asymmetric absences.
        for field, score in match.field_scores.items():
            if score != 1:
                continue
            value = query.values[field]
            if isinstance(value, frozenset):
                value = sorted(value)
            kind = 'money' if field in NUMERIC_FIELDS and field not in ('employed_members','seasonal_members') else 'text'
            explanations.append(f"{LABELS.get(field, field)}: both {display(value, kind)}.")
            if len(explanations) == 5:
                break
        if len(explanations) == 1:
            explanations.append('Selected by the combined comparison of the available intake fields; no exact active-field matches.')
        case.update(matched_fields=explanations,
                    explanation_context='These synthetic cases were retrieved from your intake using equal-weight field comparisons. Displayed grants are generated research outcomes, not actual DSWD decisions or recommendations. Food assistance and cash relief have no documented cost under the study rule.')
        output.append(case)
    return output
