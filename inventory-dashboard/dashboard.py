import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
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
    page_title="Inventory Dashboard",
    layout="wide",
    page_icon="📦",
)

# ---------------------------------------------------------------------------
# CSS — dark mode safe (no hardcoded light colors)
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Remove top padding */
    .block-container { padding-top: 1.5rem !important; }

    /* Metric cards — use transparent bg + subtle border that works in both modes */
    [data-testid="metric-container"] {
        border: 1px solid rgba(128,128,128,0.2);
        border-radius: 14px;
        padding: 18px 22px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    [data-testid="metric-container"] label {
        font-size: 11px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        opacity: 0.6;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 26px !important;
        font-weight: 800 !important;
    }

    /* Filter section card */
    .filter-card {
        border: 1px solid rgba(128,128,128,0.2);
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 1rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }

    /* Buttons */
    .stButton > button, .stDownloadButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 0.4rem 1rem !important;
    }

    /* Dividers */
    hr { opacity: 0.2 !important; }

    /* Tighten multiselect tags */
    [data-testid="stMultiSelect"] span[data-baseweb="tag"] {
        border-radius: 6px !important;
        font-size: 12px !important;
    }
</style>
""", unsafe_allow_html=True)

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
# Plotly chart helper — transparent bg, works in light + dark
# ---------------------------------------------------------------------------

CHANNEL_COLORS = ["#f59e0b", "#6366f1", "#10b981", "#4f6ef7", "#f43f5e", "#06b6d4"]

def apply_transparent_layout(fig, title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, weight="bold")),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=44, b=8, l=4, r=4),
        xaxis=dict(showgrid=False, showline=False),
        yaxis=dict(gridcolor="rgba(128,128,128,0.15)", showline=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=12)),
        font=dict(size=12),
    )
    return fig

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

real_df   = load_data()
USING_MOCK = real_df.empty
df         = get_mock_df() if USING_MOCK else real_df

# SKU options always come from real data (DB); mock SKUs are never shown in filter
real_skus = sorted(real_df["sku"].dropna().unique().tolist()) if not USING_MOCK else []

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

h_left, h_right = st.columns([4, 2])
with h_left:
    st.title("📦 Channel Inventory Dashboard")
    last_scrape = (
        df["scraped_at"].max().strftime("%b %d, %Y %H:%M UTC")
        if not USING_MOCK else "Showing sample data — no scrape run yet"
    )
    st.caption(f"Last updated: **{last_scrape}**")

with h_right:
    st.write("")  # vertical spacing
    b1, b2 = st.columns(2)
    with b1:
        if SCRAPING_AVAILABLE:
            if st.button("🔄 Scrape", use_container_width=True):
                with st.spinner("Scraping… browser windows will open."):
                    run_scrape()
                st.cache_data.clear()
                st.rerun()
        else:
            st.button("🔄 Scrape", disabled=True, use_container_width=True,
                      help="Run `python scraper.py` locally — Playwright unavailable here.")
    with b2:
        if not USING_MOCK:
            fp = export_excel()
            with open(fp, "rb") as f:
                st.download_button("📥 Export", data=f, file_name=config.EXCEL_FILE,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True)
        else:
            st.button("📥 Export", disabled=True, use_container_width=True,
                      help="Available after first real scrape.")

if USING_MOCK:
    st.info("👋 **Preview mode — sample data.** Fill in your API credentials and click Scrape to load real inventory.", icon="ℹ️")

st.divider()

# ---------------------------------------------------------------------------
# Filters — horizontal dropdowns at the top (no tag pills shown)
# ---------------------------------------------------------------------------

all_sources  = sorted(df["source"].dropna().unique().tolist())
# Always use real QuickBox SKUs; fall back to mock SKUs only if no real data
sku_options  = real_skus if real_skus else sorted(df["sku"].dropna().unique().tolist())

min_date = df["date"].min() if "date" in df.columns else date.today()
max_date = df["date"].max() if "date" in df.columns else date.today()

with st.container():
    st.markdown('<div class="filter-card">', unsafe_allow_html=True)
    fc1, fc2, fc3, fc4 = st.columns([1.5, 2, 1, 1])
    with fc1:
        sel_channel = st.selectbox("🏪 Channel", ["All channels"] + all_sources)
    with fc2:
        sel_sku = st.selectbox("🔖 SKU", ["All SKUs"] + sku_options)
    with fc3:
        start_date = st.date_input("📅 From", value=min_date, min_value=min_date, max_value=max_date)
    with fc4:
        end_date = st.date_input("📅 To", value=max_date, min_value=min_date, max_value=max_date)
    st.markdown('</div>', unsafe_allow_html=True)

# Resolve selections
selected_sources = all_sources         if sel_channel == "All channels" else [sel_channel]
filter_skus      = sku_options         if sel_sku     == "All SKUs"     else [sel_sku]

# Apply filters — always match SKUs against the real QuickBox SKU list
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
k1.metric("Total Units on Hand",   f"{int(latest_snapshot['quantity'].sum()):,}")
k2.metric("SKUs Tracked",          f"{len(sku_options):,}")
k3.metric("Channels",              df["source"].nunique())
k4.metric("Snapshots",             df["scraped_at"].nunique())

st.divider()

# ---------------------------------------------------------------------------
# Charts row 1 — By Channel bar + Donut
# ---------------------------------------------------------------------------

latest_filtered = filtered[filtered["scraped_at"] == filtered["scraped_at"].max()]
channel_totals  = latest_filtered.groupby("source", as_index=False)["quantity"].sum()

c1, c2 = st.columns(2)

with c1:
    fig = px.bar(
        channel_totals, x="source", y="quantity", color="source",
        color_discrete_sequence=CHANNEL_COLORS, text_auto=True,
        labels={"source": "Channel", "quantity": "Units"},
    )
    fig.update_traces(marker_line_width=0, textposition="outside", textfont_size=12)
    fig.update_layout(showlegend=False)
    apply_transparent_layout(fig, "Current stock by channel")
    st.plotly_chart(fig, use_container_width=True)

with c2:
    fig = px.pie(
        channel_totals, names="source", values="quantity",
        hole=0.48, color_discrete_sequence=CHANNEL_COLORS,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=12)
    apply_transparent_layout(fig, "Stock split by channel")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 2 — By SKU & channel (horizontal bar for readability with many SKUs)
# ---------------------------------------------------------------------------

sku_channel = (
    latest_filtered
    .groupby(["sku", "source"], as_index=False)["quantity"].sum()
    .sort_values("quantity", ascending=True)
)

fig = px.bar(
    sku_channel, x="quantity", y="sku", color="source",
    barmode="group", orientation="h",
    color_discrete_sequence=CHANNEL_COLORS,
    labels={"sku": "SKU", "quantity": "Units", "source": "Channel"},
    height=max(400, len(sku_channel["sku"].unique()) * 28),
)
fig.update_traces(marker_line_width=0)
apply_transparent_layout(fig, "Current stock by SKU & channel")
fig.update_layout(yaxis=dict(showgrid=False), xaxis=dict(gridcolor="rgba(128,128,128,0.15)"))
st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 3 — Time series (only when multiple snapshots exist)
# ---------------------------------------------------------------------------

if df["scraped_at"].nunique() > 1:
    ts_df = filtered.groupby(["scraped_at", "source"], as_index=False)["quantity"].sum()
    fig = px.line(
        ts_df, x="scraped_at", y="quantity", color="source",
        color_discrete_sequence=CHANNEL_COLORS, markers=True,
        labels={"scraped_at": "Date", "quantity": "Total units", "source": "Channel"},
    )
    fig.update_traces(line_width=2.5, marker_size=6)
    apply_transparent_layout(fig, "Inventory over time by channel")
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Raw data table
# ---------------------------------------------------------------------------

st.subheader(f"Inventory records  ·  {len(filtered):,} rows")
display_cols = ["scraped_at", "source", "sku", "product_name", "quantity", "location"]
st.dataframe(
    filtered[display_cols].sort_values("scraped_at", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "scraped_at":   st.column_config.DatetimeColumn("Scraped at",  format="MMM D YYYY, HH:mm"),
        "source":       st.column_config.TextColumn("Channel",         width="medium"),
        "sku":          st.column_config.TextColumn("SKU",             width="medium"),
        "product_name": st.column_config.TextColumn("Product",         width="large"),
        "quantity":     st.column_config.NumberColumn("Qty on Hand",   format="%d"),
        "location":     st.column_config.TextColumn("Location",        width="medium"),
    },
)
