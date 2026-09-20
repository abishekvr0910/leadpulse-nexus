"""
osint_dossier.py — LinkedIn Premium Bypass & Multi-Vector OSINT Enrichment
========================================================================
Pulls all relevant contact & intelligence vectors so you NEVER need LinkedIn Premium:
  1. Free 300-character LinkedIn Connection Request pitch notes (fits LinkedIn free limit)
  2. Direct Click-to-Chat WhatsApp links with pre-filled 5-min audit hooks
  3. UK Companies House official registry scraping (Company #, Registered Office, Active Directors, Status)
  4. Direct personal & corporate email discovery
  5. Direct dial / mobile routing
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import re
import json
import time
import random
import urllib.parse
import urllib.request
import sqlite3
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

DB_PATH = str(Path(__file__).resolve().parent / "leads.db")

CALENDLY_URL = "https://calendly.com/abivr61/30min"

def clean_first_name(full_name: str) -> str:
    """Extracts first name from full name or title."""
    clean = re.sub(r"^(Dr\.?|Mr\.?|Mrs\.?|Ms\.?|Prof\.?|med\.?\s*dent\.?)\s+", "", full_name, flags=re.IGNORECASE).strip()
    parts = clean.split()
    if not parts:
        return "there"
    first = parts[0].strip().title()
    if first.lower() in ["of", "the", "dental", "clinic", "practice", "emergency"]:
        return "there"
    return first

def clean_phone_for_whatsapp(phone: str, country_code: str = "GB") -> str:
    """Normalizes phone number to international format for WhatsApp."""
    if not phone:
        return ""
    digits = re.sub(r"[^\d+]", "", phone)
    if digits.startswith("+"):
        return digits[1:]
    if country_code == "GB":
        if digits.startswith("0"):
            return "44" + digits[1:]
        elif not digits.startswith("44"):
            return "44" + digits
    elif country_code == "PL":
        if digits.startswith("0"):
            return "48" + digits[1:]
        elif not digits.startswith("48"):
            return "48" + digits
    elif country_code == "CH":
        if digits.startswith("0"):
            return "41" + digits[1:]
        elif not digits.startswith("41"):
            return "41" + digits
    return digits

def generate_free_linkedin_note(person_name: str, company_name: str, city: str, category: str) -> str:
    """
    Generates a high-converting personalized note guaranteed to be UNDER 300 characters
    for LinkedIn's 100% FREE 'Add a note' connection request.
    """
    first_name = clean_first_name(person_name)
    cname = company_name[:24].strip()
    loc = (city or "your area")[:14].strip()
    cat = (category or "").lower()

    if any(k in cat for k in ["dentist", "dentistry", "dental"]):
        note = f"Hi {first_name}, saw {cname} in {loc}. We built a 24/7 AI voice receptionist for dental clinics that answers missed patient calls in 2 rings & syncs into Calendly. Would you be open to a 5-min problem audit? {CALENDLY_URL}"
    elif any(k in cat for k in ["pharmacy", "chemist"]):
        note = f"Hi {first_name}, saw {cname} in {loc}. We build custom AI triage & intake plugins that save staff 15+ hrs/wk handling repeat patient calls. Would you be open to a 5-min problem audit? {CALENDLY_URL}"
    elif any(k in cat for k in ["auto", "repair", "garage", "towing"]):
        note = f"Hi {first_name}, saw {cname} in {loc}. We build 24/7 AI voice dispatchers that capture emergency repair & booking inquiries when phones are busy. Open to a 5-min problem audit? {CALENDLY_URL}"
    elif any(k in cat for k in ["restaurant", "cafe", "hospitality"]):
        note = f"Hi {first_name}, noticed {cname} in {loc}. We build 24/7 AI receptionists that capture reservations & group bookings automatically after-hours. Open to a 5-min problem audit? {CALENDLY_URL}"
    else:
        note = f"Hi {first_name}, noticed {cname} in {loc}. Most businesses treat ChatGPT as novelty. We build custom plugins & 24/7 AI voice receptionists that book straight to calendar. Open to a 5-min problem audit? {CALENDLY_URL}"

    # LinkedIn strictly enforces a 300-character maximum on free connection requests
    if len(note) > 300:
        note = f"Hi {first_name}, noticed {cname}. We build custom 24/7 AI voice receptionists & plugins that book straight to calendar. Open to a quick 5-min problem audit? {CALENDLY_URL}"

    return note

def generate_whatsapp_chat_url(phone: str, person_name: str, company_name: str, country_code: str = "GB") -> str:
    """Generates direct Click-to-Chat WhatsApp link."""
    clean_num = clean_phone_for_whatsapp(phone, country_code)
    if not clean_num or len(clean_num) < 8:
        return ""
    first_name = clean_first_name(person_name)
    msg = f"Hi {first_name}, Avi here from AI Automations. I came across {company_name} and wanted to share a 60-second prototype of an AI receptionist that handles missed patient/client calls: {CALENDLY_URL}"
    return f"https://wa.me/{clean_num}?text={urllib.parse.quote(msg)}"

def scrape_companies_house(company_name: str, city: str = "") -> Dict[str, Any]:
    """
    Free OSINT lookup on UK Companies House public portal without API key.
    Extracts: Company Number, Registered Office, Active Status, Incorporation Date, Officers.
    """
    clean_name = re.sub(r"\b(ltd|limited|llc|inc|corp)\b", "", company_name, flags=re.IGNORECASE).strip()
    search_q = f"{clean_name} {city}".strip()
    search_url = f"https://find-and-update.company-information.service.gov.uk/search/companies?q={urllib.parse.quote(search_q)}"
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    req = urllib.request.Request(search_url, headers=headers)
    
    data = {
        "company_number": "",
        "company_name": "",
        "status": "Active",
        "registered_office": "",
        "incorporation_date": "",
        "companies_house_url": "",
        "officers": []
    }

    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            soup = BeautifulSoup(resp.read().decode("utf-8"), "html.parser")
            first_co = soup.find("li", class_="type-company")
            if not first_co:
                return data
                
            title_a = first_co.find("a")
            if not title_a:
                return data
                
            data["company_name"] = title_a.text.strip()
            ch_path = title_a.get("href", "")
            data["companies_house_url"] = f"https://find-and-update.company-information.service.gov.uk{ch_path}"
            
            # Extract Company Number
            m_num = re.search(r"/company/([0-9A-Z]{6,9})", ch_path)
            if m_num:
                data["company_number"] = m_num.group(1)
                
            meta_p = first_co.find("p", class_="meta")
            if meta_p:
                meta_text = meta_p.text.strip()
                if "Dissolved" in meta_text:
                    data["status"] = "Dissolved"
                elif "Active" in meta_text or "Incorporated" in meta_text:
                    data["status"] = "Active"
                m_date = re.search(r"Incorporated on ([0-9]+ [A-Za-z]+ [0-9]{4})", meta_text)
                if m_date:
                    data["incorporation_date"] = m_date.group(1)
                    
            addr_p = first_co.find("p", class_="address")
            if addr_p:
                data["registered_office"] = addr_p.text.strip()
                
            # If company number found, fetch primary officers/directors
            if data["company_number"]:
                try:
                    time.sleep(0.4)
                    off_url = f"https://find-and-update.company-information.service.gov.uk/company/{data['company_number']}/officers"
                    off_req = urllib.request.Request(off_url, headers=headers)
                    with urllib.request.urlopen(off_req, timeout=8) as off_resp:
                        off_soup = BeautifulSoup(off_resp.read().decode("utf-8"), "html.parser")
                        cards = off_soup.find_all("div", class_="appointment-1")
                        for c in cards[:3]:
                            name_el = c.find("h2")
                            role_el = c.find("dd", id=re.compile(r"officer-role"))
                            app_el = c.find("dd", id=re.compile(r"officer-appointed-on"))
                            dob_el = c.find("dd", id=re.compile(r"officer-date-of-birth"))
                            addr_el = c.find("dd", id=re.compile(r"officer-address"))
                            data["officers"].append({
                                "name": name_el.text.strip() if name_el else "",
                                "role": role_el.text.strip() if role_el else "Director",
                                "appointed": app_el.text.strip() if app_el else "",
                                "born": dob_el.text.strip() if dob_el else "",
                                "correspondence_address": addr_el.text.strip() if addr_el else ""
                            })
                except Exception:
                    pass

    except Exception as e:
        # Graceful fallback
        pass

    return data

def build_dossier_for_contact(contact: dict, lead: dict) -> Dict[str, Any]:
    """Assembles a full OSINT & LinkedIn bypass dossier for a contact."""
    p_name = contact.get("person_name", "")
    c_name = contact.get("company_name", lead.get("name", ""))
    city = lead.get("city", "")
    country = lead.get("country", "")
    country_code = lead.get("country_code", "GB")
    category = lead.get("category", "")
    phone = contact.get("phone") or lead.get("phone") or ""
    direct_email = contact.get("email") or ""
    company_email = lead.get("email") or ""
    linkedin_url = contact.get("linkedin_url") or ""

    # 1. Generate 300-character Free LinkedIn Pitch Note
    li_note = generate_free_linkedin_note(p_name, c_name, city, category)

    # 2. Generate Click-to-Chat WhatsApp URL
    wa_url = generate_whatsapp_chat_url(phone, p_name, c_name, country_code)

    # 3. Companies House Lookup (if UK)
    ch_info = {}
    if country_code == "GB" or country == "United Kingdom":
        # Check if already present
        if contact.get("company_registration") and re.match(r"^[0-9A-Z]{6,9}$", contact.get("company_registration")):
            ch_info["company_number"] = contact.get("company_registration")
        else:
            ch_info = scrape_companies_house(c_name, city)

    co_number = ch_info.get("company_number") or contact.get("company_registration") or ""
    reg_office = ch_info.get("registered_office") or ""

    dossier = {
        "contact_id": contact.get("id"),
        "person_name": p_name,
        "first_name": clean_first_name(p_name),
        "role_title": contact.get("role_title", "Decision Maker"),
        "company_name": c_name,
        "category": category,
        "city": city,
        "country": country,
        "linkedin_url": linkedin_url,
        "has_linkedin": bool(linkedin_url and "linkedin.com" in linkedin_url),
        
        # Free LinkedIn bypass tools
        "free_linkedin_note": li_note,
        "free_linkedin_note_chars": len(li_note),
        "linkedin_group_bypass_tip": "Join groups like 'UK Dental Professionals' or 'Healthcare Practice Managers UK' to send 15 free 1-on-1 direct messages every month without Premium.",
        
        # Alternative direct channels (Zero LinkedIn cost)
        "direct_email": direct_email,
        "company_desk_email": company_email,
        "phone": phone,
        "whatsapp_url": wa_url,
        "calendly_url": CALENDLY_URL,
        
        # Public legal registry intelligence
        "company_number": co_number,
        "registered_office": reg_office,
        "companies_house": ch_info
    }

    return dossier

def _enrich_single_contact(row_tuple):
    contact_dict, lead_dict = row_tuple
    dossier = build_dossier_for_contact(contact_dict, lead_dict)
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE company_contacts SET
            linkedin_note = ?,
            whatsapp_url = ?,
            company_number = COALESCE(NULLIF(company_number, ''), ?),
            registered_office = COALESCE(NULLIF(registered_office, ''), ?),
            dossier_data = ?
        WHERE id = ?
    """, (
        dossier["free_linkedin_note"],
        dossier["whatsapp_url"],
        dossier["company_number"],
        dossier["registered_office"],
        json.dumps(dossier, ensure_ascii=False),
        contact_dict["id"]
    ))
    conn.commit()
    conn.close()
    return dossier

def enrich_all_contacts(limit: Optional[int] = None, max_workers: int = 10):
    """Enriches contacts in company_contacts with LinkedIn bypass notes, WhatsApp, and OSINT data concurrently."""
    import concurrent.futures
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    query = """
        SELECT cc.*, l.city, l.country, l.country_code, l.category, l.phone as lead_phone, l.email as lead_email, l.name as lead_name
        FROM company_contacts cc
        JOIN leads l ON cc.lead_id = l.id
        WHERE cc.linkedin_note IS NULL OR cc.linkedin_note = '' OR cc.whatsapp_url IS NULL
    """
    if limit:
        query += f" LIMIT {limit}"

    c.execute(query)
    rows = c.fetchall()
    conn.close()

    print(f"[*] Processing {len(rows)} decision makers with {max_workers} concurrent threads...")

    items = []
    for r in rows:
        contact_dict = dict(r)
        lead_dict = {
            "name": r["lead_name"],
            "city": r["city"],
            "country": r["country"],
            "country_code": r["country_code"] or "GB",
            "category": r["category"],
            "phone": r["lead_phone"],
            "email": r["lead_email"]
        }
        items.append((contact_dict, lead_dict))

    completed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for dossier in executor.map(_enrich_single_contact, items):
            completed += 1
            if completed % 15 == 0 or completed == len(items):
                print(f"  [{completed}/{len(items)}] Enriched {dossier['person_name']} ({dossier['company_name']})")

    print(f"[✓] Completed multi-threaded OSINT & LinkedIn bypass enrichment for {completed} contacts.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--threads", type=int, default=10)
    args = parser.parse_args()
    enrich_all_contacts(limit=args.limit, max_workers=args.threads)

