"""
PestGuard AI — Database Layer
SQLite3 with auto-migration on first run.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "pestguard.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    # ── Companies (Multi-Tenant SaaS) ──────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        name                TEXT    NOT NULL,
        stripe_customer_id  TEXT,
        subscription_status TEXT    DEFAULT 'trial',
        qb_realm_id         TEXT,
        qb_access_token     TEXT,
        qb_refresh_token    TEXT,
        created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
    )""")

    # ── Technicians ────────────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS technicians (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id      INTEGER REFERENCES companies(id),
        name            TEXT    NOT NULL,
        license_no      TEXT    NOT NULL,
        license_state   TEXT    NOT NULL DEFAULT 'FL',
        license_type    TEXT    NOT NULL DEFAULT 'General Pest',
        license_expiry  TEXT    NOT NULL,
        email           TEXT,
        phone           TEXT,
        is_active       INTEGER NOT NULL DEFAULT 1,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now'))
    )""")

    # ── Chemical Application Logs ──────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS application_logs (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id          INTEGER REFERENCES companies(id),
        technician_id       INTEGER REFERENCES technicians(id),
        technician_name     TEXT,
        date_applied        TEXT    NOT NULL,
        date_logged         TEXT    NOT NULL DEFAULT (datetime('now')),
        pesticide_name      TEXT    NOT NULL,
        epa_reg_no          TEXT    NOT NULL,
        active_ingredient   TEXT,
        target_pest         TEXT    NOT NULL,
        application_site    TEXT    NOT NULL,
        site_address        TEXT    NOT NULL,
        amount_applied      REAL,
        unit                TEXT    DEFAULT 'oz',
        application_method  TEXT    DEFAULT 'Sprayer',
        weather_conditions  TEXT,
        temperature_f       REAL,
        wind_speed_mph      REAL,
        ppe_worn            TEXT,
        compliance_status   TEXT    NOT NULL DEFAULT 'pending',
        compliance_score    INTEGER DEFAULT 0,
        compliance_issues   TEXT    DEFAULT '[]',
        raw_input           TEXT,
        notes               TEXT,
        created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
    )""")

    # ── Compliance Alerts ──────────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS compliance_alerts (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id      INTEGER REFERENCES companies(id),
        alert_type      TEXT NOT NULL,
        severity        TEXT NOT NULL DEFAULT 'warning',
        entity_type     TEXT NOT NULL,
        entity_id       INTEGER,
        message         TEXT NOT NULL,
        resolved        INTEGER NOT NULL DEFAULT 0,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    )""")

    # ── Audit Report History ───────────────────────────────────────────────────
    c.execute("""
    CREATE TABLE IF NOT EXISTS audit_reports (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id      INTEGER REFERENCES companies(id),
        report_name     TEXT NOT NULL,
        date_from       TEXT NOT NULL,
        date_to         TEXT NOT NULL,
        technician_id   INTEGER,
        total_logs      INTEGER DEFAULT 0,
        compliant       INTEGER DEFAULT 0,
        violations      INTEGER DEFAULT 0,
        pdf_path        TEXT,
        created_at      TEXT NOT NULL DEFAULT (datetime('now'))
    )""")

    conn.commit()
    conn.close()
    print(f"[DB] Database ready at: {DB_PATH}")


# ── Helper queries ──────────────────────────────────────────────────────────────

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    return [dict(r) for r in rows]


def get_dashboard_stats(company_id=None):
    conn = get_conn()
    c = conn.cursor()
    stats = {}

    where_clause = ""
    params = ()
    if company_id:
        where_clause = "WHERE company_id=?"
        params = (company_id,)
        where_and = "AND company_id=?"
    else:
        where_and = ""

    stats["total_logs"] = c.execute(f"SELECT COUNT(*) FROM application_logs {where_clause}", params).fetchone()[0]
    stats["logs_this_month"] = c.execute(
        f"SELECT COUNT(*) FROM application_logs WHERE strftime('%Y-%m', date_applied) = strftime('%Y-%m', 'now') {where_and}", params
    ).fetchone()[0]
    stats["compliant"] = c.execute(
        f"SELECT COUNT(*) FROM application_logs WHERE compliance_status='compliant' {where_and}", params
    ).fetchone()[0]
    stats["violations"] = c.execute(
        f"SELECT COUNT(*) FROM application_logs WHERE compliance_status='violation' {where_and}", params
    ).fetchone()[0]
    stats["warnings"] = c.execute(
        f"SELECT COUNT(*) FROM application_logs WHERE compliance_status='warning' {where_and}", params
    ).fetchone()[0]
    stats["active_technicians"] = c.execute(
        f"SELECT COUNT(*) FROM technicians WHERE is_active=1 {where_and}", params
    ).fetchone()[0]

    # Licenses expiring in next 90 days
    stats["expiring_licenses"] = c.execute(f"""
        SELECT COUNT(*) FROM technicians
        WHERE is_active=1 AND date(license_expiry) BETWEEN date('now') AND date('now', '+90 days') {where_and}
    """, params).fetchone()[0]
    # Expired licenses
    stats["expired_licenses"] = c.execute(f"""
        SELECT COUNT(*) FROM technicians
        WHERE is_active=1 AND date(license_expiry) < date('now') {where_and}
    """, params).fetchone()[0]

    # Logs with late entry (> 14 days after application)
    stats["late_entries"] = c.execute(f"""
        SELECT COUNT(*) FROM application_logs
        WHERE julianday(date_logged) - julianday(date_applied) > 14 {where_and}
    """, params).fetchone()[0]

    stats["compliance_rate"] = (
        round(stats["compliant"] / max(stats["total_logs"], 1) * 100, 1)
    )

    conn.close()
    return stats
