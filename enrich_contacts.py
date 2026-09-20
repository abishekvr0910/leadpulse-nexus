"""
enrich_contacts.py — Multi-source contact enrichment for LeadPulse EU.

For each company in the DB missing email/phone:
  1. DuckDuckGo search → find website or contact page
  2. Scrape contact page → extract email + phone via regex
  3. Country-specific directory search as fallback

Usage:
    python enrich_contacts.py                    # all companies missing email/phone
    python enrich_contacts.py --country DE       # only Germany
    python enrich_contacts.py --country PL       # only Poland
    python enrich_contacts.py --limit 100        # cap at 100 companies
    python enrich_contacts.py --missing email    # only those missing email
    python enrich_contacts.py --missing phone    # only those missing phone
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import re
import time
import random
import argparse
import sqlite3
import requests
from typing import Optional, Tuple
from datetime import datetime

DB_PATH = r"S:\APPs\lead-finder\leads.db"

# ── Regex patterns ────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE
)
PHONE_RE = re.compile(
    r"(?:\+?[\d\s\-\(\)]{7,20})"
)

# Domains to skip when scraping (directories, social media, etc.)
SKIP_DOMAINS = {
    "facebook.com","instagram.com","twitter.com","linkedin.com","youtube.com",
    "google.com","wikipedia.org","yelp.com","tripadvisor.com","booking.com",
    "foursquare.com","openstreetmap.org","wikidata.org","maps.google.com",
    "apple.com","microsoft.com","amazon.com","ebay.com","allegro.pl",
    "panoramafirm.pl","zumi.pl","adressen.de","gelbeseiten.de","yell.com",
    "pagesjaunes.fr","herold.at","local.ch","gulesider.no","hitta.se",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# ── Country-specific directory URLs ─────────────────────────────────────────
DIRECTORY_SEARCH = {
    "DE": "https://www.gelbeseiten.de/suche/{query}/{city}",
    "AT": "https://www.herold.at/gelbe-seiten/{query}/{city}/",
    "CH": "https://www.local.ch/en/q?what={query}&where={city}",
    "NL": "https://www.detelefoongids.nl/{query}/{city}/",
    "BE": "https://www.goudengids.be/nl/zoeken/{query}/{city}/",
    "SE": "https://www.hitta.se/s%C3%B6k?vad={query}&var={city}",
    "DK": "https://www.degulesider.dk/find/{query}/{city}/",
    "NO": "https://www.gulesider.no/{query}/{city}",
    "GB": "https://www.yell.com/ucs/UcsSearchAction.do?keywords={query}&location={city}",
    "FR": "https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={query}&ou={city}",
    "PL": "https://panoramafirm.pl/{query},{city}/firmy.html",
}


# ── DuckDuckGo search ────────────────────────────────────────────────────────
def ddg_search(query: str, max_results: int = 3) -> list:
    """Returns list of URLs from DuckDuckGo search."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return [r.get("href", "") for r in results if r.get("href")]
    except Exception:
        return []


def is_skippable(url: str) -> bool:
    """Returns True if URL should not be scraped."""
    if not url:
        return True
    for dom in SKIP_DOMAINS:
        if dom in url:
            return True
    return False


# ── Web scraper ──────────────────────────────────────────────────────────────
def scrape_contact_info(url: str, timeout: int = 8) -> Tuple[str, str]:
    """
    Scrapes a page for email + phone.
    Returns (email, phone) — empty string if not found.
    """
    if is_skippable(url):
        return "", ""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout,
                            allow_redirects=True)
        if resp.status_code != 200:
            return "", ""
        text = resp.text

        # Try contact/about/impressum subpages if main page has nothing
        emails = EMAIL_RE.findall(text)
        emails = [e for e in emails if not any(skip in e.lower() for skip in
                  ["example","test","noreply","no-reply","info@example","@sentry",
                   "@w3","@schema","@google","png","jpg","svg","gif","@email","@domain"])]

        phones = PHONE_RE.findall(text)
        phones = [p.strip() for p in phones if len(re.sub(r"\D","",p)) >= 7]

        found_email = emails[0] if emails else ""
        found_phone = phones[0] if phones else ""

        # If no contact info on main page, try /contact or /kontakt or /impressum
        if not found_email and not found_phone:
            base = url.rstrip("/")
            for subpath in ["/contact", "/kontakt", "/impressum",
                            "/about", "/uber-uns", "/contact-us", "/kontaktai"]:
                try:
                    r2 = requests.get(base + subpath, headers=HEADERS,
                                      timeout=6, allow_redirects=True)
                    if r2.status_code == 200:
                        e2 = EMAIL_RE.findall(r2.text)
                        e2 = [e for e in e2 if "@" in e and "." in e
                              and not any(x in e.lower() for x in
                              ["example","noreply","@sentry","@w3","@schema"])]
                        p2 = PHONE_RE.findall(r2.text)
                        p2 = [p.strip() for p in p2 if len(re.sub(r"\D","",p)) >= 7]
                        if e2: found_email = e2[0]
                        if p2: found_phone = p2[0]
                        if found_email:
                            break
                except Exception:
                    continue

        return found_email, found_phone

    except Exception:
        return "", ""


# ── Main enrichment logic ─────────────────────────────────────────────────────
def enrich_lead(lead: dict) -> Tuple[str, str, str]:
    """
    Try to find email + phone for a lead.
    Returns (email, phone, source).
    """
    name     = lead.get("name", "")
    city     = lead.get("city", "")
    country  = lead.get("country_code", "")
    category = lead.get("category", "")

    # Search queries to try (in order)
    queries = [
        f'"{name}" {city} contact email',
        f'"{name}" {city} {category}',
        f'{name} {city} email phone',
    ]

    for query in queries:
        urls = ddg_search(query, max_results=3)
        for url in urls:
            if is_skippable(url):
                continue
            email, phone = scrape_contact_info(url)
            if email or phone:
                return email, phone, url
        time.sleep(random.uniform(1.0, 2.0))

    return "", "", ""


# ── DB helpers ────────────────────────────────────────────────────────────────
def get_leads_to_enrich(
    country_code: str = None,
    missing: str = "both",
    limit: int = None
) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if missing == "email":
        where = "(email IS NULL OR email = '')"
    elif missing == "phone":
        where = "(phone IS NULL OR phone = '')"
    else:  # both — missing at least one
        where = "((email IS NULL OR email = '') OR (phone IS NULL OR phone = ''))"

    country_clause = ""
    params = []
    if country_code:
        country_clause = f"AND country_code = ?"
        params.append(country_code.upper())

    limit_clause = f"LIMIT {limit}" if limit else ""

    sql = f"""
        SELECT id, name, city, category, country, country_code,
               email, phone, address
        FROM leads
        WHERE {where} {country_clause}
        ORDER BY avg_revenue_eur DESC, id ASC
        {limit_clause}
    """
    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    conn.close()
    return rows


def update_lead(lead_id: int, email: str, phone: str, source: str):
    conn = sqlite3.connect(DB_PATH)
    updates = []
    params  = []
    if email:
        updates.append("email = ?")
        params.append(email)
        updates.append("status = 'EMAIL_FOUND'")
    if phone:
        updates.append("phone = ?")
        params.append(phone)
    if source:
        updates.append("notes = notes || ?")
        params.append(f" | enriched from: {source[:80]}")
    if updates:
        params.append(lead_id)
        conn.execute(f"UPDATE leads SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    conn.close()


# ── Runner ────────────────────────────────────────────────────────────────────
def run(country_code=None, missing="both", limit=None):
    leads = get_leads_to_enrich(country_code, missing, limit)

    print(f"\n{'='*65}")
    print(f"  LeadPulse EU — Contact Enrichment")
    print(f"  Leads to enrich: {len(leads)}")
    print(f"  Filter: country={country_code or 'ALL'}  missing={missing}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")

    found_email = 0
    found_phone = 0

    for i, lead in enumerate(leads, 1):
        flag = {"PL":"🇵🇱","DE":"🇩🇪","AT":"🇦🇹","CH":"🇨🇭","NL":"🇳🇱",
                "BE":"🇧🇪","SE":"🇸🇪","DK":"🇩🇰","NO":"🇳🇴","GB":"🇬🇧",
                "FR":"🇫🇷","IE":"🇮🇪"}.get(lead.get("country_code",""),"🌍")

        label = f"{lead['name'][:30]:<30} {lead['city'][:15]:<15}"
        print(f"  [{i:4}/{len(leads)}] {flag} {label} ...", end=" ", flush=True)

        email, phone, source = enrich_lead(lead)

        if email or phone:
            update_lead(lead["id"], email, phone, source)
            result = []
            if email: result.append(f"📧 {email[:35]}")
            if phone: result.append(f"📞 {phone[:15]}")
            print(" | ".join(result))
            if email: found_email += 1
            if phone: found_phone += 1
        else:
            print("—")

        # Respect rate limits
        time.sleep(random.uniform(2.0, 4.0))

        # Progress every 25 leads
        if i % 25 == 0:
            print(f"\n  ── Progress: {i}/{len(leads)} · "
                  f"emails found: {found_email} · phones found: {found_phone} ──\n")

    print(f"\n{'='*65}")
    print(f"  DONE")
    print(f"  Leads processed: {len(leads)}")
    print(f"  New emails:      {found_email}")
    print(f"  New phones:      {found_phone}")
    print(f"  Finished: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Enrich contact info for EU leads")
    p.add_argument("--country", default=None,     help="Country code e.g. DE GB PL")
    p.add_argument("--missing", default="both",   help="email | phone | both")
    p.add_argument("--limit",   type=int, default=None, help="Max leads to process")
    args = p.parse_args()
    run(country_code=args.country, missing=args.missing, limit=args.limit)
