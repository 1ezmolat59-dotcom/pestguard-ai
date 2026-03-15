"""
PestGuard AI — Demo Seed Data
Populates the database with realistic demo data for demonstrations.
"""

import json
from datetime import datetime, date, timedelta
import random
from database import get_conn


def seed_demo_data():
    conn = get_conn()
    print("[SEED] Seeding demo data...")

    # ── Companies ──────────────────────────────────────────────────────────────
    c = conn.execute("INSERT INTO companies (name) VALUES (?)", ("PestGuard Demo Co.",))
    company_id = c.lastrowid
    print(f"[SEED] Created Company: PestGuard Demo Co. (ID: {company_id})")

    # ── Technicians ────────────────────────────────────────────────────────────
    technicians = [
        {
            "name": "Marcus Williams",
            "license_no": "JB123456",
            "license_state": "FL",
            "license_type": "Commercial Pest Control",
            "license_expiry": (date.today() + timedelta(days=245)).isoformat(),
            "email": "marcus@pestpro.com",
            "phone": "555-0101",
        },
        {
            "name": "Sarah Chen",
            "license_no": "JB789012",
            "license_state": "FL",
            "license_type": "Commercial Pest Control",
            "license_expiry": (date.today() + timedelta(days=52)).isoformat(),  # Expiring soon!
            "email": "sarah@pestpro.com",
            "phone": "555-0102",
        },
        {
            "name": "Derek Thompson",
            "license_no": "JB345678",
            "license_state": "FL",
            "license_type": "Commercial Pest Control + RUP",
            "license_expiry": (date.today() - timedelta(days=12)).isoformat(),  # EXPIRED!
            "email": "derek@pestpro.com",
            "phone": "555-0103",
        },
        {
            "name": "Julia Ramirez",
            "license_no": "JB901234",
            "license_state": "FL",
            "license_type": "Commercial Pest Control",
            "license_expiry": (date.today() + timedelta(days=380)).isoformat(),
            "email": "julia@pestpro.com",
            "phone": "555-0104",
        },
    ]

    tech_ids = []
    for t in technicians:
        c = conn.execute("""
            INSERT INTO technicians
              (company_id, name, license_no, license_state, license_type, license_expiry, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (company_id, t["name"], t["license_no"], t["license_state"], t["license_type"],
              t["license_expiry"], t["email"], t["phone"]))
        tech_ids.append(c.lastrowid)
    conn.commit()
    print(f"[SEED] Added {len(tech_ids)} technicians")

    # ── Application Logs ───────────────────────────────────────────────────────
    sample_logs = [
        # --- COMPLIANT ---
        {
            "technician_idx": 0,   # Marcus
            "date_applied": (date.today() - timedelta(days=2)).isoformat(),
            "date_logged": (date.today() - timedelta(days=1)).isoformat(),
            "pesticide_name": "Suspend SC",
            "epa_reg_no": "432-763",
            "active_ingredient": "Deltamethrin 4.75%",
            "target_pest": "cockroaches",
            "application_site": "Kitchen",
            "site_address": "1200 Brickell Ave, Miami, FL 33131",
            "amount_applied": 4.0, "unit": "oz",
            "application_method": "Sprayer",
            "weather_conditions": "Indoor — N/A",
            "ppe_worn": "gloves, eye protection",
            "compliance_status": "compliant", "compliance_score": 100,
            "compliance_issues": "[]",
            "notes": "Treated along baseboards and under equipment.",
        },
        {
            "technician_idx": 3,   # Julia
            "date_applied": (date.today() - timedelta(days=5)).isoformat(),
            "date_logged": (date.today() - timedelta(days=4)).isoformat(),
            "pesticide_name": "Advion Ant Bait Gel",
            "epa_reg_no": "352-742",
            "active_ingredient": "Indoxacarb 0.5%",
            "target_pest": "ants",
            "application_site": "Office",
            "site_address": "350 NW 1st Ave, Fort Lauderdale, FL 33301",
            "amount_applied": 2.0, "unit": "oz",
            "application_method": "Gel Application",
            "weather_conditions": "Indoor — N/A",
            "ppe_worn": "gloves",
            "compliance_status": "compliant", "compliance_score": 100,
            "compliance_issues": "[]",
            "notes": "Applied gel bait at entry points. Follow-up in 2 weeks.",
        },
        {
            "technician_idx": 0,   # Marcus
            "date_applied": (date.today() - timedelta(days=8)).isoformat(),
            "date_logged": (date.today() - timedelta(days=7)).isoformat(),
            "pesticide_name": "Demand CS",
            "epa_reg_no": "100-1066",
            "active_ingredient": "Lambda-Cyhalothrin 9.7%",
            "target_pest": "mosquitoes",
            "application_site": "Exterior Perimeter",
            "site_address": "8900 SW 40th St, Miami, FL 33165",
            "amount_applied": 8.0, "unit": "oz",
            "application_method": "Sprayer",
            "weather_conditions": "Sunny, 82°F, Wind 6 mph",
            "temperature_f": 82, "wind_speed_mph": 6,
            "ppe_worn": "gloves, eye protection",
            "compliance_status": "compliant", "compliance_score": 97,
            "compliance_issues": "[]",
            "notes": "Full perimeter treatment. Conditions ideal.",
        },
        {
            "technician_idx": 3,   # Julia
            "date_applied": (date.today() - timedelta(days=10)).isoformat(),
            "date_logged": (date.today() - timedelta(days=9)).isoformat(),
            "pesticide_name": "Talstar Pro",
            "epa_reg_no": "279-3206",
            "active_ingredient": "Bifenthrin 7.9%",
            "target_pest": "spiders",
            "application_site": "Exterior Perimeter",
            "site_address": "225 SE 2nd Ave, Homestead, FL 33030",
            "amount_applied": 6.0, "unit": "oz",
            "application_method": "Sprayer",
            "weather_conditions": "Partly Cloudy, 78°F, Calm winds",
            "temperature_f": 78, "wind_speed_mph": 2,
            "ppe_worn": "gloves, eye protection, long sleeves",
            "compliance_status": "compliant", "compliance_score": 100,
            "compliance_issues": "[]",
        },
        # --- WARNINGS ---
        {
            "technician_idx": 1,   # Sarah
            "date_applied": (date.today() - timedelta(days=3)).isoformat(),
            "date_logged": date.today().isoformat(),
            "pesticide_name": "Cy-Kick CS",
            "epa_reg_no": "432-1254",
            "active_ingredient": "Cyfluthrin 6%",
            "target_pest": "bed bugs",
            "application_site": "Interior General",
            "site_address": "1450 Collins Ave, Miami Beach, FL 33139",
            "amount_applied": 3.0, "unit": "oz",
            "application_method": "Sprayer",
            "weather_conditions": None,  # Missing weather → warning
            "ppe_worn": "gloves",
            "compliance_status": "warning", "compliance_score": 82,
            "compliance_issues": json.dumps([{
                "code": "WEATHER_NOT_DOCUMENTED",
                "severity": "warning",
                "rule": "Best Practice",
                "message": "Weather conditions not recorded for outdoor application.",
                "fix": "Document wind speed, temperature, and conditions for outdoor applications.",
            }]),
            "notes": "Hotel room treatment. Customer reported recent purchase.",
        },
        {
            "technician_idx": 0,   # Marcus
            "date_applied": (date.today() - timedelta(days=15)).isoformat(),
            "date_logged": (date.today() - timedelta(days=4)).isoformat(),  # 11 days lag = warning
            "pesticide_name": "Phantom",
            "epa_reg_no": "241-392",
            "active_ingredient": "Chlorfenapyr 21.45%",
            "target_pest": "ants",
            "application_site": "Commercial Kitchen",
            "site_address": "5201 Blue Lagoon Dr, Miami, FL 33126",
            "amount_applied": 2.0, "unit": "oz",
            "application_method": "Sprayer",
            "weather_conditions": "Indoor — N/A",
            "ppe_worn": "gloves, eye protection",
            "compliance_status": "warning", "compliance_score": 78,
            "compliance_issues": json.dumps([{
                "code": "LATE_RECORD_WARNING",
                "severity": "warning",
                "rule": "40 CFR 171.7",
                "message": "Record completed 11 days after application. Approaching 14-day deadline.",
                "fix": "Establish a daily logging routine to stay compliant.",
            }]),
        },
        # --- VIOLATIONS ---
        {
            "technician_idx": 2,   # Derek (EXPIRED license)
            "date_applied": (date.today() - timedelta(days=4)).isoformat(),
            "date_logged": (date.today() - timedelta(days=3)).isoformat(),
            "pesticide_name": "Termidor SC",
            "epa_reg_no": "7969-210",
            "active_ingredient": "Fipronil 9.1%",
            "target_pest": "termites",
            "application_site": "Soil",
            "site_address": "3300 NW 79th Ave, Doral, FL 33122",
            "amount_applied": 16.0, "unit": "oz",
            "application_method": "Injection",
            "weather_conditions": "Sunny, 85°F, Wind 5 mph",
            "temperature_f": 85, "wind_speed_mph": 5,
            "ppe_worn": None,  # Missing PPE + DANGER product
            "compliance_status": "violation", "compliance_score": 35,
            "compliance_issues": json.dumps([
                {
                    "code": "LICENSE_EXPIRED",
                    "severity": "violation",
                    "rule": "FIFRA § 11",
                    "message": "Technician 'Derek Thompson' license expired before this application.",
                    "fix": "Renew license immediately. Audit all applications after expiry.",
                },
                {
                    "code": "RESTRICTED_USE_VIOLATION",
                    "severity": "violation",
                    "rule": "FIFRA § 3(d)",
                    "message": "'Termidor SC' is a Restricted-Use Pesticide requiring RUP certification.",
                    "fix": "Verify technician holds RUP certification for this product.",
                },
                {
                    "code": "PPE_NOT_DOCUMENTED",
                    "severity": "warning",
                    "rule": "OSHA 29 CFR 1910.1200",
                    "message": "DANGER-level product PPE not documented.",
                    "fix": "Document gloves, eye protection, and respirator used.",
                },
            ]),
            "notes": "URGENT: License and RUP certification must be verified before next application.",
        },
        {
            "technician_idx": 1,  # Sarah
            "date_applied": (date.today() - timedelta(days=20)).isoformat(),
            "date_logged": date.today().isoformat(),  # 20 days later = VIOLATION
            "pesticide_name": "Suspend SC",
            "epa_reg_no": "432-763",
            "active_ingredient": "Deltamethrin 4.75%",
            "target_pest": "flies",
            "application_site": "Warehouse",
            "site_address": "8800 NW 36th St, Doral, FL 33178",
            "amount_applied": 10.0, "unit": "oz",
            "application_method": "Fogging",
            "weather_conditions": "Indoor — N/A",
            "ppe_worn": "gloves, respirator",
            "compliance_status": "violation", "compliance_score": 55,
            "compliance_issues": json.dumps([{
                "code": "LATE_RECORD_ENTRY",
                "severity": "violation",
                "rule": "40 CFR 171.7",
                "message": "Record completed 20 days after application. Exceeds 14-day federal requirement.",
                "fix": "Log applications within 14 days. Consider end-of-day mobile logging.",
            }]),
        },
        # Two more compliant
        {
            "technician_idx": 3,
            "date_applied": (date.today() - timedelta(days=12)).isoformat(),
            "date_logged": (date.today() - timedelta(days=11)).isoformat(),
            "pesticide_name": "Niban Granular Bait",
            "epa_reg_no": "8329-5",
            "active_ingredient": "Orthoboric Acid 5%",
            "target_pest": "cockroaches",
            "application_site": "Garage",
            "site_address": "11200 Hammocks Blvd, Miami, FL 33196",
            "amount_applied": 1.0, "unit": "lbs",
            "application_method": "Granular",
            "weather_conditions": "Indoor — N/A",
            "ppe_worn": "gloves",
            "compliance_status": "compliant", "compliance_score": 100,
            "compliance_issues": "[]",
        },
        {
            "technician_idx": 0,
            "date_applied": (date.today() - timedelta(days=18)).isoformat(),
            "date_logged": (date.today() - timedelta(days=17)).isoformat(),
            "pesticide_name": "Gentrol IGR",
            "epa_reg_no": "2724-490",
            "active_ingredient": "Hydroprene 9%",
            "target_pest": "cockroaches",
            "application_site": "Commercial Kitchen",
            "site_address": "999 Brickell Way, Miami, FL 33131",
            "amount_applied": 1.5, "unit": "oz",
            "application_method": "Sprayer",
            "weather_conditions": "Indoor — N/A",
            "ppe_worn": "gloves",
            "compliance_status": "compliant", "compliance_score": 100,
            "compliance_issues": "[]",
            "notes": "IGR treatment for cockroach population control. Follow-up with bait next visit.",
        },
    ]

    for log in sample_logs:
        idx = log.pop("technician_idx")
        tech_id = tech_ids[idx]
        tech_name = technicians[idx]["name"]
        conn.execute("""
            INSERT INTO application_logs
              (company_id, technician_id, technician_name, date_applied, date_logged,
               pesticide_name, epa_reg_no, active_ingredient, target_pest,
               application_site, site_address, amount_applied, unit,
               application_method, weather_conditions, temperature_f,
               wind_speed_mph, ppe_worn, compliance_status, compliance_score,
               compliance_issues, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            company_id, tech_id, tech_name,
            log["date_applied"],
            log.get("date_logged", log["date_applied"]),
            log["pesticide_name"], log["epa_reg_no"],
            log.get("active_ingredient", ""),
            log["target_pest"], log["application_site"], log["site_address"],
            log.get("amount_applied"), log.get("unit", "oz"),
            log.get("application_method", "Sprayer"),
            log.get("weather_conditions"),
            log.get("temperature_f"), log.get("wind_speed_mph"),
            log.get("ppe_worn"),
            log["compliance_status"], log["compliance_score"],
            log.get("compliance_issues", "[]"),
            log.get("notes", ""),
        ))

    conn.commit()
    conn.close()
    print(f"[SEED] Added {len(sample_logs)} application logs")
    print("[SEED] Demo data ready!")


if __name__ == "__main__":
    from database import init_db
    init_db()
    seed_demo_data()
