import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.queries import rows, scalar
from app.db.session import get_db

router = APIRouter(prefix="/api", tags=["leads"])


@router.get("/leads")
def get_leads(
    search: str | None = Query(default=None, max_length=255),
    country: str | None = Query(default=None, max_length=255),
    category: str | None = Query(default=None, max_length=255),
    has_phone: bool | None = None,
    has_contact: bool | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=30, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    clauses = ["1=1"]
    params: dict = {"limit": limit, "offset": (page - 1) * limit}
    if search:
        clauses.append("(LOWER(name) LIKE :search OR LOWER(city) LIKE :search OR LOWER(address) LIKE :search)")
        params["search"] = f"%{search.lower()}%"
    if country and country != "ALL":
        clauses.append("country = :country")
        params["country"] = country
    if category and category != "ALL":
        clauses.append("category = :category")
        params["category"] = category
    if has_phone:
        clauses.append("COALESCE(phone, '') != ''")
    if has_contact:
        clauses.append("COALESCE(primary_contact_name, '') != ''")
    where = " AND ".join(clauses)
    total = scalar(db, f"SELECT COUNT(*) FROM leads WHERE {where}", params) or 0
    result = rows(
        db,
        f"""
        SELECT id, name, category, city, country, phone, email, has_website, detected_website,
               primary_contact_name, primary_contact_title, primary_contact_linkedin, company_reg_number
        FROM leads WHERE {where} ORDER BY id DESC LIMIT :limit OFFSET :offset
        """,
        params,
    )
    return {"leads": result, "total": total, "page": page, "total_pages": (total + limit - 1) // limit}


@router.get("/clinics-sample")
def get_sample_clinics(limit: int = Query(default=35, ge=1, le=100), db: Session = Depends(get_db)) -> dict:
    clinics = rows(
        db,
        """
        SELECT id, name, category, city, country, phone, detected_website,
               primary_contact_name, primary_contact_title
        FROM leads WHERE COALESCE(phone, '') != '' AND name IS NOT NULL
        ORDER BY id DESC LIMIT :limit
        """,
        {"limit": limit},
    )
    return {"clinics": clinics, "count": len(clinics)}


@router.get("/export-csv")
def export_contacts_csv(db: Session = Depends(get_db)) -> Response:
    result = rows(
        db,
        """
        SELECT cc.person_name, cc.role_title, cc.company_name, cc.email AS contact_email,
               cc.phone AS contact_phone, cc.linkedin_url, cc.company_registration,
               cc.linkedin_note, cc.whatsapp_url, cc.company_number, cc.registered_office,
               l.category, l.city, l.country, l.phone AS company_phone,
               l.email AS company_email, l.detected_website
        FROM company_contacts cc LEFT JOIN leads l ON cc.lead_id = l.id ORDER BY cc.id DESC
        """,
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "First Name",
            "Last Name",
            "Full Name",
            "Job Title",
            "Company Name",
            "Category",
            "City",
            "Country",
            "Direct Email",
            "Company Desk Email",
            "Direct Phone",
            "WhatsApp Link",
            "LinkedIn URL",
            "LinkedIn Note",
            "Company Number",
            "Registered Office",
            "Website",
        ]
    )
    for item in result:
        full_name = (item["person_name"] or "").strip()
        parts = full_name.split()
        writer.writerow(
            [
                parts[0] if parts else "",
                " ".join(parts[1:]),
                full_name,
                item["role_title"] or "Owner / Decision Maker",
                item["company_name"],
                item["category"] or "",
                item["city"] or "",
                item["country"] or "",
                item["contact_email"] or "",
                item["company_email"] or "",
                item["contact_phone"] or item["company_phone"] or "",
                item["whatsapp_url"] or "",
                item["linkedin_url"] or "",
                item["linkedin_note"] or "",
                item["company_number"] or item["company_registration"] or "",
                item["registered_office"] or "",
                item["detected_website"] or "",
            ]
        )
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leadpulse_decision_makers_export.csv"},
    )
