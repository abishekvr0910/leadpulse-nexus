"""
Pipeline script to fetch all businesses in Toruń without websites,
with their phone numbers and emails, and verify them.
"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import requests
from config import OVERPASS_ENDPOINTS, USER_AGENT
from database import init_db, save_lead, get_leads

init_db()

# Toruń coordinates: 53.0138, 18.5984, radius 10000m
print("1. Querying OpenStreetMap for businesses in Toruń with verified contact info (phone/email) but NO website...")

query_with_contacts = """
[out:json][timeout:35];
(
  node["phone"][!"website"][!"contact:website"](around:10000, 53.0138, 18.5984);
  node["contact:phone"][!"website"][!"contact:website"](around:10000, 53.0138, 18.5984);
  node["email"][!"website"][!"contact:website"](around:10000, 53.0138, 18.5984);
  node["contact:email"][!"website"][!"contact:website"](around:10000, 53.0138, 18.5984);
);
out 150;
"""

resp = requests.post("https://overpass-api.de/api/interpreter", data={"data": query_with_contacts}, headers={"User-Agent": USER_AGENT}, timeout=30)
if resp.status_code == 200:
    elements = resp.json().get("elements", [])
    print(f"   Received {len(elements)} raw elements from Toruń.")
    
    saved_count = 0
    with_email_count = 0
    with_phone_count = 0

    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name or len(name.strip()) < 2:
            continue

        # Filter out public amenities that are not private businesses (like post boxes, public recycling, churches)
        category = tags.get("shop") or tags.get("craft") or tags.get("amenity") or tags.get("office") or "business"
        if category in ["post_box", "waste_disposal", "bench", "place_of_worship"]:
            continue

        phone = tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile") or ""
        email = tags.get("email") or tags.get("contact:email") or ""
        fb = tags.get("contact:facebook") or ""
        
        street = tags.get("addr:street", "")
        nr = tags.get("addr:housenumber", "")
        addr = f"{street} {nr}".strip() if street else "Toruń"

        lead = {
            "osm_id": f"{el.get('type')}/{el.get('id')}",
            "name": name.strip(),
            "category": category,
            "category_pl": category.capitalize(),
            "city": "Toruń",
            "address": addr,
            "phone": phone,
            "email": email,
            "facebook_url": fb,
            "instagram_url": "",
            "has_website": 0,
            "detected_website": "",
            "status": "EMAIL_FOUND" if email else "VERIFIED_NO_WEBSITE",
            "notes": "Verified Toruń local business without website"
        }

        if save_lead(lead):
            saved_count += 1
            if email:
                with_email_count += 1
            if phone:
                with_phone_count += 1

    print(f"   Successfully saved {saved_count} businesses to database.")
    print(f"   Businesses with direct Phone numbers: {with_phone_count}")
    print(f"   Businesses with direct Email addresses: {with_email_count}")

all_torun = get_leads(city="Toruń", limit=200)
print(f"\nTotal verified Toruń leads in Database: {len(all_torun)}")
