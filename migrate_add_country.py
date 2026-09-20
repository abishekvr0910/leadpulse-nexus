"""
migrate_add_country.py — Adds country tracking columns to leads table.
Safe to re-run.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import sqlite3, os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")

MIGRATIONS = [
    "ALTER TABLE leads ADD COLUMN country TEXT DEFAULT 'Poland'",
    "ALTER TABLE leads ADD COLUMN country_code TEXT DEFAULT 'PL'",
    "ALTER TABLE leads ADD COLUMN language TEXT DEFAULT 'pl'",
    "ALTER TABLE leads ADD COLUMN currency TEXT DEFAULT 'PLN'",
    "ALTER TABLE leads ADD COLUMN avg_revenue_eur INTEGER DEFAULT 800",
]

conn = sqlite3.connect(DB_PATH)
applied = 0
for sql in MIGRATIONS:
    try:
        conn.execute(sql)
        col = sql.split("ADD COLUMN ")[1].split(" ")[0]
        print(f"  ✅ Added: {col}")
        applied += 1
    except sqlite3.OperationalError as e:
        if "duplicate column" in str(e).lower():
            print(f"  ⏭  Already exists: {sql.split('ADD COLUMN ')[1].split(' ')[0]}")
        else:
            print(f"  ❌ Error: {e}")
conn.commit()
conn.close()
print(f"\nDone: {applied} columns added.")
