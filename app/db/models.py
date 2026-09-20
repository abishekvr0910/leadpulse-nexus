from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_country_category", "country", "category"),
        Index("ix_leads_email_stage", "email_stage"),
        Index("ix_leads_verified_email", "is_email_verified", "email"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    osm_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str | None] = mapped_column(String(255))
    category_pl: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(255))
    address: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(320))
    facebook_url: Mapped[str | None] = mapped_column(Text)
    instagram_url: Mapped[str | None] = mapped_column(Text)
    has_website: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    detected_website: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="NEW", server_default="NEW")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    email_stage: Mapped[str] = mapped_column(String(64), default="NONE", server_default="NONE")
    initial_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    followup1_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    followup2_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reply_received: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    reply_type: Mapped[str] = mapped_column(String(64), default="", server_default="")
    reply_notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    reply_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    template_used: Mapped[str] = mapped_column(String(255), default="", server_default="")
    country: Mapped[str] = mapped_column(String(255), default="Poland", server_default="Poland")
    country_code: Mapped[str] = mapped_column(String(8), default="PL", server_default="PL")
    language: Mapped[str] = mapped_column(String(16), default="pl", server_default="pl")
    currency: Mapped[str] = mapped_column(String(8), default="PLN", server_default="PLN")
    avg_revenue_eur: Mapped[int] = mapped_column(Integer, default=800, server_default="800")
    primary_contact_name: Mapped[str] = mapped_column(String(500), default="", server_default="")
    primary_contact_title: Mapped[str] = mapped_column(String(500), default="", server_default="")
    primary_contact_email: Mapped[str] = mapped_column(String(320), default="", server_default="")
    primary_contact_linkedin: Mapped[str] = mapped_column(Text, default="", server_default="")
    company_reg_number: Mapped[str] = mapped_column(String(255), default="", server_default="")
    contacts_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    email_verification_status: Mapped[str] = mapped_column(String(64), default="UNCHECKED", server_default="UNCHECKED")
    email_mx_host: Mapped[str] = mapped_column(String(500), default="", server_default="")
    cadence_stage: Mapped[str] = mapped_column(String(64), default="unassigned", server_default="unassigned")
    call_status: Mapped[str] = mapped_column(String(64), default="not_called", server_default="not_called")
    call_notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompanyContact(Base):
    __tablename__ = "company_contacts"
    __table_args__ = (
        Index("ix_contacts_lead", "lead_id"),
        Index("ix_contacts_cadence_stage", "cadence_stage"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"))
    company_name: Mapped[str | None] = mapped_column(String(500))
    person_name: Mapped[str | None] = mapped_column(String(500))
    role_title: Mapped[str | None] = mapped_column(String(500))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(Text)
    company_registration: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    email_verification_status: Mapped[str] = mapped_column(String(64), default="UNCHECKED", server_default="UNCHECKED")
    email_mx_host: Mapped[str] = mapped_column(String(500), default="", server_default="")
    company_number: Mapped[str | None] = mapped_column(String(255))
    registered_office: Mapped[str | None] = mapped_column(Text)
    whatsapp_url: Mapped[str | None] = mapped_column(Text)
    linkedin_note: Mapped[str | None] = mapped_column(Text)
    dossier_data: Mapped[str | None] = mapped_column(Text)
    cadence_stage: Mapped[str] = mapped_column(
        String(64), default="day1_secret_shopper", server_default="day1_secret_shopper"
    )
    cadence_completed_days: Mapped[list] = mapped_column(JSON, default=list)
    call_status: Mapped[str] = mapped_column(String(64), default="not_called", server_default="not_called")
    call_notes: Mapped[str] = mapped_column(Text, default="", server_default="")
    last_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    secret_shopper_rings: Mapped[int] = mapped_column(Integer, default=7, server_default="7")
    secret_shopper_time: Mapped[str] = mapped_column(String(64), default="", server_default="")
    secret_shopper_loss: Mapped[str] = mapped_column(String(64), default="", server_default="")


class ApplicationSetting(Base):
    __tablename__ = "application_settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(Text, default="", server_default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(64), default="QUEUED", server_default="QUEUED", index=True)
    dry_run: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    total: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    sent: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    failed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    suppressed: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    configuration: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CampaignEnrollment(Base):
    __tablename__ = "campaign_enrollments"
    __table_args__ = (UniqueConstraint("campaign_id", "lead_id", name="uq_campaign_lead"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey("campaigns.id", ondelete="CASCADE"), index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(64), default="ACTIVE", server_default="ACTIVE")
    current_stage: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    stopped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    stop_reason: Mapped[str | None] = mapped_column(String(255))


class OutreachAction(Base):
    __tablename__ = "outreach_actions"
    __table_args__ = (
        UniqueConstraint("enrollment_id", "stage", name="uq_enrollment_stage"),
        Index("ix_actions_due", "status", "scheduled_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    enrollment_id: Mapped[int] = mapped_column(ForeignKey("campaign_enrollments.id", ondelete="CASCADE"), index=True)
    lead_id: Mapped[int] = mapped_column(ForeignKey("leads.id", ondelete="CASCADE"), index=True)
    stage: Mapped[int] = mapped_column(Integer)
    channel: Mapped[str] = mapped_column(String(32), default="EMAIL", server_default="EMAIL")
    template_key: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(64), default="PENDING", server_default="PENDING", index=True)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    provider_message_id: Mapped[str | None] = mapped_column(String(500))
    idempotency_key: Mapped[str] = mapped_column(String(500), unique=True)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EmailEvent(Base):
    __tablename__ = "email_events"
    __table_args__ = (Index("ix_email_events_action_created", "action_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    action_id: Mapped[int | None] = mapped_column(ForeignKey("outreach_actions.id", ondelete="SET NULL"))
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(64))
    provider_message_id: Mapped[str | None] = mapped_column(String(500))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Suppression(Base):
    __tablename__ = "suppression_list"

    id: Mapped[int] = mapped_column(primary_key=True)
    normalized_email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    reason: Mapped[str] = mapped_column(String(255))
    source: Mapped[str] = mapped_column(String(255), default="operator", server_default="operator")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobRun(Base):
    __tablename__ = "job_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    kind: Mapped[str] = mapped_column(String(100), index=True)
    celery_task_id: Mapped[str | None] = mapped_column(String(255), index=True)
    status: Mapped[str] = mapped_column(String(64), default="QUEUED", server_default="QUEUED")
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    progress: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_created_action", "created_at", "action"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    actor: Mapped[str] = mapped_column(String(255), default="system", server_default="system")
    action: Mapped[str] = mapped_column(String(255))
    resource_type: Mapped[str | None] = mapped_column(String(255))
    resource_id: Mapped[str | None] = mapped_column(String(255))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProviderWebhookEvent(Base):
    __tablename__ = "provider_webhook_events"
    __table_args__ = (UniqueConstraint("provider", "provider_event_id", name="uq_provider_event"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    provider: Mapped[str] = mapped_column(String(100))
    provider_event_id: Mapped[str] = mapped_column(String(500))
    event_type: Mapped[str | None] = mapped_column(String(100))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
