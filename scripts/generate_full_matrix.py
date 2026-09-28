import json
from pathlib import Path

ROLES = {
    "Sales Executive":            {"docs": ["SOP-SALES-03", "POL-CONDUCT-01", "POL-DATA-01", "SOP-CRM-01", "POL-AML-01"]},
    "Customer Support Executive": {"docs": ["SOP-07", "POL-DATA-01", "POL-INFOSEC-01", "POL-CONDUCT-01", "SOP-CX-02"]},
    "HR Executive":               {"docs": ["HB-001", "POL-LEAVE-01", "POL-CONDUCT-01", "SOP-HR-04", "POL-DATA-01"]},
    "Finance Associate":          {"docs": ["POL-AML-01", "POL-DATA-01", "POL-INFOSEC-01", "SOP-FIN-05"]},
    "Operations Coordinator":     {"docs": ["SOP-OPS-01", "POL-INFOSEC-01", "POL-CONDUCT-01"]},
    "Marketing Executive":        {"docs": ["SOP-MKT-01", "POL-DATA-01", "POL-CONDUCT-01"]},
    "Software Support Engineer":  {"docs": ["POL-INFOSEC-01", "POL-DATA-01", "SOP-TECH-01"]},
    "Branch Manager":             {"docs": ["POL-AML-01", "POL-CONDUCT-01", "HB-001", "POL-INFOSEC-01", "POL-LEAVE-01"]},
    "Data Analyst":               {"docs": ["POL-DATA-01", "POL-INFOSEC-01", "SOP-DATA-01"]},
    "Team Leader":                {"docs": ["HB-001", "SOP-HR-04", "POL-CONDUCT-01", "POL-INFOSEC-01"]},
}

COMPETENCIES = [
    "InfoSec Basics", "Data Protection", "AML Compliance", "Escalation Handling",
    "Customer Communication", "Secure Coding", "PII Handling", "Consent Management",
    "Incident Reporting", "Access Control", "Password Hygiene", "Fraud Detection",
    "Conduct & Ethics", "Leave Administration", "Performance Feedback",
    "Process Documentation", "Brand Compliance", "Transaction Monitoring",
    "Risk Reporting", "Team Onboarding", "Coaching Skills", "Quality Assurance",
    "Analytics Ethics", "Anonymisation", "Crisis Communication",
]

PRIORITIES = ["High", "High", "High", "Medium", "Low"]
STAGES = ["Day 1", "Week 1", "Week 1", "Week 2", "First 30 Days"]

def build():
    matrix = []
    rid = 1
    for role, meta in ROLES.items():
        for doc in meta["docs"]:
            for k in range(4):
                comp = COMPETENCIES[(rid + k) % len(COMPETENCIES)]
                matrix.append({
                    "requirement_id": f"R{rid:03d}",
                    "role": role,
                    "policy_requirement": f"Complete {comp} training per {doc}",
                    "process_requirement": f"Apply {comp.lower()} procedure from {doc}",
                    "competency": comp,
                    "mandatory": k < 3,
                    "priority": PRIORITIES[(rid + k) % len(PRIORITIES)],
                    "source_document": doc,
                    "source_section": f"{((rid + k) % 9) + 1}.{k + 1}",
                    "assessment_requirement": f"{comp} quiz" if k == 0 else f"{comp} scenario task",
                    "due_stage": STAGES[(rid + k) % len(STAGES)],
                })
                rid += 1
    return matrix

if __name__ == "__main__":
    data = build()
    out = Path("data/role_matrix/nexusfintech_matrix.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    mandatory = sum(1 for r in data if r["mandatory"])
    print(f"Wrote {len(data)} requirements to {out}")
    print(f"Mandatory: {mandatory} | Roles: {len(ROLES)}")