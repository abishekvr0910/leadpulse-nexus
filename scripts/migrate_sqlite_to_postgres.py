"""Copy legacy SQLite lead/contact data into the configured PostgreSQL database."""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from sqlalchemy import JSON, Boolean, DateTime, text

from app.db.models import CompanyContact, Lead
from app.db.session import SessionLocal, engine


def convert_value(column, value):
    if value is None:
        return None
    if isinstance(column.type, Boolean):
        return bool(value)
    if isinstance(column.type, DateTime) and isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(column.type, JSON) and isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [] if column.name == "cadence_completed_days" else {}
    return value


def mapped_rows(connection: sqlite3.Connection, table: str, model) -> list[dict]:
    source_columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
    columns = [column for column in model.__table__.columns if column.name in source_columns]
    names = [column.name for column in columns]
    quoted_names = ", ".join(f'"{name}"' for name in names)
    output = []
    for source_row in connection.execute(f'SELECT {quoted_names} FROM "{table}" ORDER BY id'):
        output.append(
            {column.name: convert_value(column, value) for column, value in zip(columns, source_row, strict=True)}
        )
    return output


def import_model(model, records: list[dict], batch_size: int) -> int:
    imported = 0
    with SessionLocal() as session:
        for record in records:
            session.merge(model(**record))
            imported += 1
            if imported % batch_size == 0:
                session.commit()
        session.commit()
    return imported


def reset_postgres_sequences() -> None:
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as connection:
        for table in ("leads", "company_contacts"):
            connection.execute(
                text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM {table}), 1), true)"
                )
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("leads.db"))
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.source.exists():
        parser.error(f"SQLite source does not exist: {args.source}")
    if engine.dialect.name != "postgresql" and not args.dry_run:
        parser.error("DATABASE_URL must point to PostgreSQL for a real import")

    source = sqlite3.connect(args.source)
    try:
        leads = mapped_rows(source, "leads", Lead)
        contacts = mapped_rows(source, "company_contacts", CompanyContact)
    finally:
        source.close()

    print(f"source={args.source} leads={len(leads)} contacts={len(contacts)} dry_run={args.dry_run}")
    if args.dry_run:
        return 0
    lead_count = import_model(Lead, leads, args.batch_size)
    contact_count = import_model(CompanyContact, contacts, args.batch_size)
    reset_postgres_sequences()
    print(f"imported_leads={lead_count} imported_contacts={contact_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
