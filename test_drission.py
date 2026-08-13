from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys

# Фикс для кодировки консоли Windows
sys.stdout.reconfigure(encoding='utf-8')

def test_bypass():
    print("Start DrissionPage...")
    
    co = ChromiumOptions()
    co.set_argument('--ignore-certificate-errors')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_data_path("./chrome_profile") # Используем папку профиля

    page = ChromiumPage(co)
    
    print("Go to justjoin.it...")
    page.get('https://justjoin.it/job-offers/all-locations/python')
    
    time.sleep(5)
    
    title = page.title
    print(f"Title: {title}")
    
    if "Just Join IT" in title:
        print("Success! Cloudflare bypassed.")
    else:
        print("Failed to bypass Cloudflare.")
        
    print("Wait 30s...")
    time.sleep(30)
    page.quit()

if __name__ == "__main__":
    test_bypass()
