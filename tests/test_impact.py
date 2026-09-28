"""Tests for policy impact analysis."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.python_validation.impact_analysis import find_affected, selective_regenerate_plan


def test_impact_isolates_changed_document():
    plan = {"modules": [
        {"module_id": "M1", "source_document_id": "DOC-A", "tasks": [], "quiz": []},
        {"module_id": "M2", "source_document_id": "DOC-B", "tasks": [], "quiz": []},
    ]}
    imp = find_affected(plan, "DOC-A")
    assert imp["affected_module_ids"] == ["M1"]
    assert imp["total_affected"] == 1


def test_no_impact_when_doc_not_referenced():
    plan = {"modules": [
        {"module_id": "M1", "source_document_id": "DOC-A", "tasks": [], "quiz": []},
    ]}
    imp = find_affected(plan, "DOC-Z")
    assert imp["total_affected"] == 0


def test_selective_regeneration_preserves_other_modules():
    plan = {"modules": [
        {"module_id": "M1", "source_document_id": "DOC-A", "tasks": [], "quiz": []},
        {"module_id": "M2", "source_document_id": "DOC-B", "tasks": [], "quiz": []},
    ]}
    replacement = [{"module_id": "M1", "source_document_id": "DOC-A-NEW"}]
    new_plan = selective_regenerate_plan(plan, "DOC-A", replacement)
    ids = [m["module_id"] for m in new_plan["modules"]]
    assert "M1" in ids
    assert "M2" in ids
    assert new_plan["regenerated_module_ids"] == ["M1"]