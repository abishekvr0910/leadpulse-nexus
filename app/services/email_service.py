import smtplib
from email.message import EmailMessage
from email.utils import make_msgid

from app.core.config import get_settings


class EmailConfigurationError(RuntimeError):
    pass


def smtp_configured() -> bool:
    settings = get_settings()
    return bool(settings.smtp_user and settings.smtp_password.get_secret_value())


def test_smtp_connection(user: str | None = None, password: str | None = None) -> tuple[bool, str]:
    settings = get_settings()
    smtp_user = user or settings.smtp_user
    smtp_password = password or settings.smtp_password.get_secret_value()
    if not smtp_user or not smtp_password:
        return False, "SMTP credentials are not configured"
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as client:
            client.ehlo()
            client.starttls()
            client.ehlo()
            client.login(smtp_user, smtp_password.replace(" ", ""))
        return True, "SMTP authentication succeeded"
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP authentication failed"
    except (OSError, smtplib.SMTPException) as exc:
        return False, f"SMTP connection failed: {type(exc).__name__}"


def send_email(
    *,
    to_email: str,
    subject: str,
    body: str,
    cc_email: str | None = None,
    message_id: str | None = None,
    sender_name: str | None = None,
    sender_email: str | None = None,
) -> str:
    settings = get_settings()
    password = settings.smtp_password.get_secret_value()
    if not settings.smtp_user or not password:
        raise EmailConfigurationError("SMTP credentials are not configured")

    msg = EmailMessage()
    msg["Subject"] = subject
    from_name = sender_name or settings.sender_name
    from_email = sender_email or settings.sender_email or settings.smtp_user
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email
    if cc_email and cc_email.lower() != to_email.lower():
        msg["Cc"] = cc_email
    msg["Reply-To"] = from_email
    msg["Message-ID"] = message_id or make_msgid(domain=from_email.split("@")[-1])
    msg.set_content(body)

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as client:
        client.ehlo()
        client.starttls()
        client.ehlo()
        client.login(settings.smtp_user, password.replace(" ", ""))
        client.send_message(msg)
    return msg["Message-ID"]
