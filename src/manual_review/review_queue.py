"""
Manual Review Queue + Audit Trail
SRS 48-49: Admin reviews flagged content, can approve/reject/edit; audit trail kept.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional


# In-memory review queue (persists in session_state via app.py)
def get_review_queue() -> List[Dict[str, Any]]:
    """Return items needing manual review based on validation warnings."""
    return []


def add_to_queue(plan_id: str, requirement_id: str, reason: str,
                 content: Optional[Dict] = None) -> Dict[str, Any]:
    """Add an item to the review queue."""
    return {
        "queue_id": f"REV-{plan_id}-{requirement_id}",
        "plan_id": plan_id,
        "requirement_id": requirement_id,
        "reason": reason,
        "content": content or {},
        "status": "Pending Review",
        "created_at": datetime.utcnow().isoformat(),
        "reviewer": None,
        "decision": None,
        "comment": None,
        "decided_at": None,
    }


def apply_decision(item: Dict[str, Any], decision: str,
                   reviewer: str, comment: str = "") -> Dict[str, Any]:
    """
    decision: one of ['Approved', 'Rejected', 'Edited', 'Regenerated']
    """
    valid = {"Approved", "Rejected", "Edited", "Regenerated"}
    if decision not in valid:
        raise ValueError(f"Invalid decision: {decision}")
    item = {**item}
    item["status"] = f"Reviewed — {decision}"
    item["decision"] = decision
    item["reviewer"] = reviewer
    item["comment"] = comment
    item["decided_at"] = datetime.utcnow().isoformat()
    return item


def build_audit_record(item: Dict[str, Any]) -> Dict[str, Any]:
    """Build an audit-trail row for the DB."""
    return {
        "action": item.get("decision", "Reviewed"),
        "entity_type": "onboarding_plan",
        "entity_id": item.get("plan_id", ""),
        "old_value": json.dumps({"requirement_id": item.get("requirement_id"),
                                  "status": "Pending Review"}),
        "new_value": json.dumps({"status": item.get("status"),
                                  "comment": item.get("comment", "")}),
        "user": item.get("reviewer", "unknown"),
        "timestamp": item.get("decided_at", datetime.utcnow().isoformat()),
    }


def flag_items_from_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract items needing review from a validation report."""
    flagged = []
    plan_id = report.get("plan_id", "UNKNOWN")
    for row in report.get("detailed_comparison", []):
        if row.get("status") in ("Requirement Missing", "Unsupported", "Verified with Warning"):
            flagged.append(add_to_queue(
                plan_id=plan_id,
                requirement_id=row.get("requirement_id", ""),
                reason=row.get("status", "Needs Review"),
                content={"source_document": row.get("source_document")},
            ))
    for h in report.get("hallucinations", []):
        flagged.append(add_to_queue(
            plan_id=plan_id,
            requirement_id=h.split(":")[0].strip() if ":" in h else "UNKNOWN",
            reason="Hallucination",
            content={"detail": h},
        ))
    return flagged