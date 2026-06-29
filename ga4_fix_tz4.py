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

    # Navigate to admin → Property details
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{CORRECT_PROP}/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(6000)
    page.keyboard.press("Escape")
    w(500)
    page.get_by_text("Property details").first.click()
    w(6000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "tz4_01_form")

    # === STEP 1: Click "United States" country dropdown ===
    print("--- Step 1: Click country selector (United States) ---")
    country_el = page.get_by_text("United States").first
    country_el.click()
    w(2000)
    ss(page, "tz4_02_country_dropdown")

    # List all visible options
    opts = page.locator("[role='option'], mat-option, li").all()
    print(f"  Options found: {len(opts)}")
    for opt in opts[:15]:
        try:
            t = opt.inner_text(timeout=300).strip()
            if t:
                print(f"    '{t[:60]}'")
        except:
            pass

    # Click Croatia
    croatia_clicked = False
    for opt in opts:
        try:
            t = opt.inner_text(timeout=300).strip()
            if "croatia" in t.lower():
                opt.click()
                croatia_clicked = True
                print(f"  Clicked: '{t}'")
                w(2000)
                ss(page, "tz4_03_croatia_selected")
                break
        except:
            pass

    if not croatia_clicked:
        # Try by text directly
        try:
            page.get_by_role("option", name=re.compile("croatia", re.I)).first.click()
            croatia_clicked = True
            print("  Clicked Croatia via role=option")
            w(2000)
        except:
            pass

    if not croatia_clicked:
        print("  Croatia not found in options — trying to type in search")
        page.keyboard.type("Croatia")
        w(1500)
        opts2 = page.locator("[role='option'], mat-option").all()
        for opt in opts2:
            try:
                t = opt.inner_text(timeout=300).strip()
                if "croatia" in t.lower():
                    opt.click()
                    croatia_clicked = True
                    print(f"  Clicked: '{t}'")
                    w(2000)
                    break
            except:
                pass

    if not croatia_clicked:
        page.keyboard.press("Escape")
        print("  FAILED to select Croatia")

    # === STEP 2: Now city/timezone dropdown should appear ===
    if croatia_clicked:
        print("\n--- Step 2: Select city/timezone ---")
        w(2000)
        ss(page, "tz4_04_after_country")

        # Check what options are now shown for city
        txt = page.locator("body").inner_text(timeout=3000)
        tz_lines = [l.strip() for l in txt.split("\n") if l.strip() and ("gmt" in l.lower() or "zagreb" in l.lower() or "croatia" in l.lower())]
        print(f"  Timezone lines visible: {tz_lines[:10]}")

        # Look for city dropdown — might now show "(GMT+01:00) Zagreb Time" or similar
        city_dropdown_texts = ["(GMT", "Zagreb", "Central European"]
        city_el = None
        for text in city_dropdown_texts:
            try:
                el = page.get_by_text(text, exact=False).first
                if el.is_visible(timeout=1000):
                    box = el.bounding_box()
                    print(f"  City element '{text}': {box}")
                    el.click()
                    w(2000)
                    ss(page, "tz4_05_city_dropdown")
                    city_el = el
                    break
            except:
                pass

        if city_el:
            # Look for Zagreb option
            opts3 = page.locator("[role='option'], mat-option, li").all()
            print(f"  City options: {len(opts3)}")
            for opt in opts3[:10]:
                try:
                    t = opt.inner_text(timeout=300).strip()
                    if t:
                        print(f"    '{t[:60]}'")
                except:
                    pass

            # Click Zagreb (or first option — Croatia only has Zagreb)
            for opt in opts3:
                try:
                    t = opt.inner_text(timeout=300).strip()
                    if "zagreb" in t.lower() or "gmt+01" in t.lower() or "gmt+02" in t.lower():
                        opt.click()
                        print(f"  City selected: '{t}'")
                        w(500)
                        break
                except:
                    pass

    ss(page, "tz4_06_after_tz")

    # === STEP 3: Currency — click current currency and select EUR ===
    print("\n--- Step 3: Currency ---")
    txt = page.locator("body").inner_text(timeout=3000)
    curr_lines = [l.strip() for l in txt.split("\n") if "usd" in l.lower() or "dollar" in l.lower() or "currency" in l.lower()]
    print(f"  Currency visible: {curr_lines[:5]}")

    curr_changed = False
    for curr_text in ["US Dollar", "USD", "Dollar"]:
        try:
            el = page.get_by_text(curr_text, exact=False).first
            if el.is_visible(timeout=1500):
                print(f"  Clicking currency: '{curr_text}'")
                el.click()
                w(2000)
                ss(page, "tz4_07_curr_dropdown")

                opts = page.locator("[role='option'], mat-option").all()
                print(f"  Currency options: {len(opts)}")
                for opt in opts[:5]:
                    try:
                        print(f"    '{opt.inner_text(timeout=300).strip()[:60]}'")
                    except:
                        pass

                for opt in opts:
                    try:
                        t = opt.inner_text(timeout=300).strip()
                        if "eur" in t.lower() or "euro" in t.lower():
                            opt.click()
                            curr_changed = True
                            print(f"  Currency set: '{t}'")
                            w(500)
                            break
                    except:
                        pass

                if not curr_changed:
                    # Type to filter
                    page.keyboard.type("Euro")
                    w(1500)
                    opts2 = page.locator("[role='option'], mat-option").all()
                    for opt in opts2:
                        try:
                            t = opt.inner_text(timeout=300).strip()
                            if "eur" in t.lower():
                                opt.click()
                                curr_changed = True
                                print(f"  Currency set (typed): '{t}'")
                                w(500)
                                break
                        except:
                            pass
                break
        except:
            pass

    ss(page, "tz4_08_after_curr")

    # === STEP 4: Save ===
    print("\n--- Step 4: Save ---")
    for btn_name in ["Save", "Update", "Spremi"]:
        try:
            btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Saved via '{btn_name}'!")
                w(4000)
                ss(page, "tz4_09_saved")
                break
        except:
            pass

    page.close()

print("\nDone.")
