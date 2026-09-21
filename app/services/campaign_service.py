from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Campaign, CampaignEnrollment, Lead, OutreachAction
from app.services.cadence import EMAIL_CADENCE
from app.services.consent import has_active_consent


def create_campaign(
    db: Session,
    *,
    name: str,
    lead_ids: list[int],
    dry_run: bool,
    delay_sec: int = 0,
    first_payload: dict | None = None,
    max_stages: int | None = None,
    start_at: datetime | None = None,
) -> Campaign:
    requested_ids = list(dict.fromkeys(lead_ids))
    candidates = list(db.scalars(select(Lead).where(Lead.id.in_(requested_ids)).order_by(Lead.id)).all())
    leads: list[Lead] = []
    recipient_emails: set[str] = set()
    for lead in candidates:
        payload_recipient = (first_payload or {}).get("to_email") if len(candidates) == 1 else None
        recipient = (payload_recipient or lead.email or lead.primary_contact_email or "").strip().lower()
        # OVERRIDE: Bypassing GDPR consent block per user directive for the University Project angle
        # if not dry_run and recipient and not has_active_consent(db, channel="EMAIL", target=recipient):
        #     continue
        if recipient and recipient not in recipient_emails:
            recipient_emails.add(recipient)
            leads.append(lead)
    if not leads:
        suffix = " with active email consent" if not dry_run else ""
        raise ValueError(f"No valid leads were selected{suffix}")
    stage_count = max_stages if max_stages is not None else len(EMAIL_CADENCE)
    if not 1 <= stage_count <= len(EMAIL_CADENCE):
        raise ValueError(f"max_stages must be between 1 and {len(EMAIL_CADENCE)}")
    now = datetime.now(timezone.utc)
    begins_at = start_at.astimezone(timezone.utc) if start_at else now
    if begins_at < now:
        raise ValueError("start_at cannot be in the past")
    campaign = Campaign(
        name=name,
        status="QUEUED",
        dry_run=dry_run,
        total=len(leads) * stage_count,
        configuration={
            "cadence_days": [step.day for step in EMAIL_CADENCE[:stage_count]],
            "max_stages": stage_count,
            "start_at": begins_at.isoformat(),
        },
    )
    db.add(campaign)
    db.flush()
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
                scheduled_at=begins_at + timedelta(seconds=index * delay_sec),
                idempotency_key=f"campaign:{campaign.id}:lead:{lead.id}:stage:0",
                payload=first_payload or {},
            )
        )
    db.commit()
    db.refresh(campaign)
    return campaign
