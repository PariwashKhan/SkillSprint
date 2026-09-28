"""Database queries for dashboards."""
from src.database.models import SessionLocal, OnboardingPlanRecord, Employee, AuditLog


def get_admin_stats():
    """Return aggregate stats for the admin dashboard."""
    db = SessionLocal()
    try:
        plans = db.query(OnboardingPlanRecord).all()
        total = len(plans)

        verified = sum(1 for p in plans if p.validation_status == "Verified")
        warnings = sum(1 for p in plans if p.validation_status == "Verified with Warning")
        failed = sum(1 for p in plans if p.validation_status in
                     ("Unsupported", "Incomplete", "Contradiction Detected", "Partially Verified"))

        avg_cov = round(sum(p.coverage_score or 0 for p in plans) / total, 2) if total else 0
        avg_tra = round(sum(p.traceability_score or 0 for p in plans) / total, 2) if total else 0

        emp_count = db.query(Employee).count()
        audit_count = db.query(AuditLog).count()

        return {
            "total_plans": total,
            "verified_plans": verified,
            "warned_plans": warnings,
            "failed_plans": failed,
            "avg_coverage": avg_cov,
            "avg_traceability": avg_tra,
            "employees": emp_count,
            "audit_events": audit_count,
        }
    finally:
        db.close()


def get_recent_plans(limit: int = 10):
    """Return the most recent plans."""
    db = SessionLocal()
    try:
        rows = (db.query(OnboardingPlanRecord)
                  .order_by(OnboardingPlanRecord.created_at.desc())
                  .limit(limit).all())
        return [{
            "plan_id": p.plan_id,
            "employee_id": p.employee_id,
            "role": p.role,
            "coverage": p.coverage_score,
            "traceability": p.traceability_score,
            "status": p.validation_status,
            "created_at": str(p.created_at) if p.created_at else "",
            "model_used": p.model_used,
        } for p in rows]
    finally:
        db.close()


def get_plans_by_role():
    """Return coverage average grouped by role."""
    db = SessionLocal()
    try:
        rows = db.query(OnboardingPlanRecord).all()
        by_role = {}
        for p in rows:
            r = p.role or "Unknown"
            if r not in by_role:
                by_role[r] = {"count": 0, "total_coverage": 0, "verified": 0}
            by_role[r]["count"] += 1
            by_role[r]["total_coverage"] += p.coverage_score or 0
            if p.validation_status == "Verified":
                by_role[r]["verified"] += 1

        result = []
        for role, data in by_role.items():
            result.append({
                "role": role,
                "plans": data["count"],
                "avg_coverage": round(data["total_coverage"] / data["count"], 1),
                "verified": data["verified"],
            })
        return result
    finally:
        db.close()