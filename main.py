"""
LeadPulse PL - Automated B2B Lead Generator & Outreach for Polish Local Businesses.
"""
import sys
import argparse
from typing import Optional

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import POLISH_CITIES, BUSINESS_CATEGORIES
from database import init_db, save_lead, get_leads, update_lead_status, export_to_csv
from scraper import query_osm_for_candidates, verify_and_enrich_lead
from email_templates import TEMPLATES, render_email
from outreach import run_outreach_batch

console = Console()

def cmd_search(city: str, category: str, limit: int, enrich_now: bool):
    """Searches for businesses in a Polish city without website tags."""
    city_clean = city.lower()
    cat_clean = category.lower()

    city_info = POLISH_CITIES.get(city_clean)
    display_city = city_info["name"] if city_info else city.capitalize()

    console.print(f"\n[bold cyan]🔍 Scanning for [bold white]{cat_clean}[/bold white] businesses in [bold white]{display_city}[/bold white] without websites...[/bold cyan]")
    candidates = query_osm_for_candidates(city_clean, cat_clean, limit=limit)
    console.print(f"Discovered [bold green]{len(candidates)}[/bold green] candidate businesses.")

    saved_count = 0
    for i, lead in enumerate(candidates, 1):
        if enrich_now:
            console.print(f"  [{i}/{len(candidates)}] Verifying & Enriching: [white]{lead['name']}[/white]...")
            lead = verify_and_enrich_lead(lead)
        save_lead(lead)
        saved_count += 1

    console.print(f"[bold green]✓ Successfully processed and saved {saved_count} leads to database![/bold green]\n")

def cmd_enrich(city: Optional[str], limit: int):
    """Verifies candidate leads using search to confirm missing websites and find emails/phones."""
    leads = get_leads(city=city, status="NEW", limit=limit)
    if not leads:
        # Also check leads without emails
        leads = [l for l in get_leads(city=city, limit=limit) if not l.get("email")]

    if not leads:
        console.print("[yellow]No leads waiting for verification in this city.[/yellow]")
        return

    console.print(f"[bold cyan]🔍 Verifying {len(leads)} leads against web search (checking for domains & finding contacts)...[/bold cyan]")
    for i, lead in enumerate(leads, 1):
        console.print(f"[{i}/{len(leads)}] Checking [bold white]{lead['name']}[/bold white] ({lead['city']})...")
        enriched = verify_and_enrich_lead(lead)
        save_lead(enriched)
        if enriched.get("email"):
            console.print(f"    [green]✉ Email found:[/green] {enriched['email']}")
        if enriched.get("phone"):
            console.print(f"    [green]📞 Phone found:[/green] {enriched['phone']}")

    console.print("[bold green]✓ Enrichment complete![/bold green]")

def cmd_list(city: Optional[str], only_no_website: bool, only_with_email: bool, only_with_phone: bool, limit: int):
    """Displays leads in a formatted Rich table."""
    leads = get_leads(
        city=city,
        has_website=False if only_no_website else None,
        has_email=True if only_with_email else None,
        limit=limit * 2
    )

    if only_with_phone:
        leads = [l for l in leads if l.get("phone")]

    leads = leads[:limit]

    if not leads:
        console.print("[yellow]No leads found matching criteria. Try running 'search' first![/yellow]")
        return

    filter_info = f" ({city})" if city else ""
    table = Table(title=f"LeadPulse PL - Businesses Without Websites{filter_info} (Showing {len(leads)})", show_lines=True)
    table.add_column("ID", style="cyan", width=4)
    table.add_column("Name", style="bold white")
    table.add_column("Category", style="magenta")
    table.add_column("Address", style="dim white")
    table.add_column("Phone", style="green")
    table.add_column("Email", style="yellow")
    table.add_column("No Web?", style="bold")
    table.add_column("Status", style="cyan")

    for l in leads:
        no_web_str = "[green]YES (No Web)[/green]" if l.get("has_website") == 0 else "[red]Has Web[/red]"
        email_str = l.get("email") or "[dim]N/A[/dim]"
        phone_str = l.get("phone") or "[dim]N/A[/dim]"
        cat_str = l.get("category_pl") or l.get("category") or "Biznes"
        addr_str = l.get("address") or l.get("city") or "Polska"

        table.add_row(
            str(l["id"]),
            l["name"][:25],
            cat_str[:16],
            addr_str[:22],
            phone_str,
            email_str,
            no_web_str,
            l["status"]
        )

    console.print(table)

def cmd_preview(lead_id: Optional[int], city: Optional[str], template: str):
    """Previews the generated cold outreach email for a lead."""
    leads = get_leads(city=city, has_email=True, limit=5)
    if not leads:
        leads = get_leads(city=city, limit=1)

    if not leads:
        console.print("[yellow]No leads available in the database.[/yellow]")
        return

    target_lead = leads[0]
    if lead_id:
        match = [l for l in get_leads(limit=500) if l["id"] == lead_id]
        if match:
            target_lead = match[0]

    rendered = render_email(target_lead, template_key=template)

    panel_content = f"[bold yellow]Recipient Name:[/bold yellow] {target_lead['name']} ({target_lead.get('category_pl', '')})\n[bold yellow]To Email:[/bold yellow] {target_lead.get('email') or '[No Email - Call Phone]'}\n[bold yellow]Phone:[/bold yellow] {target_lead.get('phone') or 'N/A'}\n[bold yellow]Subject:[/bold yellow] {rendered['subject']}\n\n{rendered['body']}"
    console.print(Panel(panel_content, title=f"Personalized Pitch for: {target_lead['name']}", expand=False))

def cmd_send(city: Optional[str], template: str, dry_run: bool, max_count: int):
    """Sends cold email outreach."""
    leads = get_leads(city=city, has_website=False, has_email=True, limit=50)
    if not leads:
        console.print("[yellow]No leads with verified emails found. Run 'search' and 'enrich' first.[/yellow]")
        return

    stats = run_outreach_batch(leads, template_key=template, dry_run=dry_run, max_count=max_count)
    console.print(f"\n[bold green]Outreach Summary:[/bold green] Sent: {stats['sent']}, Failed: {stats['failed']}, Attempted: {stats['attempted']}")

def cmd_export(city: Optional[str], filename: str):
    """Exports leads to CSV file with generated pitch emails included."""
    count = export_to_csv(filename, city=city)
    console.print(f"[bold green]✓ Exported {count} leads without websites (with personalized pitches) to: [white]{filename}[/white][/bold green]")

def main():
    init_db()
    parser = argparse.ArgumentParser(description="LeadPulse PL - Polish Business Lead Finder & Outreach Engine")
    subparsers = parser.add_subparsers(dest="command")

    # search
    p_search = subparsers.add_parser("search", help="Scan for businesses without websites")
    p_search.add_argument("--city", default="torun", help="City name (torun, warszawa, krakow, etc.)")
    p_search.add_argument("--category", default="all", help="Category (all, mechanik, fryzjer, kosmetyczka, dentysta, etc.)")
    p_search.add_argument("--limit", type=int, default=40, help="Max candidates to fetch")
    p_search.add_argument("--enrich", action="store_true", help="Automatically verify domain and find contacts")

    # enrich
    p_enrich = subparsers.add_parser("enrich", help="Search the web to verify domain absence and find emails")
    p_enrich.add_argument("--city", default="torun", help="Filter by city")
    p_enrich.add_argument("--limit", type=int, default=15, help="Number of leads to enrich")

    # list
    p_list = subparsers.add_parser("list", help="List leads in database")
    p_list.add_argument("--city", default="torun", help="Filter by city")
    p_list.add_argument("--no-web-only", action="store_true", default=True, help="Only show businesses without websites")
    p_list.add_argument("--with-email-only", action="store_true", help="Only show leads where email is found")
    p_list.add_argument("--with-phone-only", action="store_true", help="Only show leads where phone number is found")
    p_list.add_argument("--limit", type=int, default=30, help="Limit output rows")

    # preview
    p_preview = subparsers.add_parser("preview", help="Preview personalized pitch email for a lead")
    p_preview.add_argument("--city", default="torun", help="Filter by city")
    p_preview.add_argument("--id", type=int, help="Lead ID to preview")
    p_preview.add_argument("--template", default="pl_modern_website", choices=list(TEMPLATES.keys()))

    # send
    p_send = subparsers.add_parser("send", help="Send outreach emails")
    p_send.add_argument("--city", default="torun", help="Filter by city")
    p_send.add_argument("--template", default="pl_modern_website", choices=list(TEMPLATES.keys()))
    p_send.add_argument("--dry-run", action="store_true", default=True, help="Simulate without sending real emails (default: True)")
    p_send.add_argument("--live", dest="dry_run", action="store_false", help="Actually send real emails via SMTP")
    p_send.add_argument("--max", type=int, default=5, help="Max emails to send in this batch")

    # export
    p_export = subparsers.add_parser("export", help="Export leads to CSV file")
    p_export.add_argument("--city", default="torun", help="Filter by city")
    p_export.add_argument("--file", default="leads_torun.csv", help="Output CSV file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "search":
        cmd_search(args.city, args.category, args.limit, args.enrich)
    elif args.command == "enrich":
        cmd_enrich(args.city, args.limit)
    elif args.command == "list":
        cmd_list(args.city, args.no_web_only, args.with_email_only, args.with_phone_only, args.limit)
    elif args.command == "preview":
        cmd_preview(args.id, args.city, args.template)
    elif args.command == "send":
        cmd_send(args.city, args.template, args.dry_run, args.max)
    elif args.command == "export":
        cmd_export(args.city, args.file)

if __name__ == "__main__":
    main()
