from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignEnrollment, Lead, OutreachAction
from app.services.cadence import EMAIL_CADENCE


def create_campaign(
    db: Session,
    *,
    name: str,
    lead_ids: list[int],
    dry_run: bool,
    delay_sec: int = 0,
    first_payload: dict | None = None,
    max_stages: int | None = None,
) -> Campaign:
    leads = list(db.scalars(select(Lead).where(Lead.id.in_(lead_ids))).all())
    if not leads:
        raise ValueError("No valid leads were selected")
    stage_count = max_stages if max_stages is not None else len(EMAIL_CADENCE)
    if not 1 <= stage_count <= len(EMAIL_CADENCE):
        raise ValueError(f"max_stages must be between 1 and {len(EMAIL_CADENCE)}")
    campaign = Campaign(
        name=name,
        status="QUEUED",
        dry_run=dry_run,
        total=len(leads) * stage_count,
        configuration={
            "cadence_days": [step.day for step in EMAIL_CADENCE[:stage_count]],
            "max_stages": stage_count,
        },
    )
    db.add(campaign)
    db.flush()
    now = datetime.now(timezone.utc)
    first_step = EMAIL_CADENCE[0]
    for index, lead in enumerate(leads):
        enrollment = CampaignEnrollment(campaign_id=campaign.id, lead_id=lead.id, status="ACTIVE", current_stage=0)
        db.add(enrollment)
        db.flush()
        db.add(
            OutreachAction(
                enrollment_id=enrollment.id,
                lead_id=lead.id,
                stage=0,
                channel="EMAIL",
                template_key=first_step.template_key,
                status="PENDING",
                scheduled_at=now + timedelta(seconds=index * delay_sec),
                idempotency_key=f"campaign:{campaign.id}:lead:{lead.id}:stage:0",
                payload=first_payload or {},
            )
        )
    db.commit()
    db.refresh(campaign)
    return campaign
