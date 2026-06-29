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

    # Step 1: Go to Admin
    print("=== Step 1: Admin page ===")
    page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
    w(3000)
    page.keyboard.press("Escape")
    w(500)

    # Click Admin in left nav
    page.get_by_text("Admin", exact=True).first.click()
    w(4000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "B01_admin")

    # Step 2: Click the dropdown arrow on Create button (small chevron/arrow part)
    print("=== Step 2: Click Create dropdown ===")
    # The Create button is at ~(128, 92). The dropdown arrow is on the right side ~(175, 92)
    # Click the arrow/chevron part of the Create button
    page.mouse.click(175, 92)
    w(2000)
    ss(page, "B02_create_dropdown")

    # Look for Property option in dropdown menu
    txt = page.locator("body").inner_text(timeout=3000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Page text (first 25):")
    for l in lines[:25]:
        print(" ", repr(l[:80]))

    # Find and click "Property" in the dropdown (not the sidebar)
    # The dropdown should appear near the Create button
    # Look for a menu item with "Property" text
    try:
        # Try to find a mat-menu-item or similar with "Property"
        menu_items = page.locator("button[role='menuitem'], mat-menu-item, [role='option']").all()
        print(f"Menu items found: {len(menu_items)}")
        for item in menu_items:
            try:
                t = item.inner_text(timeout=500)
                print(f"  Menu item: {repr(t[:50])}")
                if 'property' in t.lower():
                    item.click()
                    print("  Clicked Property menu item")
                    w(3000)
                    break
            except:
                pass
    except Exception as e:
        print(f"Menu items error: {e}")

    ss(page, "B03_after_property_click")
    print("URL:", page.url)
    w(2000)

    # Check if wizard opened
    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    has_wizard = any("create a property" in l.lower() or "property name" in l.lower() for l in lines)
    print(f"Wizard visible: {has_wizard}")
    print("First 15 lines:")
    for l in lines[:15]:
        print(" ", repr(l[:80]))

    if has_wizard:
        print("=== Filling wizard ===")
        # Find property name input
        page.keyboard.press("Escape")  # Make sure no overlay
        w(300)

        for sel in ['input[type="text"]', 'input[placeholder*="property" i]']:
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
        ss(page, "B04_name_filled")

        # Click Next
        for btn in ["Next", "Continue"]:
            try:
                b = page.get_by_role("button", name=btn).first
                if b.is_visible(timeout=2000):
                    b.click()
                    print(f"  Next: {btn}")
                    w(4000)
                    break
            except:
                pass

        ss(page, "B05_step2")

        # Step 2: business — just click Next
        for btn in ["Next", "Continue"]:
            try:
                b = page.get_by_role("button", name=btn).first
                if b.is_visible(timeout=2000):
                    b.click()
                    print(f"  Step2 Next: {btn}")
                    w(4000)
                    break
            except:
                pass

        ss(page, "B06_step3")

        # Step 3: objectives — click Create
        for btn in ["Create", "Kreiraj"]:
            try:
                b = page.get_by_role("button", name=btn).first
                if b.is_visible(timeout=2000):
                    b.click()
                    print(f"  Create: {btn}")
                    w(6000)
                    break
            except:
                pass

        ss(page, "B07_after_create")
        print("URL:", page.url)

        # Accept terms
        for btn in ["I Accept", "Accept", "Agree", "I agree"]:
            try:
                b = page.get_by_role("button", name=re.compile(btn, re.I)).first
                if b.is_visible(timeout=2000):
                    b.click()
                    print(f"  Terms: {btn}")
                    w(4000)
                    break
            except:
                pass

        ss(page, "B08_stream_page")
        print("URL:", page.url)
        w(2000)

        # Data stream — click Web
        for label in ["Web", "Website"]:
            try:
                el = page.get_by_text(label, exact=True).first
                if el.is_visible(timeout=2000):
                    el.click()
                    print(f"  Stream type: {label}")
                    w(2000)
                    break
            except:
                pass

        # URL field
        for sel in ['input[placeholder*="example.com"]', 'input[placeholder*="yoursite"]',
                    'input[type="url"]']:
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

        # Stream name
        for sel in ['input[placeholder*="stream name" i]', 'input[placeholder*="My website"]']:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=1500):
                    el.click()
                    w(200)
                    el.fill("Shake-o-mat Web")
                    print("  Stream name: Shake-o-mat Web")
                    break
            except:
                pass

        w(800)
        ss(page, "B09_stream_filled")

        # Create stream
        for btn in ["Create stream", "Create and continue", "Create"]:
            try:
                b = page.get_by_role("button", name=btn).first
                if b.is_visible(timeout=2000):
                    b.click()
                    print(f"  Stream create: {btn}")
                    w(6000)
                    break
            except:
                pass

        ss(page, "B10_stream_done")
        print("URL:", page.url)

        # Extract Measurement ID
        w(2000)
        content = page.content()
        ids = re.findall(r'G-[A-Z0-9]{8,12}', content)
        txt_body = page.locator("body").inner_text(timeout=5000)
        ids_text = re.findall(r'G-[A-Z0-9]{8,12}', txt_body)
        all_ids = set(ids + ids_text)

        # Exclude known ekohvok ID
        all_ids.discard("G-WDB5MJRKCQ")
        print(f"G- IDs found (excl. ekohvok): {all_ids}")

        ss(page, "B11_measurement")

        if all_ids:
            mid = list(all_ids)[0]
            print(f"\n{'='*50}\nMEASUREMENT ID: {mid}\n{'='*50}\n")
            with open(f"{BASE}\\ga4_measurement_id.txt", "w") as f:
                f.write(mid)
    else:
        print("WARNING: Wizard not found after property click")
        ss(page, "B_debug")

    page.close()
print("Done.")
