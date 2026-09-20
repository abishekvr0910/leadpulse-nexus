from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.schemas.api import AgencySettingsUpdate, SmtpConfigUpdate, SmtpTestRequest
from app.services.application_settings import get_overrides, save_overrides
from app.services.email_service import smtp_configured, test_smtp_connection

router = APIRouter(prefix="/api", tags=["settings"])
SECRET_FIELDS = {"twilio_account_sid", "twilio_auth_token", "twilio_from_phone", "vapi_api_key", "vapi_assistant_id"}


@router.get("/agency-settings")
def get_agency_settings(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    overrides = get_overrides(db)
    return {
        "agency_name": overrides.get("agency_name", settings.agency_name),
        "sender_name": overrides.get("sender_name", settings.sender_name),
        "sender_email": overrides.get("sender_email", settings.sender_email or settings.smtp_user),
        "demo_inbound_phone": overrides.get("demo_inbound_phone", settings.demo_inbound_phone),
        "calendly_url": overrides.get("calendly_url", settings.calendly_url),
        "default_setup_price": overrides.get("default_setup_price", settings.default_setup_price),
        "default_retainer_price": overrides.get("default_retainer_price", settings.default_retainer_price),
        "smtp_user": settings.smtp_user,
        "has_smtp_password": smtp_configured(),
        "twilio_from_phone": settings.twilio_from_phone,
        "has_twilio": bool(
            settings.twilio_account_sid and (settings.twilio_api_key or settings.twilio_auth_token.get_secret_value())
        ),
        "has_vapi": bool(settings.vapi_api_key.get_secret_value()),
    }


@router.post("/agency-settings")
def save_agency_settings(payload: AgencySettingsUpdate, db: Session = Depends(get_db)) -> dict:
    values = payload.model_dump(exclude_none=True)
    if SECRET_FIELDS.intersection(values):
        raise HTTPException(
            status_code=400,
            detail="Provider credentials must be updated as sealed Railway variables, not through the browser API",
        )
    save_overrides(db, values)
    return {"success": True, "message": "Non-secret agency settings saved"}


@router.get("/smtp-config")
def get_smtp_config(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    overrides = get_overrides(db)
    return {
        "smtp_user": settings.smtp_user,
        "sender_name": overrides.get("sender_name", settings.sender_name),
        "sender_email": overrides.get("sender_email", settings.sender_email or settings.smtp_user),
        "smtp_host": settings.smtp_host,
        "smtp_port": settings.smtp_port,
        "is_configured": smtp_configured(),
        "calendly_url": overrides.get("calendly_url", settings.calendly_url),
    }


@router.post("/smtp-config")
def save_smtp_config(payload: SmtpConfigUpdate, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    values = payload.model_dump(exclude_none=True)
    if ("smtp_user" in values or "smtp_password" in values) and settings.environment.lower() != "development":
        raise HTTPException(
            status_code=400,
            detail="SMTP credentials must be updated as sealed Railway variables",
        )
    if payload.sender_name:
        save_overrides(db, {"sender_name": payload.sender_name})
    return {
        "success": True,
        "message": "Sender name saved. Runtime credentials remain managed by environment variables.",
    }


@router.post("/test-smtp")
def test_smtp(payload: SmtpTestRequest | None = None) -> dict:
    settings = get_settings()
    if payload and payload.smtp_password and settings.environment.lower() != "development":
        raise HTTPException(status_code=400, detail="Do not send production SMTP credentials in request bodies")
    user = str(payload.smtp_user) if payload and payload.smtp_user else None
    password = payload.smtp_password if payload else None
    success, message = test_smtp_connection(user, password)
    return {"success": success, "message": message}
