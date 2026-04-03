import sqlite3
import pandas as pd
from datetime import datetime
import config


def init_db():
    """Create the snapshots table if it doesn't exist."""
    conn = sqlite3.connect(config.DB_FILE)
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
    conn.close()


def save_records(records: list[dict]):
    """Stamp records with current time and insert all in one transaction."""
    if not records:
        print("save_records: no records to save.")
        return

    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    rows = [
        (
            r.get("source", ""),
            r.get("sku", ""),
            r.get("product_name", ""),
            r.get("quantity", 0),
            r.get("location", ""),
            now,
        )
        for r in records
    ]

    conn = sqlite3.connect(config.DB_FILE)
    conn.executemany(
        "INSERT INTO snapshots (source, sku, product_name, quantity, location, scraped_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    print(f"[DB] Saved {len(rows)} records at {now}")


def export_excel() -> str:
    """Read all snapshots (newest first) and write to Excel. Returns filename."""
    conn = sqlite3.connect(config.DB_FILE)
    df = pd.read_sql_query(
        "SELECT * FROM snapshots ORDER BY scraped_at DESC", conn
    )
    conn.close()

    df.to_excel(config.EXCEL_FILE, index=False, engine="openpyxl")
    print(f"[Excel] Exported {len(df)} rows to {config.EXCEL_FILE}")
    return config.EXCEL_FILE
