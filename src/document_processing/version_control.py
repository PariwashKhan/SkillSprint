"""
Document Version Control (SRS 8)
Distinguishes active vs obsolete versions.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional


def is_newer_version(new_ver: str, old_ver: str) -> bool:
    """Compare '1.2' vs '1.10' correctly (numeric, not lexicographic)."""
    def parse(v):
        try:
            return tuple(int(x) for x in v.split("."))
        except Exception:
            return (0,)
    return parse(new_ver) > parse(old_ver)


def mark_obsolete(versions: List[Dict[str, Any]],
                  new_doc_id: str,
                  new_version: str) -> List[Dict[str, Any]]:
    """
    Given a list of document versions, mark all matching docs older
    than new_version as obsolete.
    """
    updated = []
    for v in versions:
        v = {**v}
        if v.get("document_id") == new_doc_id:
            if is_newer_version(new_version, v.get("version", "0")):
                v["status"] = "Obsolete"
                v["obsolete_since"] = datetime.utcnow().strftime("%Y-%m-%d")
            elif v.get("version") == new_version:
                v["status"] = "Active"
        updated.append(v)
    return updated


def get_active_version(versions: List[Dict[str, Any]],
                       doc_id: str) -> Optional[Dict[str, Any]]:
    """Return the currently active version for a doc_id."""
    for v in versions:
        if v.get("document_id") == doc_id and v.get("status") == "Active":
            return v
    return None


def get_all_active(versions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [v for v in versions if v.get("status") == "Active"]


def impact_of_version_change(old_version: str,
                             new_version: str,
                             affected_modules: List[str]) -> Dict[str, Any]:
    """Summarize impact of a version change."""
    return {
        "old_version": old_version,
        "new_version": new_version,
        "changed": old_version != new_version,
        "affected_module_count": len(affected_modules),
        "affected_module_ids": affected_modules,
        "detected_at": datetime.utcnow().isoformat(),
    }