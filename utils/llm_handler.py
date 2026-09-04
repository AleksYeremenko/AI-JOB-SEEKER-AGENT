import os
import time
import json
import re
from dotenv import load_dotenv

load_dotenv("Data/.env")
load_dotenv()

from langchain_core.messages import HumanMessage
from langchain_ollama import ChatOllama

class LLMHandler:
    def __init__(self):
        # Local AI does not require API keys
        self.fast_model_name = "qwen2.5-coder:7b"      # Возвращаем 7b, так как 1.5b слишком глупая
        self.smart_model_name = "job-vision-model:latest"  # Your trained model for CV generation
        import threading
        self.llm_lock = threading.Lock()

    def get_llm(self, model_type="smart", format=None):
        """Creates a local Ollama instance"""
        model_name = self.smart_model_name if model_type == "smart" else self.fast_model_name
        kwargs = {
            "model": model_name,
            "temperature": 0.2
        }
        if format:
            kwargs["format"] = format
            
        return ChatOllama(**kwargs)

    def ask(self, prompt, model_type="smart", max_retries=3, format=None):
        """Processes text requests (CV Generation, Cover Letter)"""
        current_model_type = model_type
        for attempt in range(max_retries):
            try:
                msg = HumanMessage(content=prompt)
                llm = self.get_llm(model_type=current_model_type, format=format)
                
                with self.llm_lock:
                    response = llm.invoke([msg])
                    
                content = response.content
                if isinstance(content, list):
                    texts = []
                    for block in content:
                        if isinstance(block, str):
                            texts.append(block)
                        elif isinstance(block, dict) and "text" in block:
                            texts.append(block["text"])
                        content = " ".join(texts)
                return content.strip()

            except Exception as e:
                print(f"\n⚠️ Local Ollama error ({current_model_type}): {e}")
                # If smart model fails (e.g., out of memory), try switching to fast model
                if current_model_type == "smart":
                    print("🔄 Switching to fast model to save the task...")
                    current_model_type = "fast"
                time.sleep(3)

        print("❌ Local Ollama did not respond after 3 attempts. Skipping.")
        return "REJECT"

    def ask_with_image(self, prompt, base64_image, model_type="smart", max_retries=3):
        """Processes vision requests using base64 image data"""
        current_model_type = model_type
        for attempt in range(max_retries):
            try:
                # OLLAMA Vision format
                msg = HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                ])
                llm = self.get_llm(model_type=current_model_type)
                
                with self.llm_lock:
                    response = llm.invoke([msg])
                    
                return response.content.strip()
            except Exception as e:
                print(f"\n⚠️ Local Ollama Vision error: {e}")
                time.sleep(3)
        return "UNKNOWN"

    def solve_form(self, questions_dict, profile_data):
        print("🧠 [LLM] Generating answers for custom questions (Local Ollama)...")

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

        raw_response = self.ask(prompt, format="json")

        if not raw_response or raw_response == "REJECT":
            return {}

        match = re.search(r'\{.*\}', raw_response, re.DOTALL)

        if match:
            json_string = match.group(0)
            try:
                answers = json.loads(json_string)
                print("  ✅ [LLM] JSON successfully parsed!")
                return answers
            except json.JSONDecodeError as e:
                print(f"  ❌ [LLM] JSON decode error: {e}\nRaw LLM response: {json_string}")
                return {}
        else:
            print(f"  ❌ [LLM] LLM did not return JSON structure. Raw response: {raw_response}")
            return {}

    def calculate_match_score(self, job_title, job_description, user_stack, user_seniority):
        """Analyzes job vacancy and returns match percentage (0-100)"""
        prompt = (
            f"You are an expert IT recruiter. Evaluate the match between the candidate and the job.\n"
            f"Candidate Seniority: {user_seniority}\n"
            f"Candidate Stack: {user_stack}\n"
            f"Job Title: {job_title}\n"
            f"Job Description: {job_description[:2000]}\n"
            f"Be generous. If the core technology matches, give at least 65%. "
            f"Return ONLY an integer number from 0 to 100 representing the match percentage. No other text."
        )
        try:
            result = self.ask(prompt, model_type="fast").strip()
            score_str = ''.join(filter(str.isdigit, result))
            if score_str:
                score = int(score_str)
                return min(max(score, 0), 100)
            return 60
        except Exception as e:
            print(f"⚠️ LLM match error: {e}")
            return 60

    def generate_cv_json(self, job_title, job_description, profile_data, user_stack, base_cv_text=""):
        prompt = f"""
Ты — эксперт по ATS-системам. Твоя задача — адаптировать реальный опыт кандидата под вакансию.
Целевая вакансия: {job_title}
Описание вакансии: {job_description[:2000]}
Ключевые навыки кандидата: {user_stack}

РЕАЛЬНОЕ РЕЗЮМЕ КАНДИДАТА (Используй ТОЛЬКО факты отсюда):
{base_cv_text[:3000]}

Твоя задача — переписать bullet points в опыте работы кандидата так, чтобы они лучше соответствовали ключевым словам из описания вакансии. 
КАТЕГОРИЧЕСКИ ЗАПРЕЩАЕТСЯ ВЫДУМЫВАТЬ НОВЫЕ КОМПАНИИ, НОВЫЕ МЕСТА РАБОТЫ ИЛИ ТОГО, ЧЕГО НЕТ В РЕЗЮМЕ. Используй только те компании и должности, которые есть в РЕАЛЬНОМ РЕЗЮМЕ.
КРИТИЧЕСКИ ВАЖНО ДЛЯ ATS: Используй ТОЧНО ТАКИЕ ЖЕ термины и названия технологий, как в описании вакансии. Совпадение должно быть посимвольным. Если в вакансии написано 'React.js', ты ДОЛЖЕН писать 'React.js', а не 'React' или 'ReactJS'.
ВАЖНО: Не используй дефисы или тире внутри массивов (например, внутри "description"), позволь HTML/CSS самостоятельно отрисовывать маркеры списка.

ВЕРНИ ОТВЕТ СТРОГО В ФОРМАТЕ JSON, БЕЗ МАРКДАУНА, БЕЗ ЛИШНЕГО ТЕКСТА.
CRITICAL: Ensure 100% valid JSON syntax! Do NOT forget commas between array elements. Do NOT leave trailing commas at the end of arrays.

{{
  "title": "Должность для резюме (на основе вакансии)",
  "summary": "Уверенный текст на 3-4 предложения, продающий кандидата на основе ЕГО РЕАЛЬНОГО опыта.",
  "skills": ["Skill1", "Skill2", "Skill3"],
  "education": "Образование ИЗ РЕЗЮМЕ",
  "jobs": [
    {{
      "title": "Должность ИЗ РЕЗЮМЕ",
      "company": "Компания ИЗ РЕЗЮМЕ",
      "description": [
        "Улучшенное достижение 1 (с фокусом на технологии из вакансии)",
        "Улучшенное достижение 2"
      ]
    }}
  ]
}}
"""
        raw_response = self.ask(prompt, format="json")
        if raw_response == "REJECT":
            return {}
        
        match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if match:
            json_string = match.group(0)
            json_string = re.sub(r'```json\s*|\s*```', '', json_string)
            try:
                import json_repair
                repaired_json = json_repair.repair_json(json_string, return_objects=True)
                if repaired_json:
                    return repaired_json
                else:
                    print("❌ json_repair failed to salvage the JSON.")
            except Exception as e:
                print(f"❌ JSON Decode error in CV generation: {e}\nRaw JSON: {json_string}")
        else:
            print(f"❌ No JSON structure found in CV generation. Raw response: {raw_response}")
        return {}