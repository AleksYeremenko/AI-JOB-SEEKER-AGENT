from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.pracuj.pl/praca/junior-java-developer-warszawa-zwirki-i-wigury-16a,oferta,1004966592', timeout=30000)
    page.wait_for_timeout(2000)
    buttons = page.locator('button, a').all()
    print(f"Total buttons/links: {len(buttons)}")
    found = False
    for b in buttons:
        try:
            if not b.is_visible(): continue
            dt = b.get_attribute("data-test")
            text = b.inner_text().strip()
            if "aplikuj" in text.lower() or "apply" in text.lower() or (dt and "apply" in dt.lower()):
                print(f"MATCH: <{b.evaluate('el => el.tagName')}> dt='{dt}' text='{text}'")
                found = True
        except: pass
    if not found:
        print("No match found.")
    browser.close()
