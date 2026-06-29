import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"
ACCOUNT_ID = "389031276"

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

    # Go to Account settings overview (shows all admin links including Trash)
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p533443439/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(500)

    # Click "Account settings" to expand account section
    try:
        acct_settings = page.get_by_text("Account settings").first
        if acct_settings.is_visible(timeout=2000):
            acct_settings.click()
            w(3000)
            ss(page, "r3_01_account_settings")
    except Exception as e:
        print(f"  Account settings click: {e}")

    # Now look for "Trash" link (account-level)
    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Page after Account settings click (first 40):")
    for l in lines[:40]:
        print(" ", repr(l[:100]))

    # Find all links/buttons - look for Trash near account section
    result = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('a, button, [role="link"], [role="menuitem"]'));
        return els
            .filter(el => el.offsetParent !== null)
            .map(el => {
                const rect = el.getBoundingClientRect();
                const text = el.textContent.trim();
                const href = el.getAttribute('href') || '';
                return { text: text.substring(0,60), y: Math.round(rect.y), href };
            })
            .filter(el => el.text.length > 0 && el.text.length < 100)
            .sort((a,b) => a.y - b.y);
    }""")

    print("\nAll clickable elements (sorted by y):")
    for item in result:
        if item['text'] in ['Trash', 'Trash Can'] or 'trash' in item['href'].lower():
            print(f"  *** TRASH: y={item['y']} text={repr(item['text'])} href={item['href']}")
        elif item['y'] > 200 and item['y'] < 800:
            print(f"  y={item['y']:4d} | {repr(item['text'][:50])} | href={item['href'][:60]}")

    # Navigate directly to account-level trash page
    # The URL pattern for account trash in GA4
    trash_url = f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}/admin/trash"
    print(f"\n  Navigating to: {trash_url}")
    page.goto(trash_url, wait_until="domcontentloaded", timeout=30000)
    w(6000)
    page.keyboard.press("Escape")
    w(300)
    ss(page, "r3_02_trash")

    txt2 = page.locator("body").inner_text(timeout=5000)
    lines2 = [l.strip() for l in txt2.split("\n") if l.strip()]
    print("Trash page (first 50):")
    for l in lines2[:50]:
        print(" ", repr(l[:100]))

    # Check for elitelab
    for l in lines2:
        if "elitelab" in l.lower() or "532393" in l:
            print(f"  *** FOUND: {repr(l)}")

    # Look for Restore buttons
    restore_btns = page.get_by_role("button", name=re.compile("restore", re.I)).all()
    print(f"\nRestore buttons: {len(restore_btns)}")

    # Try clicking "Trash" text link from the Account settings page
    if not restore_btns:
        print("  Trying to click 'Trash' card link...")
        # Navigate back to account settings
        page.goto(
            f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p533443439/admin/property/settings",
            wait_until="domcontentloaded", timeout=30000
        )
        w(4000)
        page.keyboard.press("Escape")
        w(300)

        # Find and click "Trash" in main content area (card)
        trash_link = page.get_by_text("Trash", exact=True).first
        if trash_link.is_visible(timeout=3000):
            trash_link.click()
            w(5000)
            ss(page, "r3_03_trash_via_card")
            txt3 = page.locator("body").inner_text(timeout=5000)
            lines3 = [l.strip() for l in txt3.split("\n") if l.strip()]
            print("Trash via card click (first 40):")
            for l in lines3[:40]:
                print(" ", repr(l[:100]))

            restore_btns2 = page.get_by_role("button", name=re.compile("restore", re.I)).all()
            print(f"Restore buttons: {len(restore_btns2)}")
            for btn in restore_btns2:
                try:
                    t = btn.inner_text(timeout=300).strip()
                    print(f"  btn: {repr(t[:40])}")
                except:
                    pass

            # Restore elitelab if found
            for btn in restore_btns2:
                try:
                    # Check nearby text for elitelab
                    parent_txt = btn.evaluate("el => el.closest('tr, [role=\"row\"], .card, section')?.textContent || ''")
                    if "elitelab" in parent_txt.lower() or "532393" in parent_txt:
                        btn.click()
                        print("  Clicked Restore for elitelab!")
                        w(3000)
                        ss(page, "r3_04_restored")
                        break
                except:
                    pass

    page.close()

print("\nDone.")
