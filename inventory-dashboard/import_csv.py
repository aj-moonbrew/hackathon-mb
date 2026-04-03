"""
Import a QuickBox inventory CSV export as a snapshot into the local DB.
No external dependencies — uses only Python stdlib (sqlite3, csv).
Usage:  python import_csv.py path/to/export.csv
"""
import sys
import csv
import re
import sqlite3
from datetime import datetime, timezone

DB_FILE  = "inventory.db"
CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "/Users/arjunshroff/Downloads/export.csv"


def safe_int(text) -> int:
    if not text:
        return 0
    cleaned = str(text).replace(",", "").strip()
    match = re.search(r"\d+", cleaned)
    return int(match.group()) if match else 0


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            source       TEXT,
            sku          TEXT,
            product_name TEXT,
            quantity     INTEGER,
            location     TEXT,
            scraped_at   TEXT
        )
    """)
    conn.commit()


def import_csv(path: str):
    conn = sqlite3.connect(DB_FILE)
    init_db(conn)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku  = (row.get("SKU") or "").strip()
            name = (row.get("Description") or "").strip()
            qty  = safe_int(row.get("Total Units On Hand") or "0")
            if not sku:
                continue
            rows.append(("LogicPod / QuickBox", sku, name, qty, "QuickBox Warehouse", now))

    if not rows:
        print("No records found — check the CSV column names.")
        conn.close()
        return

    conn.executemany(
        "INSERT INTO snapshots (source, sku, product_name, quantity, location, scraped_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()

    print(f"[DB] Saved {len(rows)} records at {now}")
    print(f"\nImported {len(rows)} SKUs from '{path}' as a QuickBox snapshot.")
    print("Refresh your Streamlit dashboard to see the live data.")


if __name__ == "__main__":
    import_csv(CSV_PATH)
