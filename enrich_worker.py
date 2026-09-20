"""
enrich_worker.py — Continuous High-Trust Decision-Maker Enrichment Worker
========================================================================
Runs continuous background enrichment cycles targeting high-ticket niches:
  1. Dental Clinics & Surgeries (UK, DE, PL, FR)
  2. Auto Repair & Diagnostics
  3. Emergency Trades (Plumbing, Electricians)
  4. Aesthetics & Salons

Uses delicate trust filters (territory match, negative role filter, registry numbers).
"""
import os
import sys
import time
import random
import sqlite3
from find_people import discover_people_for_company, save_contacts_to_db

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")

def get_unenriched_leads(category=None, country=None, limit=25):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    where = ["(contacts_count IS NULL OR contacts_count = 0)"]
    params = []
    
    if category and category != "ALL":
        if category == "dentist":
            where.append("category IN ('dentist', 'dentists')")
        else:
            where.append("category = ?")
            params.append(category)
            
    if country and country != "ALL":
        where.append("(country = ? OR country_code = ?)")
        params.extend([country, country])
        
    where_str = " AND ".join(where)
    sql = f"""
        SELECT id, name, category, city, country, country_code, phone, email, has_website, detected_website
        FROM leads 
        WHERE {where_str}
        ORDER BY CASE WHEN phone IS NOT NULL AND phone != '' THEN 0 ELSE 1 END, id ASC
        LIMIT ?
    """
    params.append(limit)
    c.execute(sql, params)
    leads = [dict(r) for r in c.fetchall()]
    conn.close()
    return leads

def run_continuous_enrichment(category="dentist", country="GB", total_target=100, pause_sec=2):
    print(f"[*] Starting Continuous Enrichment: Target={total_target}, Category={category}, Country={country}")
    enriched_total = 0
    
    while enriched_total < total_target:
        batch = get_unenriched_leads(category=category, country=country, limit=10)
        if not batch:
            print("[✓] All leads in this criteria are already enriched.")
            break
            
        for lead in batch:
            try:
                print(f"[{enriched_total+1}/{total_target}] Enriching {lead['name'][:30]} ({lead.get('city', 'Unknown')})...", end="", flush=True)
                contacts, reg = discover_people_for_company(lead)
                saved = save_contacts_to_db(lead["id"], contacts, reg)
                print(f" Found {len(contacts)} contacts (Reg: {reg or 'N/A'})")
                enriched_total += 1
                time.sleep(random.uniform(pause_sec, pause_sec + 1.5))
            except Exception as e:
                print(f" Error: {e}")
                time.sleep(2)
                
            if enriched_total >= total_target:
                break
                
    print(f"[✓] Continuous batch completed. Enriched {enriched_total} companies.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="dentist")
    parser.add_argument("--country", default="GB")
    parser.add_argument("--total", type=int, default=25)
    args = parser.parse_args()
    
    run_continuous_enrichment(category=args.category, country=args.country, total_target=args.total)
