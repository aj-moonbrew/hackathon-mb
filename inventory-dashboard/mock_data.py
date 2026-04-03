"""
Default inventory data sourced directly from the QuickBox CSV export.
This is shown on Streamlit Cloud (where the local DB isn't available)
and is replaced automatically once a real scrape runs.
"""
import pandas as pd
from datetime import datetime, timezone

# Real SKUs from QuickBox export.csv — used as the default dataset
QUICKBOX_SNAPSHOT = [
    ("10X12 POLYBAG",              'Spartan Industrial - 10" X 12" Crystal Clear Reseal',  2442),
    ("8x10-BAG",                   "8x10 BAG",                                              1241),
    ("BLK-CRKLE-PAPER",            "Black Crinkle Paper",                                     15),
    ("BRW-CRKLE-PAPER",            "Brown Crinkle Paper",                                      3),
    ("HC101",                      "MoonBrew Hot Cocoa - 30 Servings",                         1),
    ("MB-30S-SB",                  "MoonBrew - 30 Servings - Sleepy Berry V1 - HOLD",          1),
    ("MB-AC-R-1PK-10",             "MoonBrew Apple Cider - 10 Servings / Pouch",            3454),
    ("MB-BOX-CUSTOM 10x7x5",       "MB-BOX-CUSTOM 10x7x5",                                18825),
    ("MB-CC-S-1PK-25",             "MoonBrew Coconut Chocolate - 25 Servings / Jar",          42),
    ("MB-CC-S-V3-1PK-25",          "MoonBrew Coconut Chocolate v3 - 25 Servings / Jar",    5139),
    ("MB-CH-R-1PK-30",             "MoonBrew Chai - 30 Servings / 1 Pack",                 4877),
    ("MB-CM-S-1PK-10",             "MoonBrew Caramel Macchiato - 10 Servings / Pouch",      385),
    ("MB-CRM-LABEL",               "MoonBrew Caramel Creatine Label",                         41),
    ("MB-CRM-R-V3-CREA-1PK-25",   "MoonBrew Sleep+Creatine Caramel Chocolate v3 - 25 Srv", 9982),
    ("MB-CRM-S-1PK-25",            "MoonBrew Caramel Chocolate - 25 Servings / Jar",          59),
    ("MB-CRM-S-V3-1PK-25",        "MoonBrew Caramel Chocolate v3 - 25 Servings / Jar",    12237),
    ("MB-DWMUG-1PK",               "MoonBrew Mug 1 Pack",                                  3124),
    ("MB-FROTHER-1PK",             "MoonBrew Electric Frother 1 Pack",                    51844),
    ("MB-GUASHA-1PK",              "MoonBrew Gua Sha",                                       130),
    ("MB-HC-ES-1PK-25",            "MoonBrew Hot Cocoa / Extra Strength - 25 Servings",       6),
    ("MB-HC-R-1PK-14",             "MoonBrew Hot Cocoa 14-Serving Stick Packs",               24),
    ("MB-HC-R-1PK-25",             "MoonBrew Hot Cocoa / Regular - 25 Servings",             446),
    ("MB-HC-R-1PK-30",             "MoonBrew Hot Cocoa / Regular - 30 Servings",            1922),
    ("MB-HC-R-V3-1PK-25",          "MoonBrew Hot Cocoa v3 - 25 Servings / Jar",            57127),
    ("MB-HC-S-1PK-25",             "MoonBrew Homestyle Hot Cocoa - 25 Servings / Jar",      6176),
    ("MB-HOLIDAY-FROTHER-1PK",     "Holiday Frother",                                        278),
    ("MB-HOLIDAY-GB-Insert 5x8.5", "Holiday Gift Box Insert 5x8.5",                          314),
    ("MB-HOLIDAY-GB-Insert 7.5x8.5","MB-HOLIDAY-GB-Insert 7.5x8.5",                          330),
    ("MB-HOLIDAY-GB-Insert5Slots", "MB-HOLIDAY-GB-Insert5Slots",                              226),
    ("MB-HOLIDAY-GB-InsertBase10.5x9","Holiday Gift Box Insert-Base 10.5x9",                  289),
    ("MB-HOLIDAY-GIFT-BOX-1PK",    "Holiday Gift Box",                                       286),
    ("MB-HOLIDAY-GIFT-BOX-1PK-KITTED","MB-HOLIDAY-GIFT-BOX-1PK-KITTED",                       18),
    ("MB-HOLIDAY-RECIPE-BOOK-1PK", "Holiday Recipe Book",                                    328),
    ("MBINSERT",                   "MoonBrew Insert",                                         62),
    ("MB-MAILER-1",                "MoonBrew Bubble Mailer - 10.3in x 13.5in",            25188),
    ("MB-MHC-R-1PK-25",            "MoonBrew Mint Chocolate - 25 Servings / Jar",             43),
    ("MB-MHC-R-1PK-30",            "MoonBrew Mint Chocolate - 30 Servings",                6650),
    ("MB-MHC-R-V3-1PK-25",         "MoonBrew Mint Chocolate v3 - 25 Servings / Jar",       2333),
    ("MB-P65-LARGE",               "MoonBrew P65 Warning Stickers - Large Jars",           11558),
    ("MB-P65-SMALL",               "MoonBrew P65 Warning Stickers - Small Jars",            3162),
    ("MB-PR-1PK",                  "MoonBrew PR Box",                                        222),
    ("MB-P-R-V3-1PK-25",           "MoonBrew Peach v3 - 25 Servings / Jar",                4862),
    ("MB-PUR-BOX-KIT",             "MB Purple Box Kit-HC1",                                    8),
    ("MB-PUR-BOX-VLAT",            "MB PR Box-Vanilla Latte",                                  2),
    ("MB-SB-ES-1PK-30",            "MoonBrew Sleepy Berry / Extra Strength - 30 Servings",  3530),
    ("MB-SB-R-1PK-14",             "MoonBrew Sleepy Berry 14-Serving Stick Packs",          9112),
    ("MB-SB-R-1PK-25",             "MoonBrew Sleepy Berry - 25 Servings / Jar",               20),
    ("MB-SB-R-1PK-30",             "MoonBrew Sleepy Berry / Regular - 30 Servings",          216),
    ("MB-SB-R-V3-1PK-25",          "MoonBrew Sleepy Berry v3 - 25 Servings / Jar",          1372),
    ("MB-SFP-STR",                 "SFP Sticker for Strawberry - 25 Servings",               790),
    ("MB-SL-R-V3-FIBER-1PK-25",    "MoonBrew Sleep+Fiber Strawberry Lemonade v3 - 25 Srv",  5105),
    ("MB-SM-1PK",                  "MoonBrew Sleep Mask 1 Pack",                              462),
    ("MBST-30S",                   "MoonBoost",                                              4443),
    ("MB-STICKER-1PK",             "MoonBrew Sticker Sheet 1 Pack",                         2883),
    ("MB-STR-R-V3-1PK-25",         "MoonBrew Strawberry v3 - 25 Servings / Jar",            3513),
    ("MB-STR-S-G1-1PK-25",         "MoonBrew Strawberry Gummy - 25 Servings / Pouch",       1391),
    ("MB-TAPE-1PK",                "MoonBrew Mouth Tape",                                   3150),
    ("MB-TLABEL-HCR-1PK-25",       "Amazon Transparency Sticker - Hot Cocoa Regular",       7000),
    ("MB-TOTEBAG-1PK",             "MoonBrew Tote Bag",                                        8),
    ("MB-VL-S-1PK-25",             "MoonBrew Vanilla Latte - 25 Servings / Jar / Sugar",      76),
    ("MB-VL-S-V3-1PK-25",          "MoonBrew Vanilla Latte v3 - 25 Servings / Jar",        14263),
    ("MB-V-S-V3-1PK-25",           "MoonBrew Vanilla v3 - 25 Servings / Jar / Sugar",       6261),
    ("NB-GB1",                     "MoonBrew Glass Bottle",                                   234),
    ("NB-P30S",                    "NoonBrew Peach",                                          243),
    ("PR-BOX-INFLUENCER",          "PR-BOX-INFLUENCER",                                        1),
    ("SB102",                      "MoonBrew Sleepy Berry - 30 Servings",                    227),
]


EXTRA_CHANNELS = [
    ("Amazon FBA",  "Amazon FBA Warehouse"),
    ("TikTok FBT",  "TikTok Warehouse"),
]


def get_mock_df() -> pd.DataFrame:
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0).isoformat()
    rows = []
    _id = 1

    # QuickBox — real quantities
    for sku, name, qty in QUICKBOX_SNAPSHOT:
        rows.append({
            "id": _id, "source": "LogicPod / QuickBox",
            "sku": sku, "product_name": name,
            "quantity": qty, "location": "QuickBox Warehouse", "scraped_at": now,
        })
        _id += 1

    # Amazon & TikTok — same SKUs, quantity 0 (not connected yet)
    for source, location in EXTRA_CHANNELS:
        for sku, name, _ in QUICKBOX_SNAPSHOT:
            rows.append({
                "id": _id, "source": source,
                "sku": sku, "product_name": name,
                "quantity": 0, "location": location, "scraped_at": now,
            })
            _id += 1

    df = pd.DataFrame(rows)
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], utc=True)
    df["date"] = df["scraped_at"].dt.date
    return df
