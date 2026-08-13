import json
from utils.cv_generator_html import generate_html_cv

ai_rec = {
  "title": "Senior Python/Django Developer",
  "summary": "Backend developer with extensive experience in building scalable REST APIs using Python and Django framework. Proven track record of optimizing PostgreSQL databases for performance and implementing CI/CD pipelines with Docker.",
  "skills": [
    "Python", "Django", "FastAPI", "PostgreSQL", "AWS", "Docker", "CI/CD", "Redis"
  ],
  "education": "B.S. Computer Science, Tech University (2019)",
  "jobs": [
    {
      "title": "Backend Engineer",
      "company": "Acme Corp",
      "dates": "2020 - Present",
      "description": [
        "Developed and maintained RESTful APIs using Django REST Framework",
        "Designed database schema in PostgreSQL",
        "Implemented CI/CD pipeline with GitHub Actions"
      ]
    }
  ]
}

prof_data = {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone": "+1 234 567 890",
    "city": "New York",
    "linkedin": "linkedin.com/in/johndoe",
    "github": "github.com/johndoe"
}

themes = ["modern", "minimalist", "creative", "it_tech"]

for theme in themes:
    print(f"Generating {theme} theme...")
    generate_html_cv(f"Test_{theme}", ai_rec, prof_data, theme=theme)

print("✅ All themes generated in Data/ directory!")
