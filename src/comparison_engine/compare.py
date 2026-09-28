"""
GenAI vs Python Ground-Truth Comparison Engine
"""

from typing import Dict, Any, List
from src.python_validation.validator import validate_plan, ValidationResult


def compare_and_report(genai_plan: Dict[str, Any], 
                       role_matrix: List[Dict], 
                       known_doc_ids: set,
                       role: str) -> Dict[str, Any]:
    """
    Run Pipeline 2 and produce a full comparison report.
    """
    result: ValidationResult = validate_plan(genai_plan, role_matrix, known_doc_ids, role)
    
    report = {
        "plan_id": genai_plan.get("plan_id"),
        "role": role,
        "final_status": result.status,
        "coverage_score": result.coverage_score,
        "traceability_score": result.traceability_score,
        "missing_count": len(result.missing_requirements),
        "unsupported_count": len(result.unsupported_requirements),
        "hallucination_count": len(result.hallucinations),
        "duplicate_count": len(result.duplicates),
        "missing_requirements": result.missing_requirements,
        "unsupported_requirements": result.unsupported_requirements,
        "hallucinations": result.hallucinations,
        "duplicates": result.duplicates,
        "detailed_comparison": result.details,
        "verification_statuses": result.verification_statuses
    }
    return report
