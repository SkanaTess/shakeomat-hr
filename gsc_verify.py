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
    page.set_default_timeout(30000)

    # GSC should still have shakeomat.hr verification page open
    # Navigate to it directly
    page.goto("https://search.google.com/search-console/welcome", wait_until="domcontentloaded", timeout=30000)
    w(4000)
    ss(page, "V01_state")

    txt = page.locator("body").inner_text(timeout=5000)
    print("Current state (first 20):")
    for l in [x.strip() for x in txt.split("\n") if x.strip()][:20]:
        print(" ", repr(l[:80]))

    # Check if we're on the verification page for shakeomat.hr
    if "shakeomat.hr" in txt and "VERIFY" in txt:
        print("  On verification page — clicking VERIFY")
        # Click VERIFY button
        try:
            verify_btn = page.get_by_role("button", name=re.compile("VERIFY|Verify", re.I)).last
            verify_btn.click()
            print("  Clicked VERIFY")
            w(8000)
        except Exception as e:
            print(f"  VERIFY click error: {e}")
            # Try by position — VERIFY is the last button
            page.mouse.click(878, 800)  # approximate position
            w(8000)

        ss(page, "V02_after_verify")
        print("URL:", page.url)
        txt2 = page.locator("body").inner_text(timeout=5000)
        lines = [l.strip() for l in txt2.split("\n") if l.strip()]
        print("After VERIFY (first 30):")
        for l in lines[:30]:
            print(" ", repr(l[:80]))
    else:
        # Need to re-enter the domain
        print("  Not on verification page — need to add property again")
        # Click OK to dismiss any dialog
        try:
            page.get_by_role("button", name="OK").first.click()
            w(500)
        except:
            pass

        # Find domain input and fill
        inputs = page.locator("input").all()
        for inp in inputs:
            try:
                if inp.is_visible(timeout=300):
                    inp.click()
                    w(200)
                    inp.evaluate("el => el.value = ''")
                    inp.type("shakeomat.hr")
                    print("  Filled domain: shakeomat.hr")
                    w(300)
                    break
            except:
                pass

        ss(page, "V01b_filled")

        # Click CONTINUE
        for btn in page.locator("button, [role='button']").all():
            try:
                txt_b = btn.inner_text(timeout=300).strip().lower()
                if 'continue' in txt_b and btn.is_enabled(timeout=300) and btn.is_visible(timeout=300):
                    btn.click()
                    w(5000)
                    print("  Clicked Continue")
                    break
            except:
                pass

        ss(page, "V01c_verify_page")
        txt3 = page.locator("body").inner_text(timeout=5000)
        print("Now (first 25):")
        for l in [x.strip() for x in txt3.split("\n") if x.strip()][:25]:
            print(" ", repr(l[:80]))

        if "VERIFY" in txt3:
            try:
                # Click VERIFY (last button)
                btns = page.get_by_role("button").all()
                for btn in reversed(btns):
                    try:
                        if 'VERIFY' in btn.inner_text(timeout=300).upper():
                            btn.click()
                            print("  Clicked VERIFY")
                            w(10000)
                            break
                    except:
                        pass
            except Exception as e:
                print(f"  VERIFY error: {e}")

        ss(page, "V02_after_verify")
        txt4 = page.locator("body").inner_text(timeout=5000)
        lines = [l.strip() for l in txt4.split("\n") if l.strip()]
        print("After VERIFY:")
        for l in lines[:30]:
            print(" ", repr(l[:80]))

    page.close()
print("Done.")
