from xml.sax.saxutils import escape

from app.core.config import get_settings


class TelephonyConfigurationError(RuntimeError):
    pass


def place_twilio_call(*, target_phone: str, clinic_name: str) -> str:
    settings = get_settings()
    credential = settings.twilio_api_secret.get_secret_value() or settings.twilio_auth_token.get_secret_value()
    username = settings.twilio_api_key or settings.twilio_account_sid
    if not settings.twilio_account_sid or not username or not credential or not settings.twilio_from_phone:
        raise TelephonyConfigurationError("Twilio credentials are not configured")

    try:
        from twilio.rest import Client
    except ImportError as exc:
        raise TelephonyConfigurationError("Twilio SDK is not installed") from exc

    client = Client(username, credential, settings.twilio_account_sid)
    safe_name = escape(clinic_name)
    twiml = (
        "<Response><Say>"
        f"Hello. This is a LeadPulse demonstration for {safe_name}. "
        "No appointment has been booked. Please contact the clinic to confirm availability."
        "</Say></Response>"
    )
    call = client.calls.create(to=target_phone, from_=settings.twilio_from_phone, twiml=twiml)
    return call.sid
