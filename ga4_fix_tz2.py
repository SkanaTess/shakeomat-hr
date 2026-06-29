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

def dump_selects(page):
    selects = page.locator("mat-select").all()
    print(f"  mat-select count: {len(selects)}")
    for i, s in enumerate(selects[:10]):
        try:
            vis = s.is_visible(timeout=300)
            aria = s.get_attribute("aria-label") or s.get_attribute("aria-labelledby") or ""
            txt = s.inner_text(timeout=300)[:40] if vis else "(hidden)"
            print(f"    [{i}] vis={vis} aria='{aria}' text='{txt}'")
        except Exception as e:
            print(f"    [{i}] err: {e}")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    page.set_default_timeout(30000)

    # Go to Admin page with correct property
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{CORRECT_PROP}/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(6000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "tz2_01_admin")

    # Check current URL and content
    print("URL hash:", page.evaluate("() => window.location.hash"))

    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Admin page (first 25):")
    for l in lines[:25]:
        print(" ", repr(l[:100]))

    # Find and click "Property details" in the left sidebar
    print("\n--- Looking for Property details link ---")
    found = False
    for selector in [
        'text="Property details"',
        'a:has-text("Property details")',
        '[href*="property/details"]',
        'span:has-text("Property details")',
    ]:
        try:
            el = page.locator(selector).first
            if el.is_visible(timeout=2000):
                print(f"  Found via: {selector}")
                el.click()
                w(5000)
                page.keyboard.press("Escape")
                w(500)
                ss(page, "tz2_02_prop_details")
                found = True
                break
        except Exception as e:
            print(f"  {selector}: {e}")

    if not found:
        print("  Property details not found via selectors — clicking by text in sidebar")
        # Try scrolling admin sidebar and clicking
        page.evaluate("""() => {
            const links = Array.from(document.querySelectorAll('a, button, [role="link"]'));
            const target = links.find(el => el.textContent && el.textContent.includes('Property details'));
            if (target) { target.scrollIntoView(); target.click(); }
        }""")
        w(4000)
        ss(page, "tz2_02b_prop_details")

    # Now check what's on screen
    txt2 = page.locator("body").inner_text(timeout=5000)
    lines2 = [l.strip() for l in txt2.split("\n") if l.strip()]
    print("\nAfter clicking Property details (first 30):")
    for l in lines2[:30]:
        print(" ", repr(l[:100]))

    print("\n--- mat-select elements ---")
    dump_selects(page)

    # Wait longer for Angular to render the form
    print("  Waiting 5 more seconds for form to load...")
    w(5000)
    ss(page, "tz2_03_form_loaded")

    txt3 = page.locator("body").inner_text(timeout=5000)
    lines3 = [l.strip() for l in txt3.split("\n") if l.strip()]
    print("After extra wait (first 40):")
    for l in lines3[:40]:
        print(" ", repr(l[:100]))

    dump_selects(page)

    # Try to interact with mat-selects (by index, since labels may vary)
    selects = page.locator("mat-select").all()
    visible_selects = []
    for i, s in enumerate(selects):
        try:
            if s.is_visible(timeout=300):
                visible_selects.append((i, s))
        except:
            pass

    print(f"\n  Visible mat-selects: {len(visible_selects)}")

    # Try each visible select — look for timezone (usually has "UTC" or timezone names)
    tz_changed = False
    curr_changed = False

    for idx, sel in visible_selects:
        try:
            current_text = sel.inner_text(timeout=500).strip()
            print(f"  Select[{idx}] current text: '{current_text[:60]}'")

            # Check if it looks like timezone (contains UTC, GMT, or is empty)
            if any(x in current_text for x in ["UTC", "GMT", "America", "Pacific", "Eastern", "London", "Paris"]):
                print(f"  -> This looks like timezone select")
                sel.click()
                w(2000)
                ss(page, f"tz2_04_tz_dropdown_{idx}")

                # Type to search
                page.keyboard.type("Zagreb")
                w(1500)

                opts = page.locator("mat-option").all()
                print(f"  Options with 'Zagreb': {len(opts)}")
                for opt in opts[:5]:
                    try:
                        t = opt.inner_text(timeout=300)
                        print(f"    '{t[:60]}'")
                    except:
                        pass

                if opts:
                    opts[0].click()
                    tz_changed = True
                    print("  TZ set to Zagreb!")
                    w(500)
                else:
                    page.keyboard.press("Escape")
                    w(500)

            elif any(x in current_text for x in ["USD", "Dollar", "US Dollar", "$"]):
                print(f"  -> This looks like currency select")
                sel.click()
                w(2000)
                ss(page, f"tz2_05_curr_dropdown_{idx}")

                page.keyboard.type("Euro")
                w(1500)

                opts = page.locator("mat-option").all()
                print(f"  Options with 'Euro': {len(opts)}")
                for opt in opts:
                    try:
                        t = opt.inner_text(timeout=300)
                        if "eur" in t.lower():
                            opt.click()
                            curr_changed = True
                            print(f"  Currency set: '{t[:60]}'")
                            w(500)
                            break
                    except:
                        pass
                if not curr_changed:
                    page.keyboard.press("Escape")
        except Exception as e:
            print(f"  Select[{idx}] error: {e}")

    # Save
    if tz_changed or curr_changed:
        print("\n  Saving changes...")
        for btn_name in ["Save", "Update"]:
            try:
                btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"  Clicked {btn_name}")
                    w(3000)
                    ss(page, "tz2_06_saved")
                    break
            except:
                pass
    else:
        print("\n  Nothing changed. Diagnostic info:")
        # Show all text on page that might indicate current tz/currency
        for keyword in ["time zone", "timezone", "currency", "Croatia", "UTC", "USD", "EUR"]:
            matches = [l for l in lines3 if keyword.lower() in l.lower()]
            if matches:
                print(f"  Lines with '{keyword}': {matches[:3]}")

    page.close()

print("\nDone.")
