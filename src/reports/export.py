"""
Export validation reports to CSV / Excel / PDF.
"""
import io
import json
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


def to_csv(report: dict) -> bytes:
    """Return CSV bytes."""
    df = pd.DataFrame(report.get("detailed_comparison", []))
    return df.to_csv(index=False).encode("utf-8")


def to_excel(report: dict) -> bytes:
    """Return Excel bytes with Summary + Details sheets."""
    buf = io.BytesIO()
    summary = pd.DataFrame([{
        "plan_id": report.get("plan_id", ""),
        "role": report.get("role", ""),
        "final_status": report.get("final_status", ""),
        "coverage_score": report.get("coverage_score", 0),
        "traceability_score": report.get("traceability_score", 0),
        "missing_count": report.get("missing_count", 0),
        "hallucination_count": report.get("hallucination_count", 0),
    }])
    details = pd.DataFrame(report.get("detailed_comparison", []))

    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        summary.to_excel(w, index=False, sheet_name="Summary")
        if not details.empty:
            details.to_excel(w, index=False, sheet_name="Details")
    return buf.getvalue()


def to_pdf(report: dict) -> bytes:
    """Return PDF bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 25 * mm

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, y, f"SkillSprint Validation Report")
    y -= 10 * mm

    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, f"Plan ID: {report.get('plan_id', 'N/A')}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Role: {report.get('role', 'N/A')}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Final Status: {report.get('final_status', 'N/A')}")
    y -= 10 * mm

    c.setFont("Helvetica-Bold", 13)
    c.drawString(20 * mm, y, "Scores")
    y -= 8 * mm

    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, f"Coverage Score: {report.get('coverage_score', 0)}%")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Traceability Score: {report.get('traceability_score', 0)}%")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Missing Requirements: {report.get('missing_count', 0)}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Hallucinations: {report.get('hallucination_count', 0)}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Duplicates: {report.get('duplicate_count', 0)}")
    y -= 15 * mm

    # First 20 detail rows
    rows = report.get("detailed_comparison", [])[:20]
    if rows:
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, "Detail (first 20 rows)")
        y -= 8 * mm
        c.setFont("Helvetica", 9)
        for r in rows:
            line = f"{r.get('requirement_id', '')}: {str(r.get('status', ''))[:60]}"
            c.drawString(20 * mm, y, line)
            y -= 5 * mm
            if y < 20 * mm:
                c.showPage()
                y = height - 25 * mm
                c.setFont("Helvetica", 9)

    c.showPage()
    c.save()
    return buf.getvalue()