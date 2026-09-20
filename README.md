# LeadPulse PL — Automated B2B Lead Generator & Outreach

## Production architecture

The production API now lives in `app/` and uses FastAPI routers, SQLAlchemy,
PostgreSQL-compatible Alembic migrations, and Redis-backed Celery workers.
`server.py` remains only as a compatibility entry point for local commands.

Local development can continue to use SQLite:

```powershell
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
celery -A app.workers.celery_app:celery_app worker --loglevel=INFO --pool=solo
celery -A app.workers.celery_app:celery_app beat --loglevel=INFO
```

Redis must be running for background enrichment and outreach. Campaigns default
to dry-run mode. For Railway service layout, variables, migrations, and the
legacy SQLite import procedure, see [RAILWAY.md](RAILWAY.md).

A high-performance pipeline to find local Polish companies without websites, discover their contact details (phone numbers, email addresses, social links), generate personalized web design & digital marketing pitches, and manage cold outreach.

---

## 🚀 Features

* **Targeted City & Bounding Box Scraper:** Fast, sub-second OpenStreetMap Overpass queries covering Toruń, Warszawa, Kraków, Wrocław, Poznań, Gdańsk, and other Polish cities.
* **Dual-Layer Website Verification:** Distinguishes genuine company websites (`.pl`, `.com`) from directory listings (Targeo, Panorama Firm, Cylex, Booksy, Oferteo) to guarantee high-accuracy leads.
* **Contact Discovery:** Extracts direct phone numbers, email addresses, and Facebook page links.
* **Personalized Outreach Templates:** High-converting Polish & English email proposals customized by business name, niche, and city, with built-in RODO/GDPR opt-out disclaimers.
* **Safety First Outreach:** Includes `--dry-run` simulation mode, anti-spam delay throttling, and batch controls.
* **Full CSV Export:** Generates ready-to-use spreadsheets with phone numbers, emails, addresses, and full copy-paste pitch texts.

---

## 📁 Project Structure

```
S:\APPs\lead-finder\
├── config.py              # City coordinates, business categories, SMTP settings
├── database.py            # SQLite database manager and CSV exporter
├── scraper.py             # Overpass scanner and search enrichment engine
├── email_templates.py     # Polish and English pitch templates
├── outreach.py            # SMTP dispatcher with rate-limiting & dry-run mode
├── main.py                # Main CLI controller
├── run_torun_mission.py   # One-click Toruń pipeline runner
├── leads.db               # SQLite database of discovered businesses
└── leads_torun.csv        # Exported Toruń leads with personalized pitch copy
```

---

## ⚡ Quick CLI Commands

### 1. View Current Leads in Toruń
```powershell
python main.py list --city torun --limit 20
```

### 2. Search for Businesses in Any Polish City
```powershell
# Scan Toruń across all categories
python main.py search --city torun --category all --limit 40

# Scan car mechanics in Warsaw with auto-enrichment
python main.py search --city warszawa --category mechanik --limit 30 --enrich

# Scan hair salons in Kraków
python main.py search --city krakow --category fryzjer --limit 20
```

### 3. Verify Websites & Discover Emails
```powershell
python main.py enrich --city torun --limit 20
```

### 4. Preview Outreach Pitch
```powershell
python main.py preview --city torun
```

### 5. Export to CSV (with Generated Email Text)
```powershell
python main.py export --city torun --file leads_torun.csv
```

### 6. Send Outreach Emails
* **Simulation (Dry-Run, safe):**
  ```powershell
  python main.py send --city torun --dry-run
  ```
* **Live Sending via SMTP:**
  Configure `.env` first (see below), then run:
  ```powershell
  python main.py send --city torun --live --max 10
  ```

---

## 📧 Live Sending Setup (`.env`)

To send live emails, copy `.env.example` to `.env` and configure your credentials:

```ini
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password

SENDER_NAME=Twoja Agencja Webowa
SENDER_EMAIL=kontakt@twojadomena.pl
SENDER_PHONE=+48 500 000 000
```
*(For Gmail, use a 16-character Google App Password from your Google Account security settings).*
