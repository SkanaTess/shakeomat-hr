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

    # Navigate back to the wizard — it should be on the stream setup dialog
    # The URL was: #/a389031276p530166245/admin/property/create
    # But we need the NEW property's URL — let's navigate there
    page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
    w(3000)
    page.keyboard.press("Escape")
    w(500)

    # Navigate to Admin
    page.get_by_text("Admin", exact=True).first.click()
    w(4000)
    ss(page, "D01_admin")

    # Click Create dropdown arrow
    page.mouse.click(175, 92)
    w(2000)

    # Click Property in dropdown
    for item in page.locator("button[role='menuitem']").all():
        try:
            if 'property' in item.inner_text(timeout=500).lower():
                item.click()
                print("Clicked Property")
                w(4000)
                break
        except:
            pass

    ss(page, "D02_wizard")
    print("URL:", page.url)

    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("First 10 lines:", lines[:10])

    # === STEP 1: Property name ===
    if any("property name" in l.lower() for l in lines):
        for sel in ['input[type="text"]']:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    el.click()
                    el.fill("Shake-o-mat")
                    print("  Property name: Shake-o-mat")
                    break
            except:
                pass
        page.get_by_role("button", name="Next").first.click()
        w(4000)
        ss(page, "D03_step2")

    # === STEP 2: Business ===
    # Select industry
    try:
        page.get_by_text("Select one").first.click()
        w(1500)
        for opt in ["Health", "Sports", "Shopping", "Other"]:
            try:
                o = page.get_by_role("option", name=re.compile(opt, re.I)).first
                if o.is_visible(timeout=1000):
                    o.click()
                    print(f"  Industry: {opt}")
                    break
            except:
                pass
    except:
        pass

    try:
        page.get_by_text("Small").first.click()
        print("  Size: Small")
    except:
        pass

    w(500)
    page.get_by_role("button", name="Next").first.click()
    w(4000)
    ss(page, "D04_step3")

    # === STEP 3: Objectives — click Create ===
    try:
        checkboxes = page.locator("mat-checkbox, input[type='checkbox']").all()
        if checkboxes:
            checkboxes[0].click()
            w(300)
    except:
        pass

    page.get_by_role("button", name="Create").first.click()
    print("  Clicked Create")
    w(7000)
    ss(page, "D05_after_create")
    print("URL:", page.url)

    # Accept terms if present
    for btn_name in ["I Accept", "Accept", "I agree", "Agree"]:
        try:
            btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Terms: {btn_name}")
                w(5000)
                break
        except:
            pass

    ss(page, "D06_stream_choice")
    print("URL:", page.url)
    w(3000)

    # === STEP 4: Choose platform ===
    # Click Web card
    try:
        web_card = page.locator("text='Web'").first
        if web_card.is_visible(timeout=3000):
            web_card.click()
            print("  Clicked Web")
            w(3000)
    except Exception as e:
        print(f"  Web click: {e}")

    ss(page, "D07_stream_form")
    w(1000)

    # === Fill stream form ===
    # Get ALL input elements and print them
    inputs = page.locator("input").all()
    print(f"  Inputs found: {len(inputs)}")
    for i, inp in enumerate(inputs):
        try:
            ph = inp.get_attribute("placeholder") or ""
            tp = inp.get_attribute("type") or ""
            vis = inp.is_visible(timeout=500)
            print(f"    [{i}] type={tp} placeholder={ph!r} visible={vis}")
        except:
            pass

    # Fill URL input (should be the first visible text input, after the https:// dropdown)
    # The placeholder should be "www.mywebsite.com"
    filled_url = False
    for inp in inputs:
        try:
            ph = inp.get_attribute("placeholder") or ""
            if "mywebsite" in ph or "website.com" in ph or "example.com" in ph or "yoursite" in ph:
                inp.click()
                w(200)
                inp.fill("shakeomat.hr")
                print("  URL filled: shakeomat.hr")
                filled_url = True
                break
        except:
            pass

    if not filled_url:
        # Try by position — url input is first visible text input in the modal
        for inp in inputs:
            try:
                if inp.is_visible(timeout=500):
                    tp = inp.get_attribute("type") or "text"
                    if tp in ["text", "url", ""]:
                        inp.click()
                        w(200)
                        inp.fill("shakeomat.hr")
                        print("  URL filled by position")
                        filled_url = True
                        break
            except:
                pass

    # Fill stream name — second visible input
    filled_name = False
    count = 0
    for inp in inputs:
        try:
            if inp.is_visible(timeout=500):
                tp = inp.get_attribute("type") or "text"
                ph = inp.get_attribute("placeholder") or ""
                if tp in ["text", ""] and "mywebsite" not in ph and "website.com" not in ph:
                    count += 1
                    if count == 2 or "stream" in ph.lower() or "website" in ph.lower():
                        inp.click()
                        w(200)
                        inp.fill("Shake-o-mat Web")
                        print("  Stream name filled")
                        filled_name = True
                        break
        except:
            pass

    w(500)
    ss(page, "D08_stream_filled")

    # Click Create & continue
    for btn_name in ["Create & continue", "Create stream", "Create and continue", "Create"]:
        try:
            btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Clicked: {btn_name}")
                w(7000)
                break
        except:
            pass

    ss(page, "D09_stream_created")
    print("URL:", page.url)
    w(3000)

    # Extract Measurement ID from visible text
    txt_body = page.locator("body").inner_text(timeout=5000)
    ids_visible = re.findall(r'G-[A-Z0-9]{8,12}', txt_body)
    ids_html = re.findall(r'G-[A-Z0-9]{8,12}', page.content())

    exclude = {"G-WDB5MJRKCQ"}  # ekohvok

    # Look for ID that appears near "MEASUREMENT ID" text
    mid_match = re.search(r'MEASUREMENT ID[\s\S]{0,50}(G-[A-Z0-9]{8,12})', txt_body)
    if mid_match:
        measurement_id = mid_match.group(1)
        print(f"  Found via MEASUREMENT ID label: {measurement_id}")
    else:
        # Use first visible G- ID that's not ekohvok
        measurement_id = next((i for i in ids_visible if i not in exclude), None)
        if not measurement_id:
            measurement_id = next((i for i in ids_html if i not in exclude), None)

    ss(page, "D10_measurement")

    if measurement_id:
        print(f"\n{'='*50}\nMEASUREMENT ID: {measurement_id}\n{'='*50}")
        with open(f"{BASE}\\ga4_measurement_id.txt", "w") as f:
            f.write(measurement_id)
        print("Saved.")
    else:
        print("WARNING: No Measurement ID found — check D09/D10 screenshots")
        print("Visible IDs:", ids_visible)

    page.close()
print("Done.")
