"""
Realistic mock inventory data for dashboard preview.
Used automatically when no scraped data exists yet.
"""
import pandas as pd

MOCK_RECORDS = []

# Products
PRODUCTS = [
    ("MB-001", "Moon Brew Original Blend 12oz"),
    ("MB-002", "Moon Brew Dark Roast 12oz"),
    ("MB-003", "Moon Brew Decaf 12oz"),
    ("MB-004", "Moon Brew Variety Pack (3x12oz)"),
    ("MB-005", "Moon Brew Cold Brew Concentrate 32oz"),
]

# Snapshots spread across 4 weeks
SNAPSHOTS = [
    ("2024-03-04T09:00:00Z", {
        "Amazon FBA":          [420, 185, 230, 310, 95],
        "TikTok FBT":          [190, 75,  110, 145, 40],
        "LogicPod / QuickBox": [820, 340, 460, 610, 180],
    }),
    ("2024-03-11T09:00:00Z", {
        "Amazon FBA":          [380, 160, 205, 270, 80],
        "TikTok FBT":          [220, 90,  130, 170, 55],
        "LogicPod / QuickBox": [790, 310, 430, 580, 165],
    }),
    ("2024-03-18T09:00:00Z", {
        "Amazon FBA":          [510, 200, 260, 330, 120],
        "TikTok FBT":          [175, 65,  95,  130, 35],
        "LogicPod / QuickBox": [850, 360, 490, 640, 200],
    }),
    ("2024-03-25T09:00:00Z", {
        "Amazon FBA":          [460, 175, 240, 295, 105],
        "TikTok FBT":          [240, 100, 145, 190, 60],
        "LogicPod / QuickBox": [810, 325, 445, 595, 172],
    }),
]

LOCATIONS = {
    "Amazon FBA":          "Amazon FBA Warehouse",
    "TikTok FBT":          "TikTok Warehouse",
    "LogicPod / QuickBox": "Warehouse A",
}

_id = 1
for ts, channels in SNAPSHOTS:
    for channel, qtys in channels.items():
        for i, (sku, name) in enumerate(PRODUCTS):
            MOCK_RECORDS.append({
                "id":           _id,
                "source":       channel,
                "sku":          sku,
                "product_name": name,
                "quantity":     qtys[i],
                "location":     LOCATIONS[channel],
                "scraped_at":   ts,
            })
            _id += 1


def get_mock_df() -> pd.DataFrame:
    df = pd.DataFrame(MOCK_RECORDS)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True)
    df["date"] = df["scraped_at"].dt.date
    return df
