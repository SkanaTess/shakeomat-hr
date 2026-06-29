import sys, io, time, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"

def ss(page, name):
    try:
        page.screenshot(path=f"{BASE}\\ga4_{name}.png", timeout=45000)
        print(f"  [ss] {name}")
    except Exception as e:
        print(f"  [ss FAIL] {name}: {e}")

def w(ms=2000):
    time.sleep(ms / 1000)

def escape(page):
    page.keyboard.press("Escape")
    w(500)

def safe_fill(page, selector, value, label=""):
    """Click, escape any overlay, then fill."""
    for sel in (selector if isinstance(selector, list) else [selector]):
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                el.click()
                w(300)
                el.fill(value)
                print(f"  Filled {label or sel}: {value}")
                return True
        except:
            pass
    print(f"  WARNING: Could not fill {label}")
    return False

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]
    page = ctx.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    page.set_default_timeout(30000)

    # ── Navigate to GA4 Create property wizard ────────────────────────────────
    print("=== Navigating to Create property ===")
    page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
    w(4000)
    escape(page)  # Close any open overlay

    # Navigate to Admin
    try:
        page.get_by_role("link", name="Admin").click()
    except:
        page.get_by_text("Admin").first.click()
    w(3000)
    escape(page)
    ss(page, "A01_admin")
    print("URL after Admin click:", page.url)

    # Click Create property button (it's in the admin page, Property column)
    # In GA4 admin, there's a "+ Create" button and a property column
    try:
        # First click the blue "+ Create" button
        create_btn = page.locator("button:has-text('Create'), [aria-label*='Create']").first
        if create_btn.is_visible(timeout=3000):
            create_btn.click()
            w(1500)
            escape(page)
            # Look for "Property" option in dropdown
            try:
                page.get_by_text("Property", exact=True).first.click()
                print("  Clicked Property in Create menu")
                w(3000)
            except:
                pass
    except Exception as e:
        print("  Create btn error:", e)

    ss(page, "A02_after_create_click")
    print("URL:", page.url)

    # If we're not on the property creation page, try direct URL
    if "property/create" not in page.url and "propertyCreate" not in page.url:
        print("  Navigating directly to property create...")
        # Press Escape first to clear any state
        escape(page)
        # Use the admin URL
        page.goto(
            "https://analytics.google.com/analytics/web/#/a389031276/admin/property/create",
            wait_until="domcontentloaded", timeout=30000
        )
        w(4000)
        escape(page)
        ss(page, "A03_direct_nav")
        print("URL:", page.url)

    # ── Check what's on screen ────────────────────────────────────────────────
    w(2000)
    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Current page (first 20 lines):")
    for l in lines[:20]:
        print(" ", repr(l[:80]))

    # If property creation form is visible
    has_prop_name = any("property name" in l.lower() or "create a property" in l.lower() for l in lines)
    print(f"  Property name form visible: {has_prop_name}")

    if has_prop_name:
        # ── Fill property name ────────────────────────────────────────────────
        print("=== Filling property details ===")
        escape(page)  # Ensure no overlays

        # Click on property name input - be very specific
        for sel in ['input[type="text"]', 'input[placeholder*="property" i]',
                    'input[aria-label*="property name" i]', '#propertyName']:
            try:
                el = page.locator(sel).first
                if el.is_visible(timeout=2000):
                    # Click on a neutral area first
                    page.mouse.click(700, 500)
                    w(300)
                    escape(page)
                    w(300)
                    el.click()
                    w(300)
                    el.fill("Shake-o-mat")
                    print(f"  Property name filled via {sel}")
                    break
            except:
                pass

        w(500)
        ss(page, "A04_name_filled")

        # Click Next
        print("  Clicking Next...")
        try:
            next_btn = page.get_by_role("button", name=re.compile("Next|Continue|Dalje", re.I)).first
            next_btn.click()
            w(4000)
            escape(page)
        except Exception as e:
            print(f"  Next click error: {e}")

        ss(page, "A05_after_next")
        print("URL:", page.url)

        # Business details step
        print("=== Business details ===")
        w(2000)
        # Click Next again (skip industry/size selection, will default)
        try:
            next_btn = page.get_by_role("button", name=re.compile("Next|Continue", re.I)).first
            if next_btn.is_visible(timeout=3000):
                next_btn.click()
                w(4000)
                escape(page)
        except Exception as e:
            print(f"  Business Next: {e}")

        ss(page, "A06_objectives")

        # Business objectives - click Create
        print("=== Creating property ===")
        w(2000)
        for btn_name in ["Create", "Kreiraj", "Finish"]:
            try:
                btn = page.get_by_role("button", name=btn_name).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"  Clicked: {btn_name}")
                    w(6000)
                    escape(page)
                    break
            except:
                pass

        ss(page, "A07_after_create")
        print("URL:", page.url)

        # Accept Terms if visible
        for btn_name in ["I Accept", "Accept", "Agree", "I agree"]:
            try:
                btn = page.get_by_role("button", name=re.compile(btn_name, re.I)).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"  Terms: {btn_name}")
                    w(4000)
                    break
            except:
                pass

        # ── Data stream for Web ───────────────────────────────────────────────
        print("=== Setting up Web data stream ===")
        w(3000)
        ss(page, "A08_stream_choice")
        print("URL:", page.url)

        # Click Web
        for label in ["Web", "Website"]:
            try:
                el = page.get_by_text(label, exact=True).first
                if el.is_visible(timeout=2000):
                    el.click()
                    print(f"  Type: {label}")
                    w(2000)
                    break
            except:
                pass

        ss(page, "A09_web_selected")

        # URL input — click neutral area first, then fill
        page.mouse.click(700, 300)
        w(300)
        for sel in ['input[placeholder*="example.com"]', 'input[placeholder*="yoursite.com"]',
                    'input[type="url"]', 'input[aria-label*="URL" i]']:
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
        for sel in ['input[placeholder*="stream name" i]', 'input[placeholder*="My website"]',
                    'input[aria-label*="stream name" i]']:
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

        w(800)
        ss(page, "A10_stream_filled")

        # Create stream
        for btn_name in ["Create stream", "Create and continue", "Create"]:
            try:
                btn = page.get_by_role("button", name=btn_name).first
                if btn.is_visible(timeout=2000):
                    btn.click()
                    print(f"  Clicked: {btn_name}")
                    w(6000)
                    break
            except:
                pass

        ss(page, "A11_stream_done")
        print("URL:", page.url)

        # ── Extract Measurement ID ────────────────────────────────────────────
        print("=== Extracting Measurement ID ===")
        w(2000)
        content = page.content()
        m = re.search(r'G-[A-Z0-9]{8,12}', content)
        measurement_id = m.group(0) if m else None

        # Also try visible text on page
        txt = page.locator("body").inner_text(timeout=5000)
        m2 = re.search(r'G-[A-Z0-9]{8,12}', txt)
        if not measurement_id and m2:
            measurement_id = m2.group(0)

        ss(page, "A12_measurement_id")

        if measurement_id:
            print(f"\n{'='*50}")
            print(f"MEASUREMENT ID: {measurement_id}")
            print(f"{'='*50}\n")
            with open(f"{BASE}\\ga4_measurement_id.txt", "w") as f:
                f.write(measurement_id)
            print("Saved to ga4_measurement_id.txt")
        else:
            # Try to find it by clicking on the stream
            print("  Searching for ID in stream details...")
            try:
                stream_row = page.locator("[role='row']:not(:first-child), tr:not(:first-child)").first
                stream_row.click()
                w(3000)
                content2 = page.content()
                m3 = re.search(r'G-[A-Z0-9]{8,12}', content2)
                if m3:
                    measurement_id = m3.group(0)
                    print(f"\nMEASUREMENT ID: {measurement_id}\n")
                    with open(f"{BASE}\\ga4_measurement_id.txt", "w") as f:
                        f.write(measurement_id)
                ss(page, "A13_stream_detail")
            except Exception as e:
                print(f"  Stream detail error: {e}")
    else:
        print("WARNING: Property creation form not found. Check screenshots.")
        ss(page, "A_state_check")
        print("Page text:", "\n".join(lines[:30]))

    page.close()
print("Done.")
