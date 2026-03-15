"""
PestGuard AI — Cron Jobs
Scheduled tasks that run periodically via Tornado's PeriodicCallback.
"""

import os
import logging

logger = logging.getLogger(__name__)


async def check_and_send_license_alerts():
    """
    Check technician licenses for upcoming expiry and log/send alerts.
    Runs daily via PeriodicCallback in app.py.
    """
    try:
        from database import get_conn, rows_to_list
        from compliance_engine import check_license_alerts

        conn = get_conn()
        techs = rows_to_list(conn.execute(
            "SELECT * FROM technicians WHERE is_active=1"
        ).fetchall())
        conn.close()

        if not techs:
            return

        alerts = check_license_alerts(techs)

        if alerts:
            logger.info(f"License Alert Check: {len(alerts)} alert(s) found")
            for alert in alerts:
                if alert["severity"] in ("violation", "critical"):
                    logger.warning(f"[{alert['severity'].upper()}] {alert['message']}")
                    _send_alert_email(alert)
                else:
                    logger.info(f"[{alert['severity'].upper()}] {alert['message']}")
        else:
            logger.info("License Alert Check: All licenses current — no alerts")

    except Exception as e:
        logger.error(f"License alert check failed: {e}")


def _send_alert_email(alert: dict):
    """
    Send an email alert for a license issue.
    Configure ALERT_EMAIL and SMTP settings in .env to enable.
    """
    email = os.environ.get("ALERT_EMAIL")
    if not email:
        return

    logger.info(
        f"Would send email to {email}: "
        f"License alert for {alert['technician_name']} — {alert['message']}"
    )

    # Uncomment to enable real email via SMTP:
    # import smtplib
    # from email.mime.text import MIMEText
    # subject = f"PestGuard Alert: {alert['technician_name']} License Issue"
    # body = f"License Alert\n\n{alert['message']}\n\nTechnician: {alert['technician_name']}\n"
    # msg = MIMEText(body)
    # msg['Subject'] = subject
    # msg['From'] = os.environ.get("SMTP_FROM", "noreply@pestguard.ai")
    # msg['To'] = email
    # with smtplib.SMTP(os.environ.get("SMTP_HOST", "localhost"), int(os.environ.get("SMTP_PORT", 587))) as s:
    #     if os.environ.get("SMTP_USER"):
    #         s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASS"])
    #     s.sendmail(msg['From'], [email], msg.as_string())
