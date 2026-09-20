import smtplib
from datetime import datetime, timedelta, timezone
from email.utils import make_msgid

from celery.utils.log import get_task_logger
from sqlalchemy import and_, func, or_, select

from app.core.config import get_settings
from app.db.models import (
    Campaign,
    CampaignEnrollment,
    EmailEvent,
    Lead,
    OutreachAction,
    Suppression,
)
from app.db.session import SessionLocal
from app.services.application_settings import get_overrides
from app.services.cadence import EMAIL_CADENCE, get_step
from app.services.email_service import send_email
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)
FINAL_ACTION_STATUSES = {"SENT", "DRY_RUN", "FAILED", "SUPPRESSED", "UNKNOWN"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _render(action: OutreachAction, lead: Lead, sender: dict[str, str]) -> tuple[str, str, str, str | None]:
    payload = action.payload or {}
    to_email = payload.get("to_email") or lead.primary_contact_email or lead.email
    cc_email = payload.get("cc_email") or None
    if payload.get("subject") and payload.get("body"):
        return to_email, payload["subject"], payload["body"], cc_email

    from email_templates import render_email

    rendered = render_email(
        {
            "id": lead.id,
            "name": lead.name,
            "city": lead.city,
            "country": lead.country,
            "category": lead.category,
            "email": lead.email,
            "primary_contact_email": lead.primary_contact_email,
            "primary_contact_name": lead.primary_contact_name,
        },
        template_key=action.template_key,
        sender_name=sender["name"],
        sender_email=sender["email"],
        sender_phone=sender["phone"],
        calendly_link=sender["calendly_url"],
    )
    return to_email, rendered["subject"], rendered["body"], cc_email


def _finish_campaign_if_done(db, campaign: Campaign) -> None:
    remaining = db.scalar(
        select(func.count(OutreachAction.id))
        .join(CampaignEnrollment, OutreachAction.enrollment_id == CampaignEnrollment.id)
        .where(CampaignEnrollment.campaign_id == campaign.id, OutreachAction.status.not_in(FINAL_ACTION_STATUSES))
    )
    if not remaining:
        campaign.status = "COMPLETED"
        campaign.completed_at = _utcnow()


def _schedule_next(db, action: OutreachAction, enrollment: CampaignEnrollment, campaign: Campaign) -> None:
    next_stage = action.stage + 1
    max_stages = int((campaign.configuration or {}).get("max_stages", len(EMAIL_CADENCE)))
    if next_stage >= max_stages or enrollment.status != "ACTIVE":
        enrollment.status = "COMPLETED"
        return
    current_step = get_step(action.stage)
    step = get_step(next_stage)
    if db.scalar(
        select(OutreachAction.id).where(
            OutreachAction.enrollment_id == enrollment.id,
            OutreachAction.stage == next_stage,
        )
    ):
        return
    scheduled_at = _utcnow() + timedelta(days=step.day - current_step.day)
    db.add(
        OutreachAction(
            enrollment_id=enrollment.id,
            lead_id=action.lead_id,
            stage=next_stage,
            channel="EMAIL",
            template_key=step.template_key,
            status="PENDING",
            scheduled_at=scheduled_at,
            idempotency_key=f"campaign:{campaign.id}:lead:{action.lead_id}:stage:{next_stage}",
            payload={},
        )
    )
    enrollment.current_stage = next_stage


@celery_app.task(name="leadpulse.dispatch_email_action", bind=True, acks_late=True, max_retries=3)
def dispatch_email_action(self, action_id: int) -> dict:
    with SessionLocal() as db:
        action = db.scalar(select(OutreachAction).where(OutreachAction.id == action_id).with_for_update())
        if not action or action.status in FINAL_ACTION_STATUSES or action.status == "SENDING":
            return {"status": "ignored", "action_id": action_id}
        enrollment = db.get(CampaignEnrollment, action.enrollment_id)
        campaign = db.get(Campaign, enrollment.campaign_id) if enrollment else None
        lead = db.get(Lead, action.lead_id)
        if not enrollment or not campaign or not lead:
            action.status = "FAILED"
            action.last_error = "Related campaign, enrollment, or lead no longer exists"
            action.finished_at = _utcnow()
            db.commit()
            return {"status": "failed", "action_id": action_id}
        action.status = "SENDING"
        action.started_at = _utcnow()
        action.attempt_count += 1
        campaign.status = "RUNNING"
        campaign.started_at = campaign.started_at or _utcnow()
        db.commit()

    with SessionLocal() as db:
        action = db.get(OutreachAction, action_id)
        enrollment = db.get(CampaignEnrollment, action.enrollment_id)
        campaign = db.get(Campaign, enrollment.campaign_id)
        lead = db.get(Lead, action.lead_id)
        try:
            runtime = get_settings()
            overrides = get_overrides(db)
            sender = {
                "name": overrides.get("sender_name", runtime.sender_name),
                "email": overrides.get("sender_email", runtime.sender_email or runtime.smtp_user),
                "phone": runtime.sender_phone,
                "calendly_url": overrides.get("calendly_url", runtime.calendly_url),
            }
            to_email, subject, body, cc_email = _render(action, lead, sender)
            if not to_email:
                raise ValueError("Lead has no deliverable email address")
            normalized = to_email.strip().lower()
            if db.scalar(select(Suppression.id).where(Suppression.normalized_email == normalized)):
                action.status = "SUPPRESSED"
                action.finished_at = _utcnow()
                campaign.suppressed += 1
                enrollment.status = "STOPPED"
                enrollment.stop_reason = "suppressed"
                enrollment.stopped_at = _utcnow()
                db.add(
                    EmailEvent(
                        action_id=action.id, lead_id=lead.id, event_type="SUPPRESSED", detail={"email": normalized}
                    )
                )
            elif campaign.dry_run:
                action.status = "DRY_RUN"
                action.finished_at = _utcnow()
                campaign.sent += 1
                db.add(
                    EmailEvent(action_id=action.id, lead_id=lead.id, event_type="DRY_RUN", detail={"email": normalized})
                )
                _schedule_next(db, action, enrollment, campaign)
            else:
                domain = sender["email"].split("@")[-1]
                deterministic_id = make_msgid(idstring=action.idempotency_key.replace(":", "."), domain=domain)
                provider_id = send_email(
                    to_email=to_email,
                    cc_email=cc_email,
                    subject=subject,
                    body=body,
                    message_id=deterministic_id,
                    sender_name=sender["name"],
                    sender_email=sender["email"],
                )
                action.status = "SENT"
                action.provider_message_id = provider_id
                action.finished_at = _utcnow()
                campaign.sent += 1
                step = get_step(action.stage)
                lead.email_stage = step.resulting_email_stage
                lead.status = "CONTACTED"
                lead.contacted_at = _utcnow()
                lead.last_contacted_at = _utcnow()
                if action.stage == 0:
                    lead.initial_sent_at = _utcnow()
                elif action.stage == 1:
                    lead.followup1_sent_at = _utcnow()
                elif action.stage == 2:
                    lead.followup2_sent_at = _utcnow()
                db.add(
                    EmailEvent(
                        action_id=action.id,
                        lead_id=lead.id,
                        event_type="SENT",
                        provider_message_id=provider_id,
                        detail={"email": normalized},
                    )
                )
                _schedule_next(db, action, enrollment, campaign)
            _finish_campaign_if_done(db, campaign)
            db.commit()
            return {"status": action.status.lower(), "action_id": action.id}
        except Exception as exc:
            logger.exception("Email action %s failed", action_id)
            if isinstance(exc, (OSError, smtplib.SMTPException)) and self.request.retries < self.max_retries:
                action.status = "QUEUED"
                action.last_error = f"Transient {type(exc).__name__}; retry scheduled"
                action.started_at = None
                db.commit()
                raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
            action.status = "FAILED"
            action.last_error = f"{type(exc).__name__}: {str(exc)[:500]}"
            action.finished_at = _utcnow()
            campaign.failed += 1
            db.add(
                EmailEvent(
                    action_id=action.id, lead_id=lead.id, event_type="FAILED", detail={"error_type": type(exc).__name__}
                )
            )
            _finish_campaign_if_done(db, campaign)
            db.commit()
            return {"status": "failed", "action_id": action.id}


@celery_app.task(name="leadpulse.queue_due_actions")
def queue_due_actions(batch_size: int = 100) -> dict:
    queued_ids: list[int] = []
    with SessionLocal() as db:
        stale_before = _utcnow() - timedelta(minutes=15)
        stale_actions = list(
            db.scalars(
                select(OutreachAction).where(
                    or_(
                        and_(OutreachAction.status == "QUEUED", OutreachAction.locked_at < stale_before),
                        and_(OutreachAction.status == "SENDING", OutreachAction.started_at < stale_before),
                    )
                )
            )
        )
        for stale_action in stale_actions:
            stale_action.status = "PENDING"
            stale_action.locked_at = None
            stale_action.started_at = None

        statement = (
            select(OutreachAction)
            .where(
                OutreachAction.status == "PENDING",
                OutreachAction.channel == "EMAIL",
                OutreachAction.scheduled_at <= _utcnow(),
            )
            .order_by(OutreachAction.scheduled_at)
            .limit(batch_size)
        )
        if db.bind and db.bind.dialect.name == "postgresql":
            statement = statement.with_for_update(skip_locked=True)
        actions = list(db.scalars(statement))
        for action in actions:
            action.status = "QUEUED"
            action.locked_at = _utcnow()
            queued_ids.append(action.id)
        db.commit()

    for action_id in queued_ids:
        try:
            dispatch_email_action.delay(action_id)
        except Exception:
            logger.exception("Unable to publish action %s", action_id)
            with SessionLocal() as db:
                action = db.get(OutreachAction, action_id)
                if action and action.status == "QUEUED":
                    action.status = "PENDING"
                    action.locked_at = None
                    db.commit()
    return {"queued": len(queued_ids)}
