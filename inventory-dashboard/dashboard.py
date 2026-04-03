import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import date

import config
from database import export_excel
from scraper import run_scrape

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Inventory Dashboard",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data loader (cached, refreshes every 60 s)
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

st.title(":package: Channel Inventory Dashboard")

df = load_data()

last_scrape = (
    df["scraped_at"].max().strftime("%Y-%m-%d %H:%M UTC")
    if not df.empty and "scraped_at" in df.columns
    else "Never"
)
st.caption(f"Last scrape: **{last_scrape}**")

# ---------------------------------------------------------------------------
# Action buttons
# ---------------------------------------------------------------------------

col_btn1, col_btn2, col_spacer = st.columns([1, 1, 6])

with col_btn1:
    if st.button(":arrows_counterclockwise: Scrape now"):
        with st.spinner("Running scrapers… browser windows will open."):
            run_scrape()
        st.cache_data.clear()
        st.rerun()

with col_btn2:
    if st.button(":inbox_tray: Export Excel"):
        filepath = export_excel()
        with open(filepath, "rb") as f:
            st.download_button(
                label="Download inventory.xlsx",
                data=f,
                file_name=config.EXCEL_FILE,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

st.divider()

# ---------------------------------------------------------------------------
# Guard — no data yet
# ---------------------------------------------------------------------------

if df.empty:
    st.warning(
        "No inventory data found. Click **:arrows_counterclockwise: Scrape now** above "
        "to pull data from all three platforms for the first time."
    )
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.header("Filters")

all_sources = sorted(df["source"].dropna().unique().tolist())
selected_sources = st.sidebar.multiselect("Source", all_sources, default=all_sources)

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

# Unpack date range safely (user might pick only one date)
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
# Summary metric cards
# ---------------------------------------------------------------------------

latest_ts = df["scraped_at"].max()
latest_snapshot = df[df["scraped_at"] == latest_ts]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total SKUs tracked",       df["sku"].nunique())
m2.metric("Sources connected",        df["source"].nunique())
m3.metric("Snapshots taken",          df["scraped_at"].nunique())
m4.metric("Units in latest snapshot", int(latest_snapshot["quantity"].sum()))

st.divider()

# ---------------------------------------------------------------------------
# Chart 1 — Time series by source
# ---------------------------------------------------------------------------

ts_df = (
    filtered.groupby(["scraped_at", "source"], as_index=False)["quantity"]
    .sum()
)

fig1 = px.line(
    ts_df,
    x="scraped_at",
    y="quantity",
    color="source",
    title="Inventory over time by source",
    labels={"scraped_at": "Scraped at", "quantity": "Total units"},
)
st.plotly_chart(fig1, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 2 — Current stock by SKU (latest snapshot only)
# ---------------------------------------------------------------------------

latest_filtered = filtered[filtered["scraped_at"] == filtered["scraped_at"].max()]

fig2 = px.bar(
    latest_filtered,
    x="sku",
    y="quantity",
    color="source",
    barmode="group",
    title="Current stock by SKU",
    labels={"sku": "SKU", "quantity": "Units"},
)
st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------------------------
# Chart 3 — Stock distribution by channel (donut)
# ---------------------------------------------------------------------------

dist_df = latest_filtered.groupby("source", as_index=False)["quantity"].sum()

fig3 = px.pie(
    dist_df,
    names="source",
    values="quantity",
    hole=0.4,
    title="Stock distribution by channel",
)
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Raw data table
# ---------------------------------------------------------------------------

st.subheader("Raw data")
display_cols = ["scraped_at", "source", "sku", "product_name", "quantity", "location"]
st.dataframe(
    filtered[display_cols].sort_values("scraped_at", ascending=False),
    use_container_width=True,
)
