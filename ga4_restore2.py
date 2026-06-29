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

    # Navigate to admin
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p533443439/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(500)

    # Dismiss any open dialog (Shake-o-mat trash dialog from previous run)
    try:
        cancel = page.get_by_role("button", name="Cancel").first
        if cancel.is_visible(timeout=2000):
            cancel.click()
            print("  Dismissed Cancel dialog")
            w(1000)
    except:
        pass

    ss(page, "r2_01_admin")

    # Find ALL "Trash Can" links in sidebar — need the Account-level one
    # Account section is ABOVE Property section in the sidebar
    print("--- All 'Trash Can' occurrences in sidebar ---")
    trash_els = page.get_by_text("Trash Can").all()
    print(f"  Found {len(trash_els)} 'Trash Can' elements")

    for i, el in enumerate(trash_els):
        try:
            vis = el.is_visible(timeout=300)
            box = el.bounding_box()
            print(f"  [{i}] visible={vis} box={box}")
        except Exception as e:
            print(f"  [{i}] err: {e}")

    # The Account-level Trash Can is higher in the page (smaller y coordinate)
    # Find the one that is NOT inside the property settings section
    # It should be near "Account change history" link

    # Get all sidebar links with their positions
    print("\n--- Full admin sidebar links ---")
    result = page.evaluate("""() => {
        const links = Array.from(document.querySelectorAll('a[href], button'));
        return links
            .filter(el => el.offsetParent !== null)
            .map(el => {
                const rect = el.getBoundingClientRect();
                return { text: el.textContent.trim().substring(0,60), y: Math.round(rect.y), x: Math.round(rect.x), href: el.getAttribute('href') || '' };
            })
            .filter(el => el.x < 300 && el.text.length > 0)
            .sort((a,b) => a.y - b.y);
    }""")
    for item in result:
        print(f"  y={item['y']:4d} | {repr(item['text'][:50])} | href={item['href'][:60]}")

    # Find the Account-level Trash Can href
    account_trash_href = None
    for item in result:
        if 'trash' in item['href'].lower() and 'property' not in item['href'].lower():
            account_trash_href = item['href']
            print(f"\n  Found Account Trash href: {account_trash_href}")
            break

    if account_trash_href:
        # Navigate directly to account trash
        page.goto(
            f"https://analytics.google.com/analytics/web/{account_trash_href}",
            wait_until="domcontentloaded", timeout=30000
        )
        w(5000)
    else:
        # Try clicking "Account change history" first to locate Account section
        # Then find Trash Can nearby
        print("\n  Trying Account section approach...")
        try:
            # Scroll to Account section (top of admin sidebar)
            page.evaluate("""() => {
                const els = Array.from(document.querySelectorAll('*'));
                const acct = els.find(el => el.textContent.trim() === 'Account change history' && el.tagName !== 'BODY');
                if (acct) { acct.scrollIntoView(); }
            }""")
            w(500)

            # Get all trash links in Account section
            # Click the one closest to "Account change history"
            trash_links = page.locator("a[href*='trash']").all()
            print(f"  Trash links (a[href*='trash']): {len(trash_links)}")
            for i, link in enumerate(trash_links):
                try:
                    href = link.get_attribute("href") or ""
                    txt = link.inner_text(timeout=300)[:50]
                    box = link.bounding_box()
                    vis = link.is_visible(timeout=300)
                    print(f"    [{i}] vis={vis} href={href} text={repr(txt)} box={box}")
                except Exception as e:
                    print(f"    [{i}] err: {e}")

            # Click first visible trash link that's account-level
            for link in trash_links:
                try:
                    href = link.get_attribute("href") or ""
                    if "property" not in href.lower() and link.is_visible(timeout=300):
                        link.click()
                        print(f"  Clicked account trash link: {href}")
                        w(5000)
                        break
                except:
                    pass
        except Exception as e:
            print(f"  Account section error: {e}")

    ss(page, "r2_02_trash_page")
    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("\nTrash page content (first 50):")
    for l in lines[:50]:
        print(" ", repr(l[:100]))

    # Look for elitelab and restore buttons
    elitelab_lines = [l for l in lines if "elitelab" in l.lower() or "532393510" in l]
    print(f"\nelitelab lines: {elitelab_lines}")

    restore_btns = page.get_by_role("button", name=re.compile("restore", re.I)).all()
    print(f"Restore buttons: {len(restore_btns)}")
    for btn in restore_btns:
        try:
            t = btn.inner_text(timeout=300)
            print(f"  btn: {repr(t[:40])}")
        except:
            pass

    page.close()

print("\nDone.")
