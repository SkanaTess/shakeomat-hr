import sys, io, time, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from playwright.sync_api import sync_playwright

BASE = r"C:\Users\korisnik\Desktop\Claude_Code_Projects\shakeomat-hr"

def ss(page, name):
    try:
        page.screenshot(path=f"{BASE}\\gsc_{name}.png", timeout=45000)
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
    page.set_default_timeout(15000)

    # Fresh load of GSC
    page.goto("https://search.google.com/search-console/welcome", wait_until="domcontentloaded", timeout=30000)
    w(4000)
    ss(page, "01_fresh")

    # Click OK if dialog is showing
    try:
        ok = page.get_by_role("button", name="OK").first
        if ok.is_visible(timeout=1500):
            ok.click()
            w(800)
            print("  Dismissed OK")
    except:
        pass

    w(500)
    ss(page, "02_clean")

    # The Domain input visible inputs (index 4 was visible) — use Tab to focus it
    # Or click precisely on the input area (left card, input field)
    # From screenshot: input is at approx x=510, y=515 in 1440x900 viewport

    # Try clicking the visible input at index [4] directly
    inputs = page.locator("input").all()
    visible_inputs = []
    for i, inp in enumerate(inputs):
        try:
            if inp.is_visible(timeout=300):
                visible_inputs.append((i, inp))
        except:
            pass
    print(f"  Visible inputs: {len(visible_inputs)}")

    if visible_inputs:
        # First visible input should be Domain field
        idx, domain_inp = visible_inputs[0]
        domain_inp.click()
        w(300)
        # Triple click to select all existing content, then type
        domain_inp.press("End")
        domain_inp.press("Home")
        # Clear and type
        domain_inp.evaluate("el => el.value = ''")
        domain_inp.type("shakeomat.hr")
        print(f"  Typed in input[{idx}]: shakeomat.hr")
        w(500)
        ss(page, "03_filled")

        # Find Continue button under Domain section
        # It's the first "CONTINUE" button
        continue_btns = page.locator("button, [role='button']").all()
        print(f"  Buttons found: {len(continue_btns)}")
        for i, btn in enumerate(continue_btns[:10]):
            try:
                txt = btn.inner_text(timeout=300).strip()
                enabled = btn.is_enabled(timeout=300)
                vis = btn.is_visible(timeout=300)
                if txt:
                    print(f"    [{i}] {repr(txt[:30])} enabled={enabled} visible={vis}")
            except:
                pass

        # Click the first visible+enabled CONTINUE/Continue button
        clicked = False
        for btn in continue_btns:
            try:
                txt = btn.inner_text(timeout=300).strip().lower()
                if 'continue' in txt and btn.is_enabled(timeout=300) and btn.is_visible(timeout=300):
                    btn.click()
                    print("  Clicked CONTINUE")
                    w(6000)
                    clicked = True
                    break
            except:
                pass

        if not clicked:
            # Click by coordinates - first Continue button at ~(511, 607)
            print("  Clicking CONTINUE by coordinates")
            page.mouse.click(511, 607)
            w(6000)
    else:
        print("  No visible inputs found!")

    ss(page, "04_result")
    print("URL:", page.url)
    w(2000)

    # Extract TXT record
    txt_body = page.locator("body").inner_text(timeout=5000)
    content = page.content()

    m = re.search(r'google-site-verification=[\w\-_]+', txt_body) or \
        re.search(r'google-site-verification=[\w\-_]+', content)

    txt_record = m.group(0) if m else None

    ss(page, "05_txt_check")
    lines = [l.strip() for l in txt_body.split("\n") if l.strip()]
    print("Page content (first 40 lines):")
    for l in lines[:40]:
        print(" ", repr(l[:80]))

    if txt_record:
        print(f"\n{'='*50}\nTXT RECORD: {txt_record}\n{'='*50}")
        with open(f"{BASE}\\gsc_txt_record.txt", "w") as f:
            f.write(txt_record)
        print("Saved.")
    else:
        print("TXT record not found — check screenshots")

    page.close()
print("Done.")
