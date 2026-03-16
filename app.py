"""
PestGuard AI — Main Application Server
Run with: python app.py
Serves at: http://localhost:8888
"""

import os
import sys
import json
import tornado.web
import tornado.ioloop
from datetime import datetime

# Add current dir to path
sys.path.insert(0, os.path.dirname(__file__))

from database import init_db, get_conn, rows_to_list, row_to_dict, get_dashboard_stats
from compliance_engine import check_log_compliance, check_license_alerts, get_state_rules
from ai_engine import parse_log_entry, match_chemical, generate_compliance_summary
from epa_products import search_products, get_all, get_by_reg_no
from report_generator import generate_audit_report
from cron_jobs import check_and_send_license_alerts

PORT = int(os.environ.get("PORT", 8888))
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "frontend")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


# ── Base Handler ───────────────────────────────────────────────────────────────

class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.set_header("Access-Control-Allow-Headers", "Content-Type")

    def options(self, *args):
        self.set_status(204)
        self.finish()

    def get_current_company(self):
        # Allow testing via header or use secure cookie
        header_id = self.request.headers.get("X-Company-ID")
        if header_id:
            return int(header_id)

        cookie_id = self.get_secure_cookie("company_id")
        if cookie_id:
            return int(cookie_id)

        # For development / single-tenant legacy support, fallback to company 1
        return 1

    def json(self, data, status=200):
        self.set_status(status)
        self.write(json.dumps(data, default=str))
        self.finish()

    def error(self, message, status=400):
        self.json({"error": message}, status)

    def get_body(self):
        try:
            return json.loads(self.request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return {}


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardHandler(BaseHandler):
    def get(self):
        company_id = self.get_current_company()
        stats = get_dashboard_stats(company_id)
        conn = get_conn()
        # Recent logs
        recent = rows_to_list(conn.execute("""
            SELECT id, date_applied, pesticide_name, application_site,
                   technician_name, compliance_status, compliance_score
            FROM application_logs
            WHERE company_id=?
            ORDER BY created_at DESC LIMIT 8
        """, (company_id,)).fetchall())
        # License alerts
        techs = rows_to_list(conn.execute(
            "SELECT * FROM technicians WHERE is_active=1 AND company_id=?", (company_id,)
        ).fetchall())
        conn.close()
        alerts = check_license_alerts(techs)
        self.json({
            "stats": stats,
            "recent_logs": recent,
            "license_alerts": alerts[:5],
            "ai_mode": "openai" if os.environ.get("OPENAI_API_KEY") else "demo",
        })


# ── Technicians ───────────────────────────────────────────────────────────────

class TechniciansHandler(BaseHandler):
    def get(self):
        company_id = self.get_current_company()
        conn = get_conn()
        techs = rows_to_list(conn.execute(
            "SELECT * FROM technicians WHERE company_id=? ORDER BY name", (company_id,)
        ).fetchall())
        conn.close()
        alerts = check_license_alerts(techs)
        alert_map = {a["technician_id"]: a for a in alerts}
        for t in techs:
            t["alert"] = alert_map.get(t["id"])
        self.json(techs)

    def post(self):
        data = self.get_body()
        required = ["name", "license_no", "license_state", "license_expiry"]
        for f in required:
            if not data.get(f):
                return self.error(f"Missing required field: {f}")
        conn = get_conn()
        company_id = self.get_current_company()
        c = conn.execute("""
            INSERT INTO technicians
              (company_id, name, license_no, license_state, license_type, license_expiry, email, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id, data["name"], data["license_no"], data["license_state"],
            data.get("license_type", "General Pest"),
            data["license_expiry"], data.get("email"), data.get("phone")
        ))
        conn.commit()
        tech = row_to_dict(conn.execute(
            "SELECT * FROM technicians WHERE id=?", (c.lastrowid,)
        ).fetchone())
        conn.close()
        self.json(tech, 201)


class TechnicianHandler(BaseHandler):
    def get(self, tech_id):
        conn = get_conn()
        company_id = self.get_current_company()
        tech = row_to_dict(conn.execute(
            "SELECT * FROM technicians WHERE id=? AND company_id=?", (tech_id, company_id)
        ).fetchone())
        conn.close()
        if not tech:
            return self.error("Technician not found", 404)
        self.json(tech)

    def put(self, tech_id):
        data = self.get_body()
        conn = get_conn()
        company_id = self.get_current_company()
        tech = row_to_dict(conn.execute(
            "SELECT * FROM technicians WHERE id=? AND company_id=?", (tech_id, company_id)
        ).fetchone())
        if not tech:
            conn.close()
            return self.error("Technician not found", 404)
        fields = ["name", "license_no", "license_state", "license_type",
                  "license_expiry", "email", "phone", "is_active"]
        updates = {f: data.get(f, tech[f]) for f in fields}
        conn.execute("""
            UPDATE technicians SET name=?, license_no=?, license_state=?,
              license_type=?, license_expiry=?, email=?, phone=?, is_active=?
            WHERE id=?
        """, (*[updates[f] for f in fields], tech_id))
        conn.commit()
        updated = row_to_dict(conn.execute(
            "SELECT * FROM technicians WHERE id=?", (tech_id,)
        ).fetchone())
        conn.close()
        self.json(updated)

    def delete(self, tech_id):
        conn = get_conn()
        company_id = self.get_current_company()
        conn.execute("UPDATE technicians SET is_active=0 WHERE id=? AND company_id=?", (tech_id, company_id))
        conn.commit()
        conn.close()
        self.json({"success": True, "message": "Technician deactivated."})


# ── Application Logs ──────────────────────────────────────────────────────────

class LogsHandler(BaseHandler):
    def get(self):
        conn = get_conn()
        company_id = self.get_current_company()

        status_filter = self.get_argument("status", None)
        tech_filter = self.get_argument("technician_id", None)
        limit = int(self.get_argument("limit", 50))
        offset = int(self.get_argument("offset", 0))
        date_from = self.get_argument("date_from", None)
        date_to = self.get_argument("date_to", None)

        conditions = ["company_id=?"]
        params = [company_id]

        if status_filter:
            conditions.append("compliance_status=?"); params.append(status_filter)
        if tech_filter:
            conditions.append("technician_id=?"); params.append(tech_filter)
        if date_from:
            conditions.append("date_applied>=?"); params.append(date_from)
        if date_to:
            conditions.append("date_applied<=?"); params.append(date_to)

        where = "WHERE " + " AND ".join(conditions)
        logs = rows_to_list(conn.execute(
            f"SELECT * FROM application_logs {where} ORDER BY date_applied DESC LIMIT ? OFFSET ?",
            (*params, limit, offset)
        ).fetchall())
        total = conn.execute(
            f"SELECT COUNT(*) FROM application_logs {where}", params
        ).fetchone()[0]
        conn.close()

        for log in logs:
            if isinstance(log.get("compliance_issues"), str):
                try:
                    log["compliance_issues"] = json.loads(log["compliance_issues"])
                except:
                    log["compliance_issues"] = []

        self.json({"logs": logs, "total": total, "limit": limit, "offset": offset})

    def post(self):
        data = self.get_body()
        required = ["pesticide_name", "epa_reg_no", "target_pest",
                    "application_site", "site_address", "date_applied"]
        for f in required:
            if not data.get(f):
                return self.error(f"Missing required field: {f}")

        conn = get_conn()
        # Get technician info
        tech = None
        tech_id = data.get("technician_id")
        tech_name = data.get("technician_name", "")
        if tech_id:
            tech = row_to_dict(conn.execute(
                "SELECT * FROM technicians WHERE id=?", (tech_id,)
            ).fetchone())
            if tech:
                tech_name = tech["name"]

        # Run compliance check
        compliance = check_log_compliance(data, tech, data.get("state", "FL"))

        company_id = self.get_current_company()

        c = conn.execute("""
            INSERT INTO application_logs
              (company_id, technician_id, technician_name, date_applied, pesticide_name, epa_reg_no,
               active_ingredient, target_pest, application_site, site_address,
               amount_applied, unit, application_method, weather_conditions,
               temperature_f, wind_speed_mph, ppe_worn, compliance_status,
               compliance_score, compliance_issues, raw_input, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            company_id, tech_id, tech_name,
            data["date_applied"], data["pesticide_name"], data["epa_reg_no"],
            data.get("active_ingredient"), data["target_pest"],
            data["application_site"], data["site_address"],
            data.get("amount_applied"), data.get("unit", "oz"),
            data.get("application_method", "Sprayer"),
            data.get("weather_conditions"), data.get("temperature_f"),
            data.get("wind_speed_mph"), data.get("ppe_worn"),
            compliance["status"], compliance["score"],
            json.dumps(compliance["issues"]),
            data.get("raw_input", ""), data.get("notes", ""),
        ))
        conn.commit()
        log = row_to_dict(conn.execute(
            "SELECT * FROM application_logs WHERE id=?", (c.lastrowid,)
        ).fetchone())
        conn.close()
        log["compliance"] = compliance
        self.json(log, 201)


class LogHandler(BaseHandler):
    def get(self, log_id):
        conn = get_conn()
        company_id = self.get_current_company()
        log = row_to_dict(conn.execute(
            "SELECT * FROM application_logs WHERE id=? AND company_id=?", (log_id, company_id)
        ).fetchone())
        conn.close()
        if not log:
            return self.error("Log not found", 404)
        if isinstance(log.get("compliance_issues"), str):
            try:
                log["compliance_issues"] = json.loads(log["compliance_issues"])
            except:
                log["compliance_issues"] = []
        self.json(log)

    def put(self, log_id):
        data = self.get_body()
        conn = get_conn()
        company_id = self.get_current_company()
        log = row_to_dict(conn.execute(
            "SELECT * FROM application_logs WHERE id=? AND company_id=?", (log_id, company_id)
        ).fetchone())
        if not log:
            conn.close()
            return self.error("Log not found", 404)

        merged = {**log, **data}
        tech = None
        if merged.get("technician_id"):
            tech = row_to_dict(conn.execute(
                "SELECT * FROM technicians WHERE id=?", (merged["technician_id"],)
            ).fetchone())

        compliance = check_log_compliance(merged, tech, "FL")
        conn.execute("""
            UPDATE application_logs SET
              pesticide_name=?, epa_reg_no=?, active_ingredient=?,
              target_pest=?, application_site=?, site_address=?,
              date_applied=?, amount_applied=?, unit=?, application_method=?,
              weather_conditions=?, temperature_f=?, wind_speed_mph=?, ppe_worn=?,
              compliance_status=?, compliance_score=?, compliance_issues=?, notes=?
            WHERE id=?
        """, (
            merged.get("pesticide_name"), merged.get("epa_reg_no"),
            merged.get("active_ingredient"), merged.get("target_pest"),
            merged.get("application_site"), merged.get("site_address"),
            merged.get("date_applied"), merged.get("amount_applied"),
            merged.get("unit", "oz"), merged.get("application_method", "Sprayer"),
            merged.get("weather_conditions"), merged.get("temperature_f"),
            merged.get("wind_speed_mph"), merged.get("ppe_worn"),
            compliance["status"], compliance["score"],
            json.dumps(compliance["issues"]), merged.get("notes", ""),
            log_id
        ))
        conn.commit()
        updated = row_to_dict(conn.execute(
            "SELECT * FROM application_logs WHERE id=?", (log_id,)
        ).fetchone())
        conn.close()
        updated["compliance"] = compliance
        self.json(updated)

    def delete(self, log_id):
        conn = get_conn()
        company_id = self.get_current_company()
        conn.execute("DELETE FROM application_logs WHERE id=? AND company_id=?", (log_id, company_id))
        conn.commit()
        conn.close()
        self.json({"success": True})


# ── AI Parse Handler ──────────────────────────────────────────────────────────

class ParseLogHandler(BaseHandler):
    def post(self):
        data = self.get_body()
        raw_text = data.get("text", "").strip()
        if not raw_text:
            return self.error("Provide 'text' field with log entry description")

        parsed = parse_log_entry(raw_text)

        # Preview compliance
        compliance = check_log_compliance(parsed, None, "FL")

        self.json({
            "parsed": parsed,
            "compliance_preview": {
                "status": compliance["status"],
                "score": compliance["score"],
                "issues_count": len(compliance["issues"]),
                "summary": compliance["summary"],
            },
            "ai_mode": parsed.get("_parse_mode", "rule-based"),
            "confidence": parsed.get("_confidence", "medium"),
        })


# ── Chemical Database ─────────────────────────────────────────────────────────

class ChemicalsHandler(BaseHandler):
    def get(self):
        q = self.get_argument("q", "")
        if q:
            results = match_chemical(q)
            if not results:
                results = search_products(q)
        else:
            results = get_all()[:20]
        self.json(results)


class ChemicalHandler(BaseHandler):
    def get(self, reg_no):
        product = get_by_reg_no(reg_no)
        if not product:
            return self.error("Product not found", 404)
        self.json(product)


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportsHandler(BaseHandler):
    def post(self):
        data = self.get_body()
        company_id = self.get_current_company()
        date_from = data.get("date_from") or "2020-01-01"
        date_to   = data.get("date_to")   or datetime.now().strftime("%Y-%m-%d")

        conn = get_conn()
        conditions = ["date_applied>=?", "date_applied<=?", "company_id=?"]
        params = [date_from, date_to, company_id]

        tech_id = data.get("technician_id")
        if tech_id:
            conditions.append("technician_id=?")
            params.append(tech_id)

        logs = rows_to_list(conn.execute(
            f"SELECT * FROM application_logs WHERE {' AND '.join(conditions)} ORDER BY date_applied",
            params
        ).fetchall())

        techs = rows_to_list(conn.execute(
            "SELECT * FROM technicians WHERE is_active=1 AND company_id=?", (company_id,)
        ).fetchall())
        conn.close()

        if not logs:
            return self.error("No logs found for the selected period")

        for log in logs:
            if isinstance(log.get("compliance_issues"), str):
                try:
                    log["compliance_issues"] = json.loads(log["compliance_issues"])
                except:
                    log["compliance_issues"] = []

        pdf_path = generate_audit_report(
            logs=logs,
            technicians=techs,
            date_from=date_from,
            date_to=date_to,
            company_name=data.get("company_name", "PestGuard Demo Co."),
            output_dir=REPORTS_DIR,
        )

        # Save to DB
        conn = get_conn()
        compliant = sum(1 for l in logs if l.get("compliance_status") == "compliant")
        violations = sum(1 for l in logs if l.get("compliance_status") == "violation")
        report_id = conn.execute("""
            INSERT INTO audit_reports
              (company_id, report_name, date_from, date_to, total_logs, compliant, violations, pdf_path)
            VALUES (?,?,?,?,?,?,?,?)
        """, (
            company_id, f"Audit {date_from} to {date_to}",
            date_from, date_to, len(logs), compliant, violations, pdf_path
        )).lastrowid
        conn.commit()
        conn.close()

        pdf_filename = os.path.basename(pdf_path)
        self.json({
            "success": True,
            "report_id": report_id,
            "filename": pdf_filename,
            "download_url": f"/reports/{pdf_filename}",
            "stats": {
                "total": len(logs),
                "compliant": compliant,
                "violations": violations,
                "compliance_rate": round(compliant / max(len(logs), 1) * 100, 1),
            }
        }, 201)


class ReportDownloadHandler(tornado.web.StaticFileHandler):
    pass


# ── Compliance Check (Standalone) ─────────────────────────────────────────────

class ComplianceCheckHandler(BaseHandler):
    def post(self):
        data = self.get_body()
        if not data:
            return self.error("Provide log data to check")
        state = data.get("state", "FL")
        tech_id = data.get("technician_id")
        tech = None
        if tech_id:
            conn = get_conn()
            tech = row_to_dict(conn.execute(
                "SELECT * FROM technicians WHERE id=?", (tech_id,)
            ).fetchone())
            conn.close()
        result = check_log_compliance(data, tech, state)
        self.json(result)


# ── License Alerts ────────────────────────────────────────────────────────────

class AlertsHandler(BaseHandler):
    def get(self):
        company_id = self.get_current_company()
        conn = get_conn()
        techs = rows_to_list(conn.execute(
            "SELECT * FROM technicians WHERE is_active=1 AND company_id=?", (company_id,)
        ).fetchall())
        conn.close()
        alerts = check_license_alerts(techs)
        self.json(alerts)


# ── Health / Status ───────────────────────────────────────────────────────────

class HealthHandler(BaseHandler):
    def get(self):
        self.json({
            "status": "ok",
            "version": "1.0.0",
            "product": "PestGuard AI",
            "ai_mode": "openai" if os.environ.get("OPENAI_API_KEY") else "demo",
            "timestamp": datetime.now().isoformat(),
        })


# ── Frontend ──────────────────────────────────────────────────────────────────

class FrontendHandler(tornado.web.RequestHandler):
    def get(self):
        index = os.path.join(FRONTEND_DIR, "index.html")
        with open(index, "r") as f:
            self.write(f.read())


# ── Authentication & Companies ────────────────────────────────────────────────

class CompaniesHandler(BaseHandler):
    def get(self):
        conn = get_conn()
        companies = rows_to_list(conn.execute("SELECT id, name FROM companies").fetchall())
        conn.close()
        self.json(companies)

class AuthStatusHandler(BaseHandler):
    def get(self):
        cookie = self.get_secure_cookie("company_id")
        if cookie:
            company_id = int(cookie)
            conn = get_conn()
            company = row_to_dict(conn.execute("SELECT id, name FROM companies WHERE id=?", (company_id,)).fetchone())
            conn.close()
            if company:
                return self.json({"logged_in": True, "company": company})
        self.json({"logged_in": False})

class LoginHandler(BaseHandler):
    def post(self):
        data = self.get_body()
        company_id = data.get("company_id")
        if not company_id:
            return self.error("company_id is required")

        conn = get_conn()
        company = row_to_dict(conn.execute("SELECT id, name FROM companies WHERE id=?", (company_id,)).fetchone())
        conn.close()

        if not company:
            return self.error("Company not found", 404)

        self.set_secure_cookie("company_id", str(company_id))
        self.json({"success": True, "company": company})

class LogoutHandler(BaseHandler):
    def post(self):
        self.clear_cookie("company_id")
        self.json({"success": True})


# ── App ───────────────────────────────────────────────────────────────────────

def make_app():
    os.makedirs(REPORTS_DIR, exist_ok=True)
    return tornado.web.Application([
        # Frontend
        (r"/", FrontendHandler),
        (r"/app", FrontendHandler),

        # API
        (r"/api/health",              HealthHandler),
        (r"/api/auth/status",         AuthStatusHandler),
        (r"/api/auth/login",          LoginHandler),
        (r"/api/auth/logout",         LogoutHandler),
        (r"/api/companies",           CompaniesHandler),
        (r"/api/dashboard",           DashboardHandler),
        (r"/api/technicians",         TechniciansHandler),
        (r"/api/technicians/(\d+)",   TechnicianHandler),
        (r"/api/logs",                LogsHandler),
        (r"/api/logs/(\d+)",          LogHandler),
        (r"/api/logs/parse",          ParseLogHandler),
        (r"/api/chemicals",           ChemicalsHandler),
        (r"/api/chemicals/([^/]+)",   ChemicalHandler),
        (r"/api/reports",             ReportsHandler),
        (r"/api/compliance/check",    ComplianceCheckHandler),
        (r"/api/alerts",              AlertsHandler),

        # Static report downloads
        (r"/reports/(.*)", tornado.web.StaticFileHandler, {"path": REPORTS_DIR}),
    ], debug=False, cookie_secret=os.environ.get("COOKIE_SECRET", "super-secret-key-change-me"))


if __name__ == "__main__":
    # Load .env file if present
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    init_db()

    # Seed demo data if DB is empty
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM technicians").fetchone()[0]
    conn.close()
    if count == 0:
        from seed_data import seed_demo_data
        seed_demo_data()

    app = make_app()
    app.listen(PORT)

    # Run cron job daily (86400000 ms = 24 hours)
    tornado.ioloop.PeriodicCallback(check_and_send_license_alerts, 86400000).start()
    # Run once on startup just to verify
    tornado.ioloop.IOLoop.current().add_callback(check_and_send_license_alerts)

    ai_mode = "🤖 OpenAI GPT-4o" if os.environ.get("OPENAI_API_KEY") else "🔧 Demo Mode (rule-based AI)"
    print(f"""
╔══════════════════════════════════════════════════════════╗
║          🌿 PestGuard AI — Compliance Platform           ║
╠══════════════════════════════════════════════════════════╣
║  Running at:  http://localhost:{PORT}                       ║
║  AI Engine:   {ai_mode:<41} ║
║  API Docs:    http://localhost:{PORT}/api/health             ║
╚══════════════════════════════════════════════════════════╝
    """)
    tornado.ioloop.IOLoop.current().start()
