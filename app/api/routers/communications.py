from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import CompanyContact, Lead
from app.db.session import get_db
from app.schemas.api import EmailSendRequest, RouteCallRequest, VoiceInquiryRequest
from app.services.campaign_service import create_campaign
from app.services.telephony_service import (
    TelephonyConfigurationError,
    place_twilio_call,
)

router = APIRouter(prefix="/api", tags=["communications"])


@router.post("/send-email", status_code=202)
def queue_email(payload: EmailSendRequest, db: Session = Depends(get_db)) -> dict:
    lead = db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    campaign = create_campaign(
        db,
        name=f"One-off email to {lead.name}",
        lead_ids=[lead.id],
        dry_run=payload.dry_run,
        first_payload={
            "to_email": str(payload.to_email),
            "cc_email": str(payload.cc_email) if payload.cc_email else None,
            "subject": payload.subject,
            "body": payload.body,
        },
        max_stages=1,
    )
    return {
        "success": True,
        "campaign_id": campaign.id,
        "message": f"{'[DRY-RUN] ' if payload.dry_run else ''}Email queued for {payload.to_email}",
    }


@router.post("/route-call")
def route_call(payload: RouteCallRequest, db: Session = Depends(get_db)) -> dict:
    mode = "browser_dialer"
    call_id = f"local_{int(datetime.now(timezone.utc).timestamp())}"
    if payload.call_mode == "twilio":
        try:
            call_id = place_twilio_call(target_phone=payload.target_phone, clinic_name=payload.clinic_name)
            mode = "twilio_live_carrier"
        except TelephonyConfigurationError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Twilio call failed: {type(exc).__name__}") from exc
    elif payload.call_mode == "vapi":
        raise HTTPException(status_code=501, detail="Vapi dispatch is not implemented; no simulated call was recorded")

    if payload.contact_id:
        contact = db.get(CompanyContact, payload.contact_id)
        if contact:
            contact.call_status = "test_routed"
            contact.call_notes = f"Routed test call to {payload.target_phone}"
            contact.last_action_at = datetime.now(timezone.utc)
            db.commit()
    return {
        "success": True,
        "mode": mode,
        "target_phone": payload.target_phone,
        "clinic_name": payload.clinic_name,
        "clinic_phone": payload.clinic_phone,
        "tel_url": f"tel:{payload.target_phone}",
        "call_id": call_id,
        "message": f"Call route prepared for {payload.target_phone}",
        "has_live_carrier": mode == "twilio_live_carrier",
    }


@router.post("/voice-inquiry")
def voice_inquiry(payload: VoiceInquiryRequest) -> dict:
    question = payload.question.lower()
    if any(word in question for word in ("pain", "emergency", "bleeding", "abscess", "swelling")):
        intent = "emergency"
        reply = (
            f"If this may be a medical emergency, contact emergency services or {payload.clinic_name} directly. "
            "I cannot assess symptoms or confirm an appointment from this demonstration."
        )
    elif any(word in question for word in ("book", "appointment", "slot", "schedule")):
        intent = "booking"
        reply = (
            f"I can collect a booking request for {payload.clinic_name}, "
            "but availability must be confirmed by the clinic."
        )
    elif any(word in question for word in ("price", "cost", "fee")):
        intent = "pricing"
        reply = (
            f"Please contact {payload.clinic_name} for current pricing; "
            "this demonstration does not have verified fee data."
        )
    else:
        intent = "general"
        reply = (
            f"This is the {payload.clinic_name} demonstration assistant. I can collect a callback or booking request."
        )
    return {"success": True, "clinic_name": payload.clinic_name, "reply": reply, "intent": intent}
