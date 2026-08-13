import time
import sys
from DrissionPage import ChromiumPage, ChromiumOptions
from Appliers.justjoin_applier_drission import JustJoinApplier

sys.stdout.reconfigure(encoding='utf-8')

def debug_submit():
    print("Открываю страницу для отладки отправки...")
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_data_path(r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\Chrome_Profile")
    page = ChromiumPage(co)
    
    # Инициализируем applier
    MY_PROFILE = {
        "first_name": "Oleksandr",
        "last_name": "Yeremenko",
        "email": "yeremenkoaleks1@gmail.com",
        "phone": "+48516478223",
        "linkedin": "https://github.com/AleksYeremenko"
    }
    applier = JustJoinApplier(MY_PROFILE)
    test_url = "https://justjoin.it/job-offer/wavestone-poland-ifs-technical-consultant-gliwice-erp"
    cv_path = r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\my_cv.pdf"
    
    print(f"Запускаю apply для {test_url}")
    # Вызываем apply, но мы хотим перехватить конец, чтобы сделать скриншот
    # Поэтому мы сделаем скриншот после окончания apply
    status = applier.apply(page, test_url, cv_path)
    print(f"Статус после apply: {status}")
    
    print("DEBUG: All buttons on page:")
    buttons = page.eles('css:button')
    for b in buttons:
        try:
            print(f"Button text: {b.text}, name: {b.attr('name')}, type: {b.attr('type')}, class: {b.attr('class')}")
        except:
            pass
            
    # Try one more hardcore click via JS
    print("DEBUG: Executing JS click on apply_button...")
    try:
        page.run_js('document.querySelector("button[name=\'apply_button\']").click()')
        time.sleep(3)
    except Exception as e:
        print(f"JS click failed: {e}")
    
    # Делаем скриншот финального состояния экрана!
    page.get_screenshot(path="justjoin_after_submit_debug.png", full_page=True)
    print("✅ Скриншот сохранен как justjoin_after_submit_debug.png")
    
    page.quit()

if __name__ == "__main__":
    debug_submit()
