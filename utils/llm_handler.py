import os
import time
import base64
import requests
import json  # Добавлено для работы с JSON
import re  # Добавлено для парсинга ответа ИИ регулярками
from dotenv import load_dotenv

load_dotenv("Data/.env")
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

load_dotenv()


class LLMHandler:
    def __init__(self):
        # Читаем все ключи из .env и создаем из них список
        keys_str = os.getenv("GROQ_KEYS", "")
        self.api_keys = [k.strip() for k in keys_str.split(",") if k.strip()]

        if not self.api_keys:
            print("❌ ОШИБКА: Ключи GROQ_KEYS не найдены в файле .env!")
            self.api_keys = ["dummy_key"]  # Чтобы скрипт не крашнулся мгновенно

        # Начинаем с первого ключа (индекс 0)
        self.current_key_idx = 0

    def get_llm(self):
        """Создает экземпляр ИИ с текущим активным ключом (Текстовая модель)"""
        return ChatGroq(
            api_key=self.api_keys[self.current_key_idx],
            model_name="llama-3.3-70b-versatile",  # Самая мощная и новая модель!
            temperature=0.2,
            max_tokens=2000
        )

    def switch_to_next_key(self):
        """Бесконечная карусель: переключает на следующий ключ (6 -> 1)"""
        old_idx = self.current_key_idx
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        print(f"🔄 Смена ключа: #{old_idx + 1} -> #{self.current_key_idx + 1} (из {len(self.api_keys)})")

    def ask(self, prompt):
        """Обрабатывает текстовые запросы (Генерация CV, Cover Letter)"""
        messages = [
            HumanMessage(content=prompt)  # Теперь слушает только Мега-Промпт из main.py
        ]

        max_retries = len(self.api_keys) + 1

        for attempt in range(max_retries):
            try:
                llm = self.get_llm()
                response = llm.invoke(messages)
                return response.content.strip()

            except Exception as e:
                error_msg = str(e).lower()

                # Если ловят лимит (429 Rate Limit)
                if "429" in error_msg or "rate limit" in error_msg:
                    print(f"\n⚠️ Ключ #{self.current_key_idx + 1} поймал лимит токенов!")
                    self.switch_to_next_key()
                    time.sleep(2)
                else:
                    print(f"\n⚠️ Неизвестная ошибка ИИ (Ключ #{self.current_key_idx + 1}): {e}")
                    self.switch_to_next_key()
                    time.sleep(3)

        print("❌ Все ключи временно выдохлись. Пропускаю эту вакансию.")
        return "REJECT"

    def ask_vision(self, prompt, image_path):
        """НОВЫЙ МЕТОД: Отправляет скриншот в модель со зрением"""
        url = "https://api.groq.com/openai/v1/chat/completions"

        try:
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"❌ Ошибка чтения картинки: {e}")
            return "UNKNOWN"

        payload = {
            "model": "meta-llama/llama-4-scout-17b-16e-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 50
        }

        max_retries = len(self.api_keys) + 1

        for attempt in range(max_retries):
            headers = {
                "Authorization": f"Bearer {self.api_keys[self.current_key_idx]}",
                "Content-Type": "application/json"
            }
            try:
                res = requests.post(url, headers=headers, json=payload, timeout=30)
                if res.status_code == 200:
                    return res.json()["choices"][0]["message"]["content"]
                elif res.status_code == 429:
                    print(f"⚠️ Ключ (Vision) #{self.current_key_idx + 1} поймал лимит!")
                    self.switch_to_next_key()
                    time.sleep(2)
                else:
                    print(f"❌ Ошибка Vision LLM: {res.text}")
                    self.switch_to_next_key()
                    time.sleep(2)
            except Exception as e:
                print(f"❌ Ошибка соединения Vision: {e}")
                time.sleep(2)

        return "UNKNOWN"

    def solve_form(self, questions_dict, profile_data):
        """
        Принимает словарь вопросов от FormScanner и возвращает JSON с ответами.
        questions_dict формат: {"css_selector": "Текст вопроса"}
        """
        print("🧠 [LLM] Генерирую ответы на кастомные вопросы...")

        # Расширенный профиль-легенда
        # Эти дефолты закроют 90% стандартных ATS-вопросов
        # 🔥 УЛЬТИМАТИВНАЯ БАЗА ЗНАНИЙ КАНДИДАТА (Легенда) 🔥
        legend = f"""
                [PERSONAL INFO]
                - Name: {profile_data.get("first_name", "Oleksandr")} {profile_data.get("last_name", "Yeremenko")}
                - Email: {profile_data.get("email", "yeremenkoaleks1@gmail.com")}
                - Phone: {profile_data.get("phone", "+48516478223")}
                - LinkedIn / Portfolio / GitHub: {profile_data.get("github", "https://github.com/AleksYeremenko")}
                - Location / City / Address: Warszawa, Polska (Poland)

                [EXPERIENCE & SKILLS]
                - Total IT Experience: 3+ years (Backend, Python, Java, Automation, React)
                - Experience with specific technologies (Python, Java, SQL, React, etc.): 3 years
                - Highest Education Level: Bachelor's Degree in Computer Science (Inżynier / Licencjat)

                [LOGISTICS & EXPECTATIONS]
                - Notice Period / Start Date (Okres wypowiedzenia / Kiedy możesz zacząć): 1 month (1 miesiąc)
                - Salary Expectations (Oczekiwania finansowe): Negotiable / Zgodne z rynkiem
                - Contract Type Preference (Rodzaj umowy): B2B or UoP (both are fine / obojętnie)
                - Work model: Open to Remote, Hybrid, and On-site
                - Willingness to travel (Podróże służbowe): Up to 20%

                [LEGAL & COMPLIANCE]
                - Work permit in Poland/EU: Yes, full rights (no visa sponsorship needed / bez pozwoleń)
                - Do you require visa sponsorship now or in the future?: No
                - Have you previously worked at this company?: No
                - Are you subject to any non-compete agreements (NDA)?: No
                - Do you have a criminal record?: No

                [OTHER]
                - How did you hear about this job?: Job Board / LinkedIn / Pracuj.pl / JustJoin.it
                """

        prompt = f"""
Ты — AI-ассистент, который помогает Senior-кандидату заполнять кастомные формы при отклике на работу.
Тебе передан JSON с вопросами (Screening Questions), где ключ — это CSS-селектор формы, а значение — текст вопроса.

ТВОЯ ЗАДАЧА:
Вернуть JSON-ответ, где ключом останется тот же CSS-селектор, а значением будет короткий, профессиональный ответ на вопрос.

БАЗА ЗНАНИЙ КАНДИДАТА (Легенда):
{legend}

ВОПРОСЫ ДЛЯ ОТВЕТА:
{json.dumps(questions_dict, ensure_ascii=False, indent=2)}

СТРОГИЕ ПРАВИЛА:
1. Отвечай на языке вопроса (если спрашивают по-польски — отвечай по-польски, если по-английски — по-английски).
2. Ответы должны быть очень короткими. Если это выпадающий список (English level), пиши просто "B2". Если спрашивают Yes/No, пиши "Yes" или "Tak".
3. НИКАКОГО текста до или после JSON. НИКАКОГО Markdown (никаких ```json).
4. Твой ответ должен начинаться с {{ и заканчиваться на }}.
"""

        # Отправляем промпт в нашу существующую функцию ask
        raw_response = self.ask(prompt)

        if raw_response == "REJECT":
            return {}

        # 🛡️ Бронебойный парсинг JSON с помощью Regex 🛡️
        # Ищем всё, что находится между первыми { и последними }, включая переносы строк
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)

        if match:
            json_string = match.group(0)
            try:
                answers = json.loads(json_string)
                print("  ✅ [LLM] JSON успешно распарсен!")
                return answers
            except json.JSONDecodeError as e:
                print(f"  ❌ [LLM] Ошибка декодирования JSON: {e}\nСырой ответ ИИ: {json_string}")
                return {}
        else:
            print(f"  ❌ [LLM] ИИ не вернул структуру JSON. Сырой ответ: {raw_response}")
            return {}