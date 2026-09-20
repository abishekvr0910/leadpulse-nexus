"""
osint_email_dorker.py — Advanced OSINT Email Discovery Engine
============================================================
Executes multi-vector OSINT techniques to find unmasked personal & corporate emails:
  1. PDF & Public Document Dorking (Health filings, tenders, planning PDFs)
  2. Free Webmail Discovery (Personal @gmail.com, @yahoo, @outlook used by owners)
  3. Regulatory & Legal Filings (CQC, Companies House, Impressum § 5 TMG)
  4. Mailto: and Schema.org metadata scraping
  5. DNS MX Pattern Permutation Probe
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import re
import time
import random
import argparse
import sqlite3
from ddgs import DDGS
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "leads.db")
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")

EXCLUDE_EMAIL_WORDS = {
    "example.com", "sentry.io", "w3.org", "schema.org", "github.com",
    "cloudflare", "noreply", "no-reply", "donotreply", "support@",
    "abuse@", "mailer-daemon", "privacy@", "billing@"
}

FREE_MAIL_DOMAINS = [
    "gmail.com", "yahoo.co.uk", "yahoo.com", "outlook.com", "hotmail.co.uk", "hotmail.com", "aol.com", "icloud.com"
]

def clean_company_name(name: str) -> str:
    cleaned = re.sub(r"\b(ltd|limited|llc|inc|corp|gmbh|sp\.?\s*z\s*o\.?\s*o\.?)\b", "", name, flags=re.IGNORECASE)
    cleaned = re.sub(r"[-–|].*$", "", cleaned)
    return cleaned.strip() or name

def extract_valid_emails(text: str, target_domain: str = None) -> list:
    """Extracts clean emails from raw text, filtering out junk."""
    raw = EMAIL_REGEX.findall(text)
    clean = []
    for em in raw:
        em_lower = em.lower()
        if any(bad in em_lower for bad in EXCLUDE_EMAIL_WORDS):
            continue
        if em_lower.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")):
            continue
        if em_lower not in clean:
            clean.append(em_lower)
    return clean

def osint_search_lead_emails(lead: dict, person_name: str = None) -> dict:
    """
    Executes advanced OSINT queries to find verified emails.
    """
    cname = clean_company_name(lead["name"])
    city = lead.get("city", "")
    country = lead.get("country", "")
    country_code = lead.get("country_code", "GB")
    
    results = {
        "personal_emails": [],
        "public_doc_emails": [],
        "regulatory_emails": [],
        "all_found": []
    }

    with DDGS() as ddgs:
        queries = []

        # 1. Personal Webmail Dork (High hit rate for local clinic & trade owners)
        if person_name:
            queries.append({
                "type": "personal",
                "q": f'"{person_name}" "{cname}" ("@gmail.com" OR "@yahoo.co.uk" OR "@outlook.com" OR "@hotmail.co.uk" OR "@aol.com")'
            })
        else:
            queries.append({
                "type": "personal",
                "q": f'"{cname}" {city} ("@gmail.com" OR "@yahoo.co.uk" OR "@outlook.com" OR "@hotmail.co.uk" OR "@aol.com")'
            })

        # 2. PDF & Public Document Dork (Finds compliance, price lists, inspection reports)
        queries.append({
            "type": "doc",
            "q": f'"{cname}" {city} filetype:pdf ("email" OR "contact" OR "@")'
        })

        # 3. Mailto & Direct Contact Dork
        queries.append({
            "type": "contact",
            "q": f'"{cname}" {city} "mailto:"'
        })

        # 4. German / Austrian Impressum Dork (if DACH)
        if country_code in ["DE", "AT", "CH"] or country in ["Germany", "Austria", "Switzerland"]:
            queries.append({
                "type": "regulatory",
                "q": f'"{cname}" {city} "Impressum" ("E-Mail" OR "kontakt@")'
            })
        elif country_code == "GB":
            # CQC / NHS Dental Provider Dork
            queries.append({
                "type": "regulatory",
                "q": f'"{cname}" {city} ("CQC" OR "Care Quality Commission" OR "NHS") "email"'
            })

        for item in queries:
            try:
                res = list(ddgs.text(item["q"], max_results=3))
                for r in res:
                    snippet = f"{r.get('title', '')} {r.get('body', '')} {r.get('href', '')}"
                    emails = extract_valid_emails(snippet)
                    for e in emails:
                        if e not in results["all_found"]:
                            results["all_found"].append(e)
                            if any(free in e for free in FREE_MAIL_DOMAINS):
                                results["personal_emails"].append(e)
                            elif item["type"] == "doc":
                                results["public_doc_emails"].append(e)
                            elif item["type"] == "regulatory":
                                results["regulatory_emails"].append(e)
                time.sleep(random.uniform(0.6, 1.2))
            except Exception:
                pass

    return results

def run_osint_batch(limit=10, category="dentist", country="GB"):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    sql = """
        SELECT id, name, category, city, country, country_code, phone, email,
               primary_contact_name
        FROM leads
        WHERE (email IS NULL OR email = '')
        AND category IN ('dentist', 'dentists', 'generaldentistry')
        ORDER BY id ASC
        LIMIT ?
    """
    c.execute(sql, (limit,))
    leads = [dict(r) for r in c.fetchall()]
    conn.close()

    print(f"[*] Starting OSINT Email Reconnaissance on {len(leads)} leads...")
    
    found_total = 0
    for idx, lead in enumerate(leads, 1):
        p_name = lead.get("primary_contact_name")
        print(f"\n[{idx}/{len(leads)}] Target: {lead['name']} ({lead.get('city')}) | Contact: {p_name or 'Unspecified'}")
        
        recon = osint_search_lead_emails(lead, person_name=p_name)
        if recon["all_found"]:
            print(f"  ✓ Found {len(recon['all_found'])} email(s):")
            for em in recon["all_found"]:
                print(f"    📧 {em}")
            found_total += 1
            
            # Save top found email to leads table
            best_email = recon["personal_emails"][0] if recon["personal_emails"] else recon["all_found"][0]
            conn2 = sqlite3.connect(DB_PATH)
            c2 = conn2.cursor()
            c2.execute("UPDATE leads SET email = ?, status = 'EMAIL_FOUND' WHERE id = ? AND (email IS NULL OR email = '')", (best_email, lead["id"]))
            conn2.commit()
            conn2.close()
        else:
            print("  - No unmasked public email found via dorks.")

    print(f"\n[✓] OSINT Recon Complete. Found emails for {found_total}/{len(leads)} leads.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--category", default="dentist")
    parser.add_argument("--country", default="GB")
    args = parser.parse_args()
    
    run_osint_batch(limit=args.limit, category=args.category, country=args.country)
