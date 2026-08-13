from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
    page = browser.new_page()
    page.goto('https://www.pracuj.pl/praca/junior-java-developer-warszawa-zwirki-i-wigury-16a,oferta,1004966592', timeout=30000)
    
    locs = page.locator("[data-test='button-apply']").all()
    for i, l in enumerate(locs):
        print(f'{i}: Visible={l.is_visible()}')
        
    browser.close()
