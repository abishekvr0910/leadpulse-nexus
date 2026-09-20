from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ApplicationSetting

NON_SECRET_KEYS = {
    "agency_name",
    "sender_name",
    "sender_email",
    "demo_inbound_phone",
    "calendly_url",
    "default_setup_price",
    "default_retainer_price",
}


def get_overrides(db: Session) -> dict[str, str]:
    rows = db.scalars(select(ApplicationSetting)).all()
    return {row.key: row.value for row in rows}


def save_overrides(db: Session, values: dict[str, str | None]) -> None:
    for key, value in values.items():
        if key not in NON_SECRET_KEYS or value is None:
            continue
        row = db.get(ApplicationSetting, key)
        if row:
            row.value = str(value).strip()
        else:
            db.add(ApplicationSetting(key=key, value=str(value).strip()))
    db.commit()
