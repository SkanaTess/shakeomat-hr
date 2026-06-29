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

    # Navigate directly to Property Details page
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{CORRECT_PROP}/admin/property/details",
        wait_until="domcontentloaded", timeout=30000
    )
    w(6000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "tz01_details")

    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Property details page (first 40 lines):")
    for l in lines[:40]:
        print(" ", repr(l[:100]))

    # Dump all mat-select elements
    print("\n--- mat-select elements ---")
    selects = page.locator("mat-select").all()
    for i, sel in enumerate(selects):
        try:
            vis = sel.is_visible(timeout=500)
            aria = sel.get_attribute("aria-label") or ""
            val = sel.get_attribute("value") or ""
            inner = sel.inner_text(timeout=500)[:60] if vis else ""
            print(f"  [{i}] visible={vis} aria='{aria}' value='{val}' text='{inner}'")
        except Exception as e:
            print(f"  [{i}] error: {e}")

    # Try clicking the timezone select
    print("\n--- Trying timezone ---")
    tz_changed = False
    for i, sel_str in enumerate([
        'mat-select[aria-label="Time zone"]',
        'mat-select[aria-label*="time" i]',
        'mat-select[aria-label*="zone" i]',
        'mat-select[formcontrolname="timeZone"]',
        'mat-select[formcontrolname*="time" i]',
    ]):
        try:
            el = page.locator(sel_str).first
            if el.is_visible(timeout=2000):
                print(f"  Found TZ selector: {sel_str}")
                el.click()
                w(2000)
                ss(page, "tz02_dropdown")

                # Type to filter
                page.keyboard.type("Zagreb")
                w(1000)

                # Look for options
                opts = page.locator("mat-option, [role='option']").all()
                print(f"  Options after typing 'Zagreb': {len(opts)}")
                for opt in opts[:5]:
                    try:
                        t = opt.inner_text(timeout=300)
                        print(f"    option: {repr(t[:60])}")
                    except:
                        pass

                # Click first option
                if opts:
                    opts[0].click()
                    print("  Clicked first option")
                    tz_changed = True
                    w(500)
                else:
                    # Try without filter
                    page.keyboard.press("Control+a")
                    page.keyboard.type("Croatia")
                    w(1000)
                    opts2 = page.locator("mat-option, [role='option']").all()
                    for opt in opts2[:5]:
                        try:
                            t = opt.inner_text(timeout=300)
                            if "croatia" in t.lower() or "zagreb" in t.lower() or "+01" in t.lower():
                                opt.click()
                                tz_changed = True
                                print(f"  Set TZ: {t[:60]}")
                                break
                        except:
                            pass
                break
        except Exception as e:
            print(f"  [{i}] {sel_str}: {e}")

    if not tz_changed:
        print("  Timezone not changed via mat-select — trying input approach")
        # Maybe it's an input with autocomplete
        for inp_str in ['input[aria-label*="time" i]', 'input[placeholder*="time" i]']:
            try:
                el = page.locator(inp_str).first
                if el.is_visible(timeout=1000):
                    el.click()
                    w(500)
                    el.fill("Zagreb")
                    w(1500)
                    opts = page.locator("mat-option, [role='option']").all()
                    if opts:
                        opts[0].click()
                        tz_changed = True
                        print(f"  Set TZ via input")
                    break
            except:
                pass

    ss(page, "tz03_after_tz")

    # Try currency
    print("\n--- Trying currency ---")
    curr_changed = False
    for sel_str in [
        'mat-select[aria-label="Currency"]',
        'mat-select[aria-label*="currency" i]',
        'mat-select[formcontrolname*="currency" i]',
    ]:
        try:
            el = page.locator(sel_str).first
            if el.is_visible(timeout=2000):
                print(f"  Found currency selector: {sel_str}")
                el.click()
                w(2000)
                ss(page, "tz04_curr_dropdown")

                # Type EUR
                page.keyboard.type("EUR")
                w(1000)

                opts = page.locator("mat-option, [role='option']").all()
                print(f"  Options: {len(opts)}")
                for opt in opts[:5]:
                    try:
                        t = opt.inner_text(timeout=300)
                        print(f"    option: {repr(t[:60])}")
                    except:
                        pass

                for opt in opts:
                    try:
                        t = opt.inner_text(timeout=300)
                        if "eur" in t.lower() or "euro" in t.lower():
                            opt.click()
                            curr_changed = True
                            print(f"  Set currency: {t[:60]}")
                            break
                    except:
                        pass
                break
        except Exception as e:
            print(f"  {sel_str}: {e}")

    # Save if anything changed
    if tz_changed or curr_changed:
        for btn_name in ["Save", "Spremi", "Update"]:
            try:
                btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"  Saved ({btn_name})")
                    w(3000)
                    ss(page, "tz05_saved")
                    break
            except:
                pass
    else:
        print("\n  Neither TZ nor currency changed — taking diagnostic screenshot")
        # Get all inputs for diagnosis
        inputs = page.locator("input, mat-select, select").all()
        print(f"  Total form elements: {len(inputs)}")
        for i, el in enumerate(inputs[:20]):
            try:
                tag = el.evaluate("e => e.tagName")
                aria = el.get_attribute("aria-label") or ""
                vis = el.is_visible(timeout=300)
                print(f"  [{i}] {tag} aria='{aria}' visible={vis}")
            except:
                pass

    page.close()

print("\nDone.")
