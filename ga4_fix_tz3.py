import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"
ACCOUNT_ID = "389031276"
CORRECT_PROP = "533443439"

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

    # Navigate to admin settings
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{CORRECT_PROP}/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(6000)
    page.keyboard.press("Escape")
    w(500)

    # Click Property details
    page.get_by_text("Property details").first.click()
    w(6000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "tz3_01_form")

    # Inspect the DOM around "Reporting time zone"
    print("--- DOM inspection around timezone ---")
    result = page.evaluate("""() => {
        // Find element containing "Reporting time zone"
        const allEls = Array.from(document.querySelectorAll('*'));
        const tzLabel = allEls.find(el => el.childNodes.length <= 3 && el.textContent.trim() === 'Reporting time zone');
        if (!tzLabel) return 'TZ label not found';

        // Walk up to find the container, then look for the select/button
        let container = tzLabel.parentElement;
        for (let i = 0; i < 5; i++) {
            if (container) container = container.parentElement;
        }

        // Get the outer HTML of the region
        return container ? container.outerHTML.substring(0, 3000) : 'no container';
    }""")
    print("TZ region HTML:", result[:2000])

    # Try clicking on the "(GMT-07:00) Los Angeles Time" text or "United States" text
    # These should be clickable dropdowns
    print("\n--- Trying to click timezone dropdown ---")
    tz_changed = False

    for selector in [
        'text="(GMT-07:00) Los Angeles Time"',
        'text="United States"',
        '[aria-label*="Reporting time zone"]',
        '[aria-label*="time zone"]',
        'ga-select',
        '.ga-select',
        '[class*="select"]',
    ]:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=1500):
                print(f"  Found: {selector} — clicking")
                el.click()
                w(2000)
                ss(page, "tz3_02_dropdown")

                # Check for options or new content
                txt = page.locator("body").inner_text(timeout=3000)
                print("  After click (new lines):", [l.strip() for l in txt.split("\n") if "time" in l.lower() or "zone" in l.lower() or "croatia" in l.lower() or "zagreb" in l.lower() or "gmt" in l.lower()][:10])

                # Try typing in search
                page.keyboard.type("Zagreb")
                w(1500)
                ss(page, "tz3_03_typed")
                txt2 = page.locator("body").inner_text(timeout=3000)
                zagreb_lines = [l.strip() for l in txt2.split("\n") if "zagreb" in l.lower() or "croatia" in l.lower()]
                print("  Zagreb options:", zagreb_lines[:5])

                if zagreb_lines:
                    # Click on first Zagreb option
                    page.get_by_text("Zagreb", exact=False).first.click()
                    tz_changed = True
                    print("  Clicked Zagreb!")
                    w(500)
                    break
                else:
                    page.keyboard.press("Escape")
                    w(300)
        except Exception as e:
            print(f"  {selector}: {e}")

    ss(page, "tz3_04_after_tz")

    if not tz_changed:
        print("  TZ not changed — inspecting clickable elements in the form area")
        # Get coordinates of "Los Angeles Time" text and click
        try:
            el = page.get_by_text("Los Angeles Time", exact=False).first
            box = el.bounding_box()
            print(f"  'Los Angeles Time' bounding box: {box}")
            if box:
                page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                w(2000)
                ss(page, "tz3_05_la_click")
                txt = page.locator("body").inner_text(timeout=3000)
                new_lines = [l.strip() for l in txt.split("\n") if l.strip() and ("time" in l.lower() or "gmt" in l.lower() or "zone" in l.lower())]
                print("  After LA click:", new_lines[:10])
        except Exception as e:
            print(f"  LA click error: {e}")

    # Currency
    print("\n--- Trying currency ---")
    curr_changed = False
    for selector in [
        '[aria-label*="Currency"]',
        '[aria-label*="currency"]',
        'text="US Dollar (USD)"',
        'text="USD"',
    ]:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=1500):
                print(f"  Found currency: {selector}")
                el.click()
                w(2000)
                page.keyboard.type("Euro")
                w(1500)
                opts = page.locator("[role='option'], mat-option").all()
                for opt in opts:
                    try:
                        t = opt.inner_text(timeout=300)
                        if "eur" in t.lower():
                            opt.click()
                            curr_changed = True
                            print(f"  Currency: {t[:40]}")
                            break
                    except:
                        pass
                if not curr_changed:
                    page.keyboard.press("Escape")
                break
        except Exception as e:
            print(f"  {selector}: {e}")

    # Save
    if tz_changed or curr_changed:
        for btn_name in ["Save", "Update", "Spremi"]:
            try:
                btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"  Saved!")
                    w(3000)
                    ss(page, "tz3_06_saved")
                    break
            except:
                pass

    page.close()

print("\nDone.")
