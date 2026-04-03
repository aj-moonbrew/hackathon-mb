import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import date

import config
from database import export_excel
from mock_data import get_mock_df

# Scraping requires Playwright + Chromium — available locally but not on Streamlit Cloud.
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
# Custom CSS — clean card look
# ---------------------------------------------------------------------------

st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #f8fafc; }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    [data-testid="metric-container"] label {
        font-size: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748b !important;
    }
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] { background: white; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { color: #1e293b; }

    /* Buttons */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }

    /* Chart wrappers */
    [data-testid="stPlotlyChart"] {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }

    /* Divider */
    hr { border-color: #e2e8f0 !important; }

    /* Hide Streamlit default header padding */
    .block-container { padding-top: 2rem !important; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------

@st.cache_data(ttl=60)
def load_data() -> pd.DataFrame:
    try:
        conn = sqlite3.connect(config.DB_FILE)
        df = pd.read_sql_query(
            "SELECT * FROM snapshots ORDER BY scraped_at DESC", conn
        )
        conn.close()
    except Exception:
        df = pd.DataFrame(columns=[
            "id", "source", "sku", "product_name", "quantity", "location", "scraped_at"
        ])
    if not df.empty:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True, errors="coerce")
        df["date"] = df["scraped_at"].dt.date
    return df

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

col_title, col_actions = st.columns([3, 1])

with col_title:
    st.title("📦 Channel Inventory Dashboard")

df = load_data()
USING_MOCK = df.empty

if USING_MOCK:
    df = get_mock_df()

last_scrape = (
    df["scraped_at"].max().strftime("%Y-%m-%d %H:%M UTC")
    if not USING_MOCK and "scraped_at" in df.columns
    else "Never — showing sample data"
)
st.caption(f"Last scrape: **{last_scrape}**")

# ---------------------------------------------------------------------------
# Action buttons
# ---------------------------------------------------------------------------

col_btn1, col_btn2, col_spacer = st.columns([1.2, 1.2, 5])

with col_btn1:
    if SCRAPING_AVAILABLE:
        if st.button("🔄 Scrape now", use_container_width=True):
            with st.spinner("Running scrapers… browser windows will open."):
                run_scrape()
            st.cache_data.clear()
            st.rerun()
    else:
        st.button("🔄 Scrape now", disabled=True, use_container_width=True, help="Run `python scraper.py` locally — Playwright is not available in this environment.")

with col_btn2:
    if not USING_MOCK:
        filepath = export_excel()
        with open(filepath, "rb") as f:
            st.download_button(
                label="📥 Export Excel",
                data=f,
                file_name=config.EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
    else:
        st.button("📥 Export Excel", disabled=True, use_container_width=True,
                  help="Export is available once real data has been scraped.")

if USING_MOCK:
    st.info(
        "👋 **This is a preview using sample data.** "
        "Once your API credentials are set up, click **🔄 Scrape now** (or run `python scraper.py`) "
        "to load your real inventory.",
        icon="ℹ️",
    )
elif not SCRAPING_AVAILABLE:
    st.info("ℹ️ Scraping is disabled in this environment. Run `python scraper.py` locally to refresh data.", icon="ℹ️")

st.divider()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.markdown("## Filters")

all_sources = sorted(df["source"].dropna().unique().tolist())
selected_sources = st.sidebar.multiselect("Channel", all_sources, default=all_sources)

all_skus = sorted(df["sku"].dropna().unique().tolist())
selected_skus = st.sidebar.multiselect("SKU", all_skus, default=all_skus)

min_date = df["date"].min() if "date" in df.columns else date.today()
max_date = df["date"].max() if "date" in df.columns else date.today()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0] if date_range else min_date

# Apply filters
mask = (
    df["source"].isin(selected_sources)
    & df["sku"].isin(selected_skus)
    & (df["date"] >= start_date)
    & (df["date"] <= end_date)
)
filtered = df[mask].copy()

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

latest_ts       = df["scraped_at"].max()
latest_snapshot = df[df["scraped_at"] == latest_ts]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Units (latest)",   f"{int(latest_snapshot['quantity'].sum()):,}")
m2.metric("SKUs Tracked",           df["sku"].nunique())
m3.metric("Channels Connected",     df["source"].nunique())
m4.metric("Snapshots Taken",        df["scraped_at"].nunique())

st.divider()

# ---------------------------------------------------------------------------
# Chart row 1 — By Channel + Donut
# ---------------------------------------------------------------------------

ch_col, pie_col = st.columns(2)

with ch_col:
    channel_df = (
        filtered[filtered["scraped_at"] == filtered["scraped_at"].max()]
        .groupby("source", as_index=False)["quantity"].sum()
    )
    fig_ch = px.bar(
        channel_df,
        x="source", y="quantity", color="source",
        title="Current stock by channel",
        labels={"source": "Channel", "quantity": "Units"},
        color_discrete_sequence=["#f59e0b", "#6366f1", "#10b981", "#4f6ef7"],
        text_auto=True,
    )
    fig_ch.update_layout(
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
        title_font_size=14, margin=dict(t=40, b=10),
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f1f5f9"),
    )
    fig_ch.update_traces(marker_line_width=0, textposition="outside")
    st.plotly_chart(fig_ch, use_container_width=True)

with pie_col:
    fig_pie = px.pie(
        channel_df, names="source", values="quantity",
        hole=0.45,
        title="Stock split by channel",
        color_discrete_sequence=["#f59e0b", "#6366f1", "#10b981", "#4f6ef7"],
    )
    fig_pie.update_layout(
        paper_bgcolor="white", title_font_size=14, margin=dict(t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")
    st.plotly_chart(fig_pie, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 2 — By SKU grouped by channel
# ---------------------------------------------------------------------------

latest_filtered = filtered[filtered["scraped_at"] == filtered["scraped_at"].max()]

fig_sku = px.bar(
    latest_filtered,
    x="sku", y="quantity", color="source",
    barmode="group",
    title="Current stock by SKU & channel",
    labels={"sku": "SKU", "quantity": "Units", "source": "Channel"},
    color_discrete_sequence=["#f59e0b", "#6366f1", "#10b981", "#4f6ef7"],
    text_auto=True,
)
fig_sku.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    title_font_size=14, margin=dict(t=40, b=10),
    xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f1f5f9"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig_sku.update_traces(marker_line_width=0)
st.plotly_chart(fig_sku, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 3 — Time series (only if more than one snapshot)
# ---------------------------------------------------------------------------

if df["scraped_at"].nunique() > 1:
    ts_df = (
        filtered.groupby(["scraped_at", "source"], as_index=False)["quantity"].sum()
    )
    fig_ts = px.line(
        ts_df,
        x="scraped_at", y="quantity", color="source",
        title="Inventory over time by channel",
        labels={"scraped_at": "Date", "quantity": "Total units", "source": "Channel"},
        color_discrete_sequence=["#f59e0b", "#6366f1", "#10b981", "#4f6ef7"],
        markers=True,
    )
    fig_ts.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        title_font_size=14, margin=dict(t=40, b=10),
        xaxis=dict(showgrid=False), yaxis=dict(gridcolor="#f1f5f9"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    st.plotly_chart(fig_ts, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Raw data table
# ---------------------------------------------------------------------------

st.subheader(f"All records ({len(filtered):,})")
display_cols = ["scraped_at", "source", "sku", "product_name", "quantity", "location"]
st.dataframe(
    filtered[display_cols].sort_values("scraped_at", ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "scraped_at":   st.column_config.DatetimeColumn("Scraped at",    format="MMM D, YYYY HH:mm"),
        "source":       st.column_config.TextColumn("Channel"),
        "sku":          st.column_config.TextColumn("SKU"),
        "product_name": st.column_config.TextColumn("Product"),
        "quantity":     st.column_config.NumberColumn("Quantity",        format="%d"),
        "location":     st.column_config.TextColumn("Location"),
    },
)
