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

    # Go to admin
    page.goto(
        f"https://analytics.google.com/analytics/web/#/a{ACCOUNT_ID}p533443439/admin/property/settings",
        wait_until="domcontentloaded", timeout=30000
    )
    w(5000)
    page.keyboard.press("Escape")
    w(500)
    ss(page, "r4_01_admin")

    # Click left sidebar "Account" section header to expand
    print("--- Expanding Account section in sidebar ---")
    # The sidebar has collapsed sections. "Account" is a section header button
    # Find all buttons/links in the left panel (x < 200)
    result = page.evaluate("""() => {
        const sidebar = document.querySelector('[class*="admin-sidebar"], [class*="nav"], aside, [role="navigation"]');
        const container = sidebar || document.body;
        const els = Array.from(container.querySelectorAll('button, a, [role="button"], [role="link"]'));
        return els
            .filter(el => el.offsetParent !== null)
            .map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    tag: el.tagName,
                    text: el.textContent.trim().substring(0,60),
                    y: Math.round(rect.y),
                    x: Math.round(rect.x),
                    width: Math.round(rect.width),
                    href: el.getAttribute('href') || '',
                    classes: el.className.substring(0,80)
                };
            })
            .filter(el => el.x < 250 && el.text.length > 0)
            .sort((a,b) => a.y - b.y);
    }""")
    print("Left sidebar elements:")
    for item in result:
        print(f"  y={item['y']:4d} x={item['x']:3d} [{item['tag']}] {repr(item['text'][:40])} href={item['href'][:50]}")

    # Click "Account" button in sidebar (section header, not "Account settings")
    # It's likely a button with text exactly "Account"
    clicked_acct = False
    for item in result:
        if item['text'].strip() == 'Account' and item['x'] < 200:
            page.mouse.click(item['x'] + 10, item['y'] + 5)
            clicked_acct = True
            print(f"\n  Clicked 'Account' at y={item['y']}")
            w(2000)
            break

    if not clicked_acct:
        # Try by selector
        try:
            acct_btn = page.locator("button:has-text('Account')").first
            if acct_btn.is_visible(timeout=1000):
                acct_btn.click()
                print("  Clicked Account button via selector")
                w(2000)
        except:
            pass

    ss(page, "r4_02_expanded")

    # Now look for Trash Can
    result2 = page.evaluate("""() => {
        const els = Array.from(document.querySelectorAll('button, a, [role="button"], [role="link"]'));
        return els
            .filter(el => el.offsetParent !== null)
            .map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    text: el.textContent.trim().substring(0,60),
                    y: Math.round(rect.y),
                    x: Math.round(rect.x),
                    href: el.getAttribute('href') || ''
                };
            })
            .filter(el => el.x < 250 && el.text.length > 0)
            .sort((a,b) => a.y - b.y);
    }""")
    print("\nSidebar after expand:")
    for item in result2:
        marker = " *** TRASH ***" if "trash" in item['text'].lower() or "trash" in item['href'].lower() else ""
        print(f"  y={item['y']:4d} {repr(item['text'][:40])} href={item['href'][:50]}{marker}")

    # Click Trash Can
    trash_clicked = False
    for item in result2:
        if "trash" in item['text'].lower() and item['x'] < 250:
            page.mouse.click(item['x'] + 50, item['y'] + 5)
            trash_clicked = True
            print(f"\n  Clicked Trash at y={item['y']}: {item['text']}")
            w(5000)
            break

    if not trash_clicked:
        # Try by href
        for item in result2:
            if "trash" in item['href'].lower():
                page.goto(
                    f"https://analytics.google.com/analytics/web/{item['href']}",
                    wait_until="domcontentloaded", timeout=30000
                )
                trash_clicked = True
                print(f"  Navigated to trash href: {item['href']}")
                w(5000)
                break

    ss(page, "r4_03_trash_page")
    txt = page.locator("body").inner_text(timeout=5000)
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    print("\nTrash page (first 50):")
    for l in lines[:50]:
        print(" ", repr(l[:100]))

    # Look for elitelab
    for l in lines:
        if "elitelab" in l.lower() or "532393" in l:
            print(f"  *** FOUND: {repr(l)}")

    # Restore buttons
    restore_btns = page.get_by_text("Restore").all()
    print(f"\nRestore elements: {len(restore_btns)}")
    for btn in restore_btns:
        try:
            vis = btn.is_visible(timeout=300)
            box = btn.bounding_box()
            print(f"  Restore: visible={vis} box={box}")
            if vis:
                # Check parent row for elitelab
                parent_txt = btn.evaluate("el => { let p = el; for(let i=0;i<5;i++){p=p.parentElement;if(!p)break;} return p ? p.textContent.substring(0,200) : ''; }")
                print(f"  Parent text: {repr(parent_txt[:100])}")
                if "elitelab" in parent_txt.lower() or "532393" in parent_txt:
                    btn.click()
                    print("  *** RESTORED elitelab.hr! ***")
                    w(3000)
                    ss(page, "r4_04_restored")
                    break
        except Exception as e:
            print(f"  Restore err: {e}")

    page.close()

print("\nDone.")
