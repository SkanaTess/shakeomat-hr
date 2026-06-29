import sys, io, time, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"

def ss(page, name):
    path = os.path.join(BASE, f"ga4_{name}.png")
    try:
        page.screenshot(path=path, timeout=60000)
        print(f"  [ss] {name}")
    except Exception as e:
        print(f"  [ss FAIL] {name}: {e}")

def wait(ms=1500):
    time.sleep(ms / 1000)

def click_btn(page, *names):
    for name in names:
        try:
            btn = page.get_by_role("button", name=name).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Clicked: {name}")
                return True
        except:
            pass
    return False

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    page.set_default_timeout(30000)

    # Step 1: Property creation
    print("=== STEP 1: Property creation ===")
    page.goto("https://analytics.google.com/analytics/web/#/a389031276/admin/property/create",
              wait_until="domcontentloaded", timeout=30000)
    wait(4000)
    ss(page, "01_create")

    # Fill property name
    for sel in ['input[type="text"]', 'input[placeholder*="property" i]', '#propertyName']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                el.fill("")
                el.fill("Shake-o-mat")
                print("  Property name: Shake-o-mat")
                break
        except:
            pass

    wait(500)
    ss(page, "02_name_filled")

    # Click Next (timezone/currency can be changed in admin later)
    print("Clicking Next...")
    click_btn(page, "Next", "Continue", "Dalje")
    wait(4000)
    page.wait_for_load_state("domcontentloaded", timeout=15000)
    wait(2000)
    ss(page, "03_business_details")

    # Step 2: Business details
    print("=== STEP 2: Business details ===")
    # Industry dropdown — try clicking the mat-select or similar
    for sel in ['mat-select', '[role="combobox"]', '[aria-label*="industry" i]',
                '[aria-label*="Industry" i]', 'select']:
        try:
            els = page.locator(sel).all()
            for el in els:
                if el.is_visible(timeout=1000):
                    txt = el.inner_text(timeout=1000).lower()
                    if 'industry' in txt or 'other' in txt or 'select' in txt:
                        el.click()
                        wait(1000)
                        # Try to select Health option
                        try:
                            page.get_by_text("Health", exact=False).first.click()
                            print("  Industry: Health (clicked)")
                            wait(500)
                        except:
                            pass
                        break
        except:
            pass

    wait(500)

    # Business size
    for sel in ['[aria-label*="size" i]', '[aria-label*="employees" i]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                el.click()
                wait(800)
                try:
                    page.get_by_text("Small", exact=False).first.click()
                    print("  Size: Small")
                except:
                    pass
                break
        except:
            pass

    wait(500)
    ss(page, "04_business_filled")
    click_btn(page, "Next", "Continue")
    wait(4000)
    page.wait_for_load_state("domcontentloaded", timeout=15000)
    wait(2000)
    ss(page, "05_objectives")

    # Step 3: Business objectives — just click Next/Create
    print("=== STEP 3: Objectives ===")
    # Try to find and click "Get baseline reports" checkbox if needed
    wait(1000)
    # Click Create
    if not click_btn(page, "Create", "Kreiraj", "Finish", "Done"):
        click_btn(page, "Next", "Continue")
    wait(5000)
    page.wait_for_load_state("domcontentloaded", timeout=20000)
    wait(3000)
    ss(page, "06_after_create")
    print("URL:", page.url)

    # Accept terms if present
    print("=== Checking for terms ===")
    wait(2000)
    for btn_text in ["I Accept", "Accept", "Agree", "Prihvacam", "Prihvati", "I agree"]:
        try:
            btn = page.get_by_role("button", name=btn_text).first
            if btn.is_visible(timeout=2000):
                btn.click()
                print(f"  Terms: {btn_text}")
                wait(4000)
                page.wait_for_load_state("domcontentloaded", timeout=15000)
                wait(2000)
                break
        except:
            pass

    ss(page, "07_after_terms")
    print("URL:", page.url)

    # Step 4: Data stream
    print("=== STEP 4: Web data stream ===")
    wait(2000)
    ss(page, "08_stream_type")

    # Click Web
    for label in ["Web", "Website"]:
        try:
            el = page.get_by_text(label, exact=True).first
            if el.is_visible(timeout=2000):
                el.click()
                print(f"  Type: {label}")
                wait(2000)
                break
        except:
            pass

    ss(page, "09_web_selected")

    # URL
    for sel in ['input[placeholder*="example.com"]', 'input[placeholder*="yoursite.com"]',
                'input[type="url"]', 'input[aria-label*="URL" i]',
                'input[aria-label*="website" i]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=2000):
                el.click()
                el.fill("shakeomat.hr")
                print("  URL: shakeomat.hr")
                break
        except:
            pass

    # Stream name
    for sel in ['input[placeholder*="stream name" i]', 'input[placeholder*="My website"]',
                'input[aria-label*="stream name" i]']:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=1500):
                el.click()
                el.fill("Shake-o-mat Web")
                print("  Stream name: Shake-o-mat Web")
                break
        except:
            pass

    wait(800)
    ss(page, "10_stream_filled")

    # Create stream
    click_btn(page, "Create stream", "Create and continue", "Create")
    wait(6000)
    page.wait_for_load_state("domcontentloaded", timeout=20000)
    wait(3000)
    ss(page, "11_stream_created")
    print("URL:", page.url)

    # Extract Measurement ID
    print("=== Looking for Measurement ID ===")
    wait(2000)
    page_text = page.content()
    m = re.search(r'G-[A-Z0-9]{8,12}', page_text)
    measurement_id = m.group(0) if m else None

    if not measurement_id:
        try:
            el = page.locator("text=/G-[A-Z0-9]+/").first
            measurement_id = el.inner_text(timeout=3000).strip()
        except:
            pass

    ss(page, "12_measurement_id")

    if measurement_id:
        print(f"\n=== MEASUREMENT ID: {measurement_id} ===\n")
        with open(os.path.join(BASE, "ga4_measurement_id.txt"), "w") as f:
            f.write(measurement_id)
        print("Saved to ga4_measurement_id.txt")
    else:
        print("WARNING: Measurement ID not found — check ga4_12_measurement_id.png")

    browser.close()
print("Done.")
