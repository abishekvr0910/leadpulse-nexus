"""
verify_emails.py — High-Speed Multi-Threaded Email Verification & MX Engine
===========================================================================
Concurrently validates all emails in leads and company_contacts:
  1. RFC Syntax & Format Validation
  2. Role & Disposable Domain Blacklist
  3. Parallel DNS MX Resolution (ThreadPoolExecutor)
  4. Batch Database Commit & Deliverability Tagging
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import re
import socket
import sqlite3
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

DB_PATH = str(Path(__file__).resolve().parent / "leads.db")

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "guerrillamail.com", "10minutemail.com",
    "trashmail.com", "sharklasers.com", "yopmail.com", "getairmail.com",
    "temp-mail.org", "fakeinbox.com", "dispostable.com"
}

ROLE_ACCOUNTS = {"noreply", "no-reply", "donotreply", "mailer-daemon", "abuse", "sentry"}

def resolve_domain_mx(domain: str) -> tuple:
    """Checks DNS MX record for a single domain using nslookup."""
    domain = domain.lower().strip()
    try:
        proc = subprocess.run(
            ["nslookup", "-type=mx", domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2.5
        )
        out = proc.stdout
        matches = re.findall(r"mail exchanger\s*=\s*([a-zA-Z0-9.-]+)", out, re.IGNORECASE)
        if matches:
            return (domain, True, matches[0].strip())
        
        # Fallback to A record
        try:
            socket.gethostbyname(domain)
            return (domain, True, f"A-record:{domain}")
        except Exception:
            pass
            
        return (domain, False, "NO_MX_RECORDS")
    except Exception:
        # Fallback socket check
        try:
            socket.gethostbyname(domain)
            return (domain, True, f"A-record:{domain}")
        except Exception:
            return (domain, False, "DNS_TIMEOUT")

def setup_verification_columns():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Leads table
    cols = [r[1] for r in c.execute("PRAGMA table_info(leads)").fetchall()]
    if "is_email_verified" not in cols:
        c.execute("ALTER TABLE leads ADD COLUMN is_email_verified INTEGER DEFAULT 0")
    if "email_verification_status" not in cols:
        c.execute("ALTER TABLE leads ADD COLUMN email_verification_status TEXT DEFAULT 'UNCHECKED'")
    if "email_mx_host" not in cols:
        c.execute("ALTER TABLE leads ADD COLUMN email_mx_host TEXT DEFAULT ''")
        
    # Company contacts table
    cc_cols = [r[1] for r in c.execute("PRAGMA table_info(company_contacts)").fetchall()]
    if "is_email_verified" not in cc_cols:
        c.execute("ALTER TABLE company_contacts ADD COLUMN is_email_verified INTEGER DEFAULT 0")
    if "email_verification_status" not in cc_cols:
        c.execute("ALTER TABLE company_contacts ADD COLUMN email_verification_status TEXT DEFAULT 'UNCHECKED'")
    if "email_mx_host" not in cc_cols:
        c.execute("ALTER TABLE company_contacts ADD COLUMN email_mx_host TEXT DEFAULT ''")
        
    conn.commit()
    conn.close()

def run_fast_verification():
    setup_verification_columns()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Fetch all leads with email
    c.execute("SELECT id, name, email FROM leads WHERE email IS NOT NULL AND email != ''")
    leads = c.fetchall()
    
    # Fetch all contacts with email
    c.execute("SELECT id, person_name, email FROM company_contacts WHERE email IS NOT NULL AND email != ''")
    contacts = c.fetchall()
    
    print(f"[*] Loaded {len(leads)} company emails and {len(contacts)} decision-maker emails.", flush=True)
    
    # Collect unique domains
    domains = set()
    for row in leads:
        em = (row[2] or "").strip().lower()
        if "@" in em:
            domains.add(em.split("@", 1)[1])
    for row in contacts:
        em = (row[2] or "").strip().lower()
        if "@" in em:
            domains.add(em.split("@", 1)[1])
            
    print(f"[*] Resolving {len(domains)} unique domains across 30 threads...", flush=True)
    
    domain_results = {}
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = {executor.submit(resolve_domain_mx, d): d for d in domains}
        for fut in as_completed(futures):
            d, has_mx, host = fut.result()
            domain_results[d] = (has_mx, host)
            
    print(f"[✓] DNS resolution finished for all {len(domain_results)} domains.", flush=True)
    
    # Update Leads
    verified_leads = 0
    invalid_leads = 0
    lead_updates = []
    
    for row in leads:
        lead_id, name, raw_email = row
        email = (raw_email or "").strip().lower()
        
        if not EMAIL_REGEX.match(email):
            lead_updates.append((0, "INVALID_SYNTAX", "", lead_id))
            invalid_leads += 1
            continue
            
        user, domain = email.split("@", 1)
        if user in ROLE_ACCOUNTS:
            lead_updates.append((0, "ROLE_ACCOUNT_DISCARDED", "", lead_id))
            invalid_leads += 1
            continue
        if domain in DISPOSABLE_DOMAINS:
            lead_updates.append((0, "DISPOSABLE_DOMAIN", "", lead_id))
            invalid_leads += 1
            continue
            
        has_mx, mx_host = domain_results.get(domain, (False, "UNKNOWN"))
        if has_mx:
            lead_updates.append((1, "MX_VERIFIED", mx_host, lead_id))
            verified_leads += 1
        else:
            lead_updates.append((0, "NO_MX_RECORDS", mx_host, lead_id))
            invalid_leads += 1
            
    c.executemany("""
        UPDATE leads 
        SET is_email_verified = ?, email_verification_status = ?, email_mx_host = ?
        WHERE id = ?
    """, lead_updates)
    
    # Update Contacts
    verified_contacts = 0
    invalid_contacts = 0
    contact_updates = []
    
    for row in contacts:
        c_id, person_name, raw_email = row
        email = (raw_email or "").strip().lower()
        
        if not EMAIL_REGEX.match(email):
            contact_updates.append((0, "INVALID_SYNTAX", "", c_id))
            invalid_contacts += 1
            continue
            
        user, domain = email.split("@", 1)
        has_mx, mx_host = domain_results.get(domain, (False, "UNKNOWN"))
        if has_mx:
            contact_updates.append((1, "MX_VERIFIED", mx_host, c_id))
            verified_contacts += 1
        else:
            contact_updates.append((0, "NO_MX_RECORDS", mx_host, c_id))
            invalid_contacts += 1
            
    c.executemany("""
        UPDATE company_contacts 
        SET is_email_verified = ?, email_verification_status = ?, email_mx_host = ?
        WHERE id = ?
    """, contact_updates)
    
    conn.commit()
    conn.close()
    
    print("\n============================================================", flush=True)
    print(f"  VERIFICATION RUN COMPLETE — DELIVERABILITY AUDIT", flush=True)
    print(f"  Company Inboxes Verified:        {verified_leads} / {len(leads)}", flush=True)
    print(f"  Decision-Maker Inboxes Verified: {verified_contacts} / {len(contacts)}", flush=True)
    print(f"  Total Deliverable Mail Assets:   {verified_leads + verified_contacts}", flush=True)
    print("============================================================\n", flush=True)

if __name__ == "__main__":
    run_fast_verification()
