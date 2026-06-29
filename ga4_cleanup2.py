import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"
ACCOUNT_ID = "389031276"
CORRECT_PROP = "533443439"
TO_DELETE = ["533480894", "532393510"]

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

    # ── Delete duplicates ─────────────────────────────────────────────────────
    for prop_id in TO_DELETE:
        print(f"\n=== Moving {prop_id} to Trash ===")
        page = ctx.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})
        page.set_default_timeout(30000)

        page.goto(
            f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{prop_id}/admin/property/settings",
            wait_until="domcontentloaded", timeout=30000
        )
        w(5000)
        page.keyboard.press("Escape")
        w(300)

        # Scroll down to find "Move to Trash Can" button
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        w(1000)

        # Click "Move to Trash Can"
        try:
            trash_btn = page.get_by_text("Move to Trash Can").first
            if trash_btn.is_visible(timeout=3000):
                trash_btn.click()
                print("  Clicked 'Move to Trash Can'")
                w(3000)
                ss(page, f"trash_{prop_id}_dialog")

                # Confirm dialog - look for a confirm button or input
                txt = page.locator("body").inner_text(timeout=3000)
                print("  Dialog text:", [l.strip() for l in txt.split("\n") if l.strip()][:15])

                # There's usually a confirmation dialog with "Move to Trash" button
                for btn_name in ["Move to Trash", "Confirm", "Delete", "OK", "Yes"]:
                    try:
                        confirm_btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
                        if confirm_btn.is_visible(timeout=2000):
                            confirm_btn.click()
                            print(f"  Confirmed: {btn_name}")
                            w(3000)
                            break
                    except:
                        pass

                ss(page, f"trash_{prop_id}_after")
            else:
                print("  'Move to Trash Can' not visible")
        except Exception as e:
            print(f"  Trash click error: {e}")

        page.close()

    # ── Fix timezone/currency for correct property ────────────────────────────
    print(f"\n=== Fixing property {CORRECT_PROP} settings ===")
    page = ctx.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    page.set_default_timeout(30000)

    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{CORRECT_PROP}/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(300)
    ss(page, "settings_page")

    txt = page.locator("body").inner_text(timeout=5000)
    print("Settings page first 40 lines:")
    for l in [x.strip() for x in txt.split("\n") if x.strip()][:40]:
        print(" ", repr(l[:80]))

    # Click Property details link
    try:
        prop_details = page.get_by_text("Property details").first
        if prop_details.is_visible(timeout=3000):
            prop_details.click()
            w(4000)
            page.keyboard.press("Escape")
            w(300)
            ss(page, "prop_details")
            txt2 = page.locator("body").inner_text(timeout=5000)
            print("Property details page:")
            for l in [x.strip() for x in txt2.split("\n") if x.strip()][:30]:
                print(" ", repr(l[:80]))

            # Look for timezone dropdown
            # In GA4 property details, there's timezone and currency selectors
            # These are usually Material Design select components

            # Find timezone selector and change to Croatia
            # Try various selectors for the timezone dropdown
            tz_changed = False
            for sel in ['[aria-label*="time zone" i]', 'mat-select[aria-label*="time" i]',
                        '[formcontrolname*="timezone" i]', '[formcontrolname*="timeZone" i]']:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=2000):
                        el.click()
                        w(1500)
                        ss(page, "tz_dropdown")
                        # Look for Croatia option
                        for tz_name in ["Croatia", "(GMT+01:00) Central European", "Europe/Zagreb"]:
                            try:
                                opt = page.get_by_text(tz_name, exact=False).first
                                if opt.is_visible(timeout=1000):
                                    opt.click()
                                    print(f"  Timezone set: {tz_name}")
                                    tz_changed = True
                                    w(500)
                                    break
                            except:
                                pass
                        if tz_changed:
                            break
                        page.keyboard.press("Escape")
                except:
                    pass

            if not tz_changed:
                print("  Timezone not changed")

            # Find currency selector and change to EUR
            curr_changed = False
            for sel in ['[aria-label*="currency" i]', 'mat-select[aria-label*="currency" i]',
                        '[formcontrolname*="currency" i]']:
                try:
                    el = page.locator(sel).first
                    if el.is_visible(timeout=2000):
                        el.click()
                        w(1500)
                        # Look for EUR option
                        for curr_name in ["Euro (EUR)", "EUR", "Euro"]:
                            try:
                                opt = page.get_by_text(curr_name, exact=False).first
                                if opt.is_visible(timeout=1000):
                                    opt.click()
                                    print(f"  Currency set: {curr_name}")
                                    curr_changed = True
                                    w(500)
                                    break
                            except:
                                pass
                        if curr_changed:
                            break
                        page.keyboard.press("Escape")
                except:
                    pass

            if not curr_changed:
                print("  Currency not changed")

            # Save changes
            if tz_changed or curr_changed:
                for btn_name in ["Save", "Spremi", "Update"]:
                    try:
                        save_btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
                        if save_btn.is_visible(timeout=2000):
                            save_btn.click()
                            print(f"  Saved: {btn_name}")
                            w(3000)
                            break
                    except:
                        pass
                ss(page, "prop_saved")

    except Exception as e:
        print(f"  Property details error: {e}")

    # Verify correct measurement ID by clicking on stream
    print(f"\n=== Verifying stream measurement ID ===")
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{CORRECT_PROP}/admin/streams",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(300)
    ss(page, "final_streams")

    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Streams page:")
    for l in lines[:20]:
        print(" ", repr(l[:80]))

    # Click on the stream to see measurement ID
    try:
        stream_row = page.locator("table tr:nth-child(2), [role='row']:nth-child(2)").first
        if not stream_row.is_visible(timeout=1000):
            stream_row = page.get_by_text("Shake-o-mat Web").first
        stream_row.click()
        w(4000)
        ss(page, "final_stream_detail")

        content = page.content()
        txt3 = page.locator("body").inner_text(timeout=5000)
        mid_match = re.search(r'MEASUREMENT ID[\s\S]{0,100}(G-[A-Z0-9]{8,12})', txt3)
        if mid_match:
            print(f"  Confirmed Measurement ID: {mid_match.group(1)}")
        g_vis = re.findall(r'G-[A-Z0-9]{8,12}', txt3)
        print(f"  G- IDs visible: {set(g_vis)}")
    except Exception as e:
        print(f"  Stream click error: {e}")

    page.close()

print("\nDone.")
