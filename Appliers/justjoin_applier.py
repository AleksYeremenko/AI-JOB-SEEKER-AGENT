import time
import re
import sys
import os

# 🔥 БРОНЕБОЙНЫЙ ИМПОРТ 🔥
# Вычисляем путь к корню проекта (на одну папку выше, чем лежит этот файл)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

# Добавляем корень проекта в системные пути Питона
if project_root not in sys.path:
    sys.path.append(project_root)

# Теперь Питон 100% знает, что такое Appliers
from Appliers.base_applier import BaseApplier

class JustJoinApplier(BaseApplier):
    def apply(self, page, context, job_link, cv_path, cover_letter):
        print(f"🌍 [JustJoin] Открываю: {job_link}")
        page.goto(job_link, timeout=30000)
        time.sleep(3)
        self.kill_cookies(page)

        print("🖱️ [JustJoin] Ищу главную кнопку Apply...")
        apply_button = page.locator("button:has-text('Apply'):visible, button:has-text('Aplikuj'):visible").first
        target_page = page

        try:
            with context.expect_page(timeout=3000) as new_page_info:
                apply_button.click(force=True)

            target_page = new_page_info.value
            print(f"🛑 [JustJoin] ВНИМАНИЕ: Внешняя ATS! ({target_page.url})")

            # Если это редирект на стороннюю ATS с JustJoin,
            # мы отдаем статус для ручной подачи, чтобы не зависать
            return "Manual Apply Required"
        except:
            print("✅ [JustJoin] Остались на сайте, жду форму...")

        self.kill_cookies(target_page)
        time.sleep(2)

        # ==========================================
        # 🧠 ЯДЕРНЫЙ ЗАПОЛНИТЕЛЬ
        # ==========================================
        print("📝 [JustJoin] Вбиваю данные (режим грубой силы)...")

        my_first = self.profile.get("first_name", "Oleksandr")
        my_last = self.profile.get("last_name", "Yeremenko")
        my_full = f"{my_first} {my_last}"
        my_email = self.profile.get("email", "yeremenkoaleks1@gmail.com")
        my_phone = self.profile.get("phone", "+48516478223")
        my_linkedin = self.profile.get("linkedin", "https://github.com/AleksYeremenko")

        smart_fields = {
            "Имя / Full Name": {
                "val": my_full,
                "css": [
                    'input[name*="first" i]', 'input[formcontrolname*="name" i]',
                    'input[autocomplete="given-name"]',
                    'xpath=//label[contains(translate(text(), "IMIĘ", "imię"), "imię")]/following::input[1]',
                    'xpath=//*[contains(translate(text(), "IMIĘ", "imię"), "imię")]/following::input[1]',
                    'input[type="text"]:not([readonly])'
                ]
            },
            "Email": {
                "val": my_email,
                "css": ['input[type="email"]', 'input[name*="email" i]', 'input[formcontrolname*="email" i]']
            },
            "Телефон": {
                "val": my_phone,
                "css": [
                    'input[type="tel"]', 'input[name*="phone" i]', 'input[name*="telefon" i]',
                    'input[formcontrolname*="phone" i]',
                    'xpath=//*[contains(translate(text(), "TELEFON", "telefon"), "telefon")]/following::input[1]',
                    'xpath=//*[contains(translate(text(), "PHONE", "phone"), "phone")]/following::input[1]'
                ]
            },
            "LinkedIn/GitHub": {
                "val": my_linkedin,
                "css": ['input[type="url"]', 'input[name*="linkedin" i]', 'input[name*="github" i]',
                        'input[name*="url" i]']
            }
        }

        for field_name, data in smart_fields.items():
            filled = False
            regex_map = {"Имя / Full Name": r"imię|imie|name", "Email": r"e-?mail", "Телефон": r"telefon|phone|tel",
                         "LinkedIn/GitHub": r"linkedin|github|url|portfolio"}
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

            if filled: continue

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

        print("📎 [JustJoin] Прикрепляю CV...")
        file_input = target_page.locator('input[type="file"]').first
        if file_input.count() > 0:
            file_input.set_input_files(cv_path)
            print("  ✅ Файл загружен.")
        else:
            print("  ⚠️ Поле для файла не найдено!")

        # ==========================================
        # ☑️ БРОНЕБОЙНЫЕ ЧЕКБОКСЫ
        # ==========================================
        print("☑️ [JustJoin] Ищу чекбоксы согласия...")
        checkboxes = target_page.locator('input[type="checkbox"]')
        count = checkboxes.count()
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
        print("🚀 [JustJoin] Всё заполнено! Ищу кнопку Submit...")
        try:
            submit_button = target_page.locator(
                "button[type='submit'], button:has-text('Wyślij'), button:has-text('Aplikuj'), button:has-text('Apply')").last

            submit_button.click(force=True, timeout=5000)
            print("✅ Кнопка отправки НАЖАТА!")

            print("⏳ Проверяю реакцию сайта (изменение URL или сообщение об успехе)...")
            time.sleep(5)

            if "success" in target_page.url.lower() or "thank" in target_page.url.lower():
                print("🎉 УСПЕХ: URL изменился, заявка ушла!")
                return "Applied"
            elif target_page.locator("text=Dziękujemy").is_visible() or target_page.locator(
                    "text=Thank you").is_visible():
                print("🎉 УСПЕХ: Вижу сообщение 'Спасибо' на экране!")
                return "Applied"
            else:
                # Проверяем, не вылезла ли ошибка валидации
                error_text = target_page.locator(".error, .invalid, [aria-invalid='true']").first
                if error_text.is_visible(timeout=2000):
                    print("⚠️ Заявка не ушла: Сайт ругается на незаполненные поля (ошибка валидации).")
                    return "Failed - Validation Error"

                print(
                    "🤔 Клик прошел, но явного экрана 'Спасибо' не вижу. Возможно, просто закрылась модалка. Считаем успешным.")
                return "Applied (Unconfirmed)"

        except Exception as e:
            print(f"⚠️ Ошибка при нажатии финальной кнопки: {e}")
            return "Failed - Submit Error"