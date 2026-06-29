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

    # Navigate to GA4
    page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
    w(4000)
    page.keyboard.press("Escape")
    w(500)

    # Open the property switcher
    # Click the property name in the breadcrumb (header top-left)
    # Current breadcrumb: All accounts > EKO HVOK > ekohvok.com [dropdown]
    # We need to click on "ekohvok.com" to open switcher
    page.get_by_text("Admin", exact=True).first.click()
    w(4000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "F01_admin")

    # In the admin, navigate to property change history
    # Click "Account" section to expand
    try:
        # Find and click the Account section heading/button
        acct_btn = page.locator("button:has-text('Account')").first
        if acct_btn.is_visible(timeout=2000):
            acct_btn.click()
            w(1000)
    except:
        pass

    # Click Account change history
    try:
        hist_link = page.locator("text='Account change history'").first
        if hist_link.is_visible(timeout=2000):
            hist_link.click()
            w(5000)
            ss(page, "F02_change_history")

            txt = page.locator("body").inner_text(timeout=5000)
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            print("Change history:")
            for l in lines[:60]:
                print(" ", repr(l[:80]))
        else:
            print("Account change history link not visible")
    except Exception as e:
        print(f"History click error: {e}")

    # Look for property IDs in the page
    content = page.content()
    prop_urls = re.findall(r'#/a\d+p(\d+)/', content)
    print(f"\nProperty IDs in page URLs: {set(prop_urls)}")

    # Try to find via API in the network
    # Execute JS to find current property context
    try:
        result = page.evaluate('''() => {
            // Find any Angular or data store with property info
            const hash = window.location.hash;
            const m = hash.match(/p(\\d+)/);
            return { hash, propId: m ? m[1] : null };
        }''')
        print(f"Current URL hash: {result}")
    except Exception as e:
        print(f"JS eval error: {e}")

    # Navigate to the Trash to see deleted properties (to count duplicates)
    page.keyboard.press("Escape")
    w(300)

    # Try via direct link to see all properties
    page.evaluate('window.location.hash = "/a389031276/admin"')
    w(5000)
    page.keyboard.press("Escape")
    w(300)
    ss(page, "F03_admin")

    # Now try clicking the "Property" in breadcrumb/header to switch property
    # The breadcrumb usually shows current property - look for it in header
    try:
        # The property name is shown in a clickable element in the left sidebar or header
        # In admin, it shows "ekohvok.com" with a dropdown
        # Try clicking the account switcher icon
        # Navigate to analytics home - property picker is more accessible there
        page.goto("https://analytics.google.com/analytics/web/", wait_until="domcontentloaded", timeout=30000)
        w(4000)

        # The breadcrumb "All accounts > EKO HVOK > ekohvok.com" should be clickable
        # Click on "EKO HVOK" to see all properties under this account
        eko_link = page.get_by_text("EKO HVOK").first
        if eko_link.is_visible(timeout=3000):
            eko_link.click()
            w(4000)
            ss(page, "F04_eko_hvok_click")
            txt = page.locator("body").inner_text(timeout=5000)
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            print("After EKO HVOK click:")
            for l in lines[:40]:
                print(" ", repr(l[:80]))
    except Exception as e:
        print(f"EKO HVOK click error: {e}")

    page.close()
print("Done.")
