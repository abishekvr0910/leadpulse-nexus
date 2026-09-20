"""
verify_batch.py — Re-verify that companies still have no website before emailing.
Runs a quick DuckDuckGo search for each lead and updates the database.

Usage:
    python verify_batch.py --limit 50
    python verify_batch.py --city torun --limit 20
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import sqlite3
import time
import random
from datetime import datetime

DB_PATH = r"S:\APPs\lead-finder\leads.db"


def get_leads_to_verify(city=None, limit=50):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    q = """
        SELECT * FROM leads
        WHERE has_website = 0
          AND (email IS NOT NULL AND email != '' AND email != 'N/A')
          AND (email_stage IS NULL OR email_stage = 'NONE' OR email_stage = '')
    """
    params = []
    if city:
        q += " AND LOWER(city) LIKE ?"
        params.append(f"%{city.lower()}%")
    q += " ORDER BY id LIMIT ?"
    params.append(limit)

    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_lead(lead_id, has_website, detected_website, status, notes):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        UPDATE leads
        SET has_website=?, detected_website=?, status=?, notes=?
        WHERE id=?
    """, (has_website, detected_website, status, notes, lead_id))
    conn.commit()
    conn.close()


def verify_one(lead):
    """Re-verify a single lead via DuckDuckGo search."""
    import sys, os
    sys.path.insert(0, r"S:\APPs\lead-finder")
    from scraper import verify_and_enrich_lead, is_independent_website

    try:
        from ddgs import DDGS
        ddgs = DDGS()
        name = lead["name"]
        city = lead["city"]

        # Quick Google-style check
        query = f'"{name}" {city} site'
        results = list(ddgs.text(query, max_results=5))

        for r in results:
            url = r.get("href", "")
            if is_independent_website(url, name):
                return {
                    "has_website": 1,
                    "detected_website": url,
                    "status": "HAS_WEBSITE",
                    "notes": f"Website found during re-verify: {url}"
                }

        return {
            "has_website": 0,
            "detected_website": "",
            "status": lead.get("status", "VERIFIED_NO_WEBSITE"),
            "notes": "Re-verified: still no independent website found."
        }

    except Exception as e:
        return {
            "has_website": 0,
            "detected_website": "",
            "status": lead.get("status", "VERIFIED_NO_WEBSITE"),
            "notes": f"Re-verify skipped: {str(e)[:60]}"
        }


def run(city=None, limit=50, dry_run=False):
    leads = get_leads_to_verify(city=city, limit=limit)
    print(f"\n🔍 Verifying {len(leads)} leads (dry_run={dry_run})...\n")

    still_no_site = 0
    found_site = 0
    errors = 0

    for i, lead in enumerate(leads, 1):
        result = verify_one(lead)

        if result["has_website"] == 1:
            found_site += 1
            tag = "❌ HAS WEBSITE — will be excluded"
        else:
            still_no_site += 1
            tag = "✅ Confirmed no website"

        print(f"[{i:3}/{len(leads)}] {lead['name'][:35]:<35} {lead['city']:<15} {tag}")

        if not dry_run:
            update_lead(
                lead["id"],
                result["has_website"],
                result["detected_website"],
                result["status"],
                result["notes"],
            )

        # Rate limit: DuckDuckGo throttles fast queries
        if i < len(leads):
            time.sleep(random.uniform(1.5, 3.0))

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Still no website (safe to email): {still_no_site}
❌ Website found (removed from list): {found_site}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Re-verify leads before emailing")
    parser.add_argument("--city", default=None, help="Filter by city (e.g. torun)")
    parser.add_argument("--limit", type=int, default=50, help="Max leads to verify")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to DB")
    args = parser.parse_args()
    run(city=args.city, limit=args.limit, dry_run=args.dry_run)
