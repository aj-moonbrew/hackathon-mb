CREDS = {
    "logicpod": {
        "url":      "https://app.quickbox.com/login",
        "user":     "YOUR_LOGICPOD_EMAIL",
        "password": "YOUR_LOGICPOD_PASSWORD",
    },
    "amazon": {
        "url":      "https://sellercentral.amazon.com",
        "user":     "YOUR_AMAZON_EMAIL",
        "password": "YOUR_AMAZON_PASSWORD",
    },
    "tiktok": {
        "url":      "https://seller.tiktokglobalshop.com",
        "user":     "YOUR_TIKTOK_EMAIL",
        "password": "YOUR_TIKTOK_PASSWORD",
    },
}

DB_FILE    = "inventory.db"
EXCEL_FILE = "inventory.xlsx"

# How often to auto-scrape in minutes (used by the scheduler if enabled)
SCRAPE_INTERVAL_MINUTES = 60
