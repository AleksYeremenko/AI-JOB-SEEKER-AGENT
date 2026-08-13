import time
import sys
from DrissionPage import ChromiumPage, ChromiumOptions

sys.stdout.reconfigure(encoding='utf-8')

def take_screenshot():
    print("Открываю страницу для скриншота...")
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_data_path(r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\Chrome_Profile")
    page = ChromiumPage(co)
    
    page.get("https://justjoin.it/job-offer/wavestone-poland-ifs-technical-consultant-gliwice-erp")
    time.sleep(4)
    
    apply_btn = page.ele('@@data-test-id=button-apply', timeout=5)
    if not apply_btn:
        apply_btn = page.ele('tag:button@@text():Aplikuj', timeout=3)
    if not apply_btn:
        apply_btn = page.ele('tag:button@@text():Apply', timeout=3)
        
    if apply_btn:
        try:
            apply_btn.click()
        except:
            apply_btn.click(by_js=True)
        time.sleep(3)
        
        # Делаем скриншот
        page.get_screenshot(path="justjoin_modal.png", full_page=True)
        print("✅ Скриншот сохранен как justjoin_modal.png")
    else:
        print("❌ Кнопка Apply не найдена")
    
    page.quit()

if __name__ == "__main__":
    take_screenshot()
