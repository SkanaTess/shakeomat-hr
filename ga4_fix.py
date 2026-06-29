import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"

def ss(page, name):
    import os
    try:
        page.screenshot(path=f"{BASE}\\ga4_{name}.png", timeout=45000)
        print(f"  [ss] {name}")
    except Exception as e:
        print(f"  [ss FAIL] {name}: {e}")

def wait(ms=1500):
    time.sleep(ms / 1000)

def try_network_for_property_id(ctx):
    """Intercept GA4 Admin API calls to find Shake-o-mat property ID."""
    found_ids = []
    page2 = ctx.new_page()

    def on_resp(r):
        url = r.url
        if 'analyticsadmin.googleapis.com' in url or ('analytics.google.com' in url and 'management' in url):
            try:
                body = r.text()
                ids = re.findall(r'properties/(\d{8,12})', body)
                names = re.findall(r'"displayName"\s*:\s*"([^"]+)"', body)
                if ids:
                    for i, pid in enumerate(ids):
                        name = names[i] if i < len(names) else '?'
                        found_ids.append((pid, name))
            except:
                pass

    page2.on('response', on_resp)

    # Navigate to GA4 admin which triggers internal API calls
    page2.goto('https://analytics.google.com/analytics/web/', wait_until='domcontentloaded', timeout=30000)
    wait(3000)
    # Trigger property list load
    page2.evaluate('window.location.hash = "/a389031276/admin"')
    wait(6000)
    page2.close()
    return found_ids

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]

    # ── STEP 1: Find Shake-o-mat property ID via network intercept ────────────
    print("=== Finding Shake-o-mat property ID ===")
    prop_ids = try_network_for_property_id(ctx)
    print("Found property (id, name) pairs:", prop_ids[:20])

    # Known: ekohvok = 530166245
    som_prop_id = None
    for pid, name in prop_ids:
        if pid != '530166245' and pid != '389031276':
            print(f"  Candidate: {pid} ({name})")
            if som_prop_id is None:
                som_prop_id = pid

    if not som_prop_id:
        print("  Could not find via network — will scan admin page directly")
        page3 = ctx.new_page()
        page3.set_viewport_size({"width": 1440, "height": 900})
        page3.goto('https://analytics.google.com/analytics/web/', wait_until='domcontentloaded', timeout=30000)
        wait(3000)
        page3.evaluate('window.location.hash = "/a389031276/admin"')
        wait(6000)
        content = page3.content()
        all_ids = set(re.findall(r'(?:property|properties)[/\"](\d{9,12})', content, re.IGNORECASE))
        print("  All property IDs in page HTML:", all_ids)
        for pid in all_ids:
            if pid != '530166245':
                som_prop_id = pid
                print(f"  Using: {pid}")
        page3.close()

    # ── STEP 2: Navigate to Shake-o-mat property and fix timezone/currency ────
    if som_prop_id:
        print(f"\n=== Fixing timezone/currency for property {som_prop_id} ===")
        page = ctx.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})

        # Navigate to property details admin page
        page.goto(
            f"https://analytics.google.com/analytics/web/#/a389031276p{som_prop_id}/admin/property/settings",
            wait_until='domcontentloaded', timeout=30000
        )
        wait(5000)
        ss(page, "prop_settings")

        txt = page.locator('body').inner_text(timeout=5000)
        print("Page text (first 20 lines):")
        for l in [x.strip() for x in txt.split('\n') if x.strip()][:20]:
            print(" ", repr(l[:80]))

        page.close()
    else:
        print("WARNING: Could not find Shake-o-mat property ID")

    # ── STEP 3: Get Shake-o-mat data stream + confirm Measurement ID ──────────
    if som_prop_id:
        print(f"\n=== Confirming Measurement ID for property {som_prop_id} ===")
        page = ctx.new_page()
        page.set_viewport_size({"width": 1440, "height": 900})

        page.goto(
            f"https://analytics.google.com/analytics/web/#/a389031276p{som_prop_id}/admin/streams",
            wait_until='domcontentloaded', timeout=30000
        )
        wait(5000)
        ss(page, "som_streams")

        content = page.content()
        g_ids = re.findall(r'G-[A-Z0-9]{8,12}', content)
        print("G- IDs on stream page:", set(g_ids))

        # Click on stream to see details
        try:
            rows = page.locator('table tr, [role="row"]').all()
            if rows:
                rows[1].click()
                wait(3000)
                ss(page, "som_stream_detail")
                content2 = page.content()
                g_ids2 = re.findall(r'G-[A-Z0-9]{8,12}', content2)
                print("Stream detail G- IDs:", set(g_ids2))

                txt2 = page.locator('body').inner_text(timeout=3000)
                mid_lines = [l.strip() for l in txt2.split('\n') if 'G-' in l or 'MEASUREMENT' in l.upper()]
                print("Measurement lines:", mid_lines[:5])
        except Exception as e:
            print("Stream click error:", e)

        page.close()

print("\nDone.")
