"""
scan_europe.py — Scans 50 European cities across 11 high-income countries.
Finds SMBs without websites and saves them to leads.db.

Usage:
    python scan_europe.py                     # scan all (priority order)
    python scan_europe.py --country DE        # only Germany
    python scan_europe.py --country GB        # only UK
    python scan_europe.py --tier 1            # only top 10 cities
    python scan_europe.py --city zurich       # single city test
    python scan_europe.py --limit 30          # max leads per city
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import time
import random
import argparse
import sqlite3
import requests
from typing import List, Dict, Any
from datetime import datetime

from europe_config import EUROPEAN_CITIES, SCAN_PRIORITY
from config import DB_PATH, USER_AGENT

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]

# OSM tags — businesses that typically DON'T have websites
# Using plain ASCII quotes (NOT smart quotes) — critical for Overpass API
OSM_TAGS_NO_WEBSITE = [
    'node["shop"="hairdresser"][!"website"][!"contact:website"]',
    'node["shop"="beauty"][!"website"][!"contact:website"]',
    'node["craft"="car_repair"][!"website"][!"contact:website"]',
    'node["amenity"="dentist"][!"website"][!"contact:website"]',
    'node["amenity"="restaurant"][!"website"][!"contact:website"]',
    'node["amenity"="cafe"][!"website"][!"contact:website"]',
    'node["shop"="florist"][!"website"][!"contact:website"]',
    'node["shop"="bakery"][!"website"][!"contact:website"]',
    'node["shop"="optician"][!"website"][!"contact:website"]',
    'node["craft"="electrician"][!"website"][!"contact:website"]',
    'node["craft"="plumber"][!"website"][!"contact:website"]',
    'node["amenity"="veterinary"][!"website"][!"contact:website"]',
    'node["shop"="clothes"][!"website"][!"contact:website"]',
    'node["shop"="electronics"][!"website"][!"contact:website"]',
    'node["amenity"="pharmacy"][!"website"][!"contact:website"]',
    'node["shop"="massage"][!"website"][!"contact:website"]',
    'node["shop"="pet"][!"website"][!"contact:website"]',
    'node["amenity"="bar"][!"website"][!"contact:website"]',
    'node["shop"="shoes"][!"website"][!"contact:website"]',
    'node["shop"="furniture"][!"website"][!"contact:website"]',
    'node["craft"="carpenter"][!"website"][!"contact:website"]',
    'node["craft"="photographer"][!"website"][!"contact:website"]',
    'node["leisure"="fitness_centre"][!"website"][!"contact:website"]',
    'node["amenity"="fast_food"][!"website"][!"contact:website"]',
    'node["shop"="jewelry"][!"website"][!"contact:website"]',
]

# Also try WITHOUT the no-website filter (some EU cities tag differently)
OSM_TAGS_ANY = [
    'node["shop"="hairdresser"]',
    'node["shop"="beauty"]',
    'node["craft"="car_repair"]',
    'node["amenity"="dentist"]',
    'node["amenity"="restaurant"]',
    'node["amenity"="cafe"]',
    'node["shop"="florist"]',
    'node["shop"="bakery"]',
    'node["craft"="electrician"]',
    'node["craft"="plumber"]',
    'node["shop"="optician"]',
    'node["amenity"="veterinary"]',
    'node["shop"="clothes"]',
    'node["shop"="electronics"]',
    'node["amenity"="pharmacy"]',
]


def query_city(city_key: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Query Overpass API for businesses in a city. Falls back to broader query if needed."""
    city = EUROPEAN_CITIES[city_key]
    lat, lon, radius = city["lat"], city["lon"], city["radius"]

    # Try with no-website filter first
    subqueries_strict = "\n  ".join(
        [f'{tag}(around:{radius},{lat},{lon});' for tag in OSM_TAGS_NO_WEBSITE]
    )
    query_strict = f"""[out:json][timeout:30];
(
  {subqueries_strict}
);
out {limit};"""

    # Broader fallback — gets all, we filter website presence ourselves later
    subqueries_broad = "\n  ".join(
        [f'{tag}(around:{radius},{lat},{lon});' for tag in OSM_TAGS_ANY]
    )
    query_broad = f"""[out:json][timeout:30];
(
  {subqueries_broad}
);
out {limit};"""

    headers = {"User-Agent": USER_AGENT}

    for attempt, query in [(1, query_strict), (2, query_broad)]:
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                resp = requests.post(
                    endpoint,
                    data={"data": query},
                    headers=headers,
                    timeout=30
                )
                if resp.status_code == 200:
                    elements = resp.json().get("elements", [])
                    if elements:
                        return elements
                elif resp.status_code == 429:
                    time.sleep(4)
                    continue
            except Exception:
                continue
        time.sleep(1.5)

    return []


def parse_leads(elements: List[Dict], city_key: str) -> List[Dict[str, Any]]:
    """Parse OSM elements into lead dicts, filtering out businesses that have websites."""
    city = EUROPEAN_CITIES[city_key]
    leads = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name", "").strip()
        if not name or len(name) < 2:
            continue

        # Skip if they already have a website
        if tags.get("website") or tags.get("contact:website"):
            continue

        raw_cat = (
            tags.get("shop") or tags.get("craft") or
            tags.get("amenity") or tags.get("leisure") or "business"
        )
        street = tags.get("addr:street", "")
        house  = tags.get("addr:housenumber", "")
        postcode = tags.get("addr:postcode", "")
        address = f"{street} {house}".strip() or city["name"]
        if postcode:
            address = f"{address}, {postcode}".strip(", ")

        phone = (
            tags.get("phone") or tags.get("contact:phone") or
            tags.get("contact:mobile") or ""
        )
        email = tags.get("email") or tags.get("contact:email") or ""
        fb    = tags.get("contact:facebook") or ""
        ig    = tags.get("contact:instagram") or ""

        leads.append({
            "osm_id":           f"{el.get('type')}/{el.get('id')}",
            "name":             name,
            "category":         raw_cat,
            "category_pl":      raw_cat.replace("_", " ").title(),
            "city":             city["name"],
            "address":          address,
            "phone":            phone,
            "email":            email,
            "facebook_url":     fb,
            "instagram_url":    ig,
            "has_website":      0,
            "detected_website": "",
            "status":           "EMAIL_FOUND" if email else "NEW",
            "notes":            f"OSM scan — {city['country']} (no website)",
            "country":          city["country"],
            "country_code":     city["country_code"],
            "language":         city["language"],
            "currency":         city["currency"],
            "avg_revenue_eur":  city["avg_revenue_eur"],
        })
    return leads


def save_leads(leads: List[Dict]) -> int:
    """Upsert leads into database. Returns count saved."""
    if not leads:
        return 0
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()
    saved = 0
    for lead in leads:
        try:
            c.execute("""
                INSERT INTO leads (
                    osm_id, name, category, category_pl, city, address,
                    phone, email, facebook_url, instagram_url,
                    has_website, detected_website, status, notes,
                    country, country_code, language, currency, avg_revenue_eur
                ) VALUES (
                    :osm_id, :name, :category, :category_pl, :city, :address,
                    :phone, :email, :facebook_url, :instagram_url,
                    :has_website, :detected_website, :status, :notes,
                    :country, :country_code, :language, :currency, :avg_revenue_eur
                )
                ON CONFLICT(osm_id) DO UPDATE SET
                    phone    = COALESCE(excluded.phone, leads.phone),
                    email    = COALESCE(excluded.email, leads.email),
                    country  = excluded.country,
                    country_code = excluded.country_code,
                    language = excluded.language,
                    currency = excluded.currency,
                    avg_revenue_eur = excluded.avg_revenue_eur
            """, lead)
            saved += 1
        except Exception as e:
            pass
    conn.commit()
    conn.close()
    return saved


def run(country_filter=None, city_filter=None, tier=None, limit=50):
    # Build city list
    if city_filter:
        cities = [city_filter] if city_filter in EUROPEAN_CITIES else []
    elif country_filter:
        cities = [k for k, v in EUROPEAN_CITIES.items()
                  if v["country_code"] == country_filter.upper()]
    elif tier:
        tier_sizes = {1: 10, 2: 20, 3: 35, 4: len(SCAN_PRIORITY)}
        cities = SCAN_PRIORITY[:tier_sizes.get(tier, len(SCAN_PRIORITY))]
    else:
        cities = SCAN_PRIORITY

    print(f"\n{'='*65}")
    print(f"  🌍 LeadPulse Europe Scanner")
    print(f"  Cities: {len(cities)} | Max per city: {limit}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")

    total_found = 0
    total_saved = 0

    flags = {
        "DE":"🇩🇪","AT":"🇦🇹","CH":"🇨🇭","NL":"🇳🇱","BE":"🇧🇪",
        "SE":"🇸🇪","DK":"🇩🇰","NO":"🇳🇴","GB":"🇬🇧","FR":"🇫🇷","IE":"🇮🇪"
    }

    for i, city_key in enumerate(cities, 1):
        if city_key not in EUROPEAN_CITIES:
            continue
        city = EUROPEAN_CITIES[city_key]
        flag = flags.get(city["country_code"], "🌍")
        label = f"{flag} {city['name']:<14} ({city['country_code']})"

        print(f"  [{i:2}/{len(cities)}] {label} ...", end=" ", flush=True)

        try:
            elements = query_city(city_key, limit=limit)
            leads    = parse_leads(elements, city_key)
            saved    = save_leads(leads)
            total_found += len(leads)
            total_saved += saved
            print(f"found {len(leads):3}  saved {saved:3}")
        except Exception as e:
            print(f"ERROR: {str(e)[:50]}")

        if i < len(cities):
            time.sleep(random.uniform(1.2, 2.0))

    print(f"\n{'='*65}")
    print(f"  DONE — Found: {total_found:,}  Saved: {total_saved:,}")
    print(f"  Finished: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--country", default=None)
    p.add_argument("--city",    default=None)
    p.add_argument("--tier",    type=int, default=None)
    p.add_argument("--limit",   type=int, default=50)
    args = p.parse_args()
    run(country_filter=args.country, city_filter=args.city,
        tier=args.tier, limit=args.limit)
