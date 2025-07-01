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