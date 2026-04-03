"""
FastAPI backend — serves inventory data from SQLite to the React frontend.
Run with:  uvicorn api:app --reload --port 8000
"""
import sqlite3
import os
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import config
from database import init_db, export_excel
from scraper import run_scrape

app = FastAPI(title="Inventory API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/inventory")
def get_inventory():
    """Return all snapshot records as JSON."""
    init_db()
    conn = sqlite3.connect(config.DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM snapshots ORDER BY scraped_at DESC").fetchall()
    conn.close()
    return {"records": [dict(r) for r in rows]}


@app.post("/api/scrape")
def trigger_scrape():
    """Run all scrapers and return new records."""
    records = run_scrape()
    return {"status": "ok", "count": len(records)}


@app.get("/api/export")
def get_export():
    """Export to Excel and return the file."""
    filepath = export_excel()
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=config.EXCEL_FILE,
    )
