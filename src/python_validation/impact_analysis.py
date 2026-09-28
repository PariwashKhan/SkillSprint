"""
Policy version change -> impact analysis -> selective regeneration.
Pure Python. No GenAI here.
"""
from typing import Dict, Any, List
from datetime import datetime


def find_affected(plan: Dict[str, Any], changed_doc_id: str) -> Dict[str, Any]:
    """Return modules/tasks/quizzes referencing the changed document."""
    affected_modules, affected_tasks, affected_quizzes = [], [], []

    for m in plan.get("modules", []):
        if m.get("source_document_id") == changed_doc_id:
            affected_modules.append(m["module_id"])
        for t in m.get("tasks", []):
            if t.get("source_document_id") == changed_doc_id:
                affected_tasks.append(t["task_id"])
        for q in m.get("quiz", []):
            if q.get("source_document_id") == changed_doc_id:
                affected_quizzes.append(q["question_id"])

    return {
        "changed_document_id": changed_doc_id,
        "affected_module_ids": affected_modules,
        "affected_task_ids": affected_tasks,
        "affected_quiz_ids": affected_quizzes,
        "total_affected": len(affected_modules) + len(affected_tasks) + len(affected_quizzes),
        "detected_at": datetime.utcnow().isoformat(),
    }


def selective_regenerate_plan(plan: Dict[str, Any],
                              changed_doc_id: str,
                              new_requirements: List[Dict]) -> Dict[str, Any]:
    """Replace ONLY modules whose source_document_id matches the changed doc."""
    impact = find_affected(plan, changed_doc_id)
    affected = set(impact["affected_module_ids"])

    new_modules = []
    replacement_queue = list(new_requirements)

    for m in plan["modules"]:
        if m["module_id"] in affected and replacement_queue:
            new_modules.append(replacement_queue.pop(0))
        else:
            new_modules.append(m)

    return {**plan, "modules": new_modules,
            "last_regenerated": datetime.utcnow().isoformat(),
            "regenerated_module_ids": list(affected)}