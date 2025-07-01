from playwright.sync_api import sync_playwright
import time
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# ==========================================
# ⚙️ НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ
# ==========================================
TEST_URL = "https://justjoin.it/job-offer/j-labs-mid-java-developer-krakow-java"  # Recruitify
TEST_CV_PATH = os.path.abspath("Data/template.docx")

MY_FIRST_NAME = "Oleksandr"
MY_LAST_NAME = "Yeremenko"
MY_FULL_NAME = "Oleksandr Yeremenko"
MY_EMAIL = "yeremenkoaleks1@gmail.com"
MY_PHONE = "+48516478223"
MY_GITHUB = "https://github.com/AleksYeremenko"

# Настройки Email
EMAIL_SENDER = "твой_email@gmail.com"
EMAIL_PASSWORD = "твой_пароль_приложения"  # Нужен App Password от Google
EMAIL_RECEIVER = "yeremenkoaleks1@gmail.com"

MONSTER_ATS_DOMAINS = ['workday', 'taleo', 'successfactors', 'icims', 'brassring', 'myworkdayjobs', 'smartrecruiters']


# ==========================================

def send_notification_email(job_url, ats_url):
    print("📧 Отправляю email-уведомление о сложной вакансии...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = "🤖 AI-Агент: Требуется ручная подача (Workday/Корпорация)!"

        body = f"Привет!\nНашел сложную ATS. Заполни сам:\nJustJoin: {job_url}\nATS: {ats_url}"
        msg.attach(MIMEText(body, 'plain', 'utf-8'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("✅ Письмо успешно отправлено!")
    except Exception as e:
        print(f"❌ Ошибка отправки письма (проверь пароль приложения): {e}")


def kill_cookies(page):
    print("🍪 Разбираюсь с куки...")
    try:
        accept_texts = ['Accept', 'Accept All', 'Akceptuj', 'Zaakceptuj', 'Zgadzam', 'Allow', 'Got it']
        selectors = ", ".join([f"button:has-text('{text}'), span:has-text('{text}')" for text in accept_texts])
        cookie_button = page.locator(selectors).first
        if cookie_button.is_visible(timeout=2000):
            cookie_button.click(force=True)
    except:
        pass

    try:
        page.evaluate("""
            const banners = document.querySelectorAll('[id*="cookie"], [class*="cookie"], [id*="banner"], [class*="banner"], [class*="consent"]');
            banners.forEach(el => { el.style.display = 'none'; el.remove(); });
        """)
    except:
        pass
    time.sleep(1)


def test_justjoin_apply():
    print("🚀 Запускаю Универсальный Тест (Ядерный Вариант + Умные Чекбоксы + Боевая Отправка)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=200)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            print(f"🌐 Открываю: {TEST_URL}")
            page.goto(TEST_URL, timeout=30000)
            time.sleep(3)
            kill_cookies(page)

            print("🖱️ Ищу главную кнопку Apply...")
            apply_button = page.locator("button:has-text('Apply'):visible, button:has-text('Aplikuj'):visible").first
            target_page = page
            is_external = False

            try:
                with context.expect_page(timeout=3000) as new_page_info:
                    apply_button.click(force=True)

                target_page = new_page_info.value
                is_external = True
                print(f"🛑 ВНИМАНИЕ: Внешняя ATS! ({target_page.url})")

                if any(monster in target_page.url.lower() for monster in MONSTER_ATS_DOMAINS):
                    print("☠️ Это корпоративный монстр. Бот туда не лезет.")
                    send_notification_email(TEST_URL, target_page.url)
                    return

                print("⏳ Жду загрузки...")
                target_page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(3)
            except:
                print("✅ Остались на JustJoin.it, жду форму...")

            kill_cookies(target_page)

            if is_external:
                print("🔍 Ищу вторичную кнопку Apply/Aplikuj...")
                try:
                    secondary_apply = target_page.locator(
                        "button:has-text('Aplikuj'), a:has-text('Aplikuj'), button:has-text('Apply'), button:has-text('Aplikuj teraz')").first
                    if secondary_apply.is_visible(timeout=3000):
                        print("🖱️ Нашел вторичную кнопку! Кликаю...")
                        secondary_apply.click(force=True)
                        time.sleep(3)
                        kill_cookies(target_page)
                except:
                    pass

            time.sleep(2)

            # ==========================================
            # 🧠 ЯДЕРНЫЙ ЗАПОЛНИТЕЛЬ
            # ==========================================
            print("📝 Вбиваю данные (режим грубой силы)...")

            smart_fields = {
                "Имя / Full Name": {
                    "val": MY_FULL_NAME,
                    "css": [
                        'input[name*="first" i]', 'input[formcontrolname*="name" i]',
                        'input[autocomplete="given-name"]',
                        'xpath=//label[contains(translate(text(), "IMIĘ", "imię"), "imię")]/following::input[1]',
                        'xpath=//*[contains(translate(text(), "IMIĘ", "imię"), "imię")]/following::input[1]',
                        'input[type="text"]:not([readonly])'  # ПОСЛЕДНЯЯ НАДЕЖДА
                    ]
                },
                "Email": {
                    "val": MY_EMAIL,
                    "css": ['input[type="email"]', 'input[name*="email" i]', 'input[formcontrolname*="email" i]']
                },
                "Телефон": {
                    "val": MY_PHONE,
                    "css": [
                        'input[type="tel"]', 'input[name*="phone" i]', 'input[name*="telefon" i]',
                        'input[formcontrolname*="phone" i]',
                        'xpath=//*[contains(translate(text(), "TELEFON", "telefon"), "telefon")]/following::input[1]',
                        'xpath=//*[contains(translate(text(), "PHONE", "phone"), "phone")]/following::input[1]'
                    ]
                }
            }

            for field_name, data in smart_fields.items():
                filled = False
                regex_map = {"Имя / Full Name": r"imię|imie|name", "Email": r"e-?mail", "Телефон": r"telefon|phone|tel"}
                rx = re.compile(regex_map[field_name], re.IGNORECASE)

                # 1. Поиск по плейсхолдеру/лейблу
                for method in [target_page.get_by_placeholder, target_page.get_by_label]:
                    if filled: break
                    try:
                        loc = method(rx)
                        for i in range(loc.count()):
                            el = loc.nth(i)
                            if el.is_editable():
                                el.fill(data["val"], force=True)
                                print(f"  ✅ {field_name} введено (по тексту).")
                                filled = True
                                break
                    except:
                        pass

                if filled: continue

                # 2. Поиск по CSS/XPath
                for css in data["css"]:
                    elements = target_page.locator(css)
                    for i in range(elements.count()):
                        el = elements.nth(i)
                        if el.is_editable() and el.is_visible():
                            el.fill(data["val"], force=True)
                            print(f"  ✅ {field_name} введено (по CSS/XPath).")
                            filled = True
                            break
                    if filled: break

                if not filled:
                    print(f"  ⚠️ {field_name} не найдено на этой форме!")

            print("📎 Прикрепляю CV...")
            file_input = target_page.locator('input[type="file"]').first
            if file_input.count() > 0:
                file_input.set_input_files(TEST_CV_PATH)
                print("  ✅ Файл загружен.")
            else:
                print("  ⚠️ Поле для файла не найдено!")

            # ==========================================
            # ☑️ БРОНЕБОЙНЫЕ ЧЕКБОКСЫ
            # ==========================================
            print("☑️ Ищу чекбоксы согласия...")

            checkboxes = target_page.locator('input[type="checkbox"]')
            count = checkboxes.count()
            print(f"  Найдено стандартных чекбоксов: {count}")
            for i in range(count):
                try:
                    checkboxes.nth(i).check(force=True)
                except:
                    checkboxes.nth(i).evaluate("node => { if (!node.checked) node.click(); }")

            try:
                mat_checkboxes = target_page.locator('mat-checkbox:not(.mat-checkbox-checked)')
                if mat_checkboxes.count() > 0:
                    for i in range(mat_checkboxes.count()):
                        mat_checkboxes.nth(i).click(force=True)
            except:
                pass

            print("  ✅ Галочки проставлены.")

            # ==========================================
            # 🚀 ФИНАЛЬНАЯ ОТПРАВКА И ПРОВЕРКА
            # ==========================================
            print("🚀 Всё заполнено! Ищу кнопку Submit...")
            try:
                submit_button = target_page.locator(
                    "button[type='submit'], button:has-text('Wyślij'), button:has-text('Aplikuj'), button:has-text('Apply')").last

                # 🔥 БОЕВОЙ КЛИК
                submit_button.click(force=True)
                print("✅ Кнопка отправки НАЖАТА по-настоящему!")

                print("⏳ Проверяю реакцию сайта (изменение URL или сообщение об успехе)...")
                time.sleep(5)  # Ждем, пока уйдет POST-запрос

                if "success" in target_page.url.lower() or "thank" in target_page.url.lower():
                    print("🎉 УСПЕХ: URL изменился, заявка ушла!")
                elif target_page.locator("text=Dziękujemy").is_visible() or target_page.locator(
                        "text=Thank you").is_visible():
                    print("🎉 УСПЕХ: Вижу сообщение 'Спасибо' на экране!")
                else:
                    print("🤔 Клик прошел, но явного экрана 'Спасибо' не вижу. Возможно, просто закрылась модалка.")

            except Exception as e:
                print(f"⚠️ Ошибка при нажатии финальной кнопки: {e}")

            print("⏳ Завершаю работу через 10 секунд...")
            time.sleep(10)

        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(15)
        finally:
            browser.close()


if __name__ == "__main__":
    test_justjoin_apply()