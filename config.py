"""
Configuration settings for LeadPulse PL (B2B Lead Finder & Outreach for Poland).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Polish cities with geographic centers (lat, lon, default_radius_meters, display_name)
POLISH_CITIES = {
    "torun": {"lat": 53.0138, "lon": 18.5984, "radius": 9000, "name": "Toruń"},
    "warszawa": {"lat": 52.2297, "lon": 21.0122, "radius": 15000, "name": "Warszawa"},
    "krakow": {"lat": 50.0647, "lon": 19.9450, "radius": 12000, "name": "Kraków"},
    "wroclaw": {"lat": 51.1079, "lon": 17.0385, "radius": 12000, "name": "Wrocław"},
    "poznan": {"lat": 52.4064, "lon": 16.9252, "radius": 11000, "name": "Poznań"},
    "gdansk": {"lat": 54.3520, "lon": 18.6466, "radius": 13000, "name": "Gdańsk"},
    "lodz": {"lat": 51.7592, "lon": 19.4560, "radius": 12000, "name": "Łódź"},
    "szczecin": {"lat": 53.4285, "lon": 14.5528, "radius": 12000, "name": "Szczecin"},
    "bydgoszcz": {"lat": 53.1235, "lon": 18.0084, "radius": 10000, "name": "Bydgoszcz"},
    "lublin": {"lat": 51.2465, "lon": 22.5684, "radius": 10000, "name": "Lublin"},
    "katowice": {"lat": 50.2649, "lon": 19.0238, "radius": 10000, "name": "Katowice"},
    "bialystok": {"lat": 53.1325, "lon": 23.1688, "radius": 9000, "name": "Białystok"},
    "gdynia": {"lat": 54.5189, "lon": 18.5305, "radius": 10000, "name": "Gdynia"},
    "rzeszow": {"lat": 50.0412, "lon": 21.9991, "radius": 9000, "name": "Rzeszów"},
}

# High-converting local business categories in Poland
BUSINESS_CATEGORIES = {
    "mechanik": {"osm_tag": "craft=car_repair", "name_pl": "Mechanik samochodowy"},
    "fryzjer": {"osm_tag": "shop=hairdresser", "name_pl": "Fryzjer / Stylista"},
    "kosmetyczka": {"osm_tag": "shop=beauty", "name_pl": "Salon kosmetyczny"},
    "dentysta": {"osm_tag": "amenity=dentist", "name_pl": "Gabinet stomatologiczny"},
    "restauracja": {"osm_tag": "amenity=restaurant", "name_pl": "Restauracja"},
    "kawiarnia": {"osm_tag": "amenity=cafe", "name_pl": "Kawiarnia"},
    "hydraulik": {"osm_tag": "craft=plumber", "name_pl": "Hydraulik"},
    "elektryk": {"osm_tag": "craft=electrician", "name_pl": "Elektryk"},
    "stolarz": {"osm_tag": "craft=carpenter", "name_pl": "Stolarz / Meble na wymiar"},
    "kwiaciarnia": {"osm_tag": "shop=florist", "name_pl": "Kwiaciarnia"},
    "piekarnia": {"osm_tag": "shop=bakery", "name_pl": "Piekarnia / Cukiernia"},
    "optyk": {"osm_tag": "shop=optician", "name_pl": "Optyk"},
    "weterynarz": {"osm_tag": "amenity=veterinary", "name_pl": "Gabinet weterynaryjny"},
    "remonty": {"osm_tag": "craft=painter", "name_pl": "Usługi remontowo-budowlane"},
}

OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

USER_AGENT = "LeadPulseBot/1.0 (web-outreach-research)"

# Database file
DB_PATH = BASE_DIR / "leads.db"

# Email Configuration (SMTP)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SENDER_NAME = os.getenv("SENDER_NAME", "Web Studio Toruń")
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PHONE = os.getenv("SENDER_PHONE", "+48 500 000 000")

# Outreach throttling
MIN_DELAY_BETWEEN_EMAILS_SEC = 20
MAX_DELAY_BETWEEN_EMAILS_SEC = 45
MAX_EMAILS_PER_DAY = 40
