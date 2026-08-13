import os
import json
import random
from playwright.sync_api import sync_playwright

def get_css_theme(theme_name):
    themes = {
        "modern": """
            body { font-family: 'Inter', sans-serif; background: white; display: flex; }
            .left-col { width: 35%; background-color: #1A237E; color: white; padding: 40px; box-sizing: border-box; }
            .right-col { width: 65%; background-color: #FFFFFF; color: #333; padding: 40px; box-sizing: border-box; }
            .first-name { font-size: 36px; font-weight: 300; margin: 0; text-transform: uppercase; letter-spacing: 2px; }
            .last-name { font-size: 36px; font-weight: 700; margin: 0; text-transform: uppercase; letter-spacing: 2px; }
            .title { font-size: 18px; color: #1A237E; font-weight: 600; margin-top: 10px; text-transform: uppercase; }
            .section-title-left { font-size: 16px; font-weight: 600; text-transform: uppercase; border-bottom: 2px solid #3F51B5; padding-bottom: 5px; margin-top: 30px; margin-bottom: 15px; }
            .section-title-right { font-size: 20px; font-weight: 700; color: #1A237E; text-transform: uppercase; border-bottom: 2px solid #E0E0E0; padding-bottom: 5px; margin-top: 30px; margin-bottom: 15px; }
            .skill-tag { background-color: rgba(255, 255, 255, 0.1); padding: 5px 10px; border-radius: 4px; font-size: 11px; }
            .job-company { font-size: 14px; font-weight: 600; color: #1A237E; margin-bottom: 8px; }
        """,
        "minimalist": """
            body { font-family: 'Inter', sans-serif; background: white; display: block; padding: 40px; }
            .left-col { width: 100%; color: #222; padding: 0 0 20px 0; border-bottom: 1px solid #ddd; }
            .right-col { width: 100%; color: #333; padding: 20px 0; }
            .first-name, .last-name { display: inline-block; font-size: 42px; font-weight: 400; letter-spacing: -1px; margin: 0; }
            .last-name { font-weight: 700; margin-left: 10px; }
            .title { font-size: 16px; color: #666; font-weight: 400; margin-top: 5px; }
            .section-title-left, .section-title-right { font-size: 14px; font-weight: 700; color: #111; text-transform: uppercase; letter-spacing: 2px; border-bottom: 1px solid #111; padding-bottom: 5px; margin-top: 25px; margin-bottom: 15px; }
            .contact-item { display: inline-block; margin-right: 15px; font-size: 12px; color: #555; }
            .skill-container { display: flex; flex-wrap: wrap; gap: 8px; }
            .skill-tag { border: 1px solid #ddd; padding: 4px 10px; border-radius: 20px; font-size: 11px; color: #444; }
            .job-title { font-size: 16px; font-weight: 600; }
            .job-company { font-size: 14px; color: #555; font-style: italic; }
            .job-dates { float: right; font-size: 12px; font-style: normal; color: #888; }
        """,
        "creative": """
            body { font-family: 'Inter', sans-serif; background: #FAFAFA; display: flex; flex-direction: row-reverse; }
            .left-col { width: 30%; background-color: #FFDEE9; background-image: linear-gradient(0deg, #FFDEE9 0%, #B5FFFC 100%); color: #333; padding: 40px; box-sizing: border-box; border-left: 2px solid #fff; }
            .right-col { width: 70%; background-color: #FFFFFF; color: #444; padding: 40px; box-sizing: border-box; }
            .name-box { border-left: 5px solid #FF8A80; padding-left: 15px; }
            .first-name { font-size: 40px; font-weight: 700; margin: 0; color: #2D3436; }
            .last-name { font-size: 40px; font-weight: 300; margin: 0; color: #2D3436; }
            .title { font-size: 18px; color: #FF8A80; font-weight: 600; margin-top: 5px; letter-spacing: 1px; }
            .section-title-left { font-size: 16px; font-weight: 700; color: #2D3436; margin-top: 30px; margin-bottom: 15px; background: rgba(255,255,255,0.5); padding: 5px 10px; border-radius: 5px; }
            .section-title-right { font-size: 22px; font-weight: 700; color: #2D3436; margin-top: 30px; margin-bottom: 20px; position: relative; }
            .section-title-right::after { content: ''; position: absolute; left: 0; bottom: -5px; width: 40px; height: 3px; background: #B5FFFC; }
            .skill-tag { background-color: #FFFFFF; color: #FF8A80; padding: 5px 12px; border-radius: 15px; font-size: 11px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
            .job { background: #fff; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); border: 1px solid #f0f0f0; margin-bottom: 20px; }
            .job-company { color: #00B894; font-weight: 600; }
        """,
        "it_tech": """
            body { font-family: 'Courier New', Courier, monospace; background: #1E1E1E; color: #D4D4D4; display: block; padding: 40px; }
            .left-col { width: 100%; border-bottom: 1px dashed #569CD6; padding-bottom: 20px; mb-20px; }
            .right-col { width: 100%; padding-top: 20px; }
            .first-name, .last-name { display: inline-block; font-size: 32px; font-weight: bold; color: #4EC9B0; margin: 0; }
            .last-name { color: #CE9178; margin-left: 10px; }
            .title { font-size: 16px; color: #569CD6; margin-top: 10px; }
            .title::before { content: '> '; color: #DCDCAA; }
            .section-title-left, .section-title-right { font-size: 18px; color: #C586C0; margin-top: 30px; margin-bottom: 15px; }
            .section-title-left::before, .section-title-right::before { content: '## '; color: #808080; }
            .contact-item { display: inline-block; margin-right: 20px; color: #9CDCFE; font-size: 12px; }
            .contact-item strong { color: #569CD6; }
            .skill-tag { background: #2D2D2D; color: #4EC9B0; border: 1px solid #404040; padding: 4px 8px; font-size: 11px; margin-right: 5px; margin-bottom: 5px; display: inline-block; }
            .job-title { color: #DCDCAA; font-size: 16px; font-weight: bold; margin-bottom: 5px; }
            .job-company { color: #9CDCFE; font-size: 14px; }
            .job-dates { color: #6A9955; font-size: 12px; }
            .summary { color: #CE9178; }
            .job-desc { color: #D4D4D4; }
            .education { color: #4EC9B0; }
        """
    }
    return themes.get(theme_name, themes["modern"])

def generate_html_cv(company_name, ai_recommendations, profile_data, output_path=None, theme="random"):
    if output_path is None:
        os.makedirs("Data", exist_ok=True)
        output_path = f"Data/CV_{company_name}.pdf"
        
    if theme == "random":
        theme = random.choice(["modern", "minimalist", "creative", "it_tech"])

    # Extract Data
    first_name = profile_data.get('first_name', 'Alex')
    last_name = profile_data.get('last_name', 'Developer')
    email = profile_data.get('email', 'alex@example.com')
    
    phone_raw = profile_data.get('phone', '')
    phone = " | ".join(phone_raw) if isinstance(phone_raw, list) else phone_raw
    
    city = profile_data.get('city', '')
    linkedin = profile_data.get('linkedin', '')
    github = profile_data.get('github', '')
    
    title = ai_recommendations.get('title', 'Software Engineer')
    summary = ai_recommendations.get('summary', '')
    
    skills_raw = ai_recommendations.get('skills', [])
    if isinstance(skills_raw, str):
        skills = [s.strip() for s in skills_raw.split(',')]
    else:
        skills = skills_raw

    jobs = ai_recommendations.get('jobs', [])
    
    # Render Skills HTML
    skills_html = "".join([f"<span class='skill-tag'>{s}</span>" for s in skills])
    
    # Render Jobs HTML
    jobs_html = ""
    for job in jobs:
        desc = job.get('description', [])
        if isinstance(desc, str):
            desc = [d.strip() for d in desc.replace('•', '\n').split('\n') if d.strip()]
            
        # Clean up any hyphens the LLM might have still inserted
        desc_html = "".join([f"<li>{d.lstrip('-• *')}</li>" for d in desc])
        
        jobs_html += f"""
        <div class="job">
            <div class="job-title">{job.get('title', '')}</div>
            <div class="job-company">{job.get('company', '')} <span class="job-dates">| {job.get('dates', '')}</span></div>
            <ul class="job-desc">
                {desc_html}
            </ul>
        </div>
        """
        
    education = ai_recommendations.get('education', '')
    if isinstance(education, dict):
        edu_html = f"<strong>{education.get('degree', '')}</strong><br>{education.get('institution', '')} | {education.get('year', '')}"
    else:
        edu_html = str(education)
        
    css_theme = get_css_theme(theme)

    # Canva-like Modern HTML/CSS Template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
            
            /* Common Base */
            body {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                width: 210mm;
                height: 297mm; /* A4 size */
            }}
            .contact-item {{ margin-bottom: 5px; word-break: break-all; }}
            .job-desc {{ margin-top: 5px; padding-left: 18px; font-size: 13px; line-height: 1.5; }}
            .job-desc li {{ margin-bottom: 4px; }}
            .summary {{ font-size: 13px; line-height: 1.6; }}
            .education {{ font-size: 13px; line-height: 1.5; }}
            
            /* Dynamic Theme CSS */
            {css_theme}
        </style>
    </head>
    <body>
        <div class="left-col">
            <div class="section-title-left" style="margin-top: 0;">Contact</div>
            <div class="contact-item"><strong>E:</strong> {email}</div>
            <div class="contact-item"><strong>P:</strong> {phone}</div>
            <div class="contact-item"><strong>L:</strong> {city}</div>
            {f'<div class="contact-item"><strong>IN:</strong> {linkedin}</div>' if linkedin else ''}
            {f'<div class="contact-item"><strong>GH:</strong> {github}</div>' if github else ''}
            
            <div class="section-title-left">Skills</div>
            <div class="skill-container">
                {skills_html}
            </div>
        </div>
        
        <div class="right-col">
            <div class="name-box">
                <h1 class="first-name">{first_name}</h1>
                <h1 class="last-name">{last_name}</h1>
                <div class="title">{title}</div>
            </div>
            
            <div class="section-title-right">Profile</div>
            <div class="summary">{summary}</div>
            
            <div class="section-title-right">Experience</div>
            {jobs_html}
            
            <div class="section-title-right">Education</div>
            <div class="education">{edu_html}</div>
        </div>
    </body>
    </html>
    """
    
    html_path = output_path.replace('.pdf', '.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # Set to local path
            page.goto(f"file://{os.path.abspath(html_path)}")
            # Wait for fonts to load
            page.evaluate("document.fonts.ready")
            page.pdf(
                path=output_path,
                format="A4",
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}
            )
            browser.close()
            
        print(f"[OK] CV generated ({theme} theme): {output_path}")
        return output_path
    except Exception as e:
        print(f"[Error] Playwright PDF generation failed: {e}")
        print("Fallback: Using HTML template instead.")
        return html_path
