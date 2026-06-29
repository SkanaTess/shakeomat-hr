import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"
ACCOUNT_ID = "389031276"
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

    # Navigate to Account Admin → Trash Can
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}/admin/trash",
        wait_until="domcontentloaded", timeout=30000
    )
    w(6000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "restore_01_trash")

    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Trash Can page (first 40):")
    for l in lines[:40]:
        print(" ", repr(l[:100]))

    # Check what's in trash
    print("\n--- Looking for elitelab.hr in trash ---")
    has_elitelab = any("elitelab" in l.lower() for l in lines)
    has_prop = any(ELITELAB_PROP in l for l in lines)
    print(f"  Has 'elitelab': {has_elitelab}")
    print(f"  Has property ID {ELITELAB_PROP}: {has_prop}")

    # Also check if it's not there (might have different URL)
    content = page.content()
    if "elitelab" not in content.lower() and ELITELAB_PROP not in content:
        print("  Not found in trash via direct URL — trying via Admin menu")
        # Navigate to admin
        page.goto(
            f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}/admin",
            wait_until="domcontentloaded", timeout=30000
        )
        w(5000)
        page.keyboard.press("Escape")
        w(500)

        # Click "Trash Can" in Account section
        trash_link = page.get_by_text("Trash Can").first
        if trash_link.is_visible(timeout=3000):
            trash_link.click()
            w(4000)
            ss(page, "restore_02_trash_via_admin")
            txt = page.locator("body").inner_text(timeout=5000)
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            print("Trash via Admin (first 40):")
            for l in lines[:40]:
                print(" ", repr(l[:100]))

    # Try to restore elitelab.hr property
    print("\n--- Attempting restore ---")
    # Look for "Restore" button next to elitelab.hr
    restored = False

    # Find all rows in the trash table
    rows = page.locator("tr, [role='row']").all()
    print(f"  Table rows: {len(rows)}")
    for i, row in enumerate(rows):
        try:
            row_txt = row.inner_text(timeout=500)
            if "elitelab" in row_txt.lower() or ELITELAB_PROP in row_txt:
                print(f"  Found elitelab row [{i}]: {repr(row_txt[:100])}")
                # Click Restore in this row
                restore_btn = row.get_by_text("Restore").first
                if restore_btn.is_visible(timeout=1000):
                    restore_btn.click()
                    print("  Clicked Restore!")
                    w(3000)
                    ss(page, "restore_03_confirm")
                    # Confirm dialog if any
                    for btn in ["Restore", "Confirm", "OK", "Yes"]:
                        try:
                            b = page.get_by_role("button", name=re.compile(btn, re.I)).first
                            if b.is_visible(timeout=2000):
                                b.click()
                                print(f"  Confirmed: {btn}")
                                w(3000)
                                restored = True
                                break
                        except:
                            pass
                    break
        except:
            pass

    if not restored:
        print("  Could not find/restore via table rows — trying direct text search")
        # Try clicking any "Restore" button that's near "elitelab" text
        try:
            restore_btns = page.get_by_role("button", name=re.compile("restore", re.I)).all()
            print(f"  Restore buttons found: {len(restore_btns)}")
            # If only one, click it
            if len(restore_btns) == 1:
                restore_btns[0].click()
                print("  Clicked only Restore button")
                w(3000)
                ss(page, "restore_03b_confirm")
                restored = True
        except Exception as e:
            print(f"  Restore error: {e}")

    ss(page, "restore_04_result")
    txt_final = page.locator("body").inner_text(timeout=5000)
    lines_final = [l.strip() for l in txt_final.split("\n") if l.strip()]
    print("\nFinal state (first 20):")
    for l in lines_final[:20]:
        print(" ", repr(l[:100]))

    print(f"\n  Restored: {restored}")

    # Verify: navigate to elitelab.hr property to confirm it's active
    if restored:
        w(2000)
        page.goto(
            f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{ELITELAB_PROP}/reports/home",
            wait_until="domcontentloaded", timeout=30000
        )
        w(5000)
        ss(page, "restore_05_verify")
        print("  Navigate to elitelab property — check screenshot")

    page.close()

print("\nDone.")
