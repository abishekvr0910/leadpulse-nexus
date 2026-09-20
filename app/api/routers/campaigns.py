from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignEnrollment, EmailEvent, Lead, OutreachAction
from app.db.session import get_db
from app.schemas.api import CampaignLaunchRequest
from app.services.campaign_service import create_campaign

router = APIRouter(prefix="/api/campaign", tags=["campaigns"])


@router.post("/auto-send", status_code=202)
def trigger_auto_campaign(payload: CampaignLaunchRequest, db: Session = Depends(get_db)) -> dict:
    lead_ids = payload.lead_ids
    if not lead_ids:
        lead_ids = list(
            db.scalars(
                select(Lead.id)
                .where(
                    Lead.is_email_verified.is_(True),
                    Lead.email.is_not(None),
                    Lead.email != "",
                    Lead.email_stage == "NONE",
                )
                .order_by(Lead.id)
                .limit(payload.limit)
            )
        )
    if not lead_ids:
        raise HTTPException(status_code=400, detail="No eligible leads found")
    try:
        campaign = create_campaign(
            db,
            name=payload.name,
            lead_ids=lead_ids,
            dry_run=payload.dry_run,
            delay_sec=payload.delay_sec,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "status": "queued",
        "campaign_id": campaign.id,
        "message": f"Campaign queued for {len(lead_ids)} prospects (Dry-run: {payload.dry_run})",
    }


@router.get("/status")
def get_campaign_status(campaign_id: int | None = None, db: Session = Depends(get_db)) -> dict:
    campaign = (
        db.get(Campaign, campaign_id)
        if campaign_id
        else db.scalar(select(Campaign).order_by(desc(Campaign.id)).limit(1))
    )
    if not campaign:
        return {"running": False, "sent": 0, "failed": 0, "total": 0, "current": "", "logs": []}
    events = list(
        db.scalars(
            select(EmailEvent)
            .join(OutreachAction, EmailEvent.action_id == OutreachAction.id)
            .join(CampaignEnrollment, OutreachAction.enrollment_id == CampaignEnrollment.id)
            .where(CampaignEnrollment.campaign_id == campaign.id)
            .order_by(desc(EmailEvent.id))
            .limit(50)
        )
    )
    logs = [
        f"{event.event_type}: lead #{event.lead_id}"
        + (f" ({event.detail.get('email')})" if event.detail.get("email") else "")
        for event in reversed(events)
    ]
    return {
        "campaign_id": campaign.id,
        "status": campaign.status,
        "running": campaign.status in {"QUEUED", "RUNNING"},
        "sent": campaign.sent,
        "failed": campaign.failed,
        "suppressed": campaign.suppressed,
        "total": campaign.total,
        "current": "",
        "logs": logs,
    }
