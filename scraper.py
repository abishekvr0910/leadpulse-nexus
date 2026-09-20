"""
Scraper and enrichment engine for Polish local businesses.
Finds companies without websites and discovers contact info (email, phone, socials).
"""
import re
import time
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from config import OVERPASS_ENDPOINTS, USER_AGENT, POLISH_CITIES, BUSINESS_CATEGORIES

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'(?:\+48\s?)?(?:[1-9]\d{1,2}[\s-]?\d{3}[\s-]?\d{3}|[1-9]\d{2}[\s-]?\d{3}[\s-]?\d{3})')

# Common words to filter out when checking domain name similarity
STOPWORDS = {
    'salon', 'fryzjerski', 'kosmetyczny', 'gabinet', 'stomatologiczny', 
    'restauracja', 'kawiarnia', 'usługi', 'uslugi', 'firma', 'sp', 'z', 'o', 
    'dla', 'dzieci', 'warszawa', 'toruń', 'torun', 'krakow', 'wroclaw', 
    'polska', 'kwiaciarnia', 'auto', 'serwis', 'naprawa', 'mechanika', 
    'sklep', 'piekarnia', 'cukiernia', 'bar', 'pub', 'studio'
}

DIRECTORY_DOMAINS = {
    "facebook.com", "instagram.com", "linkedin.com", "panoramafirm.pl",
    "pkt.pl", "cylex-polska.pl", "favore.pl", "oferteo.pl", "olx.pl",
    "allegro.pl", "google.com", "maps.google.com", "yelp.pl", "tripadvisor.com",
    "znanylekarz.pl", "booksy.com", "fixly.pl", "gowork.pl", "krs-online.com.pl",
    "aleo.com", "baza-firm.com.pl", "firmy.net", "infoveriti.pl", "targeo.pl",
    "smstome.com", "maps.me", "whitepages.com", "nieznanynumer.pl", "telepolis.pl",
    "trojmiasto.pl", "ototorun.pl", "torun.pl", "pomorska.pl", "wyborcza.pl",
    "naszemiasto.pl", "wikipedia.org", "chillitorun.pl", "wix.com", "wordpress.com"
}

def clean_business_keywords(name: str) -> List[str]:
    """Extracts distinctive keywords from business name."""
    words = re.findall(r'[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]{3,}', name.lower())
    return [w for w in words if w not in STOPWORDS]

def is_independent_website(url: str, business_name: str) -> bool:
    """
    Checks if a URL is an independent website belonging to this business.
    Distinguishes real business sites from aggregators/directories.
    """
    if not url:
        return False
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")

        # Immediate filter on known directories/aggregators
        for d in DIRECTORY_DOMAINS:
            if d in domain:
                return False

        # Domain must contain at least one unique keyword from the business name
        keywords = clean_business_keywords(business_name)
        if not keywords:
            return False

        return any(k in domain for k in keywords)
    except Exception:
        return False

def query_osm_for_candidates(city_key: str, category_key: str = "all", limit: int = 50) -> List[Dict[str, Any]]:
    """Queries OpenStreetMap Overpass API for businesses using geographic bounding box."""
    city_info = POLISH_CITIES.get(city_key.lower())
    if not city_info:
        city_info = POLISH_CITIES.get("torun")

    lat = city_info["lat"]
    lon = city_info["lon"]
    radius = city_info["radius"]
    city_name = city_info["name"]

    tag_filters = []
    if category_key.lower() == "all":
        tag_filters = [
            'node["shop"="hairdresser"][!"website"][!"contact:website"]',
            'node["shop"="beauty"][!"website"][!"contact:website"]',
            'node["craft"="car_repair"][!"website"][!"contact:website"]',
            'node["shop"="car_repair"][!"website"][!"contact:website"]',
            'node["amenity"="dentist"][!"website"][!"contact:website"]',
            'node["amenity"="restaurant"][!"website"][!"contact:website"]',
            'node["amenity"="cafe"][!"website"][!"contact:website"]',
            'node["shop"="florist"][!"website"][!"contact:website"]',
            'node["craft"="plumber"][!"website"][!"contact:website"]',
            'node["craft"="electrician"][!"website"][!"contact:website"]',
            'node["craft"="carpenter"][!"website"][!"contact:website"]',
            'node["shop"="bakery"][!"website"][!"contact:website"]',
        ]
    else:
        cat_info = BUSINESS_CATEGORIES.get(category_key.lower())
        if cat_info:
            tag_key, tag_val = cat_info["osm_tag"].split("=")
            tag_filters.append(f'node["{tag_key}"="{tag_val}"][!"website"][!"contact:website"]')
        else:
            tag_filters.append(f'node["shop"="{category_key}"][!"website"][!"contact:website"]')

    subqueries = "\n  ".join([f"{tf}(around:{radius}, {lat}, {lon});" for tf in tag_filters])
    query = f"""
    [out:json][timeout:25];
    (
      {subqueries}
    );
    out {limit};
    """

    headers = {"User-Agent": USER_AGENT}
    elements = []

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            resp = requests.post(endpoint, data={"data": query}, headers=headers, timeout=25)
            if resp.status_code == 200:
                data = resp.json()
                elements = data.get("elements", [])
                if elements:
                    break
            elif resp.status_code == 429:
                time.sleep(2)
                continue
        except Exception:
            continue

    leads = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        if not name or len(name.strip()) < 2:
            continue

        raw_cat = tags.get("shop") or tags.get("craft") or tags.get("amenity") or category_key
        pl_name = raw_cat
        for k, v in BUSINESS_CATEGORIES.items():
            if raw_cat in v["osm_tag"]:
                pl_name = v["name_pl"]
                break

        street = tags.get("addr:street", "")
        housenumber = tags.get("addr:housenumber", "")
        address = f"{street} {housenumber}".strip() if street else city_name

        phone = tags.get("phone") or tags.get("contact:phone") or tags.get("contact:mobile") or ""
        email = tags.get("email") or tags.get("contact:email") or ""
        fb = tags.get("contact:facebook") or ""
        ig = tags.get("contact:instagram") or ""

        lead = {
            "osm_id": f"{el.get('type')}/{el.get('id')}",
            "name": name.strip(),
            "category": raw_cat,
            "category_pl": pl_name,
            "city": city_name,
            "address": address,
            "phone": phone,
            "email": email,
            "facebook_url": fb,
            "instagram_url": ig,
            "has_website": 0,
            "detected_website": "",
            "status": "EMAIL_FOUND" if email else "NEW",
            "notes": "Found via OpenStreetMap (No website tag)"
        }
        leads.append(lead)

    return leads

def verify_and_enrich_lead(lead: Dict[str, Any]) -> Dict[str, Any]:
    """
    Verifies domain absence via web search.
    If only Facebook / Booksy / Directories appear, it confirms NO WEBSITE and extracts contact details.
    """
    try:
        from ddgs import DDGS
        ddgs = DDGS()
        query = f'"{lead["name"]}" {lead["city"]} kontakt OR telefon OR email'
        results = list(ddgs.text(query, max_results=5))

        found_website = None
        found_emails = []
        found_fb = lead.get("facebook_url") or ""
        found_phone = lead.get("phone") or ""

        for r in results:
            url = r.get("href", "")
            title = r.get("title", "")
            snippet = r.get("body", "") + " " + title

            # Check if this URL is their own independent website
            if is_independent_website(url, lead["name"]):
                found_website = url
                break

            # Check for Facebook page
            if "facebook.com" in url and not found_fb:
                found_fb = url

            # Extract email addresses from snippet
            matches = EMAIL_REGEX.findall(snippet)
            for m in matches:
                lower_m = m.lower()
                # Exclude directory emails
                if not any(d in lower_m for d in [
                    "cylex", "oferteo", "panoramafirm", "booksy", "fixly", 
                    "example", "sentry", "noreply", "wix", "targeo", "whitepages"
                ]):
                    found_emails.append(m)

            # Extract phone if missing
            if not found_phone:
                p_match = PHONE_REGEX.search(snippet)
                if p_match:
                    found_phone = p_match.group(0).strip()

        if found_website:
            lead["has_website"] = 1
            lead["detected_website"] = found_website
            lead["status"] = "HAS_WEBSITE"
            lead["notes"] = f"Independent website found: {found_website}"
        else:
            lead["has_website"] = 0
            if not lead.get("email") and found_emails:
                lead["email"] = found_emails[0]
            if not lead.get("phone") and found_phone:
                lead["phone"] = found_phone
            if found_fb:
                lead["facebook_url"] = found_fb

            lead["status"] = "EMAIL_FOUND" if lead.get("email") else "VERIFIED_NO_WEBSITE"
            lead["notes"] = "Verified: Only directories/social media found. NO independent website."

    except Exception as e:
        lead["notes"] = f"Verification note: {str(e)[:50]}"

    return lead
