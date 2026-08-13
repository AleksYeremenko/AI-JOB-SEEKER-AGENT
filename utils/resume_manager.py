import os
import PyPDF2
from utils.cv_generator import generate_custom_cv

class ResumeManager:
    def __init__(self, applications_dir="Applications"):
        self.applications_dir = applications_dir
        if not os.path.exists(self.applications_dir):
            os.makedirs(self.applications_dir)

    def extract_text_from_pdf(self, pdf_path):
        """Читает текст из твоего базового резюме"""
        text = ""
        try:
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        text += page.extract_text() + "\n"
            else:
                print(f"⚠️ Файл {pdf_path} не найден! ИИ будет работать вслепую.")
        except Exception as e:
            print(f"❌ Ошибка PDF: {e}")
        return text

    def analyze_my_cv(self, llm, raw_text):
        """Вытаскивает твой реальный стек технологий"""
        if not raw_text.strip():
            return "Java, .NET, SQL, PostgreSQL, Docker, Git/GitHub, Agile, REST API, React, HTTP"

        prompt = f"Извлеки из этого резюме список всех технологий, фреймворков и инструментов через запятую. Верни ТОЛЬКО список:\n{raw_text[:4000]}"
        result = llm.ask(prompt)
        if "REJECT" in result.upper() or len(result) < 5:
            return "Java, Python, SQL, Docker, Git"
        return result

    def save_application_files(self, company, cover_letter, cv_title, cv_skills, cv_summary, j1_title, j1_desc, j2_title, j2_desc, j3_title, j3_desc):
        """Создает папку компании и генерирует туда DOCX и TXT файлы"""
        safe_company_name = "".join([c for c in company if c.isalpha() or c.isdigit() or c == ' ']).rstrip()
        company_dir = os.path.join(self.applications_dir, safe_company_name)

        if not os.path.exists(company_dir):
            os.makedirs(company_dir)

        letter_path = os.path.join(company_dir, f"Cover_Letter_{safe_company_name}.txt")
        with open(letter_path, "w", encoding="utf-8") as f:
            f.write(cover_letter)

        cv_output_path = os.path.join(company_dir, f"CV_{safe_company_name}.docx")

        # Передаем данные в генератор (из твоего корня)
        generate_custom_cv(safe_company_name, {
            "title": cv_title,
            "skills": cv_skills,
            "summary": cv_summary,
            "job1_title": j1_title,
            "job1_description": j1_desc,
            "job2_title": j2_title,
            "job2_description": j2_desc,
            "job3_title": j3_title,
            "job3_description": j3_desc
        }, output_path=cv_output_path)

        return cv_output_path, company_dir