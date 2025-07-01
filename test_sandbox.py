from playwright.sync_api import sync_playwright
import time
import os
import re
import sys
from dotenv import load_dotenv

# Подгружаем переменные окружения
load_dotenv("Data/.env")

# Добавляем корень проекта в пути
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from utils.llm_handler import LLMHandler

# ==========================================
# 🧪 НАСТРОЙКИ ПЕСОЧНИЦЫ
# ==========================================
TEST_CV_PATH = os.path.abspath("Data/template.docx")
MY_PROFILE = {
    "first_name": "Oleksandr",
    "last_name": "Yeremenko",
    "full_name": "Oleksandr Yeremenko",
    "email": "yeremenkoaleks1@gmail.com",
    "phone": "+48516478223",
    "github": "https://github.com/AleksYeremenko"
}


class SandboxApplier:
    def __init__(self, profile_data, llm_handler=None):
        self.profile = profile_data
        self.llm = llm_handler

        # 🛡️ Радар для отсечения монстров (Workday и др.)
        self.manual_domains = [
            'workday', 'taleo', 'successfactors', 'icims', 'brassring',
            'myworkdayjobs', 'smartrecruiters', 'greenhouse.io', 'lever.co',
            'breezy.hr', 'applytojob.com', 'ashbyhq.com', 'workable.com',
            'bamboohr.com'
        ]

    def kill_cookies(self, page):
        print("🍪 [ПЕСОЧНИЦА] Убиваю куки и всплывающие окна...")
        try:
            accept_texts = [
                'Accept', 'Accept All', 'Akceptuj', 'Akceptuję wszystkie',
                'Zaakceptuj', 'Zgadzam', 'Allow', 'Got it',
                'Rozumiem', 'Przejdź do serwisu', 'Zamknij'
            ]
            selectors = ", ".join([f"button:has-text('{text}'), span:has-text('{text}')" for text in accept_texts])
            pracuj_selectors = ", [data-test='button-submitCookie'], [data-test='system-message-close'], [data-test='button-close']"
            full_selectors = selectors + pracuj_selectors

            cookie_buttons = page.locator(full_selectors)
            for i in range(cookie_buttons.count()):
                if cookie_buttons.nth(i).is_visible(timeout=1000):
                    cookie_buttons.nth(i).click(force=True)
                    time.sleep(1)
        except:
            pass

        try:
            page.evaluate("""
                const banners = document.querySelectorAll('[id*="cookie"], [class*="cookie"], [id*="banner"], [class*="banner"], [class*="consent"], [class*="modal"], [class*="popup"], [class*="dialog"]');
                banners.forEach(el => { el.style.display = 'none'; el.remove(); });
                document.body.style.overflow = 'auto'; 
            """)
        except:
            pass

    def test_pracuj(self, page, context, job_link):
        print(f"🌍 [ТЕСТ Pracuj.pl] Открываю: {job_link}")

        # 🛡️ ПРЕ-ФИЛЬТР: Проверка ссылки до захода
        if any(domain in job_link.lower() for domain in self.manual_domains):
            print(f"🛑 [РАДАР] Это сложная ATS ({job_link}). Отмена теста!")
            return

        page.goto(job_link, timeout=30000)

        # 🔥 ЖДЕМ CLOUDFLARE
        if page.locator("iframe[src*='cloudflare']").is_visible(timeout=3000):
            print("🛑 [CLOUDFLARE] Вылезла защита! У тебя 15 секунд, чтобы нажать галочку руками...")
            time.sleep(15)

        time.sleep(3)
        self.kill_cookies(page)

        print("🖱️ Ищу главную кнопку Apply...")
        apply_button = page.locator("[data-test='button-apply'], :text-is('Aplikuj'), :text-is('Apply')").first

        try:
            apply_button.wait_for(state="attached", timeout=5000)
            with context.expect_page(timeout=4000) as new_page_info:
                apply_button.evaluate("node => node.click()")
            target_page = new_page_info.value
            print(f"🛑 ВНИМАНИЕ: Открылась новая вкладка/ATS! ({target_page.url})")

            # 🛡️ ПОСТ-ФИЛЬТР: Проверка ссылки после редиректа
            if any(domain in target_page.url.lower() for domain in self.manual_domains):
                print(f"🛑 [РАДАР] Нас перекинуло на сложную ATS ({target_page.url}). Бот туда не лезет. Отмена!")
                return

            time.sleep(3)
        except Exception as e:
            print("✅ Остались на сайте (или редиректа не было), жду форму...")
            try:
                apply_button.evaluate("node => node.click()")
            except:
                pass
            time.sleep(2)
            target_page = page

        # 🔥 ПРОБИВАЕМ МОДАЛКУ "ВНЕШНЯЯ ATS"
        try:
            kontynuuj_btn = target_page.locator(
                "button:has-text('Kontynuuj aplikowanie'), a:has-text('Kontynuuj aplikowanie')").first
            if kontynuuj_btn.is_visible(timeout=3000):
                print("🚧 Вижу модалку внешнего сайта. Жму 'Kontynuuj aplikowanie'...")
                with context.expect_page(timeout=5000) as ext_page_info:
                    kontynuuj_btn.evaluate("node => node.click()")
                target_page = ext_page_info.value
                print(f"🛑 Улетели на внешнюю ATS! ({target_page.url})")

                if any(domain in target_page.url.lower() for domain in self.manual_domains):
                    print(f"🛑 [РАДАР] Это монстр-ATS ({target_page.url}). Отмена!")
                    return
                time.sleep(3)
        except:
            pass

        if "login.pracuj.pl" in target_page.url:
            print("🛑 ОП! Pracuj требует авторизацию. Даю 2 минуты на логин...")
            try:
                target_page.wait_for_url(lambda url: "login" not in url.lower(), timeout=120000)
                context.storage_state(path="Data/my_session.json")
                time.sleep(3)
            except:
                print("❌ Время вышло. Прерываю тест.")
                return

        self.kill_cookies(target_page)

        # 🛡️ Ожидание формы перед заполнением
        print("⏳ Жду отрисовки полей формы (до 10 секунд)...")
        try:
            target_page.wait_for_selector("input:not([type='hidden'])", timeout=10000)
            time.sleep(2)
        except:
            print("⚠️ Инпуты не появились! Возможно, форма скрыта или страница не загрузилась.")

        # ==========================================
        # 🧠 ЯДЕРНЫЙ ЗАПОЛНИТЕЛЬ
        # ==========================================
        print("📝 Вбиваю данные (режим грубой силы)...")
        smart_fields = {
            "Имя / First Name": {"val": self.profile["first_name"],
                                 "css": ['input[name*="first" i]', 'input[autocomplete="given-name"]']},
            "Фамилия / Last Name": {"val": self.profile["last_name"],
                                    "css": ['input[name*="last" i]', 'input[autocomplete="family-name"]']},
            "Email": {"val": self.profile["email"], "css": ['input[type="email"]', 'input[name*="email" i]']},
            "Телефон / Mobile": {"val": self.profile["phone"], "css": ['input[type="tel"]', 'input[name*="phone" i]']},
            "LinkedIn/GitHub": {"val": self.profile["github"],
                                "css": ['input[type="url"]', 'input[name*="github" i]', 'input[name*="linkedin" i]']}
        }

        for field_name, data in smart_fields.items():
            filled = False
            regex_map = {
                "Имя / First Name": r"imię|imie|first", "Фамилия / Last Name": r"nazwisko|last",
                "Email": r"e-?mail", "Телефон / Mobile": r"telefon|phone|tel", "LinkedIn/GitHub": r"linkedin|github|url"
            }
            rx = re.compile(regex_map[field_name], re.IGNORECASE)

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

            if not filled:
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

        # ==========================================
        # 🤖 FORM SCANNER & LLM
        # ==========================================
        print("🔍 [FormScanner] Ищу незаполненные поля и выпадающие списки...")
        scanner_script = """
        () => {
            const result = {};
            const elements = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="file"]):not([type="checkbox"]):not([type="radio"]), textarea, select');

            elements.forEach((el, index) => {
                if ((el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') && el.value.trim() !== '') return;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;

                let questionText = el.getAttribute('aria-label') || "";
                if (!questionText && el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) questionText = label.innerText;
                }
                if (!questionText) {
                    const parentLabel = el.closest('label');
                    if (parentLabel) questionText = parentLabel.innerText.replace(el.innerText, '');
                }
                if (!questionText) {
                    const wrapper = el.closest('div, li, fieldset, .form-group'); 
                    if (wrapper) {
                        const potentialLabel = wrapper.querySelector('label, span, legend, p');
                        if (potentialLabel) questionText = potentialLabel.innerText;
                    }
                }

                let optionsText = "";
                if (el.tagName === 'SELECT') {
                    const opts = Array.from(el.querySelectorAll('option'))
                                      .map(o => o.innerText.trim())
                                      .filter(t => t && t.toLowerCase() !== 'wybierz' && t.toLowerCase() !== 'select' && t !== '-');
                    if (opts.length > 0) {
                        optionsText = " [Options to choose: " + opts.join(" | ") + "]";
                    }
                }

                if (questionText && questionText.trim() !== '') {
                    let selector = el.id ? `${el.tagName.toLowerCase()}#${el.id}` : (el.name ? `${el.tagName.toLowerCase()}[name="${el.name}"]` : "");
                    if (!selector) {
                        const uniqueId = `ai_target_${index}`;
                        el.setAttribute('data-ai-target', uniqueId);
                        selector = `${el.tagName.toLowerCase()}[data-ai-target="${uniqueId}"]`;
                    }
                    result[selector] = questionText.replace(/\\n/g, ' ').replace(/\s+/g, ' ').trim() + optionsText;
                }
            });
            return result;
        }
        """
        unfilled_questions = target_page.evaluate(scanner_script)

        if unfilled_questions:
            print(f"  ✅ Найдено {len(unfilled_questions)} кастомных вопросов!")
            for sel, quest in unfilled_questions.items():
                print(f"      ❓ {quest} -> [{sel}]")

            print("🧠 Передаю вопросы в LLM...")
            if self.llm:
                ai_answers = self.llm.solve_form(unfilled_questions, self.profile)

                for selector, answer in ai_answers.items():
                    try:
                        el = target_page.locator(selector).first
                        if el.is_visible():
                            tag_name = el.evaluate("node => node.tagName").lower()

                            if tag_name == "select":
                                print(f"  🔽 Это выпадающий список. ИИ выбрал: '{answer}'")
                                try:
                                    el.select_option(label=str(answer))
                                    print(f"  ✅ Опция '{answer}' выбрана!")
                                except:
                                    options = el.locator("option")
                                    selected = False
                                    for i in range(options.count()):
                                        opt_text = options.nth(i).text_content()
                                        if str(answer).lower() in opt_text.lower():
                                            el.select_option(index=i)
                                            print(f"  ✅ Выбрано частичное совпадение: '{opt_text}'")
                                            selected = True
                                            break
                                    if not selected:
                                        print(f"  ❌ Не смог выбрать опцию '{answer}' в селекторе!")
                            else:
                                el.fill(str(answer), force=True)
                                print(f"  ✅ Текст вписан: '{answer}'")
                    except Exception as e:
                        print(f"  ⚠️ Не удалось заполнить {selector}: {e}")

        print("📎 Настраиваю загрузку нового CV...")
        try:
            change_cv_btn = target_page.locator(
                "button:has-text('zmień lub odrzuć plik'), button:has-text('Zmień'), [data-test='button-change-cv']").first
            if change_cv_btn.is_visible(timeout=3000):
                print("  ♻️ Вижу старое резюме. Жму кнопку сброса...")
                change_cv_btn.click(force=True)
                time.sleep(1)
                add_new_btn = target_page.locator(
                    "button:has-text('Dodaj nowe CV'), button:has-text('Wgraj nowy plik')").first
                if add_new_btn.is_visible(timeout=1000):
                    add_new_btn.click(force=True)
                    time.sleep(1)
        except:
            pass

        file_input = target_page.locator('input[type="file"]').first
        if file_input.count() > 0:
            file_input.set_input_files(TEST_CV_PATH)
            print("  ✅ Новый файл CV успешно загружен!")
            time.sleep(2)
        else:
            print("  ⚠️ Поле для файла не найдено!")

        print("☑️ Ищу чекбоксы согласия...")
        checkboxes = target_page.locator('input[type="checkbox"]')
        for i in range(checkboxes.count()):
            try:
                checkboxes.nth(i).check(force=True)
            except:
                checkboxes.nth(i).evaluate("node => { if (!node.checked) node.click(); }")
        print("  ✅ Галочки проставлены.")

        print("🚀 Всё заполнено! Ищу кнопку Submit...")
        try:
            submit_button = target_page.locator(
                "button[type='submit'], button:has-text('Wyślij'), button:has-text('Aplikuj'), button:has-text('Apply')").last

            # 🔥 БОЕВОЙ КЛИК АКТИВИРОВАН 🔥
            submit_button.click(force=True, timeout=5000)
            print("✅ [ТЕСТ] КНОПКА ОТПРАВКИ НАЖАТА! ФОРМА УШЛА!")
            time.sleep(5)  # Ждем, чтобы увидеть экран успеха
        except Exception as e:
            print(f"⚠️ Ошибка при поиске финальной кнопки: {e}")


def run_sandbox():
    # Найди НОВУЮ, простую вакансию для теста (не Workday)
    CURRENT_TEST_URL = "https://www.pracuj.pl/praca/intern-business-analyst-half-time-warszawa,oferta,1004726843?s=ff84ed29&searchId=MTc3NTMwNDE1OTYzNC4yNzQy"
    print("🧪 ЗАПУСК ПЕСОЧНИЦЫ...")

    # Инициализация боевой LLM
    llm = LLMHandler()
    sandbox = SandboxApplier(MY_PROFILE, llm)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=100,
            args=["--disable-blink-features=AutomationControlled", "--disable-infobars"]
        )

        session_file = "Data/my_session.json"

        if os.path.exists(session_file):
            print("🔑 Найдена сохраненная сессия! Бот заходит под твоим аккаунтом...")
            context = browser.new_context(viewport={"width": 1920, "height": 1080}, storage_state=session_file)
        else:
            print("⚠️ Файл сессии Data/my_session.json не найден. Запускаю чистый браузер.")
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            sandbox.test_pracuj(page, context, CURRENT_TEST_URL)
            print("\n🏁 Тест завершен. Окно закроется через 15 секунд...")
            time.sleep(15)
        except Exception as e:
            print(f"💥 КРАШ ТЕСТА: {e}")
            time.sleep(15)
        finally:
            browser.close()


if __name__ == "__main__":
    run_sandbox()