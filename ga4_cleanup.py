import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"

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

    # Navigate to Admin
    page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
    w(3000)
    page.keyboard.press("Escape")
    w(500)
    page.get_by_text("Admin", exact=True).first.click()
    w(4000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "E01_admin")

    # Click on "Property" in the Create dropdown to see all properties
    # Actually, navigate to the property switcher in the ekohvok header
    # Try clicking "ekohvok.com" dropdown in header
    try:
        # Click the dropdown arrow next to property name in header
        page.get_by_text("ekohvok.com").first.click()
        w(3000)
        ss(page, "E02_picker")
        txt = page.locator("body").inner_text(timeout=5000)
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        print("After ekohvok click:")
        for l in lines[:30]:
            print(" ", repr(l[:80]))
    except Exception as e:
        print(f"ekohvok click error: {e}")

    # Try the dropdown chevron arrow
    try:
        # Find element with dropdown arrow near "ekohvok.com"
        arrow = page.locator("mat-icon:has-text('arrow_drop_down')").first
        if arrow.is_visible(timeout=2000):
            arrow.click()
            w(3000)
            ss(page, "E03_dropdown")
    except Exception as e:
        print(f"Arrow click: {e}")

    # Try Trash in admin to see all properties including deleted ones
    page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
    w(3000)
    page.keyboard.press("Escape")
    w(500)
    page.get_by_text("Admin", exact=True).first.click()
    w(4000)

    # Click on "Account" to expand
    try:
        page.get_by_role("button", name="Account").first.click()
        w(1000)
    except:
        pass

    # Click Trash
    try:
        page.get_by_text("Trash").first.click()
        w(4000)
        ss(page, "E04_trash")
        txt = page.locator("body").inner_text(timeout=5000)
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        print("Trash contents:")
        for l in lines[:40]:
            print(" ", repr(l[:80]))
    except Exception as e:
        print(f"Trash error: {e}")

    # Also check Account change history to see all created properties
    try:
        # Navigate back to admin
        page.get_by_text("Admin", exact=True).first.click()
        w(3000)
        page.get_by_role("button", name="Account").first.click()
        w(1000)
        page.get_by_text("Account change history").first.click()
        w(5000)
        ss(page, "E05_change_history")
        txt = page.locator("body").inner_text(timeout=5000)
        lines = [l.strip() for l in txt.split("\n") if l.strip()]
        print("Change history:")
        for l in lines[:50]:
            print(" ", repr(l[:80]))
    except Exception as e:
        print(f"Change history error: {e}")

    page.close()
print("Done.")
