"""
scrape_directories.py — Scrapes national business directories per country.
Adds businesses WITH phone numbers directly from yellow pages.

Directories:
  🇩🇪 Germany:     gelbeseiten.de
  🇬🇧 UK:          yell.com
  🇦🇹 Austria:     herold.at
  🇨🇭 Switzerland: local.ch
  🇳🇱 Netherlands: detelefoongids.nl
  🇧🇪 Belgium:     goudengids.be
  🇸🇪 Sweden:      hitta.se
  🇳🇴 Norway:      gulesider.no
  🇩🇰 Denmark:     degulesider.dk
  🇫🇷 France:      pagesjaunes.fr
  🇵🇱 Poland:      panoramafirm.pl

Usage:
    python scrape_directories.py --country DE
    python scrape_directories.py --country GB
    python scrape_directories.py --country ALL
    python scrape_directories.py --country DE --category restaurant --limit 100
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

import re, time, random, argparse, sqlite3, requests
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote

DB_PATH = r"S:\APPs\lead-finder\leads.db"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"[\+\d][\d\s\-\(\)]{6,20}\d")

# ── Business categories to search per directory ──────────────────────────────
CATEGORIES = {
    "restaurant": {"DE":"Restaurant","GB":"restaurant","FR":"restaurant","PL":"restauracja","AT":"Restaurant","NL":"restaurant","BE":"restaurant","SE":"restaurang","NO":"restaurant","DK":"restaurant"},
    "hairdresser": {"DE":"Friseur","GB":"hairdresser","FR":"coiffeur","PL":"fryzjer","AT":"Friseur","NL":"kapper","BE":"kapper","SE":"frisör","NO":"frisør","DK":"frisør"},
    "dentist":    {"DE":"Zahnarzt","GB":"dentist","FR":"dentiste","PL":"stomatolog","AT":"Zahnarzt","NL":"tandarts","BE":"tandarts","SE":"tandläkare","NO":"tannlege","DK":"tandlæge"},
    "mechanic":   {"DE":"Autowerkstatt","GB":"car repair","FR":"garage automobile","PL":"mechanik","AT":"Autowerkstatt","NL":"autogarage","BE":"autogarage","SE":"bilverkstad","NO":"bilverksted","DK":"bilværksted"},
    "beauty":     {"DE":"Kosmetik","GB":"beauty salon","FR":"salon de beauté","PL":"kosmetyczka","AT":"Kosmetik","NL":"schoonheidssalon","BE":"schoonheidssalon","SE":"skönhetssalong","NO":"skjønnhetssalong","DK":"skønhedssalon"},
    "cafe":       {"DE":"Café","GB":"cafe","FR":"café","PL":"kawiarnia","AT":"Café","NL":"café","BE":"café","SE":"café","NO":"kafe","DK":"café"},
    "electrician":{"DE":"Elektriker","GB":"electrician","FR":"électricien","PL":"elektryk","AT":"Elektriker","NL":"elektricien","BE":"elektricien","SE":"elektriker","NO":"elektriker","DK":"elektriker"},
    "plumber":    {"DE":"Klempner","GB":"plumber","FR":"plombier","PL":"hydraulik","AT":"Installateur","NL":"loodgieter","BE":"loodgieter","SE":"rörmokare","NO":"rørlegger","DK":"VVS"},
    "bakery":     {"DE":"Bäckerei","GB":"bakery","FR":"boulangerie","PL":"piekarnia","AT":"Bäckerei","NL":"bakkerij","BE":"bakkerij","SE":"bageri","NO":"bakeri","DK":"bageri"},
    "florist":    {"DE":"Blumenladen","GB":"florist","FR":"fleuriste","PL":"kwiaciarnia","AT":"Blumenladen","NL":"bloemist","BE":"bloemist","SE":"blomsteraffär","NO":"blomsterbutikk","DK":"blomsterhandler"},
}

# ── City lists per country ────────────────────────────────────────────────────
COUNTRY_CITIES = {
    "DE": ["Berlin","Hamburg","München","Frankfurt","Köln","Stuttgart","Düsseldorf","Dortmund","Leipzig","Dresden","Nürnberg","Bremen"],
    "GB": ["London","Manchester","Birmingham","Leeds","Glasgow","Edinburgh","Bristol","Sheffield","Liverpool","Cardiff"],
    "AT": ["Wien","Graz","Linz","Salzburg","Innsbruck","Klagenfurt"],
    "CH": ["Zürich","Bern","Basel","Genf","Lausanne","Luzern"],
    "NL": ["Amsterdam","Rotterdam","Den Haag","Utrecht","Eindhoven","Tilburg","Groningen"],
    "BE": ["Brussel","Antwerpen","Gent","Brugge","Liège","Namur"],
    "SE": ["Stockholm","Göteborg","Malmö","Uppsala","Västerås","Örebro"],
    "NO": ["Oslo","Bergen","Trondheim","Stavanger","Kristiansand"],
    "DK": ["København","Aarhus","Odense","Aalborg","Esbjerg"],
    "FR": ["Paris","Lyon","Marseille","Toulouse","Bordeaux","Nantes","Strasbourg","Montpellier","Nice","Rennes"],
    "PL": ["Warszawa","Kraków","Wrocław","Poznań","Gdańsk","Łódź","Szczecin","Katowice","Bydgoszcz","Lublin","Toruń","Rzeszów"],
}

COUNTRY_INFO = {
    "DE": {"country":"Germany",        "language":"de","currency":"EUR","avg_revenue_eur":2500},
    "GB": {"country":"United Kingdom", "language":"en","currency":"GBP","avg_revenue_eur":3200},
    "AT": {"country":"Austria",        "language":"de","currency":"EUR","avg_revenue_eur":2800},
    "CH": {"country":"Switzerland",    "language":"de","currency":"CHF","avg_revenue_eur":4500},
    "NL": {"country":"Netherlands",    "language":"nl","currency":"EUR","avg_revenue_eur":3200},
    "BE": {"country":"Belgium",        "language":"nl","currency":"EUR","avg_revenue_eur":2800},
    "SE": {"country":"Sweden",         "language":"sv","currency":"SEK","avg_revenue_eur":3200},
    "NO": {"country":"Norway",         "language":"no","currency":"NOK","avg_revenue_eur":4200},
    "DK": {"country":"Denmark",        "language":"da","currency":"DKK","avg_revenue_eur":3800},
    "FR": {"country":"France",         "language":"fr","currency":"EUR","avg_revenue_eur":2800},
    "PL": {"country":"Poland",         "language":"pl","currency":"PLN","avg_revenue_eur":800},
}


def get_soup(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12, allow_redirects=True)
        if r.status_code == 200:
            return BeautifulSoup(r.text, "html.parser")
    except Exception:
        pass
    return None


# ── Per-directory scrapers ────────────────────────────────────────────────────

def scrape_gelbeseiten(category_de, city, limit=50):
    """Germany — gelbeseiten.de"""
    results = []
    url = f"https://www.gelbeseiten.de/suche/{quote(category_de)}/{quote(city)}"
    soup = get_soup(url)
    if not soup:
        return results
    for article in soup.select("article.mod-Treffer")[:limit]:
        name_el = article.select_one("[data-wipe-name]") or article.select_one("h2")
        phone_el = article.select_one("[data-phone]") or article.select_one(".phone")
        addr_el  = article.select_one("[data-adresse]") or article.select_one(".adresse")
        email_el = article.select_one("[data-email]") or article.select_one("a[href^='mailto']")
        name  = name_el.get_text(strip=True) if name_el else ""
        phone = (phone_el.get("data-phone","") or phone_el.get_text(strip=True)) if phone_el else ""
        addr  = addr_el.get_text(" ",strip=True) if addr_el else city
        email = (email_el.get("href","").replace("mailto:","") or email_el.get_text(strip=True)) if email_el else ""
        if name:
            results.append({"name":name,"phone":phone,"email":email,"address":addr,"city":city})
    return results


def scrape_yell(category_en, city, limit=50):
    """UK — yell.com"""
    results = []
    url = f"https://www.yell.com/ucs/UcsSearchAction.do?keywords={quote(category_en)}&location={quote(city)}"
    soup = get_soup(url)
    if not soup:
        return results
    for item in soup.select(".businessCapsule--mainContent")[:limit]:
        name_el  = item.select_one(".businessCapsule--name")
        phone_el = item.select_one(".businessCapsule--telephone")
        addr_el  = item.select_one(".businessCapsule--address")
        email_el = item.select_one("a[href^='mailto']")
        name  = name_el.get_text(strip=True) if name_el else ""
        phone = phone_el.get_text(strip=True) if phone_el else ""
        addr  = addr_el.get_text(" ",strip=True) if addr_el else city
        email = email_el.get("href","").replace("mailto:","") if email_el else ""
        if name:
            results.append({"name":name,"phone":phone,"email":email,"address":addr,"city":city})
    return results


def scrape_herold(category_de, city, limit=50):
    """Austria — herold.at"""
    results = []
    url = f"https://www.herold.at/gelbe-seiten/{quote(category_de)}/{quote(city.lower())}/"
    soup = get_soup(url)
    if not soup:
        return results
    for item in soup.select(".entry-header, .company-result")[:limit]:
        name_el  = item.select_one("h2, .company-name")
        phone_el = item.select_one(".phone, [itemprop='telephone']")
        email_el = item.select_one("a[href^='mailto']")
        name  = name_el.get_text(strip=True) if name_el else ""
        phone = phone_el.get_text(strip=True) if phone_el else ""
        email = email_el.get("href","").replace("mailto:","") if email_el else ""
        if name:
            results.append({"name":name,"phone":phone,"email":email,"address":city,"city":city})
    return results


def scrape_pagesjaunes(category_fr, city, limit=50):
    """France — pagesjaunes.fr"""
    results = []
    url = f"https://www.pagesjaunes.fr/annuaire/chercherlespros?quoiqui={quote(category_fr)}&ou={quote(city)}"
    soup = get_soup(url)
    if not soup:
        return results
    for item in soup.select(".bi-content, .biAnnuaire")[:limit]:
        name_el  = item.select_one(".bi-denomination h3, .denomination-links span")
        phone_el = item.select_one(".coord-numero, [class*='phone']")
        addr_el  = item.select_one(".bi-address, [class*='address']")
        email_el = item.select_one("a[href^='mailto']")
        name  = name_el.get_text(strip=True) if name_el else ""
        phone = phone_el.get_text(strip=True) if phone_el else ""
        addr  = addr_el.get_text(" ",strip=True) if addr_el else city
        email = email_el.get("href","").replace("mailto:","") if email_el else ""
        if name:
            results.append({"name":name,"phone":phone,"email":email,"address":addr,"city":city})
    return results


def scrape_generic_directory(country_code, category_term, city, limit=50):
    """Generic fallback — tries DuckDuckGo HTML search for directory listings."""
    results = []
    query = f'site:gelbeseiten.de OR site:yell.com OR site:pagesjaunes.fr {category_term} {city}'
    # Simplified: just return empty, main scrapers handle per-country
    return results


SCRAPERS = {
    "DE": scrape_gelbeseiten,
    "GB": scrape_yell,
    "AT": scrape_herold,
    "FR": scrape_pagesjaunes,
}


def save_leads(leads_data, country_code):
    if not leads_data:
        return 0
    info = COUNTRY_INFO.get(country_code, {})
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    saved = 0
    for lead in leads_data:
        name = lead.get("name","").strip()
        if not name or len(name) < 2:
            continue
        # Generate a pseudo osm_id from name+city to avoid duplicates
        pseudo_id = f"dir/{country_code}/{name[:40]}/{lead.get('city','')}"
        try:
            c.execute("""
                INSERT INTO leads (
                    osm_id, name, category, category_pl, city, address,
                    phone, email, has_website, status, notes,
                    country, country_code, language, currency, avg_revenue_eur
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(osm_id) DO UPDATE SET
                    phone = CASE WHEN excluded.phone != '' THEN excluded.phone ELSE leads.phone END,
                    email = CASE WHEN excluded.email != '' THEN excluded.email ELSE leads.email END
            """, (
                pseudo_id, name,
                lead.get("category","business"),
                lead.get("category","business").replace("_"," ").title(),
                lead.get("city",""), lead.get("address",""),
                lead.get("phone",""), lead.get("email",""),
                "EMAIL_FOUND" if lead.get("email") else ("NEW"),
                f"Directory scrape — {info.get('country',country_code)}",
                info.get("country",country_code), country_code,
                info.get("language","en"), info.get("currency","EUR"),
                info.get("avg_revenue_eur",2000),
            ))
            saved += 1
        except Exception:
            pass
    conn.commit()
    conn.close()
    return saved


def run(country_code="ALL", category_filter=None, limit=50):
    target_countries = list(COUNTRY_INFO.keys()) if country_code == "ALL" else [country_code.upper()]

    print(f"\n{'='*65}")
    print(f"  LeadPulse — Directory Scraper")
    print(f"  Countries: {', '.join(target_countries)}")
    print(f"  Started: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")

    grand_total = 0

    for cc in target_countries:
        if cc not in COUNTRY_INFO:
            print(f"  ⚠️  Unknown country: {cc}")
            continue

        cities  = COUNTRY_CITIES.get(cc, [])
        cats    = {k: v for k, v in CATEGORIES.items()
                   if category_filter is None or k == category_filter}
        scraper = SCRAPERS.get(cc)

        flag = {"DE":"🇩🇪","GB":"🇬🇧","AT":"🇦🇹","CH":"🇨🇭","NL":"🇳🇱",
                "BE":"🇧🇪","SE":"🇸🇪","DK":"🇩🇰","NO":"🇳🇴","FR":"🇫🇷",
                "PL":"🇵🇱","IE":"🇮🇪"}.get(cc,"🌍")
        country_name = COUNTRY_INFO[cc]["country"]

        if not scraper:
            print(f"  {flag} {country_name:<15} — no scraper yet, skipping\n")
            continue

        country_total = 0
        print(f"  {flag} {country_name}")

        for cat_key, cat_terms in cats.items():
            term = cat_terms.get(cc, cat_key)
            for city in cities:
                print(f"    {cat_key:<15} {city:<15} ...", end=" ", flush=True)
                try:
                    results = scraper(term, city, limit=limit)
                    saved   = save_leads(
                        [{**r, "category": cat_key} for r in results], cc
                    )
                    country_total += saved
                    grand_total   += saved
                    print(f"found {len(results):3}  saved {saved:3}")
                except Exception as e:
                    print(f"ERROR: {str(e)[:40]}")
                time.sleep(random.uniform(2.0, 4.0))

        print(f"    ── {country_name} total: {country_total:,} ──\n")

    print(f"{'='*65}")
    print(f"  DONE — Total saved: {grand_total:,}")
    print(f"  Finished: {datetime.now():%Y-%m-%d %H:%M}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--country",  default="ALL", help="DE GB AT FR etc or ALL")
    p.add_argument("--category", default=None,  help="restaurant hairdresser etc")
    p.add_argument("--limit",    type=int, default=50)
    args = p.parse_args()
    run(country_code=args.country, category_filter=args.category, limit=args.limit)
