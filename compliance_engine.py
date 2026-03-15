"""
PestGuard AI — Compliance Engine
Validates chemical application logs against:
  - Federal FIFRA requirements (EPA)
  - State-specific rules
  - License validity checks
"""

from datetime import datetime, date, timedelta
from typing import Optional
import json

from epa_products import get_by_reg_no, get_by_name, get_restricted


# ── FIFRA Required Fields ──────────────────────────────────────────────────────
FIFRA_REQUIRED_FIELDS = [
    ("pesticide_name",      "Pesticide product name"),
    ("epa_reg_no",          "EPA Registration Number"),
    ("target_pest",         "Target pest"),
    ("application_site",    "Application site"),
    ("site_address",        "Site address"),
    ("date_applied",        "Date of application"),
    ("technician_name",     "Certified applicator name"),
]

# ── State-Specific Rules ───────────────────────────────────────────────────────
STATE_RULES = {
    "CA": {
        "name": "California",
        "record_retention_years": 3,       # CA requires 3 years vs federal 2
        "log_completion_days": 7,           # CA: 7 days (stricter than federal 14)
        "requires_dpr_report": True,        # Dept of Pesticide Regulation
        "inspector_response_hrs": 72,
        "notes": "Cal/EPA requires annual pesticide use reports to county agricultural commissioner.",
    },
    "NY": {
        "name": "New York",
        "record_retention_years": 3,
        "log_completion_days": 14,
        "requires_dpr_report": False,
        "inspector_response_hrs": 24,       # NY: must produce records within 24 hrs
        "notes": "NY DEC requires records available within 24 hours of inspector request.",
    },
    "FL": {
        "name": "Florida",
        "record_retention_years": 2,
        "log_completion_days": 14,
        "requires_dpr_report": False,
        "inspector_response_hrs": 72,
        "notes": "FDACS regulates pest control. Licenses must be posted at business.",
    },
    "TX": {
        "name": "Texas",
        "record_retention_years": 2,
        "log_completion_days": 14,
        "requires_dpr_report": False,
        "inspector_response_hrs": 72,
        "notes": "TDA regulates structural pest control. Annual renewal required.",
    },
    "DEFAULT": {
        "name": "Federal (FIFRA)",
        "record_retention_years": 2,
        "log_completion_days": 14,
        "requires_dpr_report": False,
        "inspector_response_hrs": 72,
        "notes": "Federal FIFRA minimum requirements apply.",
    },
}


def get_state_rules(state_code: str) -> dict:
    return STATE_RULES.get(state_code.upper(), STATE_RULES["DEFAULT"])


# ── Main Compliance Checker ───────────────────────────────────────────────────

def check_log_compliance(log: dict, technician: Optional[dict] = None, state: str = "FL") -> dict:
    """
    Run full compliance check on an application log.
    Returns: { status, score, issues: [{ code, severity, message }] }
    """
    issues = []
    score = 100
    state_rules = get_state_rules(state)

    # ── 1. FIFRA Required Fields Check ──────────────────────────────────────
    for field, label in FIFRA_REQUIRED_FIELDS:
        val = log.get(field, "")
        if not val or str(val).strip() == "":
            issues.append({
                "code": f"FIFRA_MISSING_{field.upper()}",
                "severity": "violation",
                "rule": "FIFRA § 171.7",
                "message": f"Required field missing: {label}",
                "fix": f"Add the {label} to complete this record.",
            })
            score -= 15

    # ── 2. EPA Registration Number Validation ────────────────────────────────
    epa_reg = log.get("epa_reg_no", "").strip()
    product = None
    if epa_reg:
        product = get_by_reg_no(epa_reg)
        if not product:
            # Try by name as fallback
            product = get_by_name(log.get("pesticide_name", ""))
        if not product:
            issues.append({
                "code": "EPA_REG_UNVERIFIED",
                "severity": "warning",
                "rule": "FIFRA § 3",
                "message": f"EPA Reg. No. '{epa_reg}' not found in EPA database. Verify product is federally registered.",
                "fix": "Confirm the EPA registration number on the product label.",
            })
            score -= 10

    # ── 3. Record Timeliness (14-day rule) ──────────────────────────────────
    max_days = state_rules["log_completion_days"]
    try:
        date_applied = datetime.strptime(log["date_applied"][:10], "%Y-%m-%d").date()
        date_logged = datetime.strptime(log.get("date_logged", datetime.now().isoformat())[:10], "%Y-%m-%d").date()
        days_lag = (date_logged - date_applied).days
        if days_lag > max_days:
            issues.append({
                "code": "LATE_RECORD_ENTRY",
                "severity": "violation",
                "rule": f"{'40 CFR 171.7' if max_days == 14 else state + ' state rule'}",
                "message": f"Record completed {days_lag} days after application. {state_rules['name']} requires completion within {max_days} days.",
                "fix": "Log applications within the required time window to avoid violations.",
            })
            score -= 20
        elif days_lag > max_days * 0.7:
            issues.append({
                "code": "LATE_RECORD_WARNING",
                "severity": "warning",
                "rule": "40 CFR 171.7",
                "message": f"Record completed {days_lag} days after application. Approaching {max_days}-day deadline.",
                "fix": "Establish a daily logging routine to stay compliant.",
            })
            score -= 5
    except (KeyError, ValueError):
        pass

    # ── 4. Technician License Validity ──────────────────────────────────────
    if technician:
        try:
            expiry = datetime.strptime(technician["license_expiry"][:10], "%Y-%m-%d").date()
            applied = datetime.strptime(log["date_applied"][:10], "%Y-%m-%d").date()
            if expiry < applied:
                issues.append({
                    "code": "LICENSE_EXPIRED",
                    "severity": "violation",
                    "rule": "FIFRA § 11 / State Licensing",
                    "message": f"Technician '{technician['name']}' license expired {expiry.strftime('%b %d, %Y')} — before this application on {applied.strftime('%b %d, %Y')}.",
                    "fix": "Renew license immediately and audit all applications performed after expiry.",
                })
                score -= 25
            elif (expiry - applied).days <= 30:
                issues.append({
                    "code": "LICENSE_EXPIRING_SOON",
                    "severity": "warning",
                    "rule": "State Licensing",
                    "message": f"License expires {expiry.strftime('%b %d, %Y')} — only {(expiry - applied).days} days from this application date.",
                    "fix": "Submit license renewal before expiry to avoid gaps in coverage.",
                })
                score -= 5
        except (KeyError, ValueError, TypeError):
            pass

    # ── 5. Restricted-Use Product Check ─────────────────────────────────────
    if product and product.get("restricted_use"):
        lic_type = (technician or {}).get("license_type", "")
        if "restricted" not in lic_type.lower() and "commercial" not in lic_type.lower():
            issues.append({
                "code": "RESTRICTED_USE_VIOLATION",
                "severity": "violation",
                "rule": "FIFRA § 3(d)",
                "message": f"'{product['product_name']}' is a Restricted-Use Pesticide. Only certified applicators with RUP authorization may apply.",
                "fix": "Verify technician holds RUP certification for this product.",
            })
            score -= 20

    # ── 6. PPE Documentation for DANGER-Level Products ──────────────────────
    if product and product.get("signal_word") == "DANGER":
        ppe = log.get("ppe_worn", "").strip()
        if not ppe:
            issues.append({
                "code": "PPE_NOT_DOCUMENTED",
                "severity": "warning",
                "rule": "FIFRA / OSHA 29 CFR 1910.1200",
                "message": f"'{product['product_name']}' is labeled DANGER. PPE worn must be documented.",
                "fix": "Add PPE documentation: gloves, eye protection, and any respirator used.",
            })
            score -= 10

    # ── 7. Weather Conditions for Outdoor Applications ──────────────────────
    site = log.get("application_site", "").lower()
    if any(s in site for s in ["outdoor", "lawn", "perimeter", "exterior", "yard"]):
        if not log.get("weather_conditions"):
            issues.append({
                "code": "WEATHER_NOT_DOCUMENTED",
                "severity": "warning",
                "rule": "Best Practice / State Regulations",
                "message": "Weather conditions not recorded for outdoor application.",
                "fix": "Document wind speed, temperature, and conditions for outdoor applications.",
            })
            score -= 5

    # ── Final Scoring ────────────────────────────────────────────────────────
    score = max(0, score)
    has_violation = any(i["severity"] == "violation" for i in issues)
    has_warning = any(i["severity"] == "warning" for i in issues)

    if has_violation:
        status = "violation"
    elif has_warning:
        status = "warning"
    else:
        status = "compliant"

    return {
        "status": status,
        "score": score,
        "issues": issues,
        "summary": _build_summary(status, issues, score),
    }


def _build_summary(status, issues, score):
    if status == "compliant":
        return f"✅ Fully compliant — Score: {score}/100. All FIFRA requirements met."
    elif status == "warning":
        count = len([i for i in issues if i["severity"] == "warning"])
        return f"⚠️ {count} warning(s) — Score: {score}/100. Review recommended but record is acceptable."
    else:
        count = len([i for i in issues if i["severity"] == "violation"])
        return f"🚨 {count} violation(s) — Score: {score}/100. Immediate action required to avoid EPA fines."


# ── License Alert Checker ─────────────────────────────────────────────────────

def check_license_alerts(technicians: list) -> list:
    """Check all technicians for license issues and return alerts."""
    today = date.today()
    alerts = []

    for tech in technicians:
        if not tech.get("is_active"):
            continue
        try:
            expiry = datetime.strptime(tech["license_expiry"][:10], "%Y-%m-%d").date()
            days_left = (expiry - today).days

            if days_left < 0:
                alerts.append({
                    "technician_id": tech["id"],
                    "technician_name": tech["name"],
                    "alert_type": "LICENSE_EXPIRED",
                    "severity": "violation",
                    "days": abs(days_left),
                    "message": f"⚠️ {tech['name']}'s license EXPIRED {abs(days_left)} days ago ({expiry.strftime('%b %d, %Y')}). Cannot legally apply pesticides.",
                })
            elif days_left <= 30:
                alerts.append({
                    "technician_id": tech["id"],
                    "technician_name": tech["name"],
                    "alert_type": "LICENSE_CRITICAL",
                    "severity": "critical",
                    "days": days_left,
                    "message": f"🔴 {tech['name']}'s license expires in {days_left} days ({expiry.strftime('%b %d, %Y')}). Renew immediately.",
                })
            elif days_left <= 60:
                alerts.append({
                    "technician_id": tech["id"],
                    "technician_name": tech["name"],
                    "alert_type": "LICENSE_WARNING",
                    "severity": "warning",
                    "days": days_left,
                    "message": f"🟡 {tech['name']}'s license expires in {days_left} days ({expiry.strftime('%b %d, %Y')}). Start renewal process.",
                })
            elif days_left <= 90:
                alerts.append({
                    "technician_id": tech["id"],
                    "technician_name": tech["name"],
                    "alert_type": "LICENSE_NOTICE",
                    "severity": "info",
                    "days": days_left,
                    "message": f"🔵 {tech['name']}'s license expires in {days_left} days ({expiry.strftime('%b %d, %Y')}). Plan for renewal.",
                })
        except (KeyError, ValueError):
            continue

    return sorted(alerts, key=lambda x: x["days"])
