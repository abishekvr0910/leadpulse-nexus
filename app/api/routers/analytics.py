from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.queries import rows, scalar
from app.db.session import get_db
from app.services.application_settings import get_overrides

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)) -> dict:
    total_leads = scalar(db, "SELECT COUNT(*) FROM leads") or 0
    verified_phones = scalar(db, "SELECT COUNT(*) FROM leads WHERE COALESCE(phone, '') != ''") or 0
    total_contacts = scalar(db, "SELECT COUNT(*) FROM company_contacts") or 0
    linkedin_count = scalar(db, "SELECT COUNT(*) FROM company_contacts WHERE COALESCE(linkedin_url, '') != ''") or 0
    dental_leads = scalar(db, "SELECT COUNT(*) FROM leads WHERE category IN ('dentist', 'dentists')") or 0
    countries_count = scalar(db, "SELECT COUNT(DISTINCT country) FROM leads WHERE COALESCE(country, '') != ''") or 0
    stage_rows = rows(db, "SELECT cadence_stage, COUNT(*) AS count FROM company_contacts GROUP BY cadence_stage")
    pipeline_stages = {item["cadence_stage"]: item["count"] for item in stage_rows if item["cadence_stage"]}
    booked_audits = scalar(db, "SELECT COUNT(*) FROM company_contacts WHERE cadence_stage = 'booked_audit'") or 0
    calls_logged = (
        scalar(db, "SELECT COUNT(*) FROM company_contacts WHERE COALESCE(call_status, 'not_called') != 'not_called'")
        or 0
    )

    settings = get_settings()
    overrides = get_overrides(db)
    return {
        "total_leads": total_leads,
        "verified_phones": verified_phones,
        "phone_rate_pct": round(verified_phones / total_leads * 100, 1) if total_leads else 0,
        "total_decision_makers": total_contacts,
        "linkedin_profiles": linkedin_count,
        "linkedin_rate_pct": round(linkedin_count / total_contacts * 100, 1) if total_contacts else 0,
        "dental_clinics": dental_leads,
        "countries_covered": countries_count,
        "pipeline_stages": pipeline_stages,
        "booked_audits": booked_audits,
        "calls_logged": calls_logged,
        "estimated_monthly_leakage_eur": dental_leads * 18 * 350,
        "calendly_url": overrides.get("calendly_url", settings.calendly_url),
        "demo_inbound_phone": overrides.get("demo_inbound_phone", settings.demo_inbound_phone),
    }


@router.get("/charts")
def get_charts(db: Session = Depends(get_db)) -> dict:
    countries = rows(
        db,
        """
        SELECT country, COUNT(*) AS leads,
               SUM(CASE WHEN COALESCE(phone, '') != '' THEN 1 ELSE 0 END) AS phones
        FROM leads WHERE COALESCE(country, '') != ''
        GROUP BY country ORDER BY leads DESC LIMIT 10
        """,
    )
    niches = rows(
        db,
        """
        SELECT CASE
            WHEN category IN ('dentist', 'dentists') THEN 'Dental Clinics'
            WHEN category = 'autorepair' THEN 'Auto Care / Body Repair'
            WHEN category IN ('plumbing', 'electricians') THEN 'Emergency Trades'
            WHEN category IN ('restaurant', 'cafe') THEN 'Hospitality & Dining'
            WHEN category IN ('hairdresser', 'beauty') THEN 'Aesthetic Salons'
            ELSE 'Professional Services' END AS niche,
            COUNT(*) AS count
        FROM leads GROUP BY niche ORDER BY count DESC
        """,
    )
    city_rows = rows(
        db,
        """
        SELECT city, country, COUNT(*) AS count FROM leads
        WHERE COALESCE(city, '') != '' GROUP BY city, country ORDER BY count DESC LIMIT 12
        """,
    )
    cities = [{"city": f"{item['city']} ({item['country']})", "count": item["count"]} for item in city_rows]
    total = scalar(db, "SELECT COUNT(*) FROM leads") or 0
    phones = scalar(db, "SELECT COUNT(*) FROM leads WHERE COALESCE(phone, '') != ''") or 0
    contacts = scalar(db, "SELECT COUNT(*) FROM company_contacts") or 0
    linkedin = scalar(db, "SELECT COUNT(*) FROM company_contacts WHERE COALESCE(linkedin_url, '') != ''") or 0
    funnel = [
        {"stage": "Market Leads Harvested", "value": total, "pct": 100},
        {"stage": "Direct Phone Verified", "value": phones, "pct": round(phones / total * 100, 1) if total else 0},
        {
            "stage": "Decision Maker Enriched",
            "value": contacts,
            "pct": round(contacts / phones * 100, 1) if phones else 0,
        },
        {
            "stage": "Direct LinkedIn Verified",
            "value": linkedin,
            "pct": round(linkedin / contacts * 100, 1) if contacts else 0,
        },
        {"stage": "Discovery Call Ready", "value": linkedin, "pct": 100},
    ]
    return {"countries": countries, "niches": niches, "cities": cities, "funnel": funnel}
