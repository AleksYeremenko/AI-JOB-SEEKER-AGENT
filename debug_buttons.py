from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://justjoin.it/job-offer/trans-eu-group-sa-senior-platform-engineer---developer-experience-ai-enablement-wroclaw-architecture")
        page.wait_for_load_state("networkidle")
        
        print("--- Все кнопки ---")
        buttons = page.locator("button")
        for i in range(buttons.count()):
            print(f"Button {i}: {buttons.nth(i).text_content().strip() if buttons.nth(i).text_content() else 'NO TEXT'} | Class: {buttons.nth(i).get_attribute('class')}")
            
        print("\n--- Все ссылки, содержащие apply или aplikuj ---")
        links = page.locator("a")
        for i in range(links.count()):
            text = links.nth(i).text_content()
            if text and ('apply' in text.lower() or 'aplikuj' in text.lower()):
                print(f"Link {i}: {text.strip()} | Href: {links.nth(i).get_attribute('href')}")
                
        browser.close()

if __name__ == "__main__":
    main()
