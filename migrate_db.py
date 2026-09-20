"""
Database migration script — adds email outreach tracking columns.
Run once. Safe to re-run (uses IF NOT EXISTS / try-except).
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")

MIGRATIONS = [
    # Track which email stage we're at
    "ALTER TABLE leads ADD COLUMN email_stage TEXT DEFAULT 'NONE'",
    # When each email was sent
    "ALTER TABLE leads ADD COLUMN initial_sent_at TIMESTAMP",
    "ALTER TABLE leads ADD COLUMN followup1_sent_at TIMESTAMP",
    "ALTER TABLE leads ADD COLUMN followup2_sent_at TIMESTAMP",
    # Reply tracking
    "ALTER TABLE leads ADD COLUMN reply_received INTEGER DEFAULT 0",
    "ALTER TABLE leads ADD COLUMN reply_type TEXT DEFAULT ''",
    "ALTER TABLE leads ADD COLUMN reply_notes TEXT DEFAULT ''",
    "ALTER TABLE leads ADD COLUMN reply_received_at TIMESTAMP",
    # Template used
    "ALTER TABLE leads ADD COLUMN template_used TEXT DEFAULT ''",
]

def run_migrations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    applied = 0
    skipped = 0
    for sql in MIGRATIONS:
        try:
            c.execute(sql)
            applied += 1
            col_name = sql.split("ADD COLUMN ")[1].split(" ")[0]
            print(f"  ✅ Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                skipped += 1
            else:
                print(f"  ❌ Error: {e}")

    conn.commit()
    conn.close()
    print(f"\nMigration complete: {applied} applied, {skipped} already existed.")

if __name__ == "__main__":
    print(f"Running migrations on {DB_PATH}...")
    run_migrations()
