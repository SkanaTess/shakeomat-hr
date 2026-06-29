import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"
ACCOUNT_ID = "389031276"
# Three candidate property IDs (all potentially Shake-o-mat)
CANDIDATES = ["533480894", "533443439", "532393510"]
# Known correct stream ID from D09 screenshot
CORRECT_STREAM_ID = "14384624844"
# Known correct measurement ID from D10 screenshot
CORRECT_MEASUREMENT_ID = "G-65B9W6C4GY"

def ss(page, name):
    try:
        page.screenshot(path=f"{BASE}\\ga4_{name}.png", timeout=45000)
        print(f"  [ss] {name}")
    except Exception as e:
        print(f"  [ss FAIL] {e}")

def w(ms=2000):
    time.sleep(ms / 1000)

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]

    correct_prop = None
    to_delete = []

    for prop_id in CANDIDATES:
        page = ctx.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})
        page.set_default_timeout(20000)

        print(f"\n=== Checking property {prop_id} ===")
        page.goto(
            f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{prop_id}/admin/streams",
            wait_until="domcontentloaded", timeout=30000
        )
        w(5000)

        content = page.content()
        txt = page.locator("body").inner_text(timeout=5000)

        # Check for correct stream ID or measurement ID
        has_correct_stream = CORRECT_STREAM_ID in content or CORRECT_STREAM_ID in txt
        has_mid = CORRECT_MEASUREMENT_ID in content

        print(f"  Has stream {CORRECT_STREAM_ID}: {has_correct_stream}")
        print(f"  Has MID {CORRECT_MEASUREMENT_ID}: {has_mid}")

        # Also get stream names to identify
        stream_names = re.findall(r'Shake-o-mat[\w\s]*', txt)
        print(f"  Stream names: {stream_names[:3]}")

        # Get all G- IDs visible
        g_ids = set(re.findall(r'G-[A-Z0-9]{8,12}', txt + content))
        print(f"  G- IDs: {g_ids}")

        if has_correct_stream or CORRECT_MEASUREMENT_ID in (txt + content):
            correct_prop = prop_id
            print(f"  >>> CORRECT PROPERTY: {prop_id}")
        else:
            to_delete.append(prop_id)
            print(f"  >>> DUPLICATE to delete")

        ss(page, f"prop_{prop_id}_streams")
        page.close()

    print(f"\n{'='*50}")
    print(f"Correct property: {correct_prop}")
    print(f"To delete: {to_delete}")

    # Fix timezone/currency for correct property
    if correct_prop:
        print(f"\n=== Fixing timezone/currency for {correct_prop} ===")
        page = ctx.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})
        page.set_default_timeout(30000)

        page.goto(
            f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{correct_prop}/admin/property/settings",
            wait_until="domcontentloaded", timeout=30000
        )
        w(5000)
        ss(page, "prop_settings_before")

        txt = page.locator("body").inner_text(timeout=5000)
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        print("Property settings page (first 30):")
        for l in lines[:30]:
            print(" ", repr(l[:80]))

        page.close()

    # Delete duplicate properties
    for prop_id in to_delete:
        print(f"\n=== Deleting property {prop_id} ===")
        page = ctx.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})
        page.set_default_timeout(30000)

        # Navigate to property settings to find Trash/Delete option
        page.goto(
            f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{prop_id}/admin/property/settings",
            wait_until="domcontentloaded", timeout=30000
        )
        w(5000)
        ss(page, f"prop_{prop_id}_settings")

        txt = page.locator("body").inner_text(timeout=5000)
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        print("Settings first 20 lines:")
        for l in lines[:20]:
            print(" ", repr(l[:80]))

        page.close()

print("\nDone.")
