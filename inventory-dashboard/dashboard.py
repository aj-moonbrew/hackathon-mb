import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

import config
from database import export_excel
from mock_data import get_mock_df

try:
    from scraper import run_scrape
    SCRAPING_AVAILABLE = True
except Exception:
    SCRAPING_AVAILABLE = False

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="MoonBrew · Inventory",
    layout="wide",
    page_icon="🌙",
)

# ---------------------------------------------------------------------------
# MoonBrew brand tokens
# ---------------------------------------------------------------------------

BG           = "#141414"
BG2          = "#1c1c1c"
BG3          = "#242424"
BORDER       = "#2e2e2e"
PURPLE       = "#3D35A8"
PURPLE_LIGHT = "#5548C8"
TEXT         = "#e2e2e2"
TEXT_MUTED   = "#6b7280"
WHITE        = "#ffffff"

# Channel colors
CHANNEL_COLORS = {
    "LogicPod / QuickBox": "#3D35A8",
    "Amazon FBA":           "#f59e0b",
    "TikTok FBT":           "#e63950",
}
COLOR_SEQ = list(CHANNEL_COLORS.values())

# ---------------------------------------------------------------------------
# MoonBrew CSS
# ---------------------------------------------------------------------------

st.markdown(f"""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  /* ── Base ── */
  html, body, [class*="css"], .stApp {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: {TEXT} !important;
  }}
  .block-container {{ padding-top: 1.8rem !important; max-width: 1400px; }}

  /* ── Logo / title bar ── */
  .mb-header {{
    display: flex; align-items: center; gap: 12px; margin-bottom: 2px;
  }}
  .mb-logo {{
    width: 36px; height: 36px; border-radius: 10px;
    background: {PURPLE};
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; line-height: 1;
  }}
  .mb-title {{
    font-size: 22px; font-weight: 800; color: {WHITE}; letter-spacing: -0.3px;
  }}
  .mb-subtitle {{
    font-size: 13px; color: {TEXT_MUTED}; margin-top: 1px;
  }}

  /* ── Cards (metrics) ── */
  [data-testid="metric-container"] {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 18px 22px !important;
  }}
  [data-testid="metric-container"] label {{
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase; letter-spacing: 0.07em;
    color: {TEXT_MUTED} !important;
  }}
  [data-testid="metric-container"] [data-testid="metric-value"] {{
    font-size: 28px !important; font-weight: 800 !important;
    color: {WHITE} !important;
  }}

  /* ── Filter strip ── */
  .filter-strip {{
    background: {BG2};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 14px 20px 10px 20px;
    margin-bottom: 1.4rem;
  }}

  /* ── Chart wrapper ── */
  [data-testid="stPlotlyChart"] {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 14px !important;
    padding: 8px !important;
  }}

  /* ── Buttons ── */
  .stButton > button {{
    background: {PURPLE} !important;
    color: {WHITE} !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 0.45rem 1.1rem !important;
    transition: background .2s;
  }}
  .stButton > button:hover {{ background: {PURPLE_LIGHT} !important; }}
  .stButton > button:disabled {{
    background: {BG3} !important;
    color: {TEXT_MUTED} !important;
    border: 1px solid {BORDER} !important;
  }}
  .stDownloadButton > button {{
    background: transparent !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    font-weight: 600 !important; font-size: 13px !important;
  }}
  .stDownloadButton > button:hover {{ border-color: {PURPLE} !important; color: {WHITE} !important; }}

  /* ── Sidebar hidden ── */
  [data-testid="stSidebar"] {{ display: none; }}

  /* ── Selectbox ── */
  [data-testid="stSelectbox"] > div > div {{
    background: {BG3} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
  }}

  /* ── Date inputs ── */
  [data-testid="stDateInput"] input {{
    background: {BG3} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
  }}

  /* ── Divider ── */
  hr {{ border-color: {BORDER} !important; opacity: 1 !important; }}

  /* ── Dataframe ── */
  [data-testid="stDataFrame"] {{ border-radius: 14px; overflow: hidden; }}
  [data-testid="stDataFrame"] th {{
    background: {BG3} !important; color: {TEXT_MUTED} !important;
    font-size: 11px !important; font-weight: 700 !important; text-transform: uppercase;
    letter-spacing: 0.06em !important;
  }}

  /* ── Info / warning banners ── */
  [data-testid="stAlert"] {{
    background: {BG2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 12px !important;
    color: {TEXT} !important;
  }}

  /* ── Section labels ── */
  .section-label {{
    font-size: 11px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: {TEXT_MUTED}; margin-bottom: 10px;
  }}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Plotly dark chart helper
# ---------------------------------------------------------------------------

def mb_chart(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, weight="bold", color=WHITE), x=0, pad=dict(l=6)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=48, b=8, l=4, r=4),
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        xaxis=dict(showgrid=False, showline=False, tickcolor=TEXT_MUTED, color=TEXT_MUTED),
        yaxis=dict(gridcolor=BORDER, showline=False, tickcolor=TEXT_MUTED, color=TEXT_MUTED),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
            font=dict(size=12, color=TEXT), bgcolor="rgba(0,0,0,0)", borderwidth=0,
        ),
        hoverlabel=dict(bgcolor=BG3, font_color=WHITE, bordercolor=BORDER),
    )
    return fig

# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    try:
        conn = sqlite3.connect(config.DB_FILE)
        df = pd.read_sql_query("SELECT * FROM snapshots ORDER BY scraped_at DESC", conn)
        conn.close()
    except Exception:
        df = pd.DataFrame(columns=["id","source","sku","product_name","quantity","location","scraped_at"])
    if not df.empty:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True, errors="coerce")
        df["date"] = df["scraped_at"].dt.date
    return df

# ---------------------------------------------------------------------------
# Load + fallback to mock
# ---------------------------------------------------------------------------

real_df    = load_data()
USING_MOCK = real_df.empty
df         = get_mock_df() if USING_MOCK else real_df
real_skus  = sorted(real_df["sku"].dropna().unique().tolist()) if not USING_MOCK else []
sku_options = real_skus if real_skus else sorted(df["sku"].dropna().unique().tolist())

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

h_left, h_right = st.columns([4, 2])

with h_left:
    last_scrape = (
        df["scraped_at"].max().strftime("%b %d, %Y · %H:%M UTC")
        if not USING_MOCK else "No scrape yet — showing QuickBox snapshot"
    )
    st.markdown(f"""
    <div class="mb-header">
      <div class="mb-logo">🌙</div>
      <div>
        <div class="mb-title">MoonBrew Inventory</div>
        <div class="mb-subtitle">Last updated: {last_scrape}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

with h_right:
    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        if SCRAPING_AVAILABLE:
            if st.button("🔄 Scrape now", use_container_width=True):
                with st.spinner("Opening browsers…"):
                    run_scrape()
                st.cache_data.clear()
                st.rerun()
        else:
            st.button("🔄 Scrape now", disabled=True, use_container_width=True,
                      help="Run `python scraper.py` locally.")
    with b2:
        if not USING_MOCK:
            fp = export_excel()
            with open(fp, "rb") as f:
                st.download_button("📥 Export", data=f, file_name=config.EXCEL_FILE,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
        else:
            st.button("📥 Export", disabled=True, use_container_width=True,
                      help="Available after first scrape.")

if USING_MOCK:
    st.info("👋 Showing your QuickBox snapshot. Connect Amazon & TikTok APIs and click **Scrape now** to populate all channels.", icon="🌙")

st.divider()

# ---------------------------------------------------------------------------
# Filters — horizontal strip
# ---------------------------------------------------------------------------

all_sources = sorted(df["source"].dropna().unique().tolist())
min_date    = df["date"].min() if "date" in df.columns else date.today()
max_date    = df["date"].max() if "date" in df.columns else date.today()

st.markdown('<div class="filter-strip">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4 = st.columns([1.5, 2, 1, 1])
with fc1:
    sel_channel = st.selectbox("🏪 Channel", ["All channels"] + all_sources, label_visibility="visible")
with fc2:
    sel_sku = st.selectbox("🔖 SKU", ["All SKUs"] + sku_options, label_visibility="visible")
with fc3:
    start_date = st.date_input("📅 From", value=min_date, min_value=min_date, max_value=max_date)
with fc4:
    end_date = st.date_input("📅 To", value=max_date, min_value=min_date, max_value=max_date)
st.markdown('</div>', unsafe_allow_html=True)

selected_sources = all_sources  if sel_channel == "All channels" else [sel_channel]
filter_skus      = sku_options  if sel_sku     == "All SKUs"     else [sel_sku]

mask = (
    df["source"].isin(selected_sources)
    & df["sku"].isin(filter_skus)
    & (df["date"] >= start_date)
    & (df["date"] <= end_date)
)
filtered = df[mask].copy()

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

latest_ts       = df["scraped_at"].max()
latest_snapshot = df[df["scraped_at"] == latest_ts]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Units on Hand",  f"{int(latest_snapshot['quantity'].sum()):,}")
k2.metric("SKUs Tracked",         f"{len(sku_options):,}")
k3.metric("Channels",             df["source"].nunique())
k4.metric("Snapshots Taken",      df["scraped_at"].nunique())

st.divider()

# ---------------------------------------------------------------------------
# Charts row 1 — By Channel + Donut
# ---------------------------------------------------------------------------

latest_filtered = filtered[filtered["scraped_at"] == filtered["scraped_at"].max()]
channel_totals  = latest_filtered.groupby("source", as_index=False)["quantity"].sum()

c1, c2 = st.columns(2)

with c1:
    color_map = {s: CHANNEL_COLORS.get(s, PURPLE) for s in channel_totals["source"]}
    fig = px.bar(
        channel_totals, x="source", y="quantity", color="source",
        color_discrete_map=color_map, text_auto=True,
        labels={"source": "", "quantity": "Units"},
    )
    fig.update_traces(marker_line_width=0, textposition="outside",
                      textfont=dict(color=TEXT, size=12))
    fig.update_layout(showlegend=False)
    mb_chart(fig, "Units on hand by channel")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.pie(
        channel_totals, names="source", values="quantity", hole=0.52,
        color="source", color_discrete_map=color_map,
    )
    fig.update_traces(
        textposition="inside", textinfo="percent+label",
        textfont=dict(size=12, color=WHITE),
        marker=dict(line=dict(color=BG, width=2)),
    )
    mb_chart(fig, "Channel distribution")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 2 — By SKU (horizontal bar)
# ---------------------------------------------------------------------------

sku_channel = (
    latest_filtered
    .groupby(["sku", "source"], as_index=False)["quantity"].sum()
    .sort_values("quantity", ascending=True)
)

fig = px.bar(
    sku_channel, x="quantity", y="sku", color="source",
    barmode="group", orientation="h",
    color_discrete_map=color_map,
    labels={"sku": "", "quantity": "Units on Hand", "source": "Channel"},
    height=max(420, len(sku_channel["sku"].unique()) * 26),
)
fig.update_traces(marker_line_width=0)
mb_chart(fig, "Stock by SKU & channel")
fig.update_layout(
    yaxis=dict(showgrid=False, tickfont=dict(size=11)),
    xaxis=dict(gridcolor=BORDER),
)
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 3 — Time series
# ---------------------------------------------------------------------------

if df["scraped_at"].nunique() > 1:
    ts_df = filtered.groupby(["scraped_at", "source"], as_index=False)["quantity"].sum()
    fig = px.line(
        ts_df, x="scraped_at", y="quantity", color="source",
        color_discrete_map=color_map, markers=True,
        labels={"scraped_at": "", "quantity": "Total Units", "source": "Channel"},
    )
    fig.update_traces(line_width=2.5, marker_size=6)
    mb_chart(fig, "Inventory over time")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Raw data table
# ---------------------------------------------------------------------------

st.markdown(f'<div class="section-label">Inventory records &nbsp;·&nbsp; {len(filtered):,} rows</div>', unsafe_allow_html=True)
display_cols = ["scraped_at", "source", "sku", "product_name", "quantity", "location"]
st.dataframe(
    filtered[display_cols].sort_values("scraped_at", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "scraped_at":   st.column_config.DatetimeColumn("Scraped at",   format="MMM D YYYY, HH:mm"),
        "source":       st.column_config.TextColumn("Channel",          width="medium"),
        "sku":          st.column_config.TextColumn("SKU",              width="medium"),
        "product_name": st.column_config.TextColumn("Product",          width="large"),
        "quantity":     st.column_config.NumberColumn("Qty on Hand",    format="%d"),
        "location":     st.column_config.TextColumn("Location",         width="medium"),
    },
)
