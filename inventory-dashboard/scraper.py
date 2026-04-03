import time
import re
from playwright.sync_api import sync_playwright
import config
from database import init_db, save_records, export_excel


# ---------------------------------------------------------------------------
# Shared helper
# ---------------------------------------------------------------------------

def safe_int(text) -> int:
    """
    Strips commas, extracts the first integer from a string.
    Returns 0 if nothing found or input is None/empty.
    Examples: "1,234" -> 1234 | "1234 units" -> 1234 | "" -> 0 | None -> 0
    """
    if not text:
        return 0
    cleaned = str(text).replace(",", "")
    match = re.search(r"\d+", cleaned)
    return int(match.group()) if match else 0


# ---------------------------------------------------------------------------
# LogicPod / QuickBox scraper
# ---------------------------------------------------------------------------

def scrape_logicpod(page):
    """
    Scrapes inventory from LogicPod / QuickBox WMS.

    If 0 rows are found:
      - The browser is still open (headless=False).
      - Right-click the inventory table → Inspect.
      - Find the repeating row element (often <tr> inside a <tbody>).
      - Update the query_selector_all() call below to match the actual HTML.
      - Common alternatives: 'tr.inventory-row', '[data-row]', '.ag-row'
    """
    creds = config.CREDS["logicpod"]
    print(f"[LogicPod] Navigating to {creds['url']}")
    page.goto(creds["url"])
    time.sleep(2)

    page.fill("input[type='email']", creds["user"])
    page.fill("input[type='password']", creds["password"])
    page.click("button[type='submit'], input[type='submit']")
    time.sleep(3)

    print("[LogicPod] Navigating to inventory page")
    page.goto("https://app.quickbox.com/inventory")
    time.sleep(2)

    rows = page.query_selector_all("table tbody tr")
    print(f"[LogicPod] Found {len(rows)} rows")

    records = []
    for row in rows:
        cells = row.query_selector_all("td")
        if len(cells) < 4:
            continue
        sku          = (cells[0].inner_text() or "").strip()
        product_name = (cells[1].inner_text() or "").strip()
        quantity     = safe_int(cells[2].inner_text())
        location     = (cells[3].inner_text() or "").strip()
        records.append({
            "source":       "LogicPod / QuickBox",
            "sku":          sku,
            "product_name": product_name,
            "quantity":     quantity,
            "location":     location,
        })

    print(f"[LogicPod] Collected {len(records)} records")
    return records


# ---------------------------------------------------------------------------
# Amazon Seller Central scraper
# ---------------------------------------------------------------------------

def scrape_amazon(page):
    """
    Scrapes inventory from Amazon Seller Central.

    MFA: If Amazon asks for a verification code the script will pause up to
    60 s and print a prompt.  Enter the code in the browser window and submit
    it; the script will resume automatically once the URL changes.

    If 0 rows are found:
      - Right-click the inventory table → Inspect.
      - Find the repeating row element.
      - Update the query_selector_all() calls below.
      - Common alternatives: 'tr.data-row', '[data-component-type="s-search-result"]'
    """
    creds = config.CREDS["amazon"]
    print(f"[Amazon] Navigating to {creds['url']}")
    page.goto(creds["url"])
    time.sleep(2)

    # Email step
    email_field = page.query_selector("input[name='email']")
    if email_field:
        email_field.fill(creds["user"])
        continue_btn = page.query_selector("input#continue, #continue")
        if continue_btn:
            continue_btn.click()
        time.sleep(2)

    # Password step
    pw_field = page.query_selector("input[name='password']")
    if pw_field:
        pw_field.fill(creds["password"])
        signin_btn = page.query_selector("input#signInSubmit, #signInSubmit")
        if signin_btn:
            signin_btn.click()
        time.sleep(3)

    # MFA check — wait up to 60 s for the user to complete it in the browser
    mfa_field = page.query_selector("input[name='otpCode'], input[id*='auth-mfa']")
    if mfa_field:
        print("[Amazon] MFA detected — please enter your verification code in the browser window.")
        print("[Amazon] Waiting up to 60 seconds for MFA completion…")
        try:
            page.wait_for_url("**/sellercentral.amazon.com/**", timeout=60_000)
        except Exception:
            print("[Amazon] Timed out waiting for MFA — continuing anyway.")
    time.sleep(2)

    print("[Amazon] Navigating to inventory page")
    page.goto("https://sellercentral.amazon.com/inventory")
    time.sleep(3)

    rows = page.query_selector_all("table tbody tr")
    if not rows:
        rows = page.query_selector_all("div[data-testid='inventory-row']")
    print(f"[Amazon] Found {len(rows)} rows")

    records = []
    for row in rows:
        cells = row.query_selector_all("td")
        if len(cells) < 5:
            # Try div-based layout
            divs = row.query_selector_all("div[class*='cell'], div[class*='col']")
            if len(divs) >= 5:
                cells = divs
            else:
                continue

        sku          = (cells[0].inner_text() or "").strip()
        product_name = (cells[1].inner_text() or "").strip()
        quantity     = safe_int(cells[4].inner_text()) if len(cells) > 4 else 0
        location     = "Amazon FBA Warehouse"
        records.append({
            "source":       "Amazon FBA",
            "sku":          sku,
            "product_name": product_name,
            "quantity":     quantity,
            "location":     location,
        })

    print(f"[Amazon] Collected {len(records)} records")
    return records


# ---------------------------------------------------------------------------
# TikTok Seller Central scraper
# ---------------------------------------------------------------------------

def scrape_tiktok(page):
    """
    Scrapes product/inventory list from TikTok Seller Central.

    If 0 rows are found:
      - Right-click the product list → Inspect.
      - Identify the repeating element for each product row.
      - Update the query_selector_all() calls below.
      - Common alternatives: '.product-item', 'tr[class*="row"]', '[data-product-id]'
    """
    creds = config.CREDS["tiktok"]
    print(f"[TikTok] Navigating to {creds['url']}")
    page.goto(creds["url"])
    time.sleep(3)

    # Try several possible email selectors
    email_field = (
        page.query_selector("input[type='email']")
        or page.query_selector("input[placeholder*='email' i]")
        or page.query_selector("input[name*='email' i]")
    )
    if email_field:
        email_field.fill(creds["user"])
    else:
        print("[TikTok] WARNING: Could not find email field — inspect the login page.")

    pw_field = page.query_selector("input[type='password']")
    if pw_field:
        pw_field.fill(creds["password"])
    else:
        print("[TikTok] WARNING: Could not find password field.")

    login_btn = (
        page.query_selector("button[type='submit']")
        or page.query_selector("button:has-text('Log in')")
        or page.query_selector("button:has-text('Login')")
    )
    if login_btn:
        login_btn.click()
    else:
        print("[TikTok] WARNING: Could not find login button — inspect the login page.")
    time.sleep(3)

    print("[TikTok] Navigating to product list")
    page.goto("https://seller.tiktokglobalshop.com/product/list")
    time.sleep(3)

    rows = page.query_selector_all("table tbody tr")
    if not rows:
        rows = page.query_selector_all("div.product-row")
    print(f"[TikTok] Found {len(rows)} rows")

    records = []
    for row in rows:
        cells = row.query_selector_all("td")
        if len(cells) < 4:
            cells = row.query_selector_all("div[class*='cell'], div[class*='col']")
        if len(cells) < 2:
            continue

        sku          = (cells[0].inner_text() or "").strip()
        product_name = (cells[1].inner_text() or "").strip()
        quantity     = safe_int(cells[3].inner_text()) if len(cells) > 3 else 0
        location     = "TikTok Warehouse"
        records.append({
            "source":       "TikTok FBT",
            "sku":          sku,
            "product_name": product_name,
            "quantity":     quantity,
            "location":     location,
        })

    print(f"[TikTok] Collected {len(records)} records")
    return records


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_scrape() -> list[dict]:
    """
    Opens one browser context, runs all three scrapers, saves to DB + Excel.
    Each scraper failure is caught individually so others still run.
    Returns the combined list of records.
    """
    init_db()
    all_records = []

    scrapers = [
        ("LogicPod", scrape_logicpod),
        ("Amazon",   scrape_amazon),
        ("TikTok",   scrape_tiktok),
    ]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()

        for name, scraper_fn in scrapers:
            page = context.new_page()
            try:
                records = scraper_fn(page)
                all_records.extend(records)
            except Exception as exc:
                print(f"[{name}] ERROR: {exc}")
            finally:
                page.close()

        context.close()
        browser.close()

    if all_records:
        save_records(all_records)
        export_excel()

    print(f"\n[Done] Total records collected: {len(all_records)}")
    return all_records


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_scrape()
