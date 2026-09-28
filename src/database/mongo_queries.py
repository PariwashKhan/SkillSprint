import os
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB using the URI from .env
client = MongoClient(os.getenv("MONGO_URI"))
db = client["skillsprint_db"] # You can name your database anything
plans_collection = db["onboarding_plans"] # This is like a 'table'

def save_plan_to_mongo(plan_dict, report):
    """Saves the generated plan and its validation report to MongoDB."""
    doc = {
        "plan_id": plan_dict["plan_id"],
        "role": plan_dict["role"],
        "plan_json": plan_dict, # Store the whole plan as a nested document
        "coverage_score": report["coverage_score"],
        "traceability_score": report["traceability_score"],
        "validation_status": report["final_status"],
        "created_at": datetime.utcnow()
    }
    # Use update_one with upsert to avoid duplicates if the plan_id already exists
    plans_collection.update_one(
        {"plan_id": plan_dict["plan_id"]},
        {"$set": doc},
        upsert=True
    )

def get_admin_stats_from_mongo():
    """Aggregate stats for the dashboard."""
    total_plans = plans_collection.count_documents({})
    verified_plans = plans_collection.count_documents({"validation_status": "Verified"})
    
    # MongoDB aggregation for averages
    pipeline = [
        {"$group": {
            "_id": None,
            "avg_coverage": {"$avg": "$coverage_score"},
            "avg_traceability": {"$avg": "$traceability_score"}
        }}
    ]
    result = list(plans_collection.aggregate(pipeline))
    stats = result[0] if result else {"avg_coverage": 0, "avg_traceability": 0}
    
    return {
        "total_plans": total_plans,
        "verified_plans": verified_plans,
        "avg_coverage": round(stats.get("avg_coverage", 0), 2),
        "avg_traceability": round(stats.get("avg_traceability", 0), 2),
        "employees": 0, # Placeholder
        "audit_events": 0 # Placeholder
    }

def get_recent_plans_from_mongo(limit=10):
    """Get recent plans for the dashboard."""
    rows = plans_collection.find().sort("created_at", -1).limit(limit)
    return [{
        "plan_id": p["plan_id"],
        "role": p["role"],
        "coverage": p["coverage_score"],
        "traceability": p["traceability_score"],
        "status": p["validation_status"],
        "created_at": str(p.get("created_at", "")),
    } for p in rows]

def get_plans_by_role_from_mongo():
    """Aggregate average coverage by role."""
    pipeline = [
        {"$group": {
            "_id": "$role",
            "plans": {"$sum": 1},
            "avg_coverage": {"$avg": "$coverage_score"},
            "verified": {"$sum": {"$cond": [{"$eq": ["$validation_status", "Verified"]}, 1, 0]}}
        }}
    ]
    rows = plans_collection.aggregate(pipeline)
    return [{
        "role": r["_id"],
        "plans": r["plans"],
        "avg_coverage": round(r["avg_coverage"], 1),
        "verified": r["verified"],
    } for r in rows]