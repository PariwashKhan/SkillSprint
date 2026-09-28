"""
GenAI Consistency Check (SRS 44-45)
Runs the same generation task twice and compares structured outputs.
"""
from typing import Dict, Any, List, Set


def extract_structured_signature(plan: Dict[str, Any]) -> Dict[str, Set[str]]:
    """Extract comparable fields from a plan."""
    sig = {
        "module_ids": set(),
        "source_documents": set(),
        "competencies": set(),
        "due_stages": set(),
    }
    for m in plan.get("modules", []):
        if m.get("module_id"):
            sig["module_ids"].add(m["module_id"])
        if m.get("source_document_id"):
            sig["source_documents"].add(m["source_document_id"])
        for kc in m.get("key_concepts", []):
            sig["competencies"].add(kc)
        if m.get("due_stage"):
            sig["due_stages"].add(m["due_stage"])
    return sig


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 1.0
    return len(a & b) / len(union)


def compare_consistency(plan1: Dict[str, Any],
                        plan2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two generations of the same structured task.
    Returns per-field Jaccard + overall consistency score.
    """
    s1 = extract_structured_signature(plan1)
    s2 = extract_structured_signature(plan2)

    per_field = {}
    for field in s1.keys():
        per_field[field] = round(jaccard(s1[field], s2[field]) * 100, 2)

    overall = round(sum(per_field.values()) / len(per_field), 2) if per_field else 0.0

    flagged = []
    for field, score in per_field.items():
        if score < 70:
            flagged.append({
                "field": field,
                "consistency": score,
                "message": f"{field} consistency below 70% — investigate."
            })

    return {
        "per_field_consistency": per_field,
        "overall_consistency_score": overall,
        "flagged_differences": flagged,
        "final_verdict": "Consistent" if overall >= 85 else
                         "Minor Differences" if overall >= 70 else
                         "Inconsistent"
    }