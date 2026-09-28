"""
Pipeline 2 – Pure Python Ground-Truth Validation Engine
NEVER uses Generative AI.
Compares GenAI structured output against Role Requirement Matrix.
"""

from typing import List, Dict, Any, Set
from collections import defaultdict
import re


class ValidationResult:
    def __init__(self):
        self.status = "Pending"
        self.coverage_score = 0.0
        self.traceability_score = 0.0
        self.consistency_score = 100.0
        self.missing_requirements: List[str] = []
        self.unsupported_requirements: List[str] = []
        self.contradictions: List[str] = []
        self.duplicates: List[str] = []
        self.role_irrelevant: List[str] = []
        self.hallucinations: List[str] = []
        self.details: List[Dict] = []
        self.verification_statuses: Dict[str, str] = {}


def calculate_coverage(genai_req_ids: Set[str], matrix_mandatory_ids: Set[str]) -> float:
    if not matrix_mandatory_ids:
        return 100.0
    covered = genai_req_ids.intersection(matrix_mandatory_ids)
    return round(len(covered) / len(matrix_mandatory_ids) * 100, 2)


def calculate_traceability(modules: List[Dict]) -> float:
    """% of modules that have valid source_document_id and source_section_id"""
    if not modules:
        return 0.0
    valid = 0
    for m in modules:
        if m.get("source_document_id") and m.get("source_section_id"):
            valid += 1
    return round(valid / len(modules) * 100, 2)


def detect_duplicates(modules: List[Dict]) -> List[str]:
    titles = defaultdict(list)
    for m in modules:
        title = m.get("module_title", "").strip().lower()
        titles[title].append(m.get("module_id"))
    dups = []
    for title, ids in titles.items():
        if len(ids) > 1:
            dups.append(f"Duplicate module title '{title}': {ids}")
    return dups


def detect_role_irrelevant(modules: List[Dict], role: str, role_keywords: Dict[str, List[str]]) -> List[str]:
    """Simple keyword-based role relevance (extend with embeddings later)"""
    irrelevant = []
    for m in modules:
        title = m.get("module_title", "").lower()
        if "finance only" in title or "sales only" in title:
            if role not in title:
                irrelevant.append(m.get("module_id"))
    return irrelevant


def detect_hallucinations(modules: List[Dict], known_doc_ids: Set[str]) -> List[str]:
    """Flag modules whose source_document_id is not in approved documents"""
    hall = []
    for m in modules:
        src = m.get("source_document_id", "")
        if src and src not in known_doc_ids:
            hall.append(f"{m.get('module_id')}: unknown source {src}")
    return hall


def validate_plan(
    genai_plan: Dict[str, Any],
    role_matrix: List[Dict[str, Any]],
    known_document_ids: Set[str],
    role: str
) -> ValidationResult:
    """
    Main entry point of Pipeline 2.
    """
    result = ValidationResult()

    # Extract GenAI requirement IDs and modules
    modules = genai_plan.get("modules", [])
    genai_req_ids = set()
    for m in modules:
        if m.get("module_id"):
            genai_req_ids.add(m["module_id"])
        for t in m.get("tasks", []):
            if t.get("task_id"):
                genai_req_ids.add(t["task_id"])

    # Matrix mandatory IDs for this role
    matrix_for_role = [r for r in role_matrix if r.get("role") == role]
    mandatory_ids = {r["requirement_id"] for r in matrix_for_role if r.get("mandatory") is True}

    # Coverage
    result.coverage_score = calculate_coverage(genai_req_ids, mandatory_ids)
    result.missing_requirements = list(mandatory_ids - genai_req_ids)

    # Traceability
    result.traceability_score = calculate_traceability(modules)

    # Unsupported (GenAI produced IDs not in matrix)
    matrix_all_ids = {r["requirement_id"] for r in matrix_for_role}
    result.unsupported_requirements = list(genai_req_ids - matrix_all_ids)

    # Duplicates
    result.duplicates = detect_duplicates(modules)

    # Hallucinations
    result.hallucinations = detect_hallucinations(modules, known_document_ids)

    # Build detailed comparison rows
    for req in matrix_for_role:
        rid = req["requirement_id"]
        genai_has = rid in genai_req_ids
        row_status = "Verified" if genai_has else "Requirement Missing"
        if genai_has and result.traceability_score < 100:
            row_status = "Verified with Warning"

        result.details.append({
            "requirement_id": rid,
            "role": role,
            "python_expected": req.get("policy_requirement") or req.get("process_requirement"),
            "genai_present": genai_has,
            "source_document": req.get("source_document"),
            "mandatory": req.get("mandatory"),
            "status": row_status
        })
        result.verification_statuses[rid] = row_status

    # ===== FINAL STATUS (corrected precedence) =====
    # Precedence: Contradiction > Unsupported (hallucinations) > Verified > Warning > Partial > Incomplete
    if result.contradictions:
        result.status = "Contradiction Detected"
    elif result.hallucinations:
        result.status = "Unsupported"
    elif (result.coverage_score == 100 and
          result.traceability_score == 100 and
          not result.unsupported_requirements and
          not result.missing_requirements):
        result.status = "Verified"
    elif result.coverage_score >= 90 and result.traceability_score >= 90:
        result.status = "Verified with Warning"
    elif result.coverage_score >= 70:
        result.status = "Partially Verified"
    elif result.coverage_score >= 40:
        result.status = "Requirement Missing"
    else:
        result.status = "Incomplete"

    return result