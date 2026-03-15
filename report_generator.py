"""
PestGuard AI — Audit Report Generator
Produces professional, inspector-ready PDF reports using ReportLab.
"""

import os
import json
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Brand Colors ────────────────────────────────────────────────────────────────
GREEN_DARK  = colors.HexColor("#1A3A2A")
GREEN_MID   = colors.HexColor("#2E6B4A")
GREEN_LITE  = colors.HexColor("#3A9C6A")
GOLD        = colors.HexColor("#F4A300")
RED         = colors.HexColor("#C0392B")
LIGHT_GREY  = colors.HexColor("#F0F7F2")
MID_GREY    = colors.HexColor("#8A9499")
WHITE       = colors.white
BLACK       = colors.black


def _status_color(status):
    return {
        "compliant": GREEN_LITE,
        "warning": GOLD,
        "violation": RED,
        "pending": MID_GREY,
    }.get(status, MID_GREY)


def generate_audit_report(
    logs: list,
    technicians: list,
    date_from: str,
    date_to: str,
    company_name: str = "PestGuard Demo Co.",
    output_dir: str = None,
    report_title: str = None,
) -> str:
    """
    Generate a PDF audit report.
    Returns the path to the generated PDF file.
    """
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(output_dir, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"PestGuard_Audit_Report_{ts}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ──────────────────────────────────────────────────────────────────
    # Top bar
    story.append(Paragraph(
        f"<font color='#1A3A2A'><b>PestGuard AI</b></font>   Compliance Audit Report",
        ParagraphStyle("TopBar", fontSize=11, textColor=GREEN_DARK)
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=GREEN_LITE, spaceAfter=10))

    # Report Title
    story.append(Paragraph(
        report_title or "Chemical Application Compliance Audit",
        ParagraphStyle("ReportTitle", fontSize=22, textColor=GREEN_DARK,
                       fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=4)
    ))
    story.append(Paragraph(
        f"<b>{company_name}</b>  |  Report Period: "
        f"{_fmt_date(date_from)} to {_fmt_date(date_to)}  |  "
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        ParagraphStyle("Meta", fontSize=9, textColor=MID_GREY, spaceAfter=14)
    ))

    # ── Summary Statistics ──────────────────────────────────────────────────────
    total = len(logs)
    compliant_count = sum(1 for l in logs if l.get("compliance_status") == "compliant")
    warning_count   = sum(1 for l in logs if l.get("compliance_status") == "warning")
    violation_count = sum(1 for l in logs if l.get("compliance_status") == "violation")
    comp_rate = round(compliant_count / max(total, 1) * 100, 1)

    summary_data = [
        ["Total Applications", "Compliant", "Warnings", "Violations", "Compliance Rate"],
        [str(total), str(compliant_count), str(warning_count), str(violation_count), f"{comp_rate}%"],
    ]

    summary_table = Table(summary_data, colWidths=[1.4*inch]*5, rowHeights=[0.3*inch, 0.5*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), GREEN_DARK),
        ("TEXTCOLOR",     (0,0), (-1,0), WHITE),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 9),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND",    (0,1), (-1,1), LIGHT_GREY),
        ("FONTNAME",      (0,1), (-1,1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,1), (3,1), 16),
        ("TEXTCOLOR",     (1,1), (1,1), GREEN_LITE),   # compliant: green
        ("TEXTCOLOR",     (2,1), (2,1), GOLD),          # warnings: gold
        ("TEXTCOLOR",     (3,1), (3,1), RED),            # violations: red
        ("TEXTCOLOR",     (4,1), (4,1), GREEN_DARK),
        ("BOX",           (0,0), (-1,-1), 0.5, GREEN_MID),
        ("LINEBELOW",     (0,0), (-1,0), 0.5, GREEN_MID),
        ("GRID",          (0,0), (-1,-1), 0.25, colors.HexColor("#CCDDCC")),
    ]))

    story.append(summary_table)
    story.append(Spacer(1, 14))

    # ── Compliance Assessment ────────────────────────────────────────────────────
    if comp_rate >= 90:
        assessment_color = GREEN_LITE
        assessment = f"EXCELLENT -- {comp_rate}% compliance rate. This record is audit-ready."
    elif comp_rate >= 75:
        assessment_color = GOLD
        assessment = f"FAIR -- {comp_rate}% compliance rate. Address warnings before next inspection."
    else:
        assessment_color = RED
        assessment = f"NEEDS ATTENTION -- {comp_rate}% compliance rate. {violation_count} violation(s) require immediate resolution."

    story.append(Paragraph(
        assessment,
        ParagraphStyle("Assessment", fontSize=10, textColor=assessment_color,
                       fontName="Helvetica-Bold", spaceBefore=2, spaceAfter=12)
    ))

    # ── Application Log Table ───────────────────────────────────────────────────
    story.append(Paragraph(
        "Chemical Application Log",
        ParagraphStyle("Section", fontSize=13, textColor=GREEN_DARK,
                       fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=6)
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=GREEN_MID, spaceAfter=8))

    col_widths = [0.9*inch, 1.45*inch, 1.1*inch, 1.1*inch, 1.05*inch, 0.85*inch, 0.8*inch]
    table_data = [["Date", "Pesticide", "EPA Reg. No.", "Target Pest", "Site", "Technician", "Status"]]

    for log in logs:
        status = log.get("compliance_status", "pending")
        status_label = {"compliant":"OK", "warning":"WARN", "violation":"VIOL", "pending":"PEND"}.get(status, status)
        table_data.append([
            _fmt_date_short(log.get("date_applied", "")),
            _truncate(log.get("pesticide_name", "Unknown"), 22),
            log.get("epa_reg_no", "-"),
            _truncate(log.get("target_pest", "-"), 14),
            _truncate(log.get("application_site", "-"), 16),
            _truncate(log.get("technician_name", "-"), 14),
            status_label,
        ])

    log_table = Table(table_data, colWidths=col_widths)
    style = [
        ("BACKGROUND",  (0,0), (-1,0), GREEN_DARK),
        ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
        ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0), (-1,-1), 8),
        ("ALIGN",       (0,0), (-1,-1), "LEFT"),
        ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT_GREY, WHITE]),
        ("GRID",        (0,0), (-1,-1), 0.25, colors.HexColor("#CCDDCC")),
        ("BOX",         (0,0), (-1,-1), 0.5, GREEN_MID),
        ("TOPPADDING",  (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 4),
    ]
    # Color-code status column
    for i, log in enumerate(logs, start=1):
        status = log.get("compliance_status", "pending")
        style.append(("TEXTCOLOR", (6, i), (6, i), _status_color(status)))
        style.append(("FONTNAME", (6, i), (6, i), "Helvetica-Bold"))

    log_table.setStyle(TableStyle(style))
    story.append(log_table)
    story.append(Spacer(1, 16))

    # ── Violations Detail ───────────────────────────────────────────────────────
    violations = [l for l in logs if l.get("compliance_status") == "violation"]
    if violations:
        story.append(Paragraph(
            "Violations Requiring Immediate Action",
            ParagraphStyle("ViolSection", fontSize=12, textColor=RED,
                           fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=6)
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=RED, spaceAfter=8))

        for log in violations:
            issues = json.loads(log.get("compliance_issues", "[]")) if isinstance(log.get("compliance_issues"), str) else (log.get("compliance_issues") or [])
            detail = (
                f"<b>{log.get('pesticide_name','?')}</b> at {log.get('site_address','?')} "
                f"({_fmt_date_short(log.get('date_applied',''))})"
            )
            story.append(Paragraph(detail, ParagraphStyle("ViolHead", fontSize=9, textColor=GREEN_DARK,
                                                           fontName="Helvetica-Bold", spaceBefore=4)))
            for issue in issues:
                if issue.get("severity") == "violation":
                    story.append(Paragraph(
                        f"  - {issue.get('message','?')} -- {issue.get('fix','')}",
                        ParagraphStyle("ViolItem", fontSize=8, textColor=RED, leftIndent=12, spaceBefore=1)
                    ))
        story.append(Spacer(1, 14))

    # ── Technician Roster ────────────────────────────────────────────────────────
    if technicians:
        story.append(Paragraph(
            "Technician Licenses",
            ParagraphStyle("Section", fontSize=13, textColor=GREEN_DARK,
                           fontName="Helvetica-Bold", spaceBefore=4, spaceAfter=6)
        ))
        story.append(HRFlowable(width="100%", thickness=1, color=GREEN_MID, spaceAfter=8))

        tech_data = [["Name", "License No.", "State", "License Type", "Expires", "Status"]]
        today = datetime.now().date()
        for tech in technicians:
            try:
                exp = datetime.strptime(tech["license_expiry"][:10], "%Y-%m-%d").date()
                days = (exp - today).days
                if days < 0:     lic_status = "EXPIRED"
                elif days <= 30: lic_status = "CRITICAL"
                elif days <= 90: lic_status = "WARNING"
                else:            lic_status = "VALID"
            except:
                lic_status = "UNKNOWN"

            tech_data.append([
                tech.get("name", "-"),
                tech.get("license_no", "-"),
                tech.get("license_state", "-"),
                tech.get("license_type", "-"),
                _fmt_date_short(tech.get("license_expiry", "")),
                lic_status,
            ])

        tech_table = Table(tech_data, colWidths=[1.2*inch, 1.1*inch, 0.55*inch, 1.3*inch, 0.95*inch, 0.85*inch])
        status_colors = {"VALID": GREEN_LITE, "WARNING": GOLD, "CRITICAL": RED, "EXPIRED": RED, "UNKNOWN": MID_GREY}
        tech_style = [
            ("BACKGROUND",  (0,0), (-1,0), GREEN_DARK),
            ("TEXTCOLOR",   (0,0), (-1,0), WHITE),
            ("FONTNAME",    (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",    (0,0), (-1,-1), 8),
            ("VALIGN",      (0,0), (-1,-1), "MIDDLE"),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [LIGHT_GREY, WHITE]),
            ("GRID",        (0,0), (-1,-1), 0.25, colors.HexColor("#CCDDCC")),
            ("BOX",         (0,0), (-1,-1), 0.5, GREEN_MID),
            ("TOPPADDING",  (0,0), (-1,-1), 4),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
        ]
        for i, tech in enumerate(technicians, start=1):
            try:
                exp = datetime.strptime(tech["license_expiry"][:10], "%Y-%m-%d").date()
                days = (exp - today).days
                if days < 0:     s = "EXPIRED"
                elif days <= 30: s = "CRITICAL"
                elif days <= 90: s = "WARNING"
                else:            s = "VALID"
            except:
                s = "UNKNOWN"
            tech_style.append(("TEXTCOLOR", (5,i), (5,i), status_colors.get(s, MID_GREY)))
            tech_style.append(("FONTNAME", (5,i), (5,i), "Helvetica-Bold"))

        tech_table.setStyle(TableStyle(tech_style))
        story.append(tech_table)
        story.append(Spacer(1, 16))

    # ── Footer ───────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCDDCC"), spaceBefore=10))
    story.append(Paragraph(
        f"This report was generated by <b>PestGuard AI</b> and covers all applications "
        f"from {_fmt_date(date_from)} to {_fmt_date(date_to)}. Records should be retained "
        f"for a minimum of 2 years per FIFRA 171.7 (3 years in CA and NY). "
        f"For support: pestguard.ai",
        ParagraphStyle("Footer", fontSize=7.5, textColor=MID_GREY, spaceAfter=0)
    ))

    doc.build(story)
    print(f"[REPORT] Generated: {filepath}")
    return filepath


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_date(d: str) -> str:
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%B %d, %Y")
    except:
        return d or "-"

def _fmt_date_short(d: str) -> str:
    try:
        return datetime.strptime(d[:10], "%Y-%m-%d").strftime("%m/%d/%Y")
    except:
        return d or "-"

def _truncate(s: str, n: int) -> str:
    return s[:n] + "..." if len(s) > n else s
