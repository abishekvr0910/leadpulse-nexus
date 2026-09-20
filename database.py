"""
Database module for managing leads with SQLite.
"""
import sqlite3
import csv
from datetime import datetime
from typing import List, Dict, Optional, Any
from config import DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema if not already present."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                osm_id TEXT UNIQUE,
                name TEXT NOT NULL,
                category TEXT,
                category_pl TEXT,
                city TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                facebook_url TEXT,
                instagram_url TEXT,
                has_website INTEGER DEFAULT 0,
                detected_website TEXT,
                status TEXT DEFAULT 'NEW',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contacted_at TIMESTAMP
            )
        """)
        conn.commit()

def save_lead(lead: Dict[str, Any]) -> bool:
    """Inserts or updates a lead based on osm_id or unique name+city."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO leads (
                    osm_id, name, category, category_pl, city, address, phone, email,
                    facebook_url, instagram_url, has_website, detected_website, status, notes
                ) VALUES (
                    :osm_id, :name, :category, :category_pl, :city, :address, :phone, :email,
                    :facebook_url, :instagram_url, :has_website, :detected_website, :status, :notes
                )
                ON CONFLICT(osm_id) DO UPDATE SET
                    phone = COALESCE(excluded.phone, leads.phone),
                    email = COALESCE(excluded.email, leads.email),
                    facebook_url = COALESCE(excluded.facebook_url, leads.facebook_url),
                    has_website = excluded.has_website,
                    detected_website = excluded.detected_website,
                    status = excluded.status,
                    notes = COALESCE(excluded.notes, leads.notes)
            """, lead)
            conn.commit()
            return True
        except Exception as e:
            # If osm_id is None, check duplicate by name and city
            return False

def get_leads(
    status: Optional[str] = None,
    city: Optional[str] = None,
    has_website: Optional[bool] = None,
    has_email: Optional[bool] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Fetches filtered leads from the database."""
    query = "SELECT * FROM leads WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if city:
        from config import POLISH_CITIES
        city_clean = city.lower()
        if city_clean in POLISH_CITIES:
            target_city = POLISH_CITIES[city_clean]["name"]
            query += " AND (LOWER(city) = LOWER(?) OR LOWER(city) = LOWER(?))"
            params.extend([city, target_city])
        else:
            query += " AND LOWER(city) = LOWER(?)"
            params.append(city)
    if has_website is not None:
        query += " AND has_website = ?"
        params.append(1 if has_website else 0)
    if has_email is True:
        query += " AND email IS NOT NULL AND email != '' AND email != 'N/A'"
    elif has_email is False:
        query += " AND (email IS NULL OR email = '' OR email = 'N/A')"

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def update_lead_status(lead_id: int, status: str, notes: Optional[str] = None, email: Optional[str] = None):
    with get_connection() as conn:
        cursor = conn.cursor()
        query = "UPDATE leads SET status = ?"
        params = [status]

        if notes:
            query += ", notes = ?"
            params.append(notes)
        if email:
            query += ", email = ?"
            params.append(email)
        if status == "CONTACTED":
            query += ", contacted_at = CURRENT_TIMESTAMP"

        query += " WHERE id = ?"
        params.append(lead_id)

        cursor.execute(query, params)
        conn.commit()

def export_to_csv(output_path: str = "leads_export.csv", only_no_website: bool = True, city: Optional[str] = None) -> int:
    """Exports leads to a CSV file with personalized outreach email content included."""
    from email_templates import render_email
    leads = get_leads(city=city, has_website=False if only_no_website else None, limit=10000)
    if not leads:
        return 0

    fields = [
        "id", "name", "category_pl", "city", "address", "phone", "email",
        "facebook_url", "has_website", "status", "email_subject", "email_pitch", "notes", "created_at"
    ]

    with open(output_path, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            rendered = render_email(lead)
            lead_row = dict(lead)
            lead_row["email_subject"] = rendered["subject"]
            lead_row["email_pitch"] = rendered["body"]
            writer.writerow(lead_row)

    return len(leads)
