"""
find_people.py — Automated Decision-Maker & LinkedIn / Email Discovery Engine
=============================================================================
Discovers:
  - Key decision makers (Owners, Founders, CEOs, Managing Directors, Partners)
  - Personal LinkedIn profiles
  - Direct personal & work emails
  - Official company registration numbers (Companies House, KRS, Handelsregister)

Saves multiple contacts per company to the company_contacts table,
and updates primary contact details directly on the leads table.

Usage:
    python find_people.py --limit 10              # Find people for 10 leads
    python find_people.py --country GB --limit 20 # Find UK decision makers
    python find_people.py --country PL --limit 20 # Find Polish owners/CEOs
    python find_people.py --lead-id 15            # Enrich specific company
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import re
import time
import random
import argparse
import urllib.parse
from datetime import datetime

from ddgs import DDGS
from sqlalchemy import func, or_, select

from app.db.models import CompanyContact, Lead
from app.db.session import SessionLocal

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

EXCLUDE_EMAIL_WORDS = {
    "example", "sample", "test", "domain", "sentry", "schema",
    "w3.org", "github", "cloudflare", "noreply", "no-reply", "support@",
    "billing@", "privacy@", "abuse@", "mailer-daemon"
}

ROLE_KEYWORDS = [
    "founder", "co-founder", "owner", "co-owner", "ceo", "chief executive",
    "managing director", "director", "partner", "general manager",
    "principal", "inhaber", "geschäftsführer", "właściciel", "prezes", "dyrektor",
    # Healthcare / Dental / Customer Success roles
    "practice manager", "clinic manager", "clinical director", "principal dentist",
    "patient coordinator", "patient care", "head of patient experience",
    "customer success", "operations manager", "reception manager"
]

INVALID_TITLE_WORDS = [
    "student", "intern", "trainee", "journalist", "reporter", "waiter", "bartender", 
    "driver", "unemployed", "model", "actress", "actor", "seeking", "looking for",
    "freelance writer", "content creator", "school", "university"
]

MISMATCH_COUNTRIES = {
    "GB": ["new york", "california", "texas", "florida", "australia", "india", "iran", "china", "dubai", "uae", "canada", "brazil", "russia"],
    "PL": ["united states", "usa", "australia", "india", "china", "canada"],
    "DE": ["united states", "usa", "australia", "india", "china", "canada"],
}

def is_trustworthy_match(lead: dict, title: str, body: str, href: str) -> bool:
    """
    Delicate validation filter: ensures the person actually matches the target company,
    geographic territory, and is not a random namesake from another continent.
    """
    combo = f"{title} {body}".lower()
    city = (lead.get("city") or "").lower()
    country_code = lead.get("country_code", "GB")
    cname = clean_company_name(lead.get("name", "")).lower()

    # 1. Exclude invalid/unrelated job roles
    if any(bad in combo for bad in INVALID_TITLE_WORDS):
        return False

    # 2. Exclude foreign geographic mismatches (e.g., someone in New York when clinic is in UK)
    bad_locations = MISMATCH_COUNTRIES.get(country_code, [])
    for bad_loc in bad_locations:
        if bad_loc in combo:
            # Only allow if the actual local city or UK is ALSO explicitly mentioned
            if city and city in combo:
                continue
            if country_code == "GB" and any(k in combo for k in ["uk", "united kingdom", "london", "england", "scotland", "wales"]):
                continue
            return False

    # 2b. Check LinkedIn country subdomain
    if country_code == "GB":
        m_sub = re.search(r"https?://([a-z]{2})\.linkedin\.com", href)
        if m_sub and m_sub.group(1) not in ["uk", "www"]:
            return False
    elif country_code == "PL":
        m_sub = re.search(r"https?://([a-z]{2})\.linkedin\.com", href)
        if m_sub and m_sub.group(1) not in ["pl", "www"]:
            return False
    elif country_code == "DE":
        m_sub = re.search(r"https?://([a-z]{2})\.linkedin\.com", href)
        if m_sub and m_sub.group(1) not in ["de", "at", "ch", "www"]:
            return False

    # 3. Ensure company name relevance (must have at least one substantial word matching)
    cname_words = [w for w in re.findall(r"\b[a-zA-Z]{3,}\b", cname) if w not in ["the", "and", "ltd", "dental", "clinic", "shop", "bar", "cafe"]]
    if cname_words and not any(w in combo for w in cname_words):
        # If no unique company word matched, it's likely a generic namesake
        return False

    return True



def clean_company_name(raw_name: str) -> str:
    """Strips legal entity suffixes and descriptors for cleaner web matching."""
    cleaned = re.sub(
        r"\b(sp\.?\s*z\s*o\.?\s*o\.?|s\.?a\.?|sp\.?\s*k\.?|gmbh|ag|ltd|limited|llc|inc|corp|co|sarl|bv|as)\b",
        "", raw_name, flags=re.IGNORECASE
    )
    cleaned = re.sub(r"[-–|].*$", "", cleaned)
    return cleaned.strip() or raw_name


def parse_linkedin_title(raw_title: str, company_name: str) -> tuple:
    """
    Parses LinkedIn titles to extract Person Name and Role Title.
    e.g. 'Brian Trollip - CEO Dishoom | LinkedIn' -> ('Brian Trollip', 'CEO')
    e.g. 'Jamie Jones - Co-Owner - The Mayfair Chippy | LinkedIn' -> ('Jamie Jones', 'Co-Owner')
    """
    clean_title = raw_title.replace("| LinkedIn", "").replace("- LinkedIn", "").strip()
    parts = [p.strip() for p in re.split(r"[-–|:]", clean_title) if p.strip()]

    if not parts:
        return "", ""

    name = parts[0]
    # Remove honorifics
    name = re.sub(r"^(Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Prof\.?)\s+", "", name).strip()
    
    # Check if first part is company name rather than person name
    if company_name.lower() in name.lower() and len(parts) > 1:
        name = parts[1]
        role = parts[0]
    else:
        role = parts[1] if len(parts) > 1 else "Executive / Owner"

    # Clean role
    role = re.sub(rf"(at|@)?\s*{re.escape(company_name)}", "", role, flags=re.IGNORECASE).strip()
    if not role or role.lower() in ["london", "uk", "poland", "germany", "france", "switzerland"]:
        role = "Decision Maker"

    return name, role


def find_person_direct_email(ddgs: DDGS, person_name: str, company_name: str) -> str:
    """Searches for the specific person's direct email."""
    if not person_name or len(person_name) < 3:
        return ""

    query = f'"{person_name}" "{company_name}" email'
    try:
        results = list(ddgs.text(query, max_results=3))
        for r in results:
            text = (r.get("body", "") + " " + r.get("title", "")).lower()
            matches = EMAIL_REGEX.findall(text)
            for email in matches:
                if not any(bad in email for bad in EXCLUDE_EMAIL_WORDS):
                    return email
    except Exception:
        pass
    return ""


def find_company_registration(ddgs: DDGS, company_name: str, city: str, country_code: str) -> str:
    """Finds official company registration number (Companies House, KRS, Handelsregister)."""
    clean_name = clean_company_name(company_name)
    if country_code == "GB":
        q = f'"{clean_name}" {city} "Companies House" "Company number"'
    elif country_code == "PL":
        q = f'"{clean_name}" {city} (KRS OR NIP OR aleo.com)'
    elif country_code in ["DE", "AT", "CH"]:
        q = f'"{clean_name}" {city} Handelsregister HRB'
    else:
        q = f'"{clean_name}" {city} "registration number"'

    try:
        results = list(ddgs.text(q, max_results=2))
        for r in results:
            body = r.get("body", "")
            title = r.get("title", "")
            combo = f"{title} {body}"
            
            # UK Companies House e.g. "Company number 11206392"
            m = re.search(r"(?:company\s*number|registered\s*number|no\.?)\s*[:#]?\s*([0-9A-Z]{6,9})", combo, re.IGNORECASE)
            if m:
                return m.group(1).strip()
                
            # Polish NIP / KRS
            m_krs = re.search(r"KRS[\s:]*([0-9]{10})", combo, re.IGNORECASE)
            if m_krs:
                return f"KRS {m_krs.group(1)}"
            m_nip = re.search(r"NIP[\s:]*([0-9\-]{10,13})", combo, re.IGNORECASE)
            if m_nip:
                return f"NIP {m_nip.group(1)}"
    except Exception:
        pass
    return ""


def discover_people_for_company(lead: dict) -> tuple:
    """
    Discovers key people, LinkedIn profiles, and personal emails for a given lead.
    """
    raw_name = lead.get("name", "")
    city = lead.get("city", "")
    country_code = lead.get("country_code", "")
    cname = clean_company_name(raw_name)

    contacts = []
    reg_number = ""

    with DDGS() as ddgs:
        # 1. Search for LinkedIn Profiles
        queries = [
            f'"{cname}" {city} (owner OR founder OR CEO OR director OR managing OR partner) site:linkedin.com/in/',
            f'"{cname}" {city} linkedin'
        ]

        found_results = []
        for q in queries:
            try:
                res = list(ddgs.text(q, max_results=4))
                if res:
                    found_results.extend(res)
                    break
            except Exception:
                pass
            time.sleep(random.uniform(0.5, 1.0))

        for r in found_results:
            href = r.get("href", "")
            title = r.get("title", "")
            body = r.get("body", "")

            # Delicate trust filter: reject geographic & role mismatches
            if not is_trustworthy_match(lead, title, body, href):
                continue

            # Check if personal LinkedIn URL
            if "linkedin.com/in/" in href:
                p_name, p_role = parse_linkedin_title(title, cname)
                if p_name and len(p_name.split()) >= 2 and len(p_name) <= 40:
                    if not any(c["person_name"].lower() == p_name.lower() for c in contacts):
                        contacts.append({
                            "lead_id": lead["id"],
                            "company_name": raw_name,
                            "person_name": p_name,
                            "role_title": p_role,
                            "linkedin_url": href,
                            "email": "",
                            "phone": lead.get("phone", ""),
                            "source": "LinkedIn Verified"
                        })

            # Check body text for co-founders / owners
            if len(contacts) < 3:
                for kw in ["co-founder", "founder", "owner", "ceo", "geschäftsführer", "inhaber", "właściciel"]:
                    m = re.search(rf"({kw}\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+))", body, re.IGNORECASE)
                    if m:
                        extracted_name = m.group(2).strip()
                        if 2 <= len(extracted_name.split()) <= 4 and not any(c["person_name"].lower() == extracted_name.lower() for c in contacts):
                            contacts.append({
                                "lead_id": lead["id"],
                                "company_name": raw_name,
                                "person_name": extracted_name,
                                "role_title": kw.title(),
                                "linkedin_url": href if "linkedin.com/in/" in href else "",
                                "email": "",
                                "phone": lead.get("phone", ""),
                                "source": "Web Verified"
                            })

        # 2. For each contact found, attempt to find their direct personal email
        for c in contacts:
            time.sleep(random.uniform(0.5, 1.0))
            p_email = find_person_direct_email(ddgs, c["person_name"], cname)
            if p_email:
                c["email"] = p_email

        # 3. Look up Company Registration Number
        time.sleep(random.uniform(0.5, 1.0))
        reg_number = find_company_registration(ddgs, raw_name, city, country_code)

    return contacts, reg_number


def save_contacts_to_db(lead_id: int, contacts: list, reg_number: str) -> int:
    """Saves discovered contacts into company_contacts and updates the leads table."""
    saved_count = 0
    primary = contacts[0] if contacts else None
    with SessionLocal() as db:
        for contact in contacts:
            existing = db.scalar(
                select(CompanyContact).where(
                    CompanyContact.lead_id == lead_id,
                    CompanyContact.person_name == contact["person_name"],
                )
            )
            if not existing:
                db.add(
                    CompanyContact(
                        lead_id=lead_id,
                        company_name=contact["company_name"],
                        person_name=contact["person_name"],
                        role_title=contact["role_title"],
                        email=contact["email"],
                        phone=contact["phone"],
                        linkedin_url=contact["linkedin_url"],
                        company_registration=reg_number,
                        source=contact["source"],
                    )
                )
                saved_count += 1
            elif contact["email"] and not existing.email:
                existing.email = contact["email"]

        db.flush()
        lead = db.get(Lead, lead_id)
        if lead and (primary or reg_number):
            if primary:
                lead.primary_contact_name = primary["person_name"] or lead.primary_contact_name
                lead.primary_contact_title = primary["role_title"] or lead.primary_contact_title
                lead.primary_contact_email = primary["email"] or lead.primary_contact_email
                lead.primary_contact_linkedin = primary["linkedin_url"] or lead.primary_contact_linkedin
            lead.company_reg_number = reg_number or lead.company_reg_number
            lead.contacts_count = db.scalar(
                select(func.count(CompanyContact.id)).where(CompanyContact.lead_id == lead_id)
            ) or 0
        db.commit()
    return saved_count


def run_people_discovery(country=None, category=None, lead_id=None, limit=20):
    statement = select(Lead)
    if lead_id:
        statement = statement.where(Lead.id == lead_id)
    else:
        statement = statement.where(or_(Lead.primary_contact_name == "", Lead.primary_contact_name.is_(None)))
        if country:
            statement = statement.where(Lead.country_code == country.upper())
        if category:
            pattern = f"%{category}%"
            statement = statement.where(or_(Lead.category.ilike(pattern), Lead.category_pl.ilike(pattern)))
    statement = statement.order_by(Lead.avg_revenue_eur.desc(), Lead.id).limit(limit)
    with SessionLocal() as db:
        records = list(db.scalars(statement))
        leads = [
            {column.name: getattr(record, column.name) for column in Lead.__table__.columns}
            for record in records
        ]

    print(f"\n{'='*70}")
    print(f"  LeadPulse — Decision-Maker & LinkedIn Discovery")
    print(f"  Target Leads: {len(leads)} | Filter: Country={country or 'ALL'}, Category={category or 'ALL'}, LeadID={lead_id or 'ANY'}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*70}\n")

    total_people_found = 0
    total_emails_found = 0

    for i, lead in enumerate(leads, 1):
        print(f"[{i:2}/{len(leads)}] {lead['name'][:30]:<30} ({lead['city']}, {lead['country_code']}) ...", end=" ", flush=True)
        contacts, reg_num = discover_people_for_company(lead)
        saved = save_contacts_to_db(lead["id"], contacts, reg_num)
        
        people_str = f"{len(contacts)} people"
        emails_in_batch = [ct['email'] for ct in contacts if ct['email']]
        email_str = f"({len(emails_in_batch)} direct emails)" if emails_in_batch else ""

        print(f"{people_str} {email_str}")
        for ct in contacts:
            print(f"       👤 {ct['person_name']} [{ct['role_title']}]")
            if ct['linkedin_url']:
                print(f"          🔗 {ct['linkedin_url']}")
            if ct['email']:
                print(f"          📧 {ct['email']}")
        if reg_num:
            print(f"       🏛️  Registration: {reg_num}")

        total_people_found += len(contacts)
        total_emails_found += len(emails_in_batch)

        time.sleep(random.uniform(1.2, 2.2))

    print(f"\n{'='*70}")
    print(f"  DONE — Discovered {total_people_found} Decision-Makers ({total_emails_found} Direct Emails) across {len(leads)} companies")
    print(f"  Finished: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find decision makers and LinkedIn contacts for companies")
    parser.add_argument("--country", default=None, help="Country code (GB, PL, CH, etc.)")
    parser.add_argument("--category", default=None, help="Category filter (dentist, autorepair, etc.)")
    parser.add_argument("--lead-id", type=int, default=None, help="Specific lead ID to enrich")
    parser.add_argument("--limit", type=int, default=10, help="Number of companies to enrich")
    args = parser.parse_args()

    run_people_discovery(country=args.country, category=args.category, lead_id=args.lead_id, limit=args.limit)
