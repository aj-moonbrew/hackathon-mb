# Channel Inventory Dashboard

A scraping-based inventory PoC that pulls stock data from LogicPod/QuickBox, Amazon Seller Central, and TikTok Seller Central, saves every run as a timestamped snapshot, and displays a live dashboard with charts and export.

---

## One-time setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install the Playwright browser
playwright install chromium

# 3. Fill in your credentials
#    Open config.py and replace every YOUR_* placeholder with real values
```

---

## How to run

```bash
# Option A — scrape first, then open dashboard
python scraper.py
streamlit run dashboard.py

# Option B — open dashboard first and click "Scrape now" inside it
streamlit run dashboard.py
```

The dashboard is also reachable at `http://localhost:8501` after starting Streamlit.

---

## Troubleshooting — scraper returns 0 rows

Each platform's HTML structure can change without notice. If a scraper reports `0 rows`:

1. Run `python scraper.py` — the browser will open in **visible mode** (headless=False).
2. Once the inventory/product page loads, **right-click** any row in the table → **Inspect**.
3. In DevTools, identify the repeating element — it is usually a `<tr>` inside `<tbody>`, but may also be a `<div>` with a class like `product-row` or `inventory-row`.
4. Copy the CSS selector.
5. Open `scraper.py` and find the relevant scraper function (`scrape_logicpod`, `scrape_amazon`, or `scrape_tiktok`).
6. Update the `query_selector_all(...)` call to use your new selector.
7. Also check the cell-index assumptions (`cells[0]`, `cells[1]`, etc.) — adjust to match the column order you see.

---

## How the time series works

Every time a scrape runs, all collected rows are inserted into the `snapshots` SQLite table with the current UTC timestamp in the `scraped_at` column. **Existing rows are never overwritten or deleted.** This means each run appends a new batch of rows, building up a full history automatically. The dashboard's time-series chart reads all rows grouped by `(scraped_at, source)` so you can see how inventory levels change across every scrape over time.
