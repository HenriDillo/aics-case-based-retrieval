"""THE ONLY FUNCTION TO REPLACE FOR REAL RETRIEVAL: retrieve_similar_cases.

Read get_cases() for the already-loaded, read-only pandas DataFrame. Return
full case dictionaries with matched_fields (plain language strings) and
explanation_context (a plain language description of the explanation source).
Keep the signature and dictionary contract; API/UI code needs no changes.
Never return a distance, score, rank, similarity percentage, or suggested amount.
"""

from copy import deepcopy
from .data_store import get_cases


def retrieve_similar_cases(new_case: dict, k: int = 8) -> list[dict]:
    """REPLACE ONLY THIS FUNCTION with the later Gower retrieval implementation.

    This stub deliberately ignores new_case. Its order and handwritten
    explanations are fixtures, not a computed ordering or match assessment.
    Explanations refer ONLY to the saved medical sample. The independent
    comparison renderer compares the actual submitted intake on the server.
    """
    del new_case
    if k <= 0:
        return []
    fixtures = [
        ("MOCK-2025-001", ["Same assistance type: medical", "Both in the SC client sector", "Both reported hospitalization and loss of livelihood"]),
        ("MOCK-2025-002", ["Same assistance type: medical", "Both in the SC client sector", "Combined family income within ₱800"]),
        ("MOCK-2025-003", ["Same assistance type: medical", "Both reported hospitalization", "Both have no emergency fund"]),
        ("MOCK-2025-004", ["Same assistance type: medical", "Both report a chronic / lifelong illness", "Both tapped PhilHealth"]),
        ("MOCK-2025-005", ["Same assistance type: medical", "Both have no savings", "Both have family support"]),
        ("MOCK-2025-011", ["Both in the SC client sector", "Both reported loss of livelihood", "Both have no emergency fund"]),
        ("MOCK-2025-021", ["Both have no savings", "Both have no emergency fund", "Both reported loss of livelihood"]),
        ("MOCK-2025-026", ["Both in the SC client sector", "Both have family support", "Both reported loss of livelihood"]),
    ]
    frame = get_cases()
    result = []
    for control, explanations in fixtures[:k]:
        selected = frame.loc[frame["control_number"] == control]
        if selected.empty:
            raise RuntimeError("The fixed mock retrieval requires mock_cases.csv. Replace retrieve_similar_cases before using study data.")
        case = deepcopy(selected.iloc[0].to_dict())
        case["matched_fields"] = explanations.copy()
        case["explanation_context"] = "This demonstration returns the same fixed cases for every intake. Handwritten explanations refer to the saved Medical · senior citizen sample; they are not recalculated for this intake."
        result.append(case)
    return result
