"""Tests for Pipeline 2 (Python validator)."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.python_validation.validator import validate_plan

MATRIX = [
    {"requirement_id": "R001", "role": "Tester", "mandatory": True,
     "policy_requirement": "x", "source_document": "DOC-1", "source_section": "1"},
    {"requirement_id": "R002", "role": "Tester", "mandatory": True,
     "policy_requirement": "y", "source_document": "DOC-2", "source_section": "2"},
]
DOCS = {"DOC-1", "DOC-2"}


def test_full_coverage_passes():
    plan = {"modules": [
        {"module_id": "R001", "source_document_id": "DOC-1", "source_section_id": "1"},
        {"module_id": "R002", "source_document_id": "DOC-2", "source_section_id": "2"},
    ]}
    r = validate_plan(plan, MATRIX, DOCS, "Tester")
    assert r.coverage_score == 100.0
    assert r.traceability_score == 100.0
    assert r.status == "Verified"


def test_missing_requirement_flagged():
    plan = {"modules": [
        {"module_id": "R001", "source_document_id": "DOC-1", "source_section_id": "1"},
    ]}
    r = validate_plan(plan, MATRIX, DOCS, "Tester")
    assert "R002" in r.missing_requirements
    assert r.coverage_score == 50.0


def test_hallucination_detected():
    plan = {"modules": [
        {"module_id": "R001", "source_document_id": "GHOST-DOC", "source_section_id": "9"},
    ]}
    r = validate_plan(plan, MATRIX, DOCS, "Tester")
    assert any("GHOST-DOC" in h for h in r.hallucinations)