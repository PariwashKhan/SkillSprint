"""
Contradiction Detection (SRS 33-34)
Detects conflicting policy versions, FAQ vs SOP, and precedence violations.
"""
from typing import List, Dict, Any
import re


def extract_numbered_section(text: str) -> str:
    """Extract things like '4.2' or 'Section 4.2' from a string."""
    m = re.search(r"(\d+\.\d+)", text)
    return m.group(1) if m else ""


def detect_version_contradictions(plan: Dict[str, Any]) -> List[str]:
    """Flag modules whose source_document_id appears with multiple versions."""
    doc_versions = {}
    contradictions = []
    for m in plan.get("modules", []):
        doc = m.get("source_document_id", "")
        ver = m.get("source_version") or m.get("document_version") or ""
        if doc and ver:
            if doc in doc_versions and doc_versions[doc] != ver:
                contradictions.append(
                    f"Version conflict for {doc}: {doc_versions[doc]} vs {ver}"
                )
            doc_versions[doc] = ver
    return contradictions


def detect_faq_sop_conflicts(modules: List[Dict]) -> List[str]:
    """Detect contradictions between FAQ and SOP on the same topic."""
    sop_topics = {m.get("module_title", "").lower() for m in modules
                  if m.get("source_document_id", "").startswith("SOP")}
    faq_topics = {m.get("module_title", "").lower() for m in modules
                  if m.get("source_document_id", "").startswith("FAQ")}
    conflicts = []
    for topic in sop_topics & faq_topics:
        # Same topic appearing in both SOP and FAQ — potential precedence issue
        conflicts.append(f"FAQ and SOP cover same topic '{topic}' — verify precedence")
    return conflicts


def apply_precedence_rule(source_doc: str,
                          active_version: str,
                          obsolete_versions: List[str]) -> str:
    """
    Apply documented policy precedence:
    1. Latest Approved Policy
    2. Department SOP
    3. Official FAQ
    4. Informal Guidance
    """
    if source_doc.startswith("POL") and active_version not in obsolete_versions:
        return "Latest Approved Policy"
    if source_doc.startswith("SOP"):
        return "Department SOP"
    if source_doc.startswith("FAQ"):
        return "Official FAQ"
    return "Informal Guidance"


def detect_all_contradictions(plan: Dict[str, Any]) -> List[str]:
    """Aggregate all contradiction detections."""
    contradictions = []
    contradictions.extend(detect_version_contradictions(plan))
    contradictions.extend(detect_faq_sop_conflicts(plan.get("modules", [])))
    return contradictions