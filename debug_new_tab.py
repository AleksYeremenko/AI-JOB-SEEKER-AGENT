import time
from playwright.sync_api import sync_playwright

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=['--start-maximized'])
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.goto("https://justjoin.it/job-offer/trans-eu-group-sa-senior-platform-engineer---developer-experience-ai-enablement-wroclaw-architecture")
        page.wait_for_load_state("networkidle")
        
        # Click cookies
        try:
            page.locator("button#cookiescript_accept").click(timeout=2000)
        except:
            pass

        print(f"Pages before click: {len(context.pages)}")
        print("Clicking Apply button...")
        
        # Try all Apply buttons
        buttons = page.locator("button:has-text('Apply')")
        for i in range(buttons.count()):
            try:
                print(f"Trying button {i}...")
                try:
                    with page.expect_popup(timeout=3000) as popup_info:
                        buttons.nth(i).click(timeout=1000)
                    print(f"Popup opened from button {i}: {popup_info.value.url}")
                    break
                except Exception as popup_e:
                    print(f"Button {i} didn't open a popup: {popup_e}")
                    # If it didn't open a popup, maybe it just navigated?
                    time.sleep(2)
                    break
            except Exception as e:
                pass
                
        print(f"Pages after 3 seconds: {len(context.pages)}")
        for i, p in enumerate(context.pages):
            print(f"Page {i}: {p.url}")
            
        time.sleep(2)
        browser.close()

if __name__ == "__main__":
    main()
