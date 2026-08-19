"""Email sending with SMTP (SendGrid compatible). Falls back to console logging."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html: str, text: str = "") -> bool:
    if not settings.SMTP_HOST:
        logger.info("[EMAIL] to=%s subject=%s", to, subject)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SENDER_EMAIL
        msg["To"] = to
        msg.attach(MIMEText(text or "See HTML", "plain"))
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SENDER_EMAIL, [to], msg.as_string())
        return True
    except Exception as exc:
        logger.error("Email send failed to %s: %s", to, exc)
        return False


def notify_email(user_email: str, subject: str, headline: str, body: str, cta_url: str = "", cta_label: str = "") -> None:
    cta_html = f'<a href="{cta_url}" style="display:inline-block;margin-top:16px;padding:12px 28px;background:#c5a059;color:#000;font-weight:700;border-radius:6px;text-decoration:none">{cta_label}</a>' if cta_url else ""
    html = f"""
    <div style="font-family:Outfit,Arial,sans-serif;background:#0d0d0d;padding:32px;color:#fff">
      <div style="max-width:520px;margin:0 auto;border:1px solid rgba(197,160,89,.3);border-radius:12px;padding:32px;background:#050505">
        <div style="font-size:22px;font-weight:800;color:#c5a059;margin-bottom:16px">DROPIFY</div>
        <h2 style="margin:0 0 12px">{headline}</h2>
        <p style="color:rgba(255,255,255,.75);line-height:1.6">{body}</p>
        {cta_html}
        <p style="color:rgba(255,255,255,.35);font-size:12px;margin-top:28px">You are receiving this because you use the DROPIFY marketplace.</p>
      </div>
    </div>
    """
    send_email(user_email, subject, html)
