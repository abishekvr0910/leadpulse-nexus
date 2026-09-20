"""
European cities configuration for LeadPulse — high-income countries.
Focused on markets with high SMB density and ability to pay for AI services.
"""

# Priority tier by avg revenue per client potential:
# 🥇 DACH (Germany, Austria, Switzerland) — highest paying, massive SMB market
# 🥈 Benelux (Netherlands, Belgium) — high income, tech-forward
# 🥉 Nordics (Sweden, Denmark, Norway) — high income, English-friendly
# 🎯 UK — English, huge market, familiar with AI services
# 🎯 France — large SMB market, lower English but high potential

EUROPEAN_CITIES = {

    # ── 🇩🇪 GERMANY — 3.5M SMBs, biggest EU market ─────────────────────────
    "berlin": {
        "lat": 52.5200, "lon": 13.4050, "radius": 18000,
        "name": "Berlin", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2500,
    },
    "hamburg": {
        "lat": 53.5753, "lon": 10.0153, "radius": 15000,
        "name": "Hamburg", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2500,
    },
    "munich": {
        "lat": 48.1351, "lon": 11.5820, "radius": 15000,
        "name": "München", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 3200,
    },
    "frankfurt": {
        "lat": 50.1109, "lon": 8.6821, "radius": 13000,
        "name": "Frankfurt", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 3000,
    },
    "cologne": {
        "lat": 50.9333, "lon": 6.9500, "radius": 14000,
        "name": "Köln", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2500,
    },
    "stuttgart": {
        "lat": 48.7758, "lon": 9.1829, "radius": 12000,
        "name": "Stuttgart", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2800,
    },
    "dusseldorf": {
        "lat": 51.2217, "lon": 6.7762, "radius": 12000,
        "name": "Düsseldorf", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2700,
    },
    "dortmund": {
        "lat": 51.5136, "lon": 7.4653, "radius": 12000,
        "name": "Dortmund", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2200,
    },
    "leipzig": {
        "lat": 51.3397, "lon": 12.3731, "radius": 11000,
        "name": "Leipzig", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2000,
    },
    "dresden": {
        "lat": 51.0504, "lon": 13.7373, "radius": 11000,
        "name": "Dresden", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2000,
    },
    "nuremberg": {
        "lat": 49.4521, "lon": 11.0767, "radius": 11000,
        "name": "Nürnberg", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2300,
    },
    "bremen": {
        "lat": 53.0793, "lon": 8.8017, "radius": 10000,
        "name": "Bremen", "country": "Germany", "country_code": "DE",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2200,
    },

    # ── 🇦🇹 AUSTRIA — Premium market, German-speaking ───────────────────────
    "vienna": {
        "lat": 48.2082, "lon": 16.3738, "radius": 18000,
        "name": "Wien", "country": "Austria", "country_code": "AT",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 3000,
    },
    "graz": {
        "lat": 47.0707, "lon": 15.4395, "radius": 11000,
        "name": "Graz", "country": "Austria", "country_code": "AT",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2500,
    },
    "linz": {
        "lat": 48.3069, "lon": 14.2858, "radius": 10000,
        "name": "Linz", "country": "Austria", "country_code": "AT",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2500,
    },
    "salzburg": {
        "lat": 47.8095, "lon": 13.0550, "radius": 9000,
        "name": "Salzburg", "country": "Austria", "country_code": "AT",
        "language": "de", "currency": "EUR", "avg_revenue_eur": 2800,
    },

    # ── 🇨🇭 SWITZERLAND — Highest paying market in Europe ───────────────────
    "zurich": {
        "lat": 47.3769, "lon": 8.5417, "radius": 13000,
        "name": "Zürich", "country": "Switzerland", "country_code": "CH",
        "language": "de", "currency": "CHF", "avg_revenue_eur": 5000,
    },
    "bern": {
        "lat": 46.9481, "lon": 7.4474, "radius": 10000,
        "name": "Bern", "country": "Switzerland", "country_code": "CH",
        "language": "de", "currency": "CHF", "avg_revenue_eur": 4500,
    },
    "basel": {
        "lat": 47.5596, "lon": 7.5886, "radius": 9000,
        "name": "Basel", "country": "Switzerland", "country_code": "CH",
        "language": "de", "currency": "CHF", "avg_revenue_eur": 4500,
    },
    "geneva": {
        "lat": 46.2044, "lon": 6.1432, "radius": 10000,
        "name": "Genf", "country": "Switzerland", "country_code": "CH",
        "language": "fr", "currency": "CHF", "avg_revenue_eur": 5000,
    },

    # ── 🇳🇱 NETHERLANDS — Tech-forward, high English fluency ────────────────
    "amsterdam": {
        "lat": 52.3676, "lon": 4.9041, "radius": 13000,
        "name": "Amsterdam", "country": "Netherlands", "country_code": "NL",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 3500,
    },
    "rotterdam": {
        "lat": 51.9244, "lon": 4.4777, "radius": 12000,
        "name": "Rotterdam", "country": "Netherlands", "country_code": "NL",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 3000,
    },
    "den_haag": {
        "lat": 52.0705, "lon": 4.3007, "radius": 11000,
        "name": "Den Haag", "country": "Netherlands", "country_code": "NL",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 3200,
    },
    "utrecht": {
        "lat": 52.0907, "lon": 5.1214, "radius": 10000,
        "name": "Utrecht", "country": "Netherlands", "country_code": "NL",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 3000,
    },
    "eindhoven": {
        "lat": 51.4416, "lon": 5.4697, "radius": 9000,
        "name": "Eindhoven", "country": "Netherlands", "country_code": "NL",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 2800,
    },

    # ── 🇧🇪 BELGIUM ──────────────────────────────────────────────────────────
    "brussels": {
        "lat": 50.8503, "lon": 4.3517, "radius": 13000,
        "name": "Brussel", "country": "Belgium", "country_code": "BE",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 3000,
    },
    "antwerp": {
        "lat": 51.2194, "lon": 4.4025, "radius": 11000,
        "name": "Antwerpen", "country": "Belgium", "country_code": "BE",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 2800,
    },
    "ghent": {
        "lat": 51.0543, "lon": 3.7174, "radius": 10000,
        "name": "Gent", "country": "Belgium", "country_code": "BE",
        "language": "nl", "currency": "EUR", "avg_revenue_eur": 2600,
    },

    # ── 🇸🇪 SWEDEN — High income, English-friendly ───────────────────────────
    "stockholm": {
        "lat": 59.3293, "lon": 18.0686, "radius": 15000,
        "name": "Stockholm", "country": "Sweden", "country_code": "SE",
        "language": "sv", "currency": "SEK", "avg_revenue_eur": 3500,
    },
    "gothenburg": {
        "lat": 57.7089, "lon": 11.9746, "radius": 12000,
        "name": "Göteborg", "country": "Sweden", "country_code": "SE",
        "language": "sv", "currency": "SEK", "avg_revenue_eur": 3000,
    },
    "malmo": {
        "lat": 55.6050, "lon": 13.0038, "radius": 10000,
        "name": "Malmö", "country": "Sweden", "country_code": "SE",
        "language": "sv", "currency": "SEK", "avg_revenue_eur": 2800,
    },

    # ── 🇩🇰 DENMARK ──────────────────────────────────────────────────────────
    "copenhagen": {
        "lat": 55.6761, "lon": 12.5683, "radius": 14000,
        "name": "København", "country": "Denmark", "country_code": "DK",
        "language": "da", "currency": "DKK", "avg_revenue_eur": 4000,
    },
    "aarhus": {
        "lat": 56.1629, "lon": 10.2039, "radius": 10000,
        "name": "Aarhus", "country": "Denmark", "country_code": "DK",
        "language": "da", "currency": "DKK", "avg_revenue_eur": 3500,
    },

    # ── 🇳🇴 NORWAY — Highest income per capita ───────────────────────────────
    "oslo": {
        "lat": 59.9139, "lon": 10.7522, "radius": 14000,
        "name": "Oslo", "country": "Norway", "country_code": "NO",
        "language": "no", "currency": "NOK", "avg_revenue_eur": 4500,
    },
    "bergen": {
        "lat": 60.3913, "lon": 5.3221, "radius": 10000,
        "name": "Bergen", "country": "Norway", "country_code": "NO",
        "language": "no", "currency": "NOK", "avg_revenue_eur": 4000,
    },

    # ── 🇬🇧 UK — English market, huge SMB base ───────────────────────────────
    "london": {
        "lat": 51.5074, "lon": -0.1278, "radius": 20000,
        "name": "London", "country": "United Kingdom", "country_code": "GB",
        "language": "en", "currency": "GBP", "avg_revenue_eur": 4000,
    },
    "manchester": {
        "lat": 53.4808, "lon": -2.2426, "radius": 13000,
        "name": "Manchester", "country": "United Kingdom", "country_code": "GB",
        "language": "en", "currency": "GBP", "avg_revenue_eur": 3000,
    },
    "birmingham": {
        "lat": 52.4862, "lon": -1.8904, "radius": 13000,
        "name": "Birmingham", "country": "United Kingdom", "country_code": "GB",
        "language": "en", "currency": "GBP", "avg_revenue_eur": 2800,
    },
    "glasgow": {
        "lat": 55.8642, "lon": -4.2518, "radius": 12000,
        "name": "Glasgow", "country": "United Kingdom", "country_code": "GB",
        "language": "en", "currency": "GBP", "avg_revenue_eur": 2500,
    },
    "leeds": {
        "lat": 53.8008, "lon": -1.5491, "radius": 11000,
        "name": "Leeds", "country": "United Kingdom", "country_code": "GB",
        "language": "en", "currency": "GBP", "avg_revenue_eur": 2600,
    },
    "edinburgh": {
        "lat": 55.9533, "lon": -3.1883, "radius": 11000,
        "name": "Edinburgh", "country": "United Kingdom", "country_code": "GB",
        "language": "en", "currency": "GBP", "avg_revenue_eur": 3000,
    },

    # ── 🇫🇷 FRANCE — Large SMB market ───────────────────────────────────────
    "paris": {
        "lat": 48.8566, "lon": 2.3522, "radius": 18000,
        "name": "Paris", "country": "France", "country_code": "FR",
        "language": "fr", "currency": "EUR", "avg_revenue_eur": 3500,
    },
    "lyon": {
        "lat": 45.7640, "lon": 4.8357, "radius": 12000,
        "name": "Lyon", "country": "France", "country_code": "FR",
        "language": "fr", "currency": "EUR", "avg_revenue_eur": 2800,
    },
    "marseille": {
        "lat": 43.2965, "lon": 5.3698, "radius": 12000,
        "name": "Marseille", "country": "France", "country_code": "FR",
        "language": "fr", "currency": "EUR", "avg_revenue_eur": 2500,
    },
    "toulouse": {
        "lat": 43.6047, "lon": 1.4442, "radius": 11000,
        "name": "Toulouse", "country": "France", "country_code": "FR",
        "language": "fr", "currency": "EUR", "avg_revenue_eur": 2600,
    },
    "bordeaux": {
        "lat": 44.8378, "lon": -0.5792, "radius": 10000,
        "name": "Bordeaux", "country": "France", "country_code": "FR",
        "language": "fr", "currency": "EUR", "avg_revenue_eur": 2600,
    },

    # ── 🇮🇪 IRELAND — English, EU hub ──────────────────────────────────────
    "dublin": {
        "lat": 53.3498, "lon": -6.2603, "radius": 13000,
        "name": "Dublin", "country": "Ireland", "country_code": "IE",
        "language": "en", "currency": "EUR", "avg_revenue_eur": 3500,
    },
}

# Countries grouped by language for email template routing
LANGUAGE_GROUPS = {
    "en": ["GB", "IE"],                    # English → en_initial_outreach
    "de": ["DE", "AT", "CH"],             # German  → de_initial_outreach (TODO)
    "nl": ["NL", "BE"],                   # Dutch   → en_initial_outreach (most speak English)
    "fr": ["FR"],                         # French  → en_initial_outreach (for now)
    "sv": ["SE"],                         # Swedish → en_initial_outreach (high English)
    "da": ["DK"],                         # Danish  → en_initial_outreach (high English)
    "no": ["NO"],                         # Norwegian→ en_initial_outreach (high English)
}

def get_template_for_country(country_code: str) -> str:
    """Returns the best email template key for a given country."""
    if country_code in ["GB", "IE"]:
        return "en_initial_outreach"
    elif country_code in ["DE", "AT", "CH"]:
        return "de_initial_outreach"   # German template (to be added)
    else:
        return "en_initial_outreach"   # English as fallback for NL, SE, DK, NO, FR

# Priority order for scanning (by revenue potential)
SCAN_PRIORITY = [
    # Tier 1 — highest paying
    "zurich", "oslo", "copenhagen", "stockholm", "munich",
    "vienna", "london", "frankfurt", "amsterdam", "bern",
    # Tier 2
    "hamburg", "berlin", "rotterdam", "brussels", "berlin",
    "gothenburg", "aarhus", "edinburgh", "manchester", "paris",
    # Tier 3
    "cologne", "stuttgart", "dusseldorf", "den_haag", "utrecht",
    "antwerp", "malmo", "birmingham", "leeds", "lyon",
    # Tier 4
    "dortmund", "leipzig", "nuremberg", "bremen", "dresden",
    "graz", "linz", "salzburg", "ghent", "eindhoven",
    "marseille", "toulouse", "bordeaux", "bergen", "glasgow", "dublin",
    "basel", "geneva",
]
