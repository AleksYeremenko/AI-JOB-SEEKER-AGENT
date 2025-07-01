import time
import os
import re
import json

class JobAnalyzer:
    def __init__(self, llm_handler, ats_db_text, my_real_stack):
        self.llm = llm_handler
        self.ats_db = ats_db_text
        self.my_real_stack = my_real_stack

    def detect_language(self, text):
        polish_markers = [' jest ', ' oraz ', ' wymagania ', ' oferta ', ' praca ', ' mile widziane ']
        polish_chars = ['ą', 'ć', 'ę', 'ł', 'ń', 'ó', 'ś', 'ź', 'ż']
        text_lower = text.lower()
        if any(char in text_lower for char in polish_chars) or any(word in text_lower for word in polish_markers):
            return "Polish"
        return "English"

    def check_grade_with_vision(self, url, page):
        print("📸 [ЗРЕНИЕ] Открываю вакансию для сканирования бейджей...")
        screenshot_path = "temp_vision.jpg"
        try:
            page.goto(url, timeout=20000)
            time.sleep(2)
            page.screenshot(path=screenshot_path, type="jpeg", quality=60, clip={'x': 0, 'y': 0, 'width': 1920, 'height': 800})
            print("⏳ Остужаю API перед отправкой картинки (4 сек)...")
            time.sleep(4)
            prompt = "Look at this job posting. Reply ONLY: JUNIOR, MID, or SENIOR. If Mid/Regular/Senior, reply SENIOR."
            vision_result = self.llm.ask_vision(prompt, screenshot_path)
            return vision_result.strip().upper()
        except: return "UNKNOWN"
        finally:
            if os.path.exists(screenshot_path):
                try: os.remove(screenshot_path)
                except: pass

    def generate_ats_resume(self, title, company, details, job_lang):
        prompt = (
            f"Ты — эксперт по обходу ATS-фильтров. Адаптируй резюме под вакансию.\n"
            f"ВАКАНСИЯ: '{title}' в '{company}'. Описание: {details[:2500]}\n"
            f"БАЗА ОПЫТА: {self.ats_db}\n\n"
            f"🔴 ШАГ 1: Если требуется СТРОГИЙ Senior, Lead ИЛИ не Warszawa/Remote — верни ТОЛЬКО ОДНО СЛОВО: REJECT\n\n"
            f"🟢 ШАГ 2: Сгенерируй опыт работы. У меня 3 места работы:\n"
            f"1. Neko Dev (Jun 2024 - Present)\n"
            f"2. CRM Solutions (May 2023 - May 2024)\n"
            f"3. CUBE (Jan 2022 - Apr 2023)\n"
            f"!!! ПРАВИЛА !!!\n"
            f"1. Адаптируй мою должность (TITLE) и опыт под вакансию. Если ищут 'Pega Developer', делай меня 'Pega Developer'. Ты можешь добавлять до 50% новых технологий, которых нет в моем исходном стеке, если они нужны для вакансии.\n"
            f"2. ИСПОЛЬЗУЙ ТЕ ЖЕ САМЫЕ ТЕРМИНЫ, что и в вакансии! Если просят 'React.js', в CV должно быть 'React.js', а не просто 'React'. Это критично для автоматических фильтров.\n"
            f"3. СТРОГО АНГЛИЙСКИЙ ЯЗЫК.\n"
            f"4. СОХРАНЯЙ ВСЕ ЦИФРЫ И МЕТРИКИ (%, SLA, 24/7) из базы.\n"
            f"5. ОТВЕТ ДОЛЖЕН БЫТЬ ТОЛЬКО В ФОРМАТЕ JSON. Никакого Markdown.\n\n"
            f"{{\n"
            f"  \"TITLE\": \"Название должности\",\n"
            f"  \"SKILLS\": [\"React.js\", \"Java\", \"Skill3\"],\n"
            f"  \"SUMMARY\": \"2 предложения о себе\",\n"
            f"  \"JOB1_TITLE\": \"Должность в Neko Dev\",\n"
            f"  \"JOB1_DESC\": \"Описание Neko Dev\",\n"
            f"  \"JOB2_TITLE\": \"Должность в CRM Solutions\",\n"
            f"  \"JOB2_DESC\": \"Описание CRM Solutions\",\n"
            f"  \"JOB3_TITLE\": \"Должность в CUBE\",\n"
            f"  \"JOB3_DESC\": \"Описание CUBE\",\n"
            f"  \"COVER_LETTER\": \"Текст письма на {job_lang}\"\n"
            f"}}"
        )
        result = self.llm.ask(prompt)
        if "REJECT" in result.upper()[:30]: return None
        try:
            clean_json = result.replace("```json", "").replace("```", "").strip()
            return json.loads(clean_json)
        except: return None