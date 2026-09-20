from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

CADENCE_STAGES = (
    "day1_secret_shopper",
    "day2_linkedin_note",
    "day3_email_5min",
    "day5_web_form",
    "day7_direct_call",
    "day9_voice_memo",
    "booked_audit",
    "deal_won",
)


class PipelineStageUpdate(BaseModel):
    contact_id: int = Field(gt=0)
    stage: Literal[
        "day1_secret_shopper",
        "day2_linkedin_note",
        "day3_email_5min",
        "day5_web_form",
        "day7_direct_call",
        "day9_voice_memo",
        "booked_audit",
        "deal_won",
    ]
    completed_days: list[str] | None = None


class CallLogRequest(BaseModel):
    contact_id: int = Field(gt=0)
    call_status: str = Field(default="completed", min_length=1, max_length=64)
    call_notes: str = Field(default="", max_length=5000)
    rings: int | None = Field(default=None, ge=0, le=100)
    loss: str | None = Field(default=None, max_length=64)
    advance_stage: bool = False


class RouteCallRequest(BaseModel):
    target_phone: str = Field(min_length=7, max_length=32)
    clinic_name: str = Field(default="Clinic", min_length=1, max_length=255)
    clinic_phone: str = Field(default="", max_length=32)
    call_mode: Literal["mobile_bridge", "twilio", "vapi"] = "mobile_bridge"
    contact_id: int | None = Field(default=None, gt=0)

    @field_validator("target_phone", "clinic_phone")
    @classmethod
    def normalize_phone(cls, value: str) -> str:
        if not value:
            return value
        cleaned = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        if not cleaned.startswith("+") or not cleaned[1:].isdigit() or not 8 <= len(cleaned) <= 16:
            raise ValueError("phone number must be in E.164 format, e.g. +442071234567")
        return cleaned


class VoiceInquiryRequest(BaseModel):
    clinic_name: str = Field(default="Clinic", min_length=1, max_length=255)
    question: str = Field(min_length=1, max_length=2000)


class EmailSendRequest(BaseModel):
    lead_id: int = Field(gt=0)
    to_email: EmailStr
    cc_email: EmailStr | None = None
    subject: str = Field(min_length=1, max_length=998)
    body: str = Field(min_length=1, max_length=100_000)
    dry_run: bool = True

    @field_validator("subject")
    @classmethod
    def reject_header_injection(cls, value: str) -> str:
        if "\r" in value or "\n" in value:
            raise ValueError("subject must not contain line breaks")
        return value


class CampaignLaunchRequest(BaseModel):
    lead_ids: list[int] = Field(default_factory=list, max_length=5000)
    delay_sec: int = Field(default=30, ge=0, le=86_400)
    dry_run: bool = True
    limit: int = Field(default=20, ge=1, le=5000)
    name: str = Field(default="LeadPulse outreach", min_length=1, max_length=500)


class EnrichmentRequest(BaseModel):
    country: str = Field(default="GB", min_length=2, max_length=64)
    category: str = Field(default="dentist", min_length=1, max_length=100)
    limit: int = Field(default=15, ge=1, le=500)


class AgencySettingsUpdate(BaseModel):
    agency_name: str | None = Field(default=None, max_length=255)
    sender_name: str | None = Field(default=None, max_length=255)
    sender_email: EmailStr | None = None
    demo_inbound_phone: str | None = Field(default=None, max_length=32)
    calendly_url: str | None = Field(default=None, max_length=2000)
    default_setup_price: str | None = Field(default=None, max_length=64)
    default_retainer_price: str | None = Field(default=None, max_length=64)
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_from_phone: str | None = None
    vapi_api_key: str | None = None
    vapi_assistant_id: str | None = None


class SmtpConfigUpdate(BaseModel):
    smtp_user: EmailStr | None = None
    smtp_password: str | None = None
    sender_name: str | None = Field(default=None, max_length=255)


class SmtpTestRequest(BaseModel):
    smtp_user: EmailStr | None = None
    smtp_password: str | None = None
