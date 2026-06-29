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

    # The wizard should be at step 2. First check current state.
    page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
    w(3000)
    page.keyboard.press("Escape")
    w(500)

    # Navigate to the property create wizard again via Create > Property
    page.get_by_text("Admin", exact=True).first.click()
    w(4000)
    page.keyboard.press("Escape")
    w(500)

    # Click the dropdown arrow of Create button
    page.mouse.click(175, 92)
    w(2000)

    # Click Property menu item
    menu_items = page.locator("button[role='menuitem'], mat-menu-item").all()
    for item in menu_items:
        try:
            if 'property' in item.inner_text(timeout=500).lower():
                item.click()
                print("Clicked Property")
                w(4000)
                break
        except:
            pass

    ss(page, "C01_wizard_state")
    print("URL:", page.url)

    # Check which step we're on
    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Wizard state:", [l for l in lines[:5]])

    # If on step 1 (property creation), fill name and go Next
    if any("property name" in l.lower() or "create a property" in l.lower() for l in lines):
        print("=== On Step 1 — filling property name ===")
        for sel in ['input[type="text"]']:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    w(200)
                    el.fill("Shake-o-mat")
                    print("  Property name: Shake-o-mat")
                    break
            except:
                pass

        w(500)
        page.get_by_role("button", name="Next").first.click()
        w(4000)
        ss(page, "C02_step2")

    # Step 2: Business details — Industry + Size required
    print("=== Step 2: Business details ===")
    w(1000)
    ss(page, "C03_business")

    # Click Industry dropdown "Select one"
    try:
        industry_btn = page.get_by_text("Select one").first
        if industry_btn.is_visible(timeout=2000):
            industry_btn.click()
            w(1500)
            ss(page, "C04_industry_open")

            # Look for Health/Sports options in dropdown
            for opt in ["Health", "Sports", "Shopping", "Food", "Travel", "Education", "Games", "Finance", "Other"]:
                try:
                    option = page.get_by_role("option", name=re.compile(opt, re.I)).first
                    if option.is_visible(timeout=1000):
                        option.click()
                        print(f"  Industry: {opt}")
                        w(500)
                        break
                except:
                    pass
    except Exception as e:
        print(f"  Industry error: {e}")

    # Click "Small" radio button
    try:
        small_btn = page.get_by_text("Small").first
        if small_btn.is_visible(timeout=2000):
            small_btn.click()
            print("  Size: Small")
            w(500)
    except Exception as e:
        print(f"  Size error: {e}")

    ss(page, "C05_business_filled")

    # Click Next
    try:
        next_btn = page.get_by_role("button", name="Next").first
        if next_btn.is_visible(timeout=2000):
            next_btn.click()
            print("  Next clicked")
            w(4000)
    except Exception as e:
        print(f"  Next error: {e}")

    ss(page, "C06_step3_objectives")
    print("URL:", page.url)

    # Step 3: Business objectives — select one or just Create
    print("=== Step 3: Objectives ===")
    w(1000)

    # Try to check a checkbox to enable Create button
    try:
        checkboxes = page.locator("mat-checkbox, input[type='checkbox']").all()
        print(f"  Checkboxes: {len(checkboxes)}")
        if checkboxes:
            checkboxes[0].click()
            w(500)
            print("  Checked first objective")
    except:
        pass

    # Click Create
    created = False
    for btn_name in ["Create", "Kreiraj"]:
        try:
            btn = page.get_by_role("button", name=btn_name).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Clicked: {btn_name}")
                w(6000)
                created = True
                break
        except:
            pass

    ss(page, "C07_after_create")
    print("URL:", page.url)

    # Accept Terms if visible
    for btn_name in ["I Accept", "Accept", "I agree", "Agree"]:
        try:
            btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
            if btn.is_visible(timeout=3000):
                btn.click()
                print(f"  Terms: {btn_name}")
                w(5000)
                break
        except:
            pass

    ss(page, "C08_stream_page")
    print("URL:", page.url)
    w(3000)

    # Step 4: Data collection — Web stream
    print("=== Step 4: Data stream ===")

    # Click Web
    for label in ["Web"]:
        try:
            el = page.get_by_text(label, exact=True).first
            if el.is_visible(timeout=3000):
                el.click()
                print(f"  Type: {label}")
                w(2000)
                break
        except:
            pass

    ss(page, "C09_web_selected")

    # Fill URL
    for sel in ['input[placeholder*="example.com"]', 'input[placeholder*="yoursite"]', 'input[type="url"]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                w(200)
                el.fill("shakeomat.hr")
                print("  URL: shakeomat.hr")
                break
        except:
            pass

    # Fill stream name
    for sel in ['input[placeholder*="stream name" i]', 'input[placeholder*="My website"]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                el.click()
                w(200)
                el.fill("Shake-o-mat Web")
                print("  Stream: Shake-o-mat Web")
                break
        except:
            pass

    w(500)
    ss(page, "C10_stream_filled")

    # Create stream
    for btn_name in ["Create stream", "Create and continue", "Create"]:
        try:
            btn = page.get_by_role("button", name=btn_name).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Stream: {btn_name}")
                w(7000)
                break
        except:
            pass

    ss(page, "C11_stream_done")
    print("URL:", page.url)

    # Extract Measurement ID from page
    w(3000)
    content = page.content()
    txt_body = page.locator("body").inner_text(timeout=5000)

    # Find all G- IDs
    ids_html = set(re.findall(r'G-[A-Z0-9]{8,12}', content))
    ids_text = set(re.findall(r'G-[A-Z0-9]{8,12}', txt_body))

    # Known wrong IDs
    exclude = {"G-WDB5MJRKCQ"}  # ekohvok
    ids_html -= exclude
    ids_text -= exclude

    print(f"G- IDs in HTML: {ids_html}")
    print(f"G- IDs visible: {ids_text}")

    # Prefer visible text IDs (more likely to be the current stream)
    measurement_id = list(ids_text)[0] if ids_text else (list(ids_html)[0] if ids_html else None)

    ss(page, "C12_measurement_id")

    if measurement_id:
        print(f"\n{'='*50}\nMEASUREMENT ID: {measurement_id}\n{'='*50}")
        with open(f"{BASE}\\ga4_measurement_id.txt", "w") as f:
            f.write(measurement_id)
        print("Saved to ga4_measurement_id.txt")
    else:
        print("WARNING: No Measurement ID found — check C12 screenshot")

    page.close()
print("Done.")
