"""
scrape_yelp.py — Uses Yelp Fusion API to get businesses for UK, France,
Netherlands, Belgium, Sweden, Norway, Denmark, Ireland.

FREE tier: 500 API calls/day — each call returns up to 50 businesses.
= 25,000 businesses/day on free tier.

Setup (one time):
  1. Go to https://www.yelp.com/developers/v3/manage_app
  2. Create a free app → get API key
  3. Set environment variable or paste below:
     YELP_API_KEY=your_key_here

Usage:
    python scrape_yelp.py --country GB --limit 50
    python scrape_yelp.py --country FR
    python scrape_yelp.py --country ALL
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import os, time, random, argparse, sqlite3, requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ── PASTE YOUR YELP API KEY HERE ─────────────────────────────────────────────
YELP_API_KEY = os.getenv("YELP_API_KEY", "YOUR_YELP_KEY_HERE")
YELP_ENDPOINT = "https://api.yelp.com/v3/businesses/search"

DB_PATH = str(BASE_DIR / "leads.db")

COUNTRY_INFO = {
    "GB": {"country":"United Kingdom","language":"en","currency":"GBP","avg_revenue_eur":3200,"locale":"en_GB"},
    "FR": {"country":"France",        "language":"fr","currency":"EUR","avg_revenue_eur":2800,"locale":"fr_FR"},
    "NL": {"country":"Netherlands",   "language":"nl","currency":"EUR","avg_revenue_eur":3200,"locale":"nl_NL"},
    "BE": {"country":"Belgium",       "language":"nl","currency":"EUR","avg_revenue_eur":2800,"locale":"nl_BE"},
    "SE": {"country":"Sweden",        "language":"sv","currency":"SEK","avg_revenue_eur":3200,"locale":"sv_SE"},
    "NO": {"country":"Norway",        "language":"no","currency":"NOK","avg_revenue_eur":4200,"locale":"nb_NO"},
    "DK": {"country":"Denmark",       "language":"da","currency":"DKK","avg_revenue_eur":3800,"locale":"da_DK"},
    "IE": {"country":"Ireland",       "language":"en","currency":"EUR","avg_revenue_eur":3500,"locale":"en_IE"},
    "AT": {"country":"Austria",       "language":"de","currency":"EUR","avg_revenue_eur":2800,"locale":"de_AT"},
    "CH": {"country":"Switzerland",   "language":"de","currency":"CHF","avg_revenue_eur":4500,"locale":"de_CH"},
    "IT": {"country":"Italy",         "language":"it","currency":"EUR","avg_revenue_eur":2000,"locale":"it_IT"},
    "ES": {"country":"Spain",         "language":"es","currency":"EUR","avg_revenue_eur":1800,"locale":"es_ES"},
}

COUNTRY_CITIES = {
    "GB": ["London","Manchester","Birmingham","Leeds","Glasgow","Edinburgh","Bristol","Sheffield","Liverpool","Cardiff"],
    "FR": ["Paris","Lyon","Marseille","Toulouse","Bordeaux","Nantes","Strasbourg","Montpellier","Nice","Rennes"],
    "NL": ["Amsterdam","Rotterdam","Den Haag","Utrecht","Eindhoven","Tilburg","Groningen"],
    "BE": ["Brussels","Antwerp","Ghent","Bruges","Liège"],
    "SE": ["Stockholm","Gothenburg","Malmö","Uppsala","Västerås"],
    "NO": ["Oslo","Bergen","Trondheim","Stavanger"],
    "DK": ["Copenhagen","Aarhus","Odense","Aalborg"],
    "IE": ["Dublin","Cork","Galway","Limerick"],
    "AT": ["Vienna","Graz","Linz","Salzburg","Innsbruck"],
    "CH": ["Zurich","Bern","Basel","Geneva","Lausanne"],
    "IT": ["Rome","Milan","Naples","Turin","Florence","Bologna"],
    "ES": ["Madrid","Barcelona","Valencia","Seville","Bilbao","Málaga"],
}

# High-ticket AI phone/voice agent target categories
HIGH_TICKET_CATEGORIES = [
    "dentists",       # Missed appointment = €200-€1000 lost
    "autorepair",     # Dirty hands, loud shop, misses 40%+ of calls
    "beautysvc",      # Busy with treatments, can't pick up
    "hairstylists",   # Busy styling, booking appointments
    "restaurants",    # Busy dinner rush, table reservations
    "plumbing",       # Emergency callouts, always driving/working
    "electricians",   # Urgent jobs, high hourly rate
]

# All Yelp business categories
YELP_CATEGORIES = HIGH_TICKET_CATEGORIES + [
    "cafes", "florists", "bakeries", "opticians",
    "fitness", "petservices", "photographers", "massage", "food"
]



def yelp_search(term_or_category, location, country_code, limit=50, offset=0):
    """Call Yelp Fusion API for businesses in a location."""
    if YELP_API_KEY == "YOUR_YELP_KEY_HERE":
        return []

    info = COUNTRY_INFO.get(country_code, {})
    params = {
        "location":   f"{location}, {info.get('country', '')}",
        "categories": term_or_category,
        "limit":      min(limit, 50),
        "offset":     offset,
        "locale":     info.get("locale", "en_US"),
    }
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    try:
        r = requests.get(YELP_ENDPOINT, headers=headers, params=params, timeout=12)
        if r.status_code == 200:
            return r.json().get("businesses", [])
        elif r.status_code == 429:
            print("  [RATE LIMIT] Waiting 60s...")
            time.sleep(60)
        else:
            print(f"  [YELP {r.status_code}] {r.text[:100]}")
    except Exception as e:
        print(f"  [ERROR] {e}")
    return []


def parse_yelp_business(biz, city, country_code):
    """Convert Yelp API response to our lead dict."""
    info = COUNTRY_INFO.get(country_code, {})
    loc  = biz.get("location", {})
    coords = biz.get("coordinates", {})

    address_parts = [
        loc.get("address1",""),
        loc.get("address2",""),
        loc.get("zip_code",""),
    ]
    address = ", ".join(p for p in address_parts if p)

    cats = biz.get("categories",[])
    cat  = cats[0].get("alias","business") if cats else "business"
    cat_title = cats[0].get("title","Business") if cats else "Business"

    phone   = biz.get("phone","") or biz.get("display_phone","")
    website = biz.get("url","")  # Yelp listing URL, not actual website

    return {
        "osm_id":         f"yelp/{biz.get('id','')}",
        "name":           biz.get("name",""),
        "category":       cat,
        "category_pl":    cat_title,
        "city":           loc.get("city", city),
        "address":        address or city,
        "phone":          phone,
        "email":          "",
        "facebook_url":   "",
        "instagram_url":  "",
        "has_website":    0,  # We'd need to check their actual website
        "detected_website": "",
        "status":         "NEW",
        "notes":          f"Yelp scrape — {info.get('country', country_code)}",
        "country":        info.get("country", country_code),
        "country_code":   country_code,
        "language":       info.get("language","en"),
        "currency":       info.get("currency","EUR"),
        "avg_revenue_eur": info.get("avg_revenue_eur", 2000),
    }


def save_leads(leads):
    if not leads: return 0
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = 0
    for lead in leads:
        if not lead.get("name"): continue
        try:
            c.execute("""
                INSERT INTO leads (
                    osm_id, name, category, category_pl, city, address,
                    phone, email, has_website, status, notes,
                    country, country_code, language, currency, avg_revenue_eur
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(osm_id) DO UPDATE SET
                    phone = CASE WHEN excluded.phone != '' THEN excluded.phone ELSE leads.phone END
            """, (
                lead["osm_id"], lead["name"], lead["category"], lead["category_pl"],
                lead["city"], lead["address"], lead["phone"], lead["email"],
                lead["has_website"], lead["status"], lead["notes"],
                lead["country"], lead["country_code"], lead["language"],
                lead["currency"], lead["avg_revenue_eur"],
            ))
            saved += 1
        except Exception: pass
    conn.commit()
    conn.close()
    return saved


def run(country_code="ALL", city_filter=None, category_filter=None, high_ticket=False, limit=50):
    if not YELP_API_KEY or YELP_API_KEY == "YOUR_YELP_KEY_HERE":
        print("\n⚠️  No Yelp API key set!")
        print("   Get a free key at: https://www.yelp.com/developers/v3/manage_app")
        print("   Then set: YELP_API_KEY=your_key in .env or environment\n")
        return

    targets = list(COUNTRY_INFO.keys()) if country_code == "ALL" else [country_code.upper()]
    flags = {"GB":"🇬🇧","FR":"🇫🇷","NL":"🇳🇱","BE":"🇧🇪","SE":"🇸🇪",
             "NO":"🇳🇴","DK":"🇩🇰","IE":"🇮🇪","AT":"🇦🇹","CH":"🇨🇭",
             "IT":"🇮🇹","ES":"🇪🇸"}

    print(f"\n{'='*65}")
    print(f"  LeadPulse — Yelp API Scraper (Verified Phone Numbers)")
    print(f"  Countries: {', '.join(targets)}")
    print(f"  Mode: {'HIGH-TICKET AI TARGETS' if high_ticket else 'ALL CATEGORIES'}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")

    grand_total = 0

    for cc in targets:
        cities = [city_filter] if city_filter else COUNTRY_CITIES.get(cc, [])
        if category_filter:
            cats = [category_filter]
        elif high_ticket:
            cats = HIGH_TICKET_CATEGORIES
        else:
            cats = YELP_CATEGORIES

        info   = COUNTRY_INFO.get(cc, {})
        flag   = flags.get(cc, "🌍")
        print(f"  {flag} {info.get('country', cc)}")
        country_total = 0

        for city in cities:
            for cat in cats:
                print(f"    {cat:<18} {city:<15} ...", end=" ", flush=True)
                bizs = yelp_search(cat, city, cc, limit=limit)
                parsed = [parse_yelp_business(b, city, cc) for b in bizs]
                saved = save_leads(parsed)
                country_total += saved
                grand_total   += saved
                print(f"found {len(bizs):3}  saved {saved:3}")
                time.sleep(random.uniform(0.3, 0.8))  # Yelp rate limit friendly

        print(f"    ── {info.get('country',cc)} total: {country_total:,} ──\n")

    print(f"{'='*65}")
    print(f"  DONE — Total: {grand_total:,}")
    print(f"  Finished: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--country",     default="ALL")
    p.add_argument("--city",        default=None)
    p.add_argument("--category",    default=None)
    p.add_argument("--high-ticket", action="store_true", help="Scrape high-converting AI receptionist niches")
    p.add_argument("--limit",       type=int, default=50)
    args = p.parse_args()
    run(country_code=args.country, city_filter=args.city,
        category_filter=args.category, high_ticket=args.high_ticket, limit=args.limit)


