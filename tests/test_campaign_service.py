from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, CampaignEnrollment, EmailEvent, Lead, OutreachAction
from app.services.campaign_service import create_campaign
from app.workers.tasks import campaigns as campaign_tasks
from app.workers.tasks.campaigns import _schedule_next


def make_session() -> Session:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return Session(engine, expire_on_commit=False)


def test_one_off_campaign_does_not_schedule_followups():
    with make_session() as db:
        lead = Lead(name="Test Clinic", email="owner@example.test")
        db.add(lead)
        db.commit()

        campaign = create_campaign(
            db,
            name="One-off",
            lead_ids=[lead.id],
            dry_run=True,
            max_stages=1,
        )
        enrollment = db.scalar(select(CampaignEnrollment))
        action = db.scalar(select(OutreachAction))
        assert enrollment is not None
        assert action is not None

        _schedule_next(db, action, enrollment, campaign)
        db.flush()

        assert campaign.total == 1
        assert enrollment.status == "COMPLETED"
        assert db.scalar(select(func.count(OutreachAction.id))) == 1


def test_full_campaign_tracks_all_available_templates():
    with make_session() as db:
        lead = Lead(name="Test Clinic", email="owner@example.test")
        db.add(lead)
        db.commit()

        campaign = create_campaign(
            db,
            name="Cadence",
            lead_ids=[lead.id],
            dry_run=True,
        )

        assert campaign.total == 3
        assert campaign.configuration == {"cadence_days": [0, 3, 7], "max_stages": 3}


def test_dry_run_worker_records_event_and_schedules_next_stage(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False, class_=Session)
    monkeypatch.setattr(campaign_tasks, "SessionLocal", factory)

    with factory() as db:
        lead = Lead(name="Test Clinic", email="owner@example.test")
        db.add(lead)
        db.commit()
        campaign = create_campaign(db, name="Dry run", lead_ids=[lead.id], dry_run=True)
        first_action = db.scalar(select(OutreachAction))
        assert first_action is not None
        action_id = first_action.id
        campaign_id = campaign.id

    result = campaign_tasks.dispatch_email_action.run(action_id)

    with factory() as db:
        actions = list(db.scalars(select(OutreachAction).order_by(OutreachAction.stage)))
        events = list(db.scalars(select(EmailEvent)))
        campaign = db.get(campaign_tasks.Campaign, campaign_id)
        assert result == {"status": "dry_run", "action_id": action_id}
        assert [action.status for action in actions] == ["DRY_RUN", "PENDING"]
        assert [event.event_type for event in events] == ["DRY_RUN"]
        assert campaign is not None
        assert campaign.sent == 1
        assert campaign.status == "RUNNING"
