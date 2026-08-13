from DrissionPage import ChromiumPage, ChromiumOptions
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_drission_apply():
    print("🚀 Запускаем DrissionPage для теста АППЛАЯ...")
    
    co = ChromiumOptions()
    co.set_argument('--ignore-certificate-errors')
    co.set_argument('--disable-blink-features=AutomationControlled')
    # Используем профиль, если нужно
    co.set_user_data_path("./chrome_profile")
    
    page = ChromiumPage(co)
    
    test_url = "https://justjoin.it/job-offer/wavestone-poland-ifs-technical-consultant-gliwice-erp"
    print(f"🌐 Переходим на {test_url}")
    page.get(test_url)
    
    time.sleep(5)
    
    print("🖱️ Ищем кнопку Apply/Aplikuj...")
    # Ищем кнопку по атрибутам или тексту, кликаем через JS если она перекрыта
    apply_btn = page.ele('@@data-test-id=button-apply', timeout=3)
    if not apply_btn:
        apply_btn = page.ele('tag:button@@text():Aplikuj', timeout=3)
    if not apply_btn:
        apply_btn = page.ele('tag:button@@text():Apply', timeout=3)
        
    if apply_btn:
        print("✅ Кнопка найдена, нажимаем!")
        try:
            apply_btn.click()
        except Exception:
            apply_btn.click(by_js=True)
        time.sleep(3)
        
        print("📝 Пытаемся заполнить Имя...")
        # Ищем инпут для имени
        name_input = page.ele('css:input[name*="name"], input[name*="first"]')
        if name_input:
            name_input.input("Oleksandr Yeremenko", clear=True)
            print("✅ Имя введено!")
            
        print("📝 Пытаемся заполнить Email...")
        email_input = page.ele('css:input[type="email"]')
        if email_input:
            email_input.input("yeremenkoaleks1@gmail.com", clear=True)
            print("✅ Email введен!")
            
        print("🚀 Нажимаю кнопку отправки (заглушка снята!)...")
        submit_btn = None
        for selector in ['css:form#apply-form button[type="submit"]', 'css:button[type="submit"]', 'tag:button@@text():Wyślij', 'tag:button@@text():Aplikuj', 'tag:button@@text():Apply']:
            btn = page.ele(selector, timeout=2)
            if btn:
                submit_btn = btn
                break
                
        if submit_btn:
            submit_btn.scroll.to_see()
            time.sleep(0.5)
            submit_btn.click()
            print("✅ Клик по кнопке отправки совершён! Ждем 10 секунд для проверки результата...")
            time.sleep(10)
        else:
            print("❌ Кнопка отправки не найдена!")
    else:
        print("❌ Не нашли кнопку Apply на этой вакансии.")
        
    page.quit()

if __name__ == "__main__":
    test_drission_apply()
