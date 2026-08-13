import os
import time
from playwright.sync_api import sync_playwright

def get_html_template(template_name="Classic_ATS.html"):
    template_path = os.path.join("Data", "templates", template_name)
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        # Fallback to default
        fallback = os.path.join("Data", "templates", "Classic_ATS.html")
        if os.path.exists(fallback):
            with open(fallback, "r", encoding="utf-8") as f:
                return f.read()
        return "<html><body><h1>Template Not Found</h1></body></html>"

def format_contact_info(profile_data, separator=" | "):
    email = profile_data.get('email', '')
    phone = profile_data.get('phone', '')
    city = profile_data.get('city', '')
    linkedin = profile_data.get('linkedin', '')
    
    if isinstance(phone, list): phone = separator.join(phone)
    parts = [p for p in [email, phone, city, linkedin] if p]
    return separator.join(parts)

def format_contact_info_list(profile_data):
    email = profile_data.get('email', '')
    phone = profile_data.get('phone', '')
    city = profile_data.get('city', '')
    linkedin = profile_data.get('linkedin', '')
    
    if isinstance(phone, list): phone = " | ".join(phone)
    parts = [p for p in [email, phone, city, linkedin] if p]
    return "".join([f'<div class="contact-item">{p}</div>' for p in parts])

def safe_str(val):
    if not val:
        return ""
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return "\n".join(safe_str(v) for v in val)
    if isinstance(val, dict):
        return "\n".join(f"{safe_str(k)}: {safe_str(v)}" for k, v in val.items())
    return str(val)

def generate_custom_cv(company_name, ai_recommendations, profile_data, output_path=None, template_name="Classic_ATS.html"):
    if output_path is None or output_path.endswith(".docx"):
        output_path = f"Data/CV_{company_name}.pdf"
        
    os.makedirs("Data", exist_ok=True)
    template = get_html_template(template_name)
    
    # Names & Contact
    template = template.replace("{{FIRST_NAME}}", safe_str(profile_data.get('first_name', 'Name')))
    template = template.replace("{{LAST_NAME}}", safe_str(profile_data.get('last_name', 'Surname')))
    template = template.replace("{{CONTACT_INFO}}", format_contact_info(profile_data, " | "))
    template = template.replace("{{CONTACT_INFO_BR}}", format_contact_info(profile_data, "<br/>"))
    template = template.replace("{{CONTACT_INFO_LIST}}", format_contact_info_list(profile_data))
    template = template.replace("{{SUMMARY}}", safe_str(ai_recommendations.get('summary', '')))
    
    # Skills
    skills_raw = ai_recommendations.get('skills', [])
    if isinstance(skills_raw, str):
        skills_list = [s.strip() for s in skills_raw.split(',') if s.strip()]
    else:
        skills_list = skills_raw
        
    template = template.replace("{{SKILLS}}", " • ".join(skills_list))
    template = template.replace("{{SKILLS_TAGS}}", "".join([f'<span class="skill-tag">{s}</span>' for s in skills_list]))
    template = template.replace("{{SKILLS_BADGES}}", "".join([f'<span class="skill-badge">{s}</span>' for s in skills_list]))
    
    # Experience
    jobs = ai_recommendations.get('jobs', [])
    
    exp_classic = ""
    exp_modern = ""
    exp_creative = ""
    
    for job in jobs:
        j_title = job.get("title", "Position")
        j_comp = job.get("company", "Company")
        
        # Parse bullets
        bullets = []
        desc = job.get('description', '')
        if isinstance(desc, list):
            for point in desc:
                if isinstance(point, dict):
                    bullets.append(next(iter(point.values()), ""))
                else:
                    bullets.append(str(point))
        elif isinstance(desc, str):
            bullets = [p.strip() for p in desc.replace('•', '\n').split('\n') if p.strip()]
            
        bullets_html = '<ul>' + "".join([f'<li>{b}</li>' for b in bullets]) + '</ul>'
        
        # Classic
        exp_classic += f'<div style="margin-bottom:15px;"><div class="job-title">{j_title}</div><div class="company">{j_comp}</div><div class="clear"></div>{bullets_html}</div>'
        
        # Modern
        exp_modern += f'<div class="job-entry"><div class="job-header"><span class="job-title">{j_title}</span><span class="company">{j_comp}</span></div>{bullets_html}</div>'
        
        # Creative
        exp_creative += f'<div class="job-entry"><div class="job-title">{j_title}</div><div class="company">{j_comp}</div>{bullets_html}</div>'
    
    template = template.replace("{{EXPERIENCE_CLASSIC}}", exp_classic)
    template = template.replace("{{EXPERIENCE_MODERN}}", exp_modern)
    template = template.replace("{{EXPERIENCE_CREATIVE}}", exp_creative)
    
    # Education
    template = template.replace("{{EDUCATION}}", safe_str(ai_recommendations.get('education', '')))
    
    # Save temporary HTML
    temp_html_path = f"Data/temp_cv_{company_name}.html"
    with open(temp_html_path, "w", encoding="utf-8") as f:
        f.write(template)
        
    # PDF
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('file://' + os.path.abspath(temp_html_path))
        page.pdf(path=output_path, format="A4", print_background=True, margin={"top": "0px", "bottom": "0px", "left": "0px", "right": "0px"})
        browser.close()
        
    try: os.remove(temp_html_path)
    except: pass
        
    print(f"📄 Generated {template_name} -> PDF: {output_path}")
    return output_path