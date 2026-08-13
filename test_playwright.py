from playwright.sync_api import sync_playwright
import time
from playwright_stealth import Stealth

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
    context = browser.new_context()
    stealth = Stealth()
    stealth.apply_stealth_sync(context)
    page = context.new_page()
    page.goto('https://www.pracuj.pl/praca/junior-java-developer-warszawa-zwirki-i-wigury-16a,oferta,1004966592', timeout=30000)
    time.sleep(5)
    
    print("ALL APLIKUJ TAGS:")
    locs = page.locator("a:has-text('Aplikuj'), button:has-text('Aplikuj')").all()
    for l in locs:
        box = l.bounding_box()
        print(f"TAG: {l.evaluate('el => el.tagName')}, Visible: {l.is_visible()}, Box: {box}")

    browser.close()
