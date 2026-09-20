import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import CompanyContact
from app.db.queries import row, rows
from app.db.session import get_db
from app.schemas.api import CallLogRequest, PipelineStageUpdate
from app.services.application_settings import get_overrides

router = APIRouter(prefix="/api", tags=["contacts", "pipeline"])

STAGE_FLOW = {
    "day1_secret_shopper": "day2_linkedin_note",
    "day2_linkedin_note": "day3_email_5min",
    "day3_email_5min": "day5_web_form",
    "day5_web_form": "day7_direct_call",
    "day7_direct_call": "day9_voice_memo",
    "day9_voice_memo": "booked_audit",
    "booked_audit": "deal_won",
}
STAGE_KEYS = tuple(STAGE_FLOW) + ("deal_won",)


def _completed_days(value) -> list[str]:
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value:
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


@router.get("/decision-makers")
def get_decision_makers(
    search: str | None = Query(default=None, max_length=255),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    where = ""
    params: dict = {"limit": limit}
    if search:
        where = """
        WHERE LOWER(cc.person_name) LIKE :search OR LOWER(cc.company_name) LIKE :search
           OR LOWER(cc.role_title) LIKE :search OR LOWER(l.city) LIKE :search OR LOWER(l.country) LIKE :search
        """
        params["search"] = f"%{search.lower()}%"
    contacts = rows(
        db,
        f"""
        SELECT cc.id, cc.lead_id, cc.company_name, cc.person_name, cc.role_title,
               cc.email AS contact_email, cc.phone AS contact_phone, cc.linkedin_url,
               cc.company_registration, cc.created_at, cc.company_number, cc.registered_office,
               cc.whatsapp_url, cc.linkedin_note, cc.dossier_data,
               l.city, l.country, l.category, l.phone AS company_phone, l.email AS company_email,
               l.has_website, l.detected_website
        FROM company_contacts cc LEFT JOIN leads l ON cc.lead_id = l.id
        {where} ORDER BY cc.id DESC LIMIT :limit
        """,
        params,
    )
    return {"contacts": contacts, "count": len(contacts)}


@router.get("/decision-makers/{contact_id}/dossier")
def get_contact_dossier(contact_id: int, db: Session = Depends(get_db)) -> dict:
    item = row(
        db,
        """
        SELECT cc.*, l.city, l.country, l.category, l.phone AS company_phone,
               l.email AS company_email, l.detected_website, l.address
        FROM company_contacts cc JOIN leads l ON cc.lead_id = l.id WHERE cc.id = :contact_id
        """,
        {"contact_id": contact_id},
    )
    if not item:
        raise HTTPException(status_code=404, detail="Contact not found")
    if item.get("dossier_data"):
        try:
            return json.loads(item["dossier_data"])
        except (TypeError, json.JSONDecodeError):
            pass
    from osint_dossier import build_dossier_for_contact

    lead = {
        "name": item["company_name"],
        "city": item["city"],
        "country": item["country"],
        "category": item["category"],
        "phone": item["company_phone"],
        "email": item["company_email"],
    }
    return build_dossier_for_contact(item, lead)


@router.get("/pipeline")
def get_pipeline(search: str | None = Query(default=None, max_length=255), db: Session = Depends(get_db)) -> dict:
    where = ""
    params: dict = {}
    if search:
        where = """
        WHERE LOWER(cc.person_name) LIKE :search OR LOWER(cc.company_name) LIKE :search
           OR LOWER(cc.role_title) LIKE :search OR LOWER(l.city) LIKE :search OR LOWER(l.country) LIKE :search
        """
        params["search"] = f"%{search.lower()}%"
    result = rows(
        db,
        f"""
        SELECT cc.id, cc.lead_id, cc.company_name, cc.person_name, cc.role_title,
               cc.email AS contact_email, cc.phone AS contact_phone, cc.linkedin_url,
               cc.company_registration, cc.company_number, cc.registered_office,
               cc.whatsapp_url, cc.linkedin_note, cc.cadence_stage, cc.cadence_completed_days,
               cc.call_status, cc.call_notes, cc.secret_shopper_rings, cc.secret_shopper_time,
               cc.secret_shopper_loss, l.city, l.country, l.category,
               l.phone AS company_phone, l.email AS company_email, l.detected_website
        FROM company_contacts cc LEFT JOIN leads l ON cc.lead_id = l.id
        {where} ORDER BY cc.id DESC
        """,
        params,
    )
    grouped = {key: [] for key in STAGE_KEYS}
    grouped["other"] = []
    for item in result:
        item["completed_days"] = _completed_days(item.pop("cadence_completed_days", None))
        grouped.get(item.get("cadence_stage") or "day1_secret_shopper", grouped["other"]).append(item)
    return {"pipeline": grouped, "counts": {key: len(value) for key, value in grouped.items()}, "total": len(result)}


@router.post("/pipeline/update-stage")
def update_pipeline_stage(payload: PipelineStageUpdate, db: Session = Depends(get_db)) -> dict:
    contact = db.get(CompanyContact, payload.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact.cadence_stage = payload.stage
    if payload.completed_days is not None:
        contact.cadence_completed_days = payload.completed_days
    db.commit()
    return {"success": True, "contact_id": contact.id, "new_stage": contact.cadence_stage}


@router.post("/pipeline/log-call")
def log_pipeline_call(payload: CallLogRequest, db: Session = Depends(get_db)) -> dict:
    contact = db.get(CompanyContact, payload.contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    current = contact.cadence_stage or "day1_secret_shopper"
    completed = _completed_days(contact.cadence_completed_days)
    if payload.advance_stage:
        if current == "day1_secret_shopper" and "d1" not in completed:
            completed.append("d1")
        elif current == "day7_direct_call" and "d7" not in completed:
            completed.append("d7")
        contact.cadence_stage = STAGE_FLOW.get(current, current)
    contact.call_status = payload.call_status
    contact.call_notes = payload.call_notes
    contact.cadence_completed_days = completed
    if payload.rings is not None:
        contact.secret_shopper_rings = payload.rings
    if payload.loss is not None:
        contact.secret_shopper_loss = payload.loss
    db.commit()
    return {
        "success": True,
        "contact_id": contact.id,
        "call_status": contact.call_status,
        "cadence_stage": contact.cadence_stage,
        "completed_days": completed,
    }


@router.get("/mailing-list")
def get_mailing_list(
    search: str | None = Query(default=None, max_length=255),
    category: str | None = Query(default=None, max_length=255),
    country: str | None = Query(default=None, max_length=255),
    verified_only: bool = True,
    limit: int = Query(default=150, ge=1, le=500),
    db: Session = Depends(get_db),
) -> dict:
    clauses = ["(COALESCE(l.email, '') != '' OR COALESCE(cc.email, '') != '')"]
    params: dict = {"limit": limit}
    if verified_only:
        clauses.append("(l.is_email_verified IS TRUE OR cc.is_email_verified IS TRUE)")
    if country and country != "ALL":
        clauses.append("l.country = :country")
        params["country"] = country
    if category and category != "ALL":
        clauses.append("l.category = :category")
        params["category"] = category
    if search:
        clauses.append(
            "(LOWER(l.name) LIKE :search OR LOWER(cc.person_name) LIKE :search OR LOWER(l.city) LIKE :search)"
        )
        params["search"] = f"%{search.lower()}%"
    result = rows(
        db,
        f"""
        SELECT l.id AS lead_id, l.name AS company_name, l.category, l.city, l.country,
               l.phone AS company_phone, l.email AS company_email, l.is_email_verified AS lead_verified,
               l.email_mx_host AS lead_mx, l.email_stage, l.detected_website,
               cc.id AS contact_id, cc.person_name, cc.role_title, cc.email AS contact_email,
               cc.linkedin_url, cc.is_email_verified AS contact_verified, cc.email_mx_host AS contact_mx
        FROM leads l LEFT JOIN company_contacts cc ON l.id = cc.lead_id AND COALESCE(cc.email, '') != ''
        WHERE {" AND ".join(clauses)}
        ORDER BY CASE WHEN cc.email IS NOT NULL THEN 0 ELSE 1 END, l.is_email_verified DESC, l.id DESC
        LIMIT :limit
        """,
        params,
    )
    settings = get_settings()
    overrides = get_overrides(db)
    sender_name = overrides.get("sender_name", settings.sender_name)
    calendly_url = overrides.get("calendly_url", settings.calendly_url)
    output = []
    for item in result:
        direct = (item["contact_email"] or "").strip()
        company = (item["company_email"] or "").strip()
        company_name = item["company_name"]
        person_name = item["person_name"] or "Managing Director"
        city = item["city"] or "your area"
        subject = f"5 minutes: custom AI receptionist & plugins for {company_name}"
        body = (
            f"Hi {person_name},\n\nI noticed {company_name} in {city} and wanted to ask how your team "
            "handles after-hours inquiries. We build AI reception and workflow automation for local businesses.\n\n"
            f"If useful, you can book a short call here: {calendly_url}\n\n"
            f"Best regards,\n{sender_name}"
        )
        output.append(
            {
                "lead_id": item["lead_id"],
                "contact_id": item["contact_id"],
                "person_name": person_name,
                "role_title": item["role_title"] or "Owner / Decision Maker",
                "company_name": company_name,
                "category": item["category"],
                "city": city,
                "country": item["country"],
                "to_email": direct or company,
                "cc_email": company if direct and company and direct.lower() != company.lower() else "",
                "phone": item["company_phone"] or "",
                "linkedin_url": item["linkedin_url"] or "",
                "is_verified": bool(item["contact_verified"] or item["lead_verified"]),
                "status": "MX_VERIFIED" if item["contact_verified"] or item["lead_verified"] else "SYNTAX_VALID",
                "mx_host": item["contact_mx"] or item["lead_mx"] or "",
                "email_stage": item["email_stage"] or "READY",
                "website": item["detected_website"] or "",
                "preview_subject": subject,
                "preview_body": body,
            }
        )
    return {"mailing_list": output, "count": len(output)}
