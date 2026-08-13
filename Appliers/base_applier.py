import time


class BaseApplier:
    def __init__(self, profile_data, llm_handler=None):
        # Сохраняем данные профиля (имя, email, телефон) и ИИ-модуль,
        # чтобы они были доступны любому дочернему классу
        self.profile = profile_data
        self.llm = llm_handler

    def kill_cookies(self, page):
        print("🍪 [BaseApplier] Разбираюсь с куки-баннерами...")
        try:
            # Ищем любые кнопки согласия на разных языках
            accept_texts = ['Accept', 'Accept All', 'Akceptuj', 'Zaakceptuj', 'Zgadzam', 'Allow', 'Got it', 'Rozumiem']
            selectors = ", ".join([f"button:has-text('{text}'), span:has-text('{text}')" for text in accept_texts])
            cookie_button = page.locator(selectors).first

            if cookie_button.is_visible(timeout=2000):
                cookie_button.click(force=True)
                time.sleep(1)
        except:
            pass

        try:
            # Жестко скрываем через JavaScript всё, что похоже на баннер, если кнопка не сработала
            page.evaluate("""
                const banners = document.querySelectorAll('[id*="cookie"], [class*="cookie"], [id*="banner"], [class*="banner"], [class*="consent"]');
                banners.forEach(el => { el.style.display = 'none'; el.remove(); });
            """)
        except:
            pass

    def apply(self, page, context, job_link, cv_path, cover_letter):
        """
        Это 'контракт'. Этот метод ОБЯЗАН быть написан в каждом классе-наследнике.
        Если ты создашь класс для Pracuj, но забудешь написать там def apply(...),
        программа выдаст эту ошибку и не даст коду тихо сломаться.
        """
        raise NotImplementedError("Метод apply() должен быть реализован в дочернем классе!")

    def robust_fill_field(self, element, value):
        """Пытается заполнить поле используя несколько разных стратегий по возрастанию жесткости."""
        if not value: return False
        value = str(value)
        try:
            tag_name = element.evaluate("el => el.tagName.toLowerCase()")
            if tag_name == "select":
                try:
                    element.select_option(label=value, timeout=2000)
                    return True
                except:
                    try:
                        element.select_option(value=value, timeout=2000)
                        return True
                    except:
                        pass # fallback to JS
        except:
            pass

        try:
            # Уровень 1: Стандартный Playwright
            element.fill(value, force=True, timeout=2000)
            return True
        except:
            try:
                # Уровень 2: Имитация клавиатуры
                element.click(force=True, timeout=1000)
                element.press("Control+A")
                element.press("Backspace")
                element.type(value, delay=50)
                return True
            except:
                try:
                    # Уровень 3: Прямая инъекция через JavaScript с триггером событий
                    js_code = """
                    (el, val) => {
                        if (el.tagName.toLowerCase() === 'select') {
                            // Try to find matching option text
                            let options = Array.from(el.options);
                            let match = options.find(opt => opt.text.includes(val) || opt.value === val);
                            if (match) {
                                el.value = match.value;
                            } else {
                                el.value = val;
                            }
                        } else {
                            el.value = val;
                        }
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Enter' }));
                    }
                    """
                    element.evaluate(js_code, value, timeout=2000)
                    return True
                except Exception as e:
                    print(f"⚠️ robust_fill_field JS fail: {e}")
                    return False

    def take_screenshot_safe(self, page, suffix="screenshot"):
        """Делает скриншот без падения при ошибке (удобно для диагностики)."""
        import os
        import time
        os.makedirs("Data/screenshots", exist_ok=True)
        session_id = int(time.time())
        try:
            path = f"Data/screenshots/{session_id}_{suffix}.png"
            page.screenshot(path=path)
            print(f"📸 Скриншот сохранен: {path}")
            return path
        except Exception as e:
            print(f"⚠️ Не удалось сделать скриншот {suffix}: {e}")
            return None