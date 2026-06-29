import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"
ACCOUNT_ID = "389031276"
PROP_ID = "533443439"

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

    # Try multiple URL patterns for account trash
    trash_urls = [
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{PROP_ID}/admin/account/trash",
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{PROP_ID}/admin/trash",
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{PROP_ID}/admin/account-trash",
    ]

    for url in trash_urls:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        w(5000)
        page.keyboard.press("Escape")
        w(300)
        current_hash = page.evaluate("() => window.location.hash")
        txt = page.locator("body").inner_text(timeout=3000)
        print(f"URL: {url}")
        print(f"  hash: {current_hash}")
        has_trash_content = "trash" in txt.lower() and ("restore" in txt.lower() or "empty" in txt.lower() or "property" in txt.lower())
        print(f"  has trash content: {has_trash_content}")
        if has_trash_content:
            ss(page, "r5_trash_found")
            lines = [l.strip() for l in txt.split("\n") if l.strip()]
            print("  Content:")
            for l in lines[:30]:
                print("   ", repr(l[:100]))
            break
        print()

    # Try the Account settings overview page, find Trash link in the main content
    print("=== Navigate to Account Settings overview ===")
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p{PROP_ID}/admin",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(300)
    ss(page, "r5_admin_overview")

    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("Admin overview (all lines with 'trash' or 'account'):")
    for l in lines:
        if "trash" in l.lower() or ("account" in l.lower() and len(l) < 60):
            print(f"  {repr(l[:100])}")

    # Find all links/anchors with trash in href
    links = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]'))
            .map(a => ({ text: a.textContent.trim(), href: a.getAttribute('href') }))
            .filter(a => a.text.length > 0);
    }""")
    print("\nAll <a> links on page:")
    for link in links:
        print(f"  {repr(link['text'][:40])} → {link['href'][:80]}")

    # Find and click Trash link
    for link in links:
        if "trash" in link['text'].lower() or "trash" in link['href'].lower():
            full_url = f"https://analytics.google.com/analytics/web/{link['href']}"
            print(f"\n  Navigating to trash: {full_url}")
            page.goto(full_url, wait_until="domcontentloaded", timeout=30000)
            w(6000)
            page.keyboard.press("Escape")
            w(300)
            ss(page, "r5_trash_page")
            txt2 = page.locator("body").inner_text(timeout=5000)
            lines2 = [l.strip() for l in txt2.split("\n") if l.strip()]
            print("Trash page:")
            for l in lines2[:40]:
                print("  ", repr(l[:100]))
            break

    page.close()

print("\nDone.")
