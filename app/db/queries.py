from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def rows(db: Session, statement: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return [dict(row) for row in db.execute(text(statement), params or {}).mappings().all()]


def row(db: Session, statement: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    result = db.execute(text(statement), params or {}).mappings().first()
    return dict(result) if result else None


def scalar(db: Session, statement: str, params: dict[str, Any] | None = None) -> Any:
    return db.execute(text(statement), params or {}).scalar()
