import os
import sys

# Ensure project root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

from utils.llm_handler import LLMHandler
from utils.cv_generator_html import generate_html_cv
import json

class TestCVGenerator:
    def __init__(self):
        self.llm = LLMHandler()

    def run_test(self):
        print("🚀 Starting CV Generation Test...")

        # 1. Mock Data
        job_title = "Senior Python/Django Developer"
        job_description = """
        We are looking for a backend developer with 3+ years of experience in Python and Django.
        You will be building scalable APIs, integrating with AWS, and managing PostgreSQL databases.
        Experience with Docker, CI/CD, and Redis is highly desirable.
        Responsibilities:
        - Design and implement REST APIs
        - Optimize database queries
        - Mentor junior developers
        """

        profile_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": ["+1 555 123 4567", "+44 20 7946 0958"],
            "city": "New York, USA",
            "github": "https://github.com/johndoe",
            "linkedin": "https://linkedin.com/in/johndoe"
        }

        user_stack = "Python, Django, FastAPI, PostgreSQL, Docker, AWS, React"

        base_cv_text = """
        Work Experience:
        Company: Acme Corp
        Title: Backend Engineer
        Dates: Jan 2021 - Present
        - Wrote some python scripts
        - Managed a local database
        - Helped the team with deployments

        Company: TechStart Inc
        Title: Junior Developer
        Dates: 2019 - 2021
        - Built web pages
        - Learned SQL
        
        Education:
        B.S. in Computer Science, Tech University, 2019
        """

        # 2. Generate JSON using LLM
        print("\n🧠 Sending data to LLM (Generating CV JSON)...")
        print(f"Target Role: {job_title}")
        
        ai_recommendations = self.llm.generate_cv_json(
            job_title=job_title,
            job_description=job_description,
            profile_data=profile_data,
            user_stack=user_stack,
            base_cv_text=base_cv_text
        )

        if not ai_recommendations:
            print("❌ LLM failed to return valid JSON.")
            return

        print("\n✅ LLM Output JSON:")
        print(json.dumps(ai_recommendations, indent=2, ensure_ascii=False))

        # 3. Generate HTML/PDF CV
        print("\n📄 Generating PDF CV via Playwright...")
        company_name = "TestCompany_LLM_CV"
        output_path = generate_html_cv(
            company_name=company_name,
            ai_recommendations=ai_recommendations,
            profile_data=profile_data
        )

        print(f"\n🎉 Test Complete! Check the generated file at: {output_path}")


if __name__ == "__main__":
    tester = TestCVGenerator()
    tester.run_test()
