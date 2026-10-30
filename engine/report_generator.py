#!/usr/bin/env python3
"""Generate package-specific customer deliverables from a processed assessment."""
from __future__ import annotations

from pathlib import Path
from html import escape
import json, math

HERE = Path(__file__).resolve().parent
PROFILES = json.loads((HERE / "package_profiles.json").read_text(encoding="utf-8"))

CATEGORY_LABELS = {
    "data_model_architecture": "Data Model Architecture",
    "relationships": "Relationships",
    "dax_quality": "DAX Quality",
    "power_query_transformation": "Power Query / Transformation",
    "performance": "Performance",
    "dashboard_ux_visual_design": "Dashboard UX & Visual Design",
    "business_kpi_alignment": "Business & KPI Alignment",
    "maintainability_governance": "Maintainability & Governance",
}
PRIORITY_ORDER = {"P1": 1, "P2": 2, "P3": 3, "P4": 4}
SEVERITY_ORDER = {"critical": 1, "high": 2, "medium": 3, "low": 4}


def _sorted_findings(result):
    return sorted(
        result["assessment"].get("findings", []),
        key=lambda f: (PRIORITY_ORDER.get(f.get("priority"), 9), SEVERITY_ORDER.get(f.get("severity"), 9), f.get("title", "")),
    )


def _recommendation(finding):
    title = finding.get("title", "the identified issue")
    category = finding.get("category", "")
    actions = {
        "data_model_architecture": "Refactor toward a clear star-schema structure and remove unnecessary model complexity where practical.",
        "relationships": "Simplify relationship paths, prefer single-direction filtering and validate cardinality and active paths.",
        "dax_quality": "Refactor the affected DAX for correctness, readability and efficient filter/context behavior.",
        "power_query_transformation": "Move suitable transformations upstream, simplify query steps and preserve query folding where possible.",
        "performance": "Reduce avoidable query/render cost and validate the improvement with Power BI performance tooling.",
        "dashboard_ux_visual_design": "Reduce visual friction, strengthen KPI hierarchy and simplify navigation around key decisions.",
        "business_kpi_alignment": "Clarify KPI definitions, ownership and business meaning before further technical optimization.",
        "maintainability_governance": "Standardize naming, documentation and reusable patterns to reduce future maintenance effort.",
    }
    return actions.get(category, f"Review and remediate {title.lower()} using Microsoft Power BI modeling best practices.")


def _effort_hours(findings):
    bands = {"low": (0.5, 1.5), "medium": (1.5, 4.0), "high": (4.0, 8.0)}
    low = high = 0.0
    for f in findings:
        lo, hi = bands.get(f.get("effort", "medium"), bands["medium"])
        if f.get("priority") == "P1":
            hi *= 1.2
        low += lo
        high += hi
    return max(1.0, low), max(2.0, high)


def _round50(value):
    return int(math.ceil(value / 50.0) * 50)


def build_optimization_offer(result):
    findings = _sorted_findings(result)
    profile = PROFILES[result["package"]]
    low_h, high_h = _effort_hours(findings)
    hourly = 95
    low_price = max(250, _round50(low_h * hourly))
    high_price = max(low_price + 100, _round50(high_h * hourly))
    top = findings[:5]
    bullets = "\n".join(f"- {f.get('priority', 'P?')}: {f.get('title')}" for f in top) or "- No remediation scope has been confirmed yet."
    return {
        "estimated_hours_low": round(low_h, 1),
        "estimated_hours_high": round(high_h, 1),
        "suggested_price_low_usd": low_price,
        "suggested_price_high_usd": high_price,
        "text": f"""Power BI Optimization – Custom Offer\n\nBased on the assessment, I recommend a focused optimization phase addressing the highest-priority findings first.\n\nProposed scope:\n{bullets}\n\nEstimated implementation effort: {low_h:.1f}–{high_h:.1f} hours\nSuggested Fiverr custom-offer range: ${low_price}–${high_price}\n\nThe final fixed price should be confirmed after a short scope check. Implementation is separate from the assessment and can be followed by a Re-Validation to verify the improvements.\n"""
    }


def build_delivery_summary(result):
    score = result["assessment"]["score"]
    band = result["assessment"]["band"]
    findings = _sorted_findings(result)
    p1 = sum(1 for f in findings if f.get("priority") == "P1")
    p2 = sum(1 for f in findings if f.get("priority") == "P2")
    top = findings[:3]
    top_text = "\n".join(f"- {f['priority']}: {f['title']}" for f in top) or "- No confirmed technical findings in the assessed scope."
    return f"""Hi {result.get('customer_name', 'there')},

thank you for your order. I completed the Power BI assessment for {result.get('project_name', 'your project')}.

Health Score: {score}/100 – {band}
Confirmed priority findings: {len(findings)} ({p1} P1, {p2} P2)

Top priorities:
{top_text}

The attached report explains the findings, business/technical impact and recommended next steps. I have also prepared an optional optimization scope based on the identified priorities.

Best regards,
Daniel
"""


def _safe(text):
    return escape(str(text or ""))


def generate_pdf(result, output_path: Path):
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    except ImportError as exc:
        raise RuntimeError("PDF generation requires reportlab. Install with: pip install -r requirements.txt") from exc

    profile = PROFILES[result["package"]]
    findings = _sorted_findings(result)[: profile["max_priority_findings"]]
    score = result["assessment"]["score"]
    band = result["assessment"]["band"]
    review_count = result.get("review", {}).get("review_required_count", 0)

    navy = colors.HexColor("#0B1F33")
    blue = colors.HexColor("#2F6BFF")
    green = colors.HexColor("#1E9E63")
    orange = colors.HexColor("#E39A22")
    red = colors.HexColor("#D64545")
    light = colors.HexColor("#F5F7FA")
    muted = colors.HexColor("#66788A")

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleWhite", parent=styles["Title"], textColor=colors.white, fontSize=25, leading=30, spaceAfter=8))
    styles.add(ParagraphStyle(name="SubWhite", parent=styles["BodyText"], textColor=colors.white, fontSize=11, leading=16))
    styles.add(ParagraphStyle(name="H1Navy", parent=styles["Heading1"], textColor=navy, fontSize=20, leading=24, spaceAfter=10))
    styles.add(ParagraphStyle(name="H2Blue", parent=styles["Heading2"], textColor=blue, fontSize=13, leading=16, spaceAfter=5))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9.5, leading=14, textColor=colors.HexColor("#1E2A36")))
    styles.add(ParagraphStyle(name="Score", parent=styles["Title"], alignment=TA_CENTER, fontSize=34, textColor=green if score >= 85 else orange if score >= 70 else red))
    styles.add(ParagraphStyle(name="Muted", parent=styles["BodyText"], fontSize=8.5, leading=12, textColor=muted))

    doc = SimpleDocTemplate(str(output_path), pagesize=A4, rightMargin=16*mm, leftMargin=16*mm, topMargin=14*mm, bottomMargin=14*mm,
                            title=f"Power BI Health Assessment – {result.get('project_name', '')}", author="Daniel Wauer")
    story = []

    cover = Table([[Paragraph("POWER BI HEALTH ASSESSMENT", styles["TitleWhite"])],
                   [Paragraph(_safe(profile["name"]), styles["SubWhite"])],
                   [Spacer(1, 14*mm)],
                   [Paragraph(_safe(result.get("project_name", "Power BI Project")), styles["TitleWhite"])],
                   [Paragraph(f"Prepared for {_safe(result.get('customer_name', 'Client'))}", styles["SubWhite"])],
                   [Spacer(1, 9*mm)],
                   [Paragraph("Clear findings. Clear priorities. Actionable next steps.", styles["SubWhite"])]],
                  colWidths=[178*mm], rowHeights=[None,None,20*mm,None,None,12*mm,None])
    cover.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), navy), ("BOX", (0,0), (-1,-1), 0, navy), ("LEFTPADDING", (0,0), (-1,-1), 12*mm), ("RIGHTPADDING", (0,0), (-1,-1), 12*mm), ("TOPPADDING", (0,0), (-1,-1), 8*mm), ("BOTTOMPADDING", (0,0), (-1,-1), 8*mm)]))
    story.extend([cover, PageBreak()])

    story.append(Paragraph("Executive Summary", styles["H1Navy"]))
    story.append(Paragraph(f"The assessed Power BI solution achieved a Health Score of <b>{score}/100</b> ({_safe(band)}). The assessment focused on technical quality, maintainability and reporting readiness within the available static project evidence.", styles["BodySmall"]))
    story.append(Spacer(1, 5*mm))
    score_table = Table([[Paragraph(f"{score}/100", styles["Score"]), Paragraph(f"<b>{len(result['assessment'].get('findings', []))}</b><br/>confirmed findings", styles["BodySmall"]), Paragraph(f"<b>{review_count}</b><br/>items requiring expert review", styles["BodySmall"])]], colWidths=[55*mm,55*mm,55*mm])
    score_table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), light), ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#D9E0E7")), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("ALIGN", (0,0), (-1,-1), "CENTER"), ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)]))
    story.extend([score_table, Spacer(1, 6*mm)])
    story.append(Paragraph("Business goal", styles["H2Blue"]))
    story.append(Paragraph(_safe(result.get("business_goal")), styles["BodySmall"]))
    story.append(Paragraph("Primary concern", styles["H2Blue"]))
    story.append(Paragraph(_safe(result.get("primary_concern")), styles["BodySmall"]))

    if profile.get("include_category_scores"):
        story.extend([Spacer(1, 6*mm), Paragraph("Health Overview", styles["H1Navy"])])
        rows = [["Area", "Score"]]
        for key, value in result["assessment"].get("category_scores", {}).items():
            rows.append([CATEGORY_LABELS.get(key, key.replace("_", " ").title()), str(value)])
        t = Table(rows, colWidths=[135*mm,30*mm], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), navy), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"), ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D9E0E7")), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, light]), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
        story.append(t)

    story.extend([PageBreak(), Paragraph("Priority Findings", styles["H1Navy"])])
    if not findings:
        story.append(Paragraph("No confirmed findings were identified in the currently assessed automated scope. This does not guarantee that the report is free of issues; hybrid and manual checks may still require expert validation.", styles["BodySmall"]))
    for f in findings:
        color = red if f.get("priority") == "P1" else orange if f.get("priority") == "P2" else blue
        header = Table([[Paragraph(f"<b>{_safe(f.get('priority'))} · {_safe(f.get('title'))}</b>", styles["BodySmall"])]], colWidths=[165*mm])
        header.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#EEF3F8")), ("LINEBEFORE", (0,0), (0,-1), 4, color), ("LEFTPADDING", (0,0), (-1,-1), 8), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
        body = [header,
                Paragraph(f"<b>Area:</b> {_safe(CATEGORY_LABELS.get(f.get('category'), f.get('category')))} &nbsp;&nbsp; <b>Severity:</b> {_safe(f.get('severity'))} &nbsp;&nbsp; <b>Effort:</b> {_safe(f.get('effort'))}", styles["Muted"]),
                Paragraph(f"<b>Recommendation:</b> {_safe(_recommendation(f))}", styles["BodySmall"]), Spacer(1, 4*mm)]
        story.append(KeepTogether(body))

    story.extend([PageBreak(), Paragraph("Recommended Next Steps", styles["H1Navy"])])
    roadmap = [
        ("1", "Address P1/P2 findings first", "Fix the highest-risk structural and correctness issues before cosmetic changes."),
        ("2", "Implement low-effort quick wins", "Remove avoidable complexity and improve maintainability where the effort is small."),
        ("3", "Validate performance and behavior", "Re-test model behavior, refresh/query performance and key report interactions."),
        ("4", "Re-Validate", "Run the assessment again after implementation and document the improvement."),
    ]
    rows = [[Paragraph(f"<b>{n}</b>", styles["BodySmall"]), Paragraph(f"<b>{_safe(title)}</b><br/>{_safe(desc)}", styles["BodySmall"])] for n,title,desc in roadmap]
    rt = Table(rows, colWidths=[12*mm,153*mm])
    rt.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP"), ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, light]), ("GRID", (0,0), (-1,-1), 0.3, colors.HexColor("#D9E0E7")), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
    story.append(rt)

    if profile.get("include_blueprint"):
        story.extend([Spacer(1, 7*mm), Paragraph("Optimization Blueprint", styles["H1Navy"]), Paragraph("The recommended implementation sequence is: model correctness → relationship/filter behavior → DAX and transformation quality → performance → UX/reporting polish → governance. This sequence minimizes rework by fixing structural causes before downstream symptoms.", styles["BodySmall"])])

    story.extend([Spacer(1, 8*mm), Paragraph("Assessment Boundary", styles["H2Blue"]), Paragraph("This assessment is a static technical review of the provided Power BI project evidence. It does not replace production monitoring, business-owner validation, data-source verification or user acceptance testing. Findings requiring runtime or business context must be validated before implementation.", styles["Muted"])])
    doc.build(story)


def generate_deliverables(result, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    review_count = result.get("review", {}).get("review_required_count", 0)
    prefix = "DRAFT_" if review_count else ""
    report_path = out_dir / f"{prefix}Power_BI_Health_Assessment_{result['order_id']}.pdf"
    generate_pdf(result, report_path)

    delivery = build_delivery_summary(result)
    (out_dir / "fiverr_delivery_message.txt").write_text(delivery, encoding="utf-8")

    offer = build_optimization_offer(result)
    (out_dir / "optimization_offer.md").write_text(offer["text"], encoding="utf-8")

    summary = {
        "order_id": result["order_id"],
        "package": result["package"],
        "score": result["assessment"]["score"],
        "band": result["assessment"]["band"],
        "confirmed_findings": len(result["assessment"].get("findings", [])),
        "review_required": review_count,
        "customer_report": report_path.name,
        "final_ready": review_count == 0,
        "optimization_offer": {k: v for k, v in offer.items() if k != "text"},
    }
    (out_dir / "delivery_manifest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return summary
