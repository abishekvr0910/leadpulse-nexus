"""
Mission Runner: Toruń Lead Generation & Outreach Pipeline.
Scrapes, verifies, enriches contacts, generates pitches, and exports the full lead list.
"""
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

import time
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import USER_AGENT
from database import init_db, save_lead, get_leads, export_to_csv, update_lead_status
from scraper import query_osm_for_candidates, verify_and_enrich_lead
from email_templates import render_email, TEMPLATES
from outreach import run_outreach_batch

console = Console()

def run_torun_mission(enrich_limit: int = 15):
    init_db()
    console.print(Panel("[bold cyan]🚀 LEADPULSE PL: MISSION TORUŃ[/bold cyan]\n[white]Goal: Identify all local companies in Toruń without websites, extract phone numbers & emails, generate personalized pitches, and prepare outreach.[/white]", expand=False))

    # Phase 1: Ingest businesses from Toruń
    console.print("\n[bold yellow]Phase 1: Querying businesses in Toruń without websites...[/bold yellow]")
    leads = query_osm_for_candidates("torun", "all", limit=50)
    saved_count = 0
    for l in leads:
        if save_lead(l):
            saved_count += 1
    console.print(f"✓ Found and stored [bold green]{saved_count}[/bold green] businesses in Toruń.")

    # Phase 2: Verification and Contact Enrichment
    console.print(f"\n[bold yellow]Phase 2: Verifying website absence & finding contact details (Top {enrich_limit})...[/bold yellow]")
    candidates = get_leads(city="Toruń", limit=enrich_limit)
    enriched_count = 0
    emails_discovered = 0
    phones_discovered = 0

    for i, lead in enumerate(candidates, 1):
        console.print(f"  [{i}/{len(candidates)}] Checking: [white]{lead['name']}[/white] ({lead['category_pl']})...")
        enriched = verify_and_enrich_lead(lead)
        save_lead(enriched)
        enriched_count += 1
        if enriched.get("email"):
            emails_discovered += 1
            console.print(f"     [bold green]✉ Email found:[/bold green] {enriched['email']}")
        if enriched.get("phone"):
            phones_discovered += 1
            console.print(f"     [bold green]📞 Phone found:[/bold green] {enriched['phone']}")
        time.sleep(1)  # Polite pause between search queries

    console.print(f"✓ Enrichment complete. Processed: {enriched_count} | Emails found: {emails_discovered} | Phones: {phones_discovered}")

    # Phase 3: Display Results
    console.print("\n[bold yellow]Phase 3: Verified Leads in Toruń[/bold yellow]")
    all_torun_leads = get_leads(city="Toruń", limit=40)

    table = Table(title="Toruń Businesses Without Websites", show_lines=True)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Company Name", style="bold white")
    table.add_column("Category", style="magenta")
    table.add_column("Address", style="dim white")
    table.add_column("Phone", style="green")
    table.add_column("Email", style="yellow")
    table.add_column("No Web?", style="bold")
    table.add_column("Status", style="cyan")

    for l in all_torun_leads:
        no_web = "[green]YES[/green]" if l.get("has_website") == 0 else "[red]NO[/red]"
        phone_val = l.get("phone") or "[dim]N/A[/dim]"
        email_val = l.get("email") or "[dim]N/A[/dim]"
        table.add_row(
            str(l["id"]),
            l["name"][:25],
            l.get("category_pl", l.get("category", ""))[:18],
            l.get("address", "")[:25],
            phone_val,
            email_val,
            no_web,
            l.get("status", "")
        )

    console.print(table)

    # Phase 4: Generate Outreach Pitch Preview
    console.print("\n[bold yellow]Phase 4: Sample Outreach Pitch for Toruń Company[/bold yellow]")
    with_email = [l for l in all_torun_leads if l.get("email")]
    sample_lead = with_email[0] if with_email else all_torun_leads[0]
    rendered = render_email(sample_lead, template_key="pl_modern_website")
    console.print(Panel(f"[bold yellow]To:[/bold yellow] {sample_lead.get('email') or '[No Email - Call Phone]'}\n[bold yellow]Subject:[/bold yellow] {rendered['subject']}\n\n{rendered['body']}", title=f"Generated Cold Email for {sample_lead['name']}", expand=False))

    # Phase 5: Export to CSV
    export_filename = "torun_leads_verified.csv"
    count = export_to_csv(export_filename)
    console.print(f"\n[bold green]✓ Full database of {count} verified Toruń leads exported to: [white]{export_filename}[/white][/bold green]")

    # Phase 6: Dry-Run Outreach Execution
    console.print("\n[bold yellow]Phase 5: Outreach Delivery Simulation (Dry-Run Safety Mode)[/bold yellow]")
    if with_email:
        run_outreach_batch(all_torun_leads, template_key="pl_modern_website", dry_run=True, max_count=5)
    else:
        console.print("[dim]Dry-run simulation ready. Once additional emails are added, live SMTP will send directly.[/dim]")

if __name__ == "__main__":
    run_torun_mission(enrich_limit=12)
