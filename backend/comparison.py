"""Server-owned field comparison, never an aggregate similarity measure."""

from .catalog import SECTIONS


def display(value, kind):
    if value is None or value == "":
        return "Not recorded"
    if kind == "money":
        return f"₱{value:,.2f}"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return "; ".join(value) if value else "None reported"
    return str(value)


def compare_cases(current: dict, past: dict) -> list[dict]:
    sections = []
    for section in SECTIONS:
        rows = []
        for field in section["fields"]:
            a, b = current.get(field["key"]), past.get(field["key"])
            if a in (None, "") or b in (None, ""):
                status = "not_recorded"
            elif isinstance(a, list):
                status = "same" if set(a) == set(b) else "different"
            else:
                status = "same" if a == b else "different"
            rows.append({"key": field["key"], "label": field["label"], "current": display(a, field["kind"]), "past": display(b, field["kind"]), "status": status})
        sections.append({"id": section["id"], "title": section["title"], "rows": rows})
    return sections

