"""
LeadPulse EU — B2B Lead Dashboard
===================================
Launch:  streamlit run dashboard.py
"""
import sys, os, io
sys.stdout.reconfigure(encoding="utf-8")

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import subprocess
import plotly.express as px
import plotly.graph_objects as go

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "leads.db")

def make_dark_layout(fig, height=360, showlegend=True):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.4)",
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#94A3B8", size=11),
        height=height,
        margin=dict(l=15, r=15, t=30, b=15),
        showlegend=showlegend,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#CBD5E1")
        ),
        hoverlabel=dict(
            bgcolor="#0F172A",
            bordercolor="#6366F1",
            font=dict(family="Plus Jakarta Sans, sans-serif", color="#FFFFFF", size=12)
        )
    )
    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#94A3B8")
    )
    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.05)",
        zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#94A3B8")
    )
    return fig

st.set_page_config(
    page_title="LeadPulse EU",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_modern_styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }

    /* Background & Global Surfaces */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #0F172A 0%, #020617 100%) !important;
        color: #F8FAFC !important;
    }

    /* Header styling */
    h1 {
        font-weight: 800 !important;
        letter-spacing: -0.03em !important;
        background: linear-gradient(135deg, #FFFFFF 20%, #94A3B8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    h2, h3 {
        font-weight: 700 !important;
        letter-spacing: -0.02em !important;
        color: #F8FAFC !important;
    }

    /* Live Pulsing Badge */
    .pulse-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 10px;
        border-radius: 9999px;
        color: #34D399;
        font-size: 0.75rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    .pulse-dot {
        width: 8px;
        height: 8px;
        background: #10B981;
        border-radius: 50%;
        box-shadow: 0 0 8px #10B981;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Modern Glassmorphic Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 14px;
        margin-top: 10px;
        margin-bottom: 24px;
    }
    .modern-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border-radius: 16px;
        padding: 18px 16px;
        transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        position: relative;
        overflow: hidden;
    }
    .modern-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 20px 30px -10px rgba(99, 102, 241, 0.2);
    }
    .card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .card-title {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
    }
    .card-icon {
        font-size: 1.25rem;
    }
    .card-val {
        font-size: 1.85rem;
        font-weight: 800;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }
    .card-sub {
        font-size: 0.75rem;
        color: #64748B;
        margin-top: 6px;
        font-weight: 500;
    }
    .badge-green {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.68rem;
        font-weight: 600;
    }
    .badge-indigo {
        background: rgba(99, 102, 241, 0.15);
        color: #818CF8;
        border: 1px solid rgba(99, 102, 241, 0.3);
        padding: 2px 8px;
        border-radius: 9999px;
        font-size: 0.68rem;
        font-weight: 600;
    }

    /* Sidebar Customization */
    section[data-testid="stSidebar"] {
        background: #090D16 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 6px;
    }
    section[data-testid="stSidebar"] .stRadio label {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 10px 14px;
        color: #94A3B8 !important;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(99, 102, 241, 0.12);
        border-color: rgba(99, 102, 241, 0.3);
        color: #FFFFFF !important;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 12px !important;
        padding: 10px 22px !important;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.35) !important;
        transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(79, 70, 229, 0.5) !important;
    }

    /* Download Buttons */
    .stDownloadButton > button {
        background: rgba(30, 41, 59, 0.8) !important;
        color: #F1F5F9 !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease;
    }
    .stDownloadButton > button:hover {
        background: rgba(51, 65, 85, 0.9) !important;
        border-color: rgba(99, 102, 241, 0.4) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px);
    }

    /* Tables & DataFrames */
    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        overflow: hidden;
        background: rgba(15, 23, 42, 0.75);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    /* Expanders */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        background: rgba(15, 23, 42, 0.5) !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
    }

    /* Inputs */
    .stTextInput > div > div > input {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: #F8FAFC !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.25) !important;
    }
    </style>
    """, unsafe_allow_html=True)

inject_modern_styles()

FLAGS = {
    "Poland":"🇵🇱","Germany":"🇩🇪","Austria":"🇦🇹","Switzerland":"🇨🇭",
    "Netherlands":"🇳🇱","Belgium":"🇧🇪","Sweden":"🇸🇪","Denmark":"🇩🇰",
    "Norway":"🇳🇴","United Kingdom":"🇬🇧","France":"🇫🇷","Ireland":"🇮🇪",
}

# ── DB helpers ───────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def run_sql(sql, params=()):
    conn = get_conn()
    conn.execute(sql, params)
    conn.commit()
    conn.close()

@st.cache_data(ttl=20)
def load_data() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM leads ORDER BY id DESC", conn)
    conn.close()

    df["created_at"]   = pd.to_datetime(df["created_at"],   errors="coerce")
    df["contacted_at"] = pd.to_datetime(df["contacted_at"], errors="coerce")
    df["has_phone"]    = df["phone"].apply(lambda x: bool(x and str(x).strip()))
    df["has_email_addr"]= df["email"].apply(
        lambda x: bool(x and str(x).strip() not in ("", "N/A")))

    # Safe defaults for optional columns
    defaults = {
        "email_stage":"NONE","reply_type":"","reply_notes":"",
        "template_used":"","country":"Poland","country_code":"PL",
        "language":"pl","currency":"PLN","avg_revenue_eur":800,
        "primary_contact_name":"","primary_contact_title":"",
        "primary_contact_email":"","primary_contact_linkedin":"",
        "company_reg_number":"","contacts_count":0,
    }
    for col, val in defaults.items():
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].fillna(val)

    df["reply_received"] = df.get("reply_received", pd.Series([0]*len(df))).fillna(0).astype(int)
    df["flag"] = df["country"].map(FLAGS).fillna("🌍")
    return df

@st.cache_data(ttl=15)
def load_contacts() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    try:
        cdf = pd.read_sql_query("SELECT * FROM company_contacts ORDER BY id DESC", conn)
    except Exception:
        cdf = pd.DataFrame()
    conn.close()
    return cdf

def to_csv(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False, encoding="utf-8-sig")
    return buf.getvalue()


def preview_email_for(lead_row: dict, tpl: str, name: str, email: str, phone: str, uni: str) -> dict:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from email_templates import render_email
    return render_email(lead=lead_row, template_key=tpl,
                        sender_name=name, sender_email=email,
                        sender_phone=phone, university_name=uni)

# ── Load ─────────────────────────────────────────────────────────────────────
df_all = load_data()

# ── Sidebar nav ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🌍 LeadPulse EU")
    st.caption(f"{len(df_all):,} leads · {df_all['country'].nunique()} countries")

    page = st.radio("", [
        "📊 Overview",
        "📋 Company List",
        "👥 Decision Makers",
        "📧 Email Outreach",
        "📬 Replies",
        "🌍 Scan Europe",
        "⚙️ Settings",
    ], label_visibility="collapsed")


    st.markdown("---")
    st.subheader("Filters")

    # Country
    all_countries = sorted(df_all["country"].dropna().unique())
    country_opts  = [f"{FLAGS.get(c,'🌍')} {c}" for c in all_countries]
    sel_c = st.multiselect("🌍 Country", country_opts, default=[])
    sel_countries = [c.split(" ", 1)[1] for c in sel_c]

    # City
    city_pool = df_all[df_all["country"].isin(sel_countries)]["city"] if sel_countries else df_all["city"]
    cities_list = sorted(city_pool.dropna().unique())
    sel_cities  = st.multiselect("🏙️ City", cities_list, default=[])

    # Category
    sel_cats = st.multiselect("📂 Category", sorted(df_all["category_pl"].dropna().unique()), default=[])

    # Status
    sel_statuses = st.multiselect("📌 Status", sorted(df_all["status"].dropna().unique()), default=[])

    st.markdown("")
    has_email = st.checkbox("📧 Has email only")
    has_phone = st.checkbox("📞 Has phone only")
    no_web    = st.checkbox("🚫 No website only")

# ── Apply filters ─────────────────────────────────────────────────────────────
df = df_all.copy()
if sel_countries: df = df[df["country"].isin(sel_countries)]
if sel_cities:    df = df[df["city"].isin(sel_cities)]
if sel_cats:      df = df[df["category_pl"].isin(sel_cats)]
if sel_statuses:  df = df[df["status"].isin(sel_statuses)]
if has_email:     df = df[df["has_email_addr"]]
if has_phone:     df = df[df["has_phone"]]
if no_web:        df = df[df["has_website"] == 0]

# ══════════════════════════════════════════════════════════════════════════════
# OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Overview":
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(6, 182, 212, 0.15) 100%); border: 1px solid rgba(99, 102, 241, 0.4); border-radius: 14px; padding: 14px 20px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; items-center; gap: 12px;">
            <span style="font-size: 22px;">⚡</span>
            <div>
                <strong style="color: #FFFFFF; font-size: 14px;">Next-Gen 60fps Executive Web App Live on Port 8000</strong>
                <p style="margin: 0; color: #94A3B8; font-size: 12px;">Instant zero-lag filtering, animated ApexCharts, interactive ROI calculator & live AI voice phone simulator.</p>
            </div>
        </div>
        <a href="http://localhost:8000" target="_blank" style="background: #6366F1; color: #FFFFFF; font-weight: 700; font-size: 12px; padding: 8px 18px; border-radius: 10px; text-decoration: none; box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);">
            Open Web App ↗
        </a>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="pulse-badge"><div class="pulse-dot"></div> LeadPulse Engine Live · European SMB Pipeline</div>', unsafe_allow_html=True)
    st.title("📊 Continental Intelligence Overview")
    st.caption(f"Showing **{len(df):,}** of **{len(df_all):,}** leads across **{df['country'].nunique()}** European countries · Live auto-refresh")

    # Top Modern KPIs
    kpi_html = f"""
    <div class="metric-grid">
        <div class="modern-card">
            <div class="card-header">
                <span class="card-title">Total Database</span>
                <span class="card-icon">🏢</span>
            </div>
            <div class="card-val">{len(df):,}</div>
            <div class="card-sub"><span class="badge-indigo">{df['country'].nunique()} Countries</span> across EU</div>
        </div>
        <div class="modern-card" style="border-top: 3px solid #10B981;">
            <div class="card-header">
                <span class="card-title">Verified Direct Phones</span>
                <span class="card-icon">📞</span>
            </div>
            <div class="card-val" style="color: #34D399;">{df['has_phone'].sum():,}</div>
            <div class="card-sub"><span class="badge-green">Voice-Ready</span> Direct dials</div>
        </div>
        <div class="modern-card" style="border-top: 3px solid #38BDF8;">
            <div class="card-header">
                <span class="card-title">Verified Emails</span>
                <span class="card-icon">📧</span>
            </div>
            <div class="card-val" style="color: #38BDF8;">{df['has_email_addr'].sum():,}</div>
            <div class="card-sub">Inboxes & Executives</div>
        </div>
        <div class="modern-card" style="border-top: 3px solid #F59E0B;">
            <div class="card-header">
                <span class="card-title">No Website (Prime Leads)</span>
                <span class="card-icon">🚫</span>
            </div>
            <div class="card-val" style="color: #FBBF24;">{(df['has_website']==0).sum():,}</div>
            <div class="card-sub">Highest conversion bottleneck</div>
        </div>
        <div class="modern-card" style="border-top: 3px solid #A855F7;">
            <div class="card-header">
                <span class="card-title">Metropolitan Hubs</span>
                <span class="card-icon">🏙️</span>
            </div>
            <div class="card-val" style="color: #C084FC;">{df['city'].nunique()}</div>
            <div class="card-sub">Active City Markets</div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

    st.markdown("---")

    # Modern Outreach funnel
    st.subheader("📧 Email & Deal Pipeline")
    funnel_html = f"""
    <div class="metric-grid" style="grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
        <div class="modern-card">
            <div class="card-header"><span class="card-title">Email-Ready</span><span>📬</span></div>
            <div class="card-val">{df['has_email_addr'].sum():,}</div>
            <div class="card-sub">In Queue</div>
        </div>
        <div class="modern-card">
            <div class="card-header"><span class="card-title">Uncontacted</span><span>⏳</span></div>
            <div class="card-val">{(df['email_stage'].isin(['NONE',''])).sum():,}</div>
            <div class="card-sub">Fresh Prospects</div>
        </div>
        <div class="modern-card">
            <div class="card-header"><span class="card-title">Initial Sent</span><span>📤</span></div>
            <div class="card-val" style="color: #818CF8;">{(df['email_stage']=='INITIAL_SENT').sum():,}</div>
            <div class="card-sub">Stage 1 Hook</div>
        </div>
        <div class="modern-card">
            <div class="card-header"><span class="card-title">Follow-up 1</span><span>🔄</span></div>
            <div class="card-val" style="color: #F59E0B;">{(df['email_stage']=='FOLLOWUP1_SENT').sum():,}</div>
            <div class="card-sub">Stage 2 Followup</div>
        </div>
        <div class="modern-card">
            <div class="card-header"><span class="card-title">Follow-up 2</span><span>⚡</span></div>
            <div class="card-val" style="color: #EC4899;">{(df['email_stage']=='FOLLOWUP2_SENT').sum():,}</div>
            <div class="card-sub">Stage 3 Final</div>
        </div>
        <div class="modern-card" style="border-top: 3px solid #10B981;">
            <div class="card-header"><span class="card-title">Replied / Meeting</span><span>🎉</span></div>
            <div class="card-val" style="color: #10B981;">{(df['email_stage']=='REPLIED').sum():,}</div>
            <div class="card-sub"><span class="badge-green">Warm Leads</span></div>
        </div>
    </div>
    """
    st.markdown(funnel_html, unsafe_allow_html=True)


    st.markdown("---")

    # Country breakdown table
    st.subheader("Leads by Country")
    country_stats = (
        df.groupby("country")
        .agg(
            Leads=("id","count"),
            With_Email=("has_email_addr","sum"),
            With_Phone=("has_phone","sum"),
            No_Website=("has_website", lambda x: (x==0).sum()),
        )
        .reset_index()
        .sort_values("Leads", ascending=False)
    )
    country_stats.insert(0, "Flag", country_stats["country"].map(FLAGS).fillna("🌍"))
    country_stats = country_stats.rename(columns={"country":"Country"})
    st.dataframe(country_stats, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Interactive Visual Intelligence Suite ─────────────────────────────────────
    st.subheader("📈 Continental Market & Niche Intelligence")
    
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        st.markdown("##### 🏙️ Top Metropolises by Lead Density")
        top_cities = df["city"].value_counts().head(14).reset_index()
        top_cities.columns = ["City", "Leads"]
        top_cities = top_cities.sort_values("Leads", ascending=True)
        fig_cities = px.bar(
            top_cities, x="Leads", y="City", orientation="h",
            color="Leads",
            color_continuous_scale=[[0, "#4F46E5"], [0.5, "#6366F1"], [1, "#06B6D4"]]
        )
        fig_cities.update_traces(
            marker=dict(line=dict(color="rgba(255,255,255,0.15)", width=1), opacity=0.9),
            hovertemplate="<b>%{y}</b><br>Verified Leads: <b>%{x:,}</b><extra></extra>"
        )
        fig_cities = make_dark_layout(fig_cities, height=390, showlegend=False)
        fig_cities.update_coloraxes(showscale=False)
        st.plotly_chart(fig_cities, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    with col_g2:
        st.markdown("##### 🔥 High-Ticket Target Niches")
        top_cats = df["category_pl"].value_counts().head(8).reset_index()
        top_cats.columns = ["Category", "Count"]
        fig_donut = px.pie(
            top_cats, names="Category", values="Count", hole=0.62,
            color_discrete_sequence=["#10B981", "#06B6D4", "#6366F1", "#EC4899", "#F59E0B", "#8B5CF6", "#3B82F6", "#64748B"]
        )
        fig_donut.update_traces(
            textposition="inside", textinfo="percent",
            marker=dict(line=dict(color="#0F172A", width=2)),
            hovertemplate="<b>%{label}</b><br>Leads: <b>%{value:,}</b> (%{percent})<extra></extra>"
        )
        fig_donut = make_dark_layout(fig_donut, height=390, showlegend=True)
        fig_donut.add_annotation(
            text=f"<b>{len(df):,}</b><br><span style='font-size:11px;color:#94A3B8'>Total</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=18, color="#FFFFFF")
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.markdown("##### 🌍 Market Saturation: Leads vs Verified Phones")
        top_countries = (
            df.groupby("country")
            .agg(Total=("id","count"), Phones=("has_phone","sum"))
            .sort_values("Total", ascending=False)
            .head(10)
            .reset_index()
        )
        fig_countries = go.Figure()
        fig_countries.add_trace(go.Bar(
            x=top_countries["country"], y=top_countries["Total"],
            name="Total Leads", marker_color="#4F46E5",
            hovertemplate="<b>%{x}</b><br>Total Leads: <b>%{y:,}</b><extra></extra>"
        ))
        fig_countries.add_trace(go.Bar(
            x=top_countries["country"], y=top_countries["Phones"],
            name="Verified Phones", marker_color="#10B981",
            hovertemplate="<b>%{x}</b><br>Direct Phones: <b>%{y:,}</b><extra></extra>"
        ))
        fig_countries = make_dark_layout(fig_countries, height=390, showlegend=True)
        fig_countries.update_layout(barmode="group", xaxis_tickangle=-25)
        st.plotly_chart(fig_countries, use_container_width=True, config={"displayModeBar": False, "responsive": True})

    with col_g4:
        st.markdown("##### ⚡ Outreach Deal Velocity Funnel")
        stages = ["Database Prospects", "Direct Phones Ready", "Inboxes Verified", "Contacted", "Replied / Meeting"]
        counts = [
            len(df),
            int(df["has_phone"].sum()),
            int(df["has_email_addr"].sum()),
            int((df["email_stage"] != "NONE").sum()),
            int((df["email_stage"] == "REPLIED").sum())
        ]
        fig_funnel = go.Figure(go.Funnel(
            y=stages, x=counts,
            textinfo="value+percent initial",
            marker=dict(color=["#6366F1", "#3B82F6", "#06B6D4", "#F59E0B", "#10B981"]),
            connector=dict(line=dict(color="rgba(255,255,255,0.12)", width=1)),
            opacity=0.9
        ))
        fig_funnel = make_dark_layout(fig_funnel, height=390, showlegend=False)
        st.plotly_chart(fig_funnel, use_container_width=True, config={"displayModeBar": False, "responsive": True})


# ══════════════════════════════════════════════════════════════════════════════
# COMPANY LIST
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Company List":
    st.title("📋 Company List")

    search = st.text_input("🔎 Search by name", "")
    if search:
        df = df[df["name"].str.contains(search, case=False, na=False)]

    st.caption(f"{len(df):,} companies")

    show_cols = ["id","flag","name","primary_contact_name","primary_contact_title",
                 "primary_contact_email","primary_contact_linkedin","company_reg_number",
                 "category_pl","city","country","address","phone","email",
                 "facebook_url","has_website","status","email_stage","created_at"]
    show_cols = [c for c in show_cols if c in df.columns]

    st.dataframe(
        df[show_cols].rename(columns={
            "id":"ID","flag":"","name":"Company",
            "primary_contact_name":"Key Person",
            "primary_contact_title":"Role",
            "primary_contact_email":"Personal Email",
            "primary_contact_linkedin":"LinkedIn",
            "company_reg_number":"Reg No",
            "category_pl":"Category",
            "city":"City","country":"Country","address":"Address",
            "phone":"Phone","email":"Company Email","facebook_url":"Facebook",
            "has_website":"Has Site","status":"Status",
            "email_stage":"Stage","created_at":"Added",
        }),
        use_container_width=True, height=600, hide_index=True,
    )

    st.markdown("---")
    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button("⬇️ All results (CSV)", to_csv(df[show_cols]),
            f"leads_{datetime.now():%Y%m%d}.csv", "text/csv")
    with d2:
        em = df[df["has_email_addr"]]
        st.download_button(f"📧 Email-ready ({len(em)})", to_csv(em[show_cols]),
            f"leads_email_{datetime.now():%Y%m%d}.csv", "text/csv")
    with d3:
        ph = df[df["has_phone"]]
        st.download_button(f"📞 Phone-ready ({len(ph)})", to_csv(ph[show_cols]),
            f"leads_phone_{datetime.now():%Y%m%d}.csv", "text/csv")

# ══════════════════════════════════════════════════════════════════════════════
# DECISION MAKERS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "👥 Decision Makers":
    st.title("👥 Decision Makers & Key People")
    st.caption("Founders, CEOs, Owners, and Managing Directors identified via LinkedIn and Corporate Registries")

    contacts_df = load_contacts()

    with st.expander("🔍 Find Decision Makers & LinkedIn Profiles for Companies", expanded=False):
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            en_country = st.selectbox("Select Country to Enrich", [
                "All Countries", "GB (UK)", "PL (Poland)", "CH (Switzerland)",
                "NL (Netherlands)", "FR (France)", "AT (Austria)", "BE (Belgium)",
                "SE (Sweden)", "NO (Norway)", "DK (Denmark)", "ES (Spain)", "IT (Italy)"
            ])
        with c_col2:
            en_limit = st.slider("Companies to enrich", 5, 100, 20)

        if st.button("🚀 Run Decision-Maker Discovery", type="primary"):
            cmd = ["python", os.path.join(os.path.dirname(DB_PATH), "find_people.py"), "--limit", str(en_limit)]
            if en_country != "All Countries":
                cc = en_country.split()[0]
                cmd += ["--country", cc]
            subprocess.Popen(cmd, cwd=os.path.dirname(DB_PATH))
            st.info(f"Started discovery in background: `{' '.join(cmd)}`. Refresh in a moment to see new people!")

    st.markdown("---")

    if contacts_df.empty:
        st.info("No decision makers discovered yet. Open the panel above and click 'Run Decision-Maker Discovery' to find Founders, CEOs, and LinkedIn profiles!")
    else:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total People Found", f"{len(contacts_df):,}")
        has_li = (contacts_df["linkedin_url"] != "").sum() if "linkedin_url" in contacts_df.columns else 0
        m2.metric("LinkedIn Profiles 🔗", f"{has_li:,}")
        has_pemail = (contacts_df["email"] != "").sum() if "email" in contacts_df.columns else 0
        m3.metric("Direct Emails 📧", f"{has_pemail:,}")
        has_reg = (contacts_df["company_registration"] != "").sum() if "company_registration" in contacts_df.columns else 0
        m4.metric("Corporate Registrations 🏛️", f"{has_reg:,}")

        c_search = st.text_input("🔎 Search by Person Name, Job Title, or Company", "")
        filtered_c = contacts_df.copy()
        if c_search:
            filtered_c = filtered_c[
                filtered_c["person_name"].str.contains(c_search, case=False, na=False) |
                filtered_c["role_title"].str.contains(c_search, case=False, na=False) |
                filtered_c["company_name"].str.contains(c_search, case=False, na=False)
            ]

        st.caption(f"Showing {len(filtered_c):,} decision makers")

        c_cols = ["id", "company_name", "person_name", "role_title", "email", "phone", "linkedin_url", "company_registration", "source"]
        c_cols = [c for c in c_cols if c in filtered_c.columns]

        st.dataframe(
            filtered_c[c_cols].rename(columns={
                "id": "ID", "company_name": "Company", "person_name": "Decision Maker",
                "role_title": "Role / Title", "email": "Direct Email", "phone": "Phone",
                "linkedin_url": "LinkedIn Profile", "company_registration": "Company Reg No",
                "source": "Source"
            }),
            use_container_width=True, height=500, hide_index=True
        )

        st.markdown("---")
        st.download_button(
            "⬇️ Export Decision Makers (CSV)",
            to_csv(filtered_c[c_cols]),
            f"decision_makers_{datetime.now():%Y%m%d}.csv",
            "text/csv"
        )


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL OUTREACH
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📧 Email Outreach":
    st.title("📧 Email Outreach")

    # Sender config
    with st.expander("✏️ Your sender details", expanded=False):
        if "s_name"  not in st.session_state: st.session_state.s_name  = "Your Name"
        if "s_email" not in st.session_state: st.session_state.s_email = "abivr0910@gmail.com"
        if "s_phone" not in st.session_state: st.session_state.s_phone = "+48 000 000 000"
        if "s_uni"   not in st.session_state: st.session_state.s_uni   = "AI Studio"
        st.session_state.s_name  = st.text_input("Name",        st.session_state.s_name)
        st.session_state.s_email = st.text_input("Email",       st.session_state.s_email)
        st.session_state.s_phone = st.text_input("Phone",       st.session_state.s_phone)
        st.session_state.s_uni   = st.text_input("Company/Uni", st.session_state.s_uni)

    st.markdown("---")

    # Verify step
    with st.expander("🔍 Step 1 — Verify companies still have no website", expanded=True):
        v_limit = st.slider("Companies to verify", 5, 100, 30, key="v_lim")
        v_city  = st.text_input("City filter (optional)", "", key="v_city")
        if st.button("▶️ Run Verification", type="primary"):
            cmd = ["python", os.path.join(os.path.dirname(DB_PATH), "verify_batch.py"),
                   "--limit", str(v_limit)]
            if v_city.strip(): cmd += ["--city", v_city.strip()]
            with st.spinner("Verifying via DuckDuckGo... (~2s/company)"):
                r = subprocess.run(cmd, capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", timeout=300)
            if r.returncode == 0:
                ok = r.stdout.count("Confirmed no website")
                found = r.stdout.count("HAS WEBSITE")
                st.success(f"✅ {ok} confirmed no website · {found} excluded (has site)")
                with st.expander("Full log"):
                    st.text(r.stdout)
                st.cache_data.clear()
            else:
                st.error(r.stderr[:400])

    st.markdown("---")

    # Pipeline summary
    email_df = df[df["has_email_addr"]]
    not_yet  = email_df[email_df["email_stage"].isin(["NONE",""])]
    fu1_due  = email_df[email_df["email_stage"]=="INITIAL_SENT"]
    fu2_due  = email_df[email_df["email_stage"]=="FOLLOWUP1_SENT"]

    p1,p2,p3,p4 = st.columns(4)
    p1.metric("📧 Email-ready",    len(email_df))
    p2.metric("🆕 Not contacted",  len(not_yet))
    p3.metric("📨 Initial sent",   len(fu1_due))
    p4.metric("🔄 Follow-up 1 due",len(fu2_due))

    tab1, tab2, tab3, tab4 = st.tabs([
        "📨 Initial Email", "🔄 Follow-up 1", "🔁 Follow-up 2", "👁️ Preview"
    ])

    def send_batch(batch_df, stage_label, email_stage_val, sent_field):
        if batch_df.empty:
            st.info(f"No leads ready for {stage_label}.")
            return
        n = st.slider("Batch size", 1, min(50, len(batch_df)), min(10, len(batch_df)), key=f"sz_{stage_label}")
        batch = batch_df.head(n)
        st.dataframe(batch[["id","name","city","country","email"]].rename(
            columns={"id":"ID","name":"Company","city":"City","country":"Country","email":"Email"}),
            use_container_width=True, hide_index=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button(f"🧪 Preview first 3", key=f"prev_{stage_label}"):
                tpl_map = {"initial":"pl_initial_outreach","fu1":"pl_follow_up_1","fu2":"pl_follow_up_2"}
                for _, row in batch.head(3).iterrows():
                    r = preview_email_for(row.to_dict(),
                        tpl_map.get(stage_label,"pl_initial_outreach"),
                        st.session_state.s_name, st.session_state.s_email,
                        st.session_state.s_phone, st.session_state.s_uni)
                    with st.expander(f"✉️ {row['name']} ({row['email']})"):
                        st.markdown(f"**Subject:** {r['subject']}")
                        st.text(r["body"])
        with c2:
            if st.button(f"🚀 Mark {n} as Sent", type="primary", key=f"send_{stage_label}"):
                prog = st.progress(0)
                for i, (_, row) in enumerate(batch.iterrows()):
                    run_sql(f"UPDATE leads SET email_stage=?, {sent_field}=?, "
                            f"status='CONTACTED', contacted_at=? WHERE id=?",
                            (email_stage_val, datetime.now().isoformat(),
                             datetime.now().isoformat(), int(row["id"])))
                    prog.progress((i+1)/len(batch))
                st.success(f"✅ Marked {len(batch)} as {stage_label}!")
                st.cache_data.clear(); st.rerun()

    with tab1:
        st.subheader(f"Send Initial Emails — {len(not_yet)} ready")
        send_batch(not_yet, "initial", "INITIAL_SENT", "initial_sent_at")

    with tab2:
        st.subheader(f"Follow-up 1 — {len(fu1_due)} non-responders")
        send_batch(fu1_due, "fu1", "FOLLOWUP1_SENT", "followup1_sent_at")

    with tab3:
        fu2_due2 = email_df[email_df["email_stage"]=="FOLLOWUP1_SENT"]
        st.subheader(f"Follow-up 2 — {len(fu2_due2)} non-responders")
        send_batch(fu2_due2, "fu2", "FOLLOWUP2_SENT", "followup2_sent_at")

    with tab4:
        st.subheader("Preview any email")
        tpl = st.selectbox("Template", ["pl_initial_outreach","pl_follow_up_1",
                           "pl_follow_up_2","pl_thank_you_reply","en_initial_outreach"])
        q = st.text_input("Company name", "")
        if q:
            for _, row in df_all[df_all["name"].str.contains(q,case=False,na=False)].head(5).iterrows():
                r = preview_email_for(row.to_dict(), tpl,
                    st.session_state.s_name, st.session_state.s_email,
                    st.session_state.s_phone, st.session_state.s_uni)
                with st.expander(f"✉️ {row['name']} · {row['city']}, {row['country']}"):
                    st.markdown(f"**Subject:** {r['subject']}")
                    st.text(r["body"])

# ══════════════════════════════════════════════════════════════════════════════
# REPLIES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📬 Replies":
    st.title("📬 Reply Tracker")

    replied_df = df_all[df_all["reply_received"]==1] if "reply_received" in df_all.columns else pd.DataFrame()

    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Total Replies",     len(replied_df))
    r2.metric("Interested ✅",     (df_all.get("reply_type","")=="INTERESTED").sum())
    r3.metric("Not Interested ❌", (df_all.get("reply_type","")=="NOT_INTERESTED").sum())
    r4.metric("Questions ❓",      (df_all.get("reply_type","")=="QUESTION").sum())

    st.markdown("---")
    st.subheader("Log a Reply")
    col_a, col_b, col_c = st.columns([1,1,2])
    with col_a:
        rid = st.number_input("Lead ID", min_value=1, step=1)
    with col_b:
        rtype = st.selectbox("Reply Type",
            ["INTERESTED","NOT_INTERESTED","QUESTION","UNSUBSCRIBE","OTHER"])
    with col_c:
        rnotes = st.text_area("Notes", height=80)
    if st.button("💾 Save Reply", type="primary"):
        run_sql("UPDATE leads SET reply_received=1, reply_type=?, reply_notes=?, "
                "reply_received_at=?, email_stage='REPLIED' WHERE id=?",
                (rtype, rnotes, datetime.now().isoformat(), int(rid)))
        st.success(f"Logged {rtype} for lead #{rid}")
        st.cache_data.clear(); st.rerun()

    if not replied_df.empty:
        st.markdown("---")
        st.subheader("All Replies")
        rcols = [c for c in ["id","name","city","country","email","reply_type","reply_notes","reply_received_at"]
                 if c in replied_df.columns]
        st.dataframe(replied_df[rcols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("⏳ Contacted — Awaiting Reply")
    waiting = df_all[
        df_all["email_stage"].isin(["INITIAL_SENT","FOLLOWUP1_SENT","FOLLOWUP2_SENT"]) &
        (df_all["reply_received"]==0)
    ]
    if not waiting.empty:
        wcols = [c for c in ["id","name","city","country","email","email_stage","initial_sent_at"]
                 if c in waiting.columns]
        st.dataframe(waiting[wcols], use_container_width=True, hide_index=True, height=400)
    else:
        st.info("No companies awaiting reply yet.")

# ══════════════════════════════════════════════════════════════════════════════
# SCAN EUROPE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌍 Scan Europe":
    st.title("🌍 Scan Europe")
    st.info("Scrapes businesses without websites from OpenStreetMap across European cities.")

    e_col1, e_col2 = st.columns([1, 1])
    with e_col1:
        engine = st.selectbox("Scraping Engine", [
            "🌐 Yelp Fusion API (Includes Direct Phone Numbers)",
            "🗺️ OpenStreetMap (No-Website Map Scan)"
        ])
    with e_col2:
        if "Yelp" in engine:
            target_filter = st.selectbox("Target Niche", [
                "🔥 High-Ticket AI Receptionist Targets (Dentists, Auto, Hair, Beauty, Plumbers)",
                "All Categories"
            ])
        else:
            target_filter = "All"

    col1, col2 = st.columns(2)
    with col1:
        scan_mode = st.radio("Scan mode", ["By country", "Single city", "All countries / cities"])
    with col2:
        scan_limit = st.slider("Max leads per city/niche", 10, 100, 30)

    if "Yelp" in engine:
        cmd_args = ["python",
                    os.path.join(os.path.dirname(DB_PATH), "scrape_yelp.py"),
                    "--limit", str(scan_limit)]
        if "High-Ticket" in target_filter:
            cmd_args.append("--high-ticket")

        if scan_mode == "By country":
            country_codes = {
                "🇬🇧 United Kingdom": "GB",
                "🇨🇭 Switzerland": "CH",
                "🇦🇹 Austria": "AT",
                "🇳🇱 Netherlands": "NL",
                "🇫🇷 France": "FR",
                "🇸🇪 Sweden": "SE",
                "🇳🇴 Norway": "NO",
                "🇩🇰 Denmark": "DK",
                "🇮🇪 Ireland": "IE",
                "🇧🇪 Belgium": "BE",
                "🇮🇹 Italy": "IT",
                "🇪🇸 Spain": "ES",
            }
            sel = st.selectbox("Country", list(country_codes.keys()))
            cmd_args += ["--country", country_codes[sel]]
        elif scan_mode == "Single city":
            city_in = st.text_input("City name (e.g. London, Zurich, Paris)", "London")
            cc_in = st.selectbox("Country for city", ["GB", "CH", "AT", "NL", "FR", "SE", "NO", "DK", "IE", "BE"])
            cmd_args += ["--city", city_in, "--country", cc_in]
        else:
            cmd_args += ["--country", "ALL"]
    else:
        cmd_args = ["python",
                    os.path.join(os.path.dirname(DB_PATH), "scan_europe.py"),
                    "--limit", str(scan_limit)]

        if scan_mode == "By country":
            country_codes = {
                "🇩🇪 Germany":"DE","🇦🇹 Austria":"AT","🇨🇭 Switzerland":"CH",
                "🇳🇱 Netherlands":"NL","🇧🇪 Belgium":"BE","🇸🇪 Sweden":"SE",
                "🇩🇰 Denmark":"DK","🇳🇴 Norway":"NO","🇬🇧 United Kingdom":"GB",
                "🇫🇷 France":"FR","🇮🇪 Ireland":"IE",
            }
            sel = st.selectbox("Country", list(country_codes.keys()))
            cmd_args += ["--country", country_codes[sel]]
        elif scan_mode == "Single city":
            from europe_config import EUROPEAN_CITIES
            city_opts = {f"{FLAGS.get(v['country_code'],'🌍')} {v['name']} ({v['country']})": k
                         for k, v in EUROPEAN_CITIES.items()}
            sel_city_label = st.selectbox("City", sorted(city_opts.keys()))
            cmd_args += ["--city", city_opts[sel_city_label]]
        else:
            cmd_args += ["--tier", "4"]

    st.markdown("---")

    # Country revenue table
    from europe_config import EUROPEAN_CITIES as _EC
    _rows = []
    for k, v in _EC.items():
        _rows.append({"Country": v["country"], "City": v["name"],
                      "Avg Revenue (€)": v["avg_revenue_eur"],
                      "Language": v["language"].upper(),
                      "Currency": v["currency"]})
    epdf = pd.DataFrame(_rows).sort_values(["Country","Avg Revenue (€)"], ascending=[True, False])
    epdf.insert(0, "Flag", epdf["Country"].map(FLAGS).fillna("🌍"))

    with st.expander("📊 All 50 European cities by revenue potential"):
        st.dataframe(epdf, use_container_width=True, hide_index=True)

    if st.button("🚀 Start Scan", type="primary"):
        st.warning("⏳ Scan running in background — check terminal or come back in a few minutes.")
        subprocess.Popen(cmd_args, cwd=os.path.dirname(DB_PATH))
        st.info(f"Started: `{' '.join(cmd_args)}`")


# ══════════════════════════════════════════════════════════════════════════════
# SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.title("⚙️ Settings")

    st.subheader("📧 Gmail SMTP Setup")
    env_path = os.path.join(os.path.dirname(DB_PATH), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            content = f.read()
        if "YOUR_APP_PASSWORD_HERE" in content:
            st.warning("⚠️ App Password not set yet — emails won't actually send!")
            st.markdown("""
**How to fix:**
1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Create app password → name it `LeadPulse`
3. Open `S:\\APPs\\lead-finder\\.env` and replace `YOUR_APP_PASSWORD_HERE`
""")
        else:
            st.success("✅ Gmail configured!")
    else:
        st.error("❌ No `.env` file found!")

    st.markdown("---")
    st.subheader("📊 Database Stats")
    stats = {
        "Total leads": f"{len(df_all):,}",
        "Countries":   df_all["country"].nunique(),
        "Cities":      df_all["city"].nunique(),
        "With email":  f"{df_all['has_email_addr'].sum():,}",
        "With phone":  f"{df_all['has_phone'].sum():,}",
        "No website":  f"{(df_all['has_website']==0).sum():,}",
        "DB size":     f"{os.path.getsize(DB_PATH)//1024:,} KB",
    }
    for k, v in stats.items():
        st.text(f"  {k}: {v}")

    st.markdown("---")
    st.subheader("🔄 Reset Outreach Data")
    st.warning("Resets all email stages, sent dates, and replies. Lead data stays.")
    if st.button("Reset Outreach Tracking", type="secondary"):
        run_sql("""UPDATE leads SET email_stage='NONE', initial_sent_at=NULL,
            followup1_sent_at=NULL, followup2_sent_at=NULL, reply_received=0,
            reply_type='', reply_notes='', reply_received_at=NULL,
            template_used='', contacted_at=NULL""")
        st.success("✅ Reset complete!")
        st.cache_data.clear(); st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("---")
st.sidebar.caption("LeadPulse EU v3.0")
