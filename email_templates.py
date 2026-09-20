"""
Email outreach templates for LeadPulse PL — AI Agency Edition.
Works for ANY business type — no assumptions about their specific problem.
Pitch: website + AI receptionist + automation + referral ask + Calendly booking.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from typing import Dict, Any

CALENDLY_LINK = "https://calendly.com/abivr61/30min"

# ── Category-specific pain point hooks (bonus personalization when category matches) ──
# Used to add ONE specific line when we know the category.
# For everything else → universal fallback that works for any business.
CATEGORY_HOOKS: Dict[str, str] = {
    # Food & drink
    "restauracja":    "Wiemy, że restauracje tracą rezerwacje przez nieodebrane telefony — zwłaszcza w piątek i sobotę.",
    "kawiarnia":      "Kawiarnie często tracą rezerwacje na events i urodziny, bo nie ma gdzie zarezerwować online.",
    "fast food":      "Lokale szybkiej obsługi mogą zautomatyzować zamówienia i powiadomienia SMS.",
    "bar":            "Bary i puby tracą rezerwacje grupowe przez brak formularza online.",
    "piekarnia":      "Piekarnie tracą zamówienia zbiorcze (wesela, eventy) przez brak kontaktu online.",
    "bakery":         "Piekarnie tracą zamówienia zbiorcze (wesela, eventy) przez brak kontaktu online.",
    "cukiernia":      "Cukiernie tracą zamówienia tortów i wypieków na zamówienie przez brak strony z formularzem.",

    # Beauty & health
    "fryzjer":        "Salony fryzjerskie tracą wizyty poza godzinami pracy — AI umawia o 23:00 kiedy właściciel śpi.",
    "hairdresser":    "Salony fryzjerskie tracą wizyty poza godzinami pracy — AI umawia o 23:00 kiedy właściciel śpi.",
    "kosmetyczka":    "Salony kosmetyczne tracą klientki, które nie mogą dodzwonić się podczas zabiegów.",
    "beauty":         "Salony beauty tracą klientki, które nie mogą dodzwonić się podczas zabiegów.",
    "salon":          "Salony tracą klientów przez nieodebrane telefony gdy pracownik jest zajęty.",
    "masaż":          "Gabinety masażu tracą rezerwacje gdy linia jest zajęta lub poza godzinami.",
    "massage":        "Gabinety masażu tracą rezerwacje gdy linia jest zajęta lub poza godzinami.",
    "tattoo":         "Studia tatuażu tracą zapytania o wycenę przez brak formularza online.",

    # Medical
    "stomatolog":     "Pacjenci wybierają gabinet po stronie z opiniami — brak strony = brak zaufania.",
    "dentysta":       "Pacjenci wybierają gabinet po stronie z opiniami — brak strony = brak zaufania.",
    "dentist":        "Pacjenci wybierają gabinet po stronie z opiniami — brak strony = brak zaufania.",
    "lekarz":         "Pacjenci szukają lekarza online — brak strony oznacza utratę nowych pacjentów.",
    "clinic":         "Kliniki i gabinety tracą pacjentów, którzy szukają informacji online przed wizytą.",
    "doctors":        "Pacjenci szukają lekarza online — brak strony oznacza utratę nowych pacjentów.",
    "weterynarz":     "Właściciele zwierząt w nagłych przypadkach szukają weterynarza w Google.",
    "veterinary":     "Właściciele zwierząt w nagłych przypadkach szukają weterynarza w Google.",
    "optician":       "Optyk bez strony traci klientów do tych, których można znaleźć w Google.",
    "pharmacy":       "Apteki mogą zautomatyzować odpowiedzi na pytania o dostępność leków i godziny.",

    # Auto
    "mechanik":       "Warsztaty tracą zlecenia w nagłych sytuacjach — klienci dzwonią do następnego jeśli nikt nie odbiera.",
    "car_repair":     "Warsztaty tracą zlecenia w nagłych sytuacjach — klienci dzwonią do następnego jeśli nikt nie odbiera.",
    "car repair":     "Warsztaty tracą zlecenia w nagłych sytuacjach — klienci dzwonią do następnego jeśli nikt nie odbiera.",
    "warsztat":       "Warsztaty tracą zlecenia w nagłych sytuacjach — klienci dzwonią do następnego jeśli nikt nie odbiera.",
    "car wash":       "Myjnie mogą przyjmować rezerwacje online i wysyłać powiadomienia SMS o gotowości auta.",
    "car parts":      "Sklepy z częściami mogą zautomatyzować sprawdzanie dostępności przez chat lub telefon AI.",
    "tyres":          "Sklepy oponiarskie mogą rezerwować terminy wymiany opon automatycznie.",

    # Professional services
    "prawnik":        "Kancelarie prawne tracą klientów, którzy nie mogą umówić konsultacji szybko online.",
    "lawyer":         "Kancelarie prawne tracą klientów, którzy nie mogą umówić konsultacji szybko online.",
    "księgowy":       "Biura rachunkowe mogą zautomatyzować przyjmowanie dokumentów i przypominanie o terminach.",
    "accountant":     "Biura rachunkowe mogą zautomatyzować przyjmowanie dokumentów i przypominanie o terminach.",
    "notariusz":      "Kancelarie notarialne mogą zautomatyzować umawianie terminów i wstępną kwalifikację spraw.",
    "notary":         "Kancelarie notarialne mogą zautomatyzować umawianie terminów i wstępną kwalifikację spraw.",
    "szkoła jazdy":   "Szkoły jazdy tracą kursantów przez brak możliwości zapisu online.",
    "driving school": "Szkoły jazdy tracą kursantów przez brak możliwości zapisu online.",
    "estate agent":   "Agencje nieruchomości mogą używać AI do kwalifikowania zapytań i umawiania oglądań.",
    "insurance":      "Agencje ubezpieczeniowe mogą zautomatyzować wstępną wycenę i umawianie spotkań.",
    "tax advisor":    "Doradcy podatkowi mogą zautomatyzować przyjmowanie zapytań i przypomnienia o terminach.",

    # Retail
    "sklep":          "Sklepy bez strony są niewidoczne dla klientów szukających w Google przed zakupem.",
    "shop":           "Sklepy bez strony są niewidoczne dla klientów szukających w Google przed zakupem.",
    "clothes":        "Sklepy odzieżowe mogą prezentować kolekcje online i zbierać zamówienia przez chat.",
    "shoes":          "Sklepy obuwnicze mogą pokazywać dostępność rozmiarów online i redukować pytania telefoniczne.",
    "electronics":    "Sklepy elektroniczne mogą automatyzować odpowiedzi o dostępność i wycenę napraw.",
    "furniture":      "Sklepy meblowe tracą klientów przez brak galerii online i formularza wyceny.",
    "jewellery":      "Jubilerzy mogą prezentować kolekcję i przyjmować zamówienia indywidualne przez stronę.",
    "florist":        "Kwiaciarnie tracą zamówienia na bukiety i dekoracje przez brak formularza online.",
    "kwiaciarnia":    "Kwiaciarnie tracą zamówienia na bukiety i dekoracje przez brak formularza online.",

    # Food retail
    "butcher":        "Masarnie mogą przyjmować zamówienia zbiorcze online i redukować czas przy kasie.",
    "deli":           "Delikatesy mogą prezentować ofertę tygodniową online i przyjmować zamówienia.",
    "grocery":        "Sklepy spożywcze mogą automatyzować pytania o godziny i dostępność produktów.",

    # Education
    "szkoła":         "Szkoły i ośrodki szkoleniowe mogą zautomatyzować zapisy i przypomnienia o zajęciach.",
    "language school":"Szkoły językowe mogą przyjmować zapisy online i wysyłać materiały automatycznie.",
    "music school":   "Szkoły muzyczne mogą zautomatyzować zapisy na lekcje i powiadamianie rodziców.",

    # Other services
    "hotel":          "Hotele mogą zautomatyzować rezerwacje i odpowiedzi na pytania o dostępność.",
    "travel":         "Biura podróży mogą zautomatyzować wyceny i odpowiadać na pytania o oferty.",
    "cleaning":       "Firmy sprzątające mogą przyjmować zlecenia online i wyceniać usługi automatycznie.",
    "electrician":    "Elektrycy tracą zlecenia, bo klienci w nagłych sytuacjach dzwonią do tego, kto odbierze.",
    "elektryk":       "Elektrycy tracą zlecenia, bo klienci w nagłych sytuacjach dzwonią do tego, kto odbierze.",
    "plumber":        "Hydraulicy tracą zlecenia, bo klienci w nagłych sytuacjach dzwonią do tego, kto odbierze.",
    "hydraulik":      "Hydraulicy tracą zlecenia, bo klienci w nagłych sytuacjach dzwonią do tego, kto odbierze.",
    "photographer":   "Fotografowie tracą zlecenia przez brak portfolio i formularza zapytań online.",
    "studio":         "Studia tracą klientów przez brak portfolio i możliwości rezerwacji online.",
    "gym":            "Siłownie i kluby fitness mogą zautomatyzować zapisy i przypomnienia o treningach.",
    "sport":          "Obiekty sportowe mogą zautomatyzować rezerwacje kortów, torów i sal.",
    "taxi":           "Firmy taxi mogą przyjmować zamówienia przez chat i potwierdzać SMS automatycznie.",
    "laundry":        "Pralnie mogą informować klientów o statusie zlecenia i przyjmować odbiory online.",
    "pet":            "Sklepy i usługi dla zwierząt mogą zautomatyzować umawianie wizyt i pytania o produkty.",
    "childcare":      "Żłobki i przedszkola mogą zautomatyzować zapisy i komunikację z rodzicami.",
}

# ── Universal fallback — works for ANY business ──────────────────────────────
UNIVERSAL_HOOK = (
    "Większość firm w Polsce traci klientów przez jedno z trzech: "
    "brak strony w Google, nieodebrane telefony, lub brak rezerwacji online. "
    "Które z tych trzech dotyczy {name}?"
)

def get_category_hook(category_pl: str, business_name: str = "") -> str:
    """
    Returns a one-line pain point for the business category.
    Falls back to a universal hook that works for any business.
    """
    if category_pl:
        cat_lower = category_pl.lower()
        for key, hook in CATEGORY_HOOKS.items():
            if key in cat_lower:
                return hook
    # Universal fallback — works for literally any business
    return UNIVERSAL_HOOK.format(name=business_name or "Państwa firma")


# ── Templates ────────────────────────────────────────────────────────────────
TEMPLATES = {

    # ── Initial outreach — universal AI Agency pitch ─────────────────────────
    "pl_initial_outreach": {
        "name": "Pierwszy kontakt — AI Agency, dowolna branża (PL)",
        "subject": "Krótkie pytanie do {name} w {city}",
        "body": """Dzień dobry,

Nazywam się {sender_name} — pomagam polskim firmom rozwiązywać konkretne problemy za pomocą AI i automatyzacji.

Natrafiłem na {name} w {city} i zauważyłem, że nie mają Państwo strony internetowej. {category_hook}

Co robimy w praktyce — zależy od problemu:

→ Brak strony? Stawiamy szybką, profesjonalną stronę widoczną w Google
→ Nieodebrane telefony? AI odbiera zamiast Państwa — 24/7, po polsku
→ Za dużo czasu na administrację? Automatyzujemy powtarzalne zadania
→ Inny problem? Proszę powiedzieć — znajdziemy rozwiązanie lub powiemy wprost, że AI tu nie pomoże

Jak to działa finansowo: Państwo płacą tylko za narzędzia (hosting, AI) — zwykle 100–300 zł/mies. My zarabiamy na wdrożeniu. Zero lock-inu.

Czy możemy porozmawiać 15 minut? Proszę wybrać termin:
👉 {calendly_link}

Albo po prostu odpowiedzieć na tego maila jednym zdaniem: jaki jest największy problem w firmie, który chcieliby Państwo rozwiązać?

Pozdrawiam,
{sender_name}
Tel: {sender_phone} | {sender_email}

P.S. Jeśli znacie Państwo innego właściciela firmy, który mógłby skorzystać — proszę przekazać ten mail. Pracujemy z polecenia. 🙏

---
Wiadomość wysłana na podstawie publicznie dostępnych danych. Aby wypisać się z korespondencji, proszę odpowiedzieć „Wypisz" (RODO).
""",
    },

    # ── Follow-up 1 — 3-5 days, ask their problem directly ──────────────────
    "pl_follow_up_1": {
        "name": "Follow-up 1 — 3-5 dni, pytanie o problem (PL)",
        "subject": "RE: {name} — jedno pytanie",
        "body": """Dzień dobry,

Pisałem kilka dni temu — chciałem tylko sprawdzić, czy dotarło.

Rozumiem, że prowadzenie {name} pochłania mnóstwo czasu. Dlatego mam tylko jedno pytanie:

Co w tej chwili najbardziej „boli" w Państwa firmie?

Może to:
• Klienci, których nie można znaleźć online?
• Telefony, które nie są odbierane?
• Za dużo czasu na powtarzalne zadania?
• Coś zupełnie innego?

Proszę napisać jednym zdaniem — a ja odpiszę konkretnie co AI może zrobić i co to kosztuje (lub powiem wprost, że nie warto).

Albo od razu 15 minut rozmowy:
👉 {calendly_link}

Pozdrawiam,
{sender_name}
Tel: {sender_phone}

---
Aby wypisać się, proszę odpowiedzieć „Wypisz" (RODO).
""",
    },

    # ── Follow-up 2 — last attempt, leave door open ──────────────────────────
    "pl_follow_up_2": {
        "name": "Follow-up 2 — ostatnia wiadomość (PL)",
        "subject": "Ostatnia wiadomość — {name}",
        "body": """Dzień dobry,

To moja ostatnia wiadomość — nie chcę przeszkadzać.

Jeśli AI i automatyzacja nie są teraz tematem dla {name}, w pełni rozumiem. Proszę zachować kontakt na przyszłość:

{sender_name} | {sender_phone} | {sender_email}

Kiedy pojawi się potrzeba — nieważne co to: strona, AI recepcjonistka, automatyzacja faktur, chatbot, cokolwiek — proszę pisać lub dzwonić. Powiemy wprost co się da zrobić i za ile.

A jeśli znacie Państwo kogoś, kto mógłby skorzystać — będę bardzo wdzięczny za polecenie. 🙏

Życzę samych dobrych klientów!

{sender_name}
👉 {calendly_link}

---
To jest ostatnia wiadomość z mojej strony. Adres zostanie usunięty z bazy (RODO).
""",
    },

    # ── Reply: positive interest ─────────────────────────────────────────────
    "pl_thank_you_reply": {
        "name": "Odpowiedź na zainteresowanie (PL)",
        "subject": "RE: {name} — super, kiedy rozmawiamy?",
        "body": """Dzień dobry,

Dziękuję za odpowiedź — cieszę się!

Proszę wybrać dowolny termin na 15-minutową rozmowę:
👉 {calendly_link}

Żeby lepiej się przygotować — jeśli możliwe, proszę napisać w jednym zdaniu:
• Jaki jest główny problem, który chcieliby Państwo rozwiązać?

Nie ma obowiązku — możemy też po prostu porozmawiać i wspólnie to ustalić.

Do usłyszenia!

{sender_name}
Tel: {sender_phone}
""",
    },

    # ── English version ──────────────────────────────────────────────────────
    "en_initial_outreach": {
        "name": "Initial Outreach — universal AI Agency (EN)",
        "subject": "Quick question for {name} in {city}",
        "body": """Hello,

My name is {sender_name} — I help Polish businesses solve specific problems using AI and automation.

I came across {name} in {city} and noticed you don't have a website yet. {category_hook}

What we do depends on the problem:

→ No website? We build a fast, professional site visible on Google
→ Missed calls? AI answers instead of you — 24/7, in Polish
→ Too much time on admin? We automate repetitive tasks
→ Something else? Tell us — we'll find a solution or be honest that AI won't help here

How does pricing work: you pay only for the tools (hosting, AI APIs) — typically $30–80/month. We earn on setup. No lock-in.

Can we talk for 15 minutes? Pick a time here:
👉 {calendly_link}

Or just reply with one sentence: what's the biggest problem in your business you'd like to fix?

Best regards,
{sender_name}
Tel: {sender_phone} | {sender_email}

P.S. If you know another business owner who could benefit — please forward this. We work from referrals. 🙏

---
This message was sent based on publicly available contact data. Reply "Unsubscribe" to be removed (GDPR).
""",
    },
}


def render_email(
    lead: Dict[str, Any],
    template_key: str = "pl_initial_outreach",
    sender_name: str = "Twoje Imię",
    sender_email: str = "abivr0910@gmail.com",
    sender_phone: str = "+48 000 000 000",
    university_name: str = "AI Studio",
    calendly_link: str = CALENDLY_LINK,
) -> Dict[str, str]:
    """Renders a fully personalized email for any business lead."""
    if template_key not in TEMPLATES:
        raise ValueError(
            f"Template '{template_key}' not found. "
            f"Available: {list(TEMPLATES.keys())}"
        )

    template = TEMPLATES[template_key]
    category_pl = lead.get("category_pl") or lead.get("category") or ""
    business_name = lead.get("name", "Państwa firma")
    hook = get_category_hook(category_pl, business_name)

    context = {
        "name":           business_name,
        "city":           lead.get("city", "Państwa okolicy"),
        "address":        lead.get("address", ""),
        "category_pl":    category_pl,
        "category_hook":  hook,
        "sender_name":    sender_name,
        "sender_email":   sender_email,
        "sender_phone":   sender_phone,
        "university_name": university_name,
        "calendly_link":  calendly_link,
    }

    subject = template["subject"].format(**context)
    body    = template["body"].format(**context)
    return {"subject": subject, "body": body}


def get_template_names() -> Dict[str, str]:
    """Returns template_key → human readable name."""
    return {k: v["name"] for k, v in TEMPLATES.items()}
