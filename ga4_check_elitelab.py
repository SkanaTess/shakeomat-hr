import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"
ACCOUNT_ID = "389031276"
ELITELAB_MID = "G-LFP8P5KG38"
ELITELAB_PROP = "532393510"

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
    page = ctx.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    page.set_default_timeout(30000)

    # 1. Try to navigate directly to elitelab.hr property (532393510)
    print("=== Test 1: Navigate to property 532393510 ===")
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{ELITELAB_PROP}/reports/home",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(300)
    ss(page, "el_01_property")

    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    # What property name shows in breadcrumb?
    print("Breadcrumb/header:")
    for l in lines[:15]:
        print(" ", repr(l[:100]))

    url_hash = page.evaluate("() => window.location.hash")
    print(f"URL hash: {url_hash}")

    # 2. Check property switcher — list all properties in this account
    print("\n=== Test 2: Property switcher ===")
    page.goto(
        "https://analytics.google.com/analytics/web/",
        wait_until="domcontentloaded", timeout=30000
    )
    w(4000)
    page.keyboard.press("Escape")
    w(300)

    # Click breadcrumb to open property switcher
    try:
        # Click on the account/property name in the breadcrumb
        breadcrumb = page.locator("[class*='breadcrumb'], [class*='account-name'], [class*='property-name']").first
        if breadcrumb.is_visible(timeout=2000):
            breadcrumb.click()
            w(2000)
            ss(page, "el_02_switcher")
    except:
        pass

    # Try clicking "All accounts" link
    try:
        page.get_by_text("All accounts").first.click()
        w(3000)
        ss(page, "el_03_all_accounts")
        txt2 = page.locator("body").inner_text(timeout=5000)
        lines2 = [l.strip() for l in txt2.split("\n") if l.strip()]
        print("All accounts page (first 30):")
        for l in lines2[:30]:
            print(" ", repr(l[:100]))
    except Exception as e:
        print(f"  All accounts click: {e}")

    # 3. Go to Admin, look for Trash Can via sidebar
    print("\n=== Test 3: Admin → Trash Can via sidebar ===")
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p533443439/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(300)

    # Look for "Trash Can" in the Account section of admin sidebar
    try:
        trash_link = page.get_by_text("Trash Can").first
        if trash_link.is_visible(timeout=3000):
            trash_link.click()
            w(5000)
            page.keyboard.press("Escape")
            w(300)
            ss(page, "el_04_trash")
            txt3 = page.locator("body").inner_text(timeout=5000)
            lines3 = [l.strip() for l in txt3.split("\n") if l.strip()]
            print("Trash Can (first 40):")
            for l in lines3[:40]:
                print(" ", repr(l[:100]))

            # Check if elitelab.hr is there
            for l in lines3:
                if "elitelab" in l.lower() or "532393510" in l or ELITELAB_MID in l:
                    print(f"  FOUND: {repr(l)}")

            # Try to restore
            restore_btns = page.get_by_role("button", name=re.compile("restore", re.I)).all()
            print(f"  Restore buttons: {len(restore_btns)}")
            for btn in restore_btns:
                try:
                    print(f"    btn: {repr(btn.inner_text(timeout=300)[:40])}")
                except:
                    pass
        else:
            print("  'Trash Can' not visible in sidebar")
            # Show sidebar content
            txt_admin = page.locator("body").inner_text(timeout=3000)
            admin_lines = [l.strip() for l in txt_admin.split("\n") if l.strip()]
            print("  Admin sidebar (first 30):")
            for l in admin_lines[:30]:
                print("   ", repr(l[:100]))
    except Exception as e:
        print(f"  Trash Can error: {e}")

    page.close()

print("\nDone.")
