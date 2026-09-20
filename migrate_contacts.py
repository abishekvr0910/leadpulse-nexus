"""
migrate_contacts.py — Adds company_contacts table and decision-maker fields to leads.
"""
import sys, sqlite3
sys.stdout.reconfigure(encoding="utf-8")

DB_PATH = r"S:\APPs\lead-finder\leads.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# 1. Create company_contacts table (supports multiple people per company)
c.execute("""
CREATE TABLE IF NOT EXISTS company_contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER,
    company_name TEXT,
    person_name TEXT,
    role_title TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    company_registration TEXT,
    notes TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads(id)
)
""")
c.execute("CREATE INDEX IF NOT EXISTS idx_contacts_lead ON company_contacts(lead_id)")
print("✅ Created table company_contacts & index")

# 2. Add decision-maker summary columns to leads table
lead_cols = [
    ("primary_contact_name", "TEXT DEFAULT ''"),
    ("primary_contact_title", "TEXT DEFAULT ''"),
    ("primary_contact_email", "TEXT DEFAULT ''"),
    ("primary_contact_linkedin", "TEXT DEFAULT ''"),
    ("company_reg_number", "TEXT DEFAULT ''"),
    ("contacts_count", "INTEGER DEFAULT 0"),
]

for col_name, col_type in lead_cols:
    try:
        c.execute(f"ALTER TABLE leads ADD COLUMN {col_name} {col_type}")
        print(f"  ✅ Added column leads.{col_name}")
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"  ⏭  Column already exists: leads.{col_name}")
        else:
            print(f"  ❌ Error on leads.{col_name}: {e}")

conn.commit()
conn.close()
print("🎉 Contacts migration complete!")
