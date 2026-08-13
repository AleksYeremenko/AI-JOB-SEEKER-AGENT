import time
import os
import urllib.parse
from DrissionPage import ChromiumPage, ChromiumOptions

def scrape_djinni(keyword, seniority_filter="Junior", settings=None):
    print(f"🔍 [Djinni] Starting scrape for: {keyword}...")
    
    co = ChromiumOptions()
    co.set_user_data_path(os.path.abspath("Data/job_boards_profile"))
    co.headless(True)
    co.set_argument('--disable-blink-features=AutomationControlled')
    
    jobs = []
    try:
        page = ChromiumPage(co)
    except Exception as e:
        print(f"⚠️ [Djinni] Error launching browser: {e}")
        return jobs
        
    try:
        # Determine exp level
        exp = "no_exp"
        if "Junior" in seniority_filter: exp = "1y"
        elif "Mid" in seniority_filter: exp = "2y"
        elif "Senior" in seniority_filter or "Lead" in seniority_filter: exp = "5y"
        
        safe_keyword = urllib.parse.quote_plus(keyword)
        search_url = f"https://djinni.co/jobs/?all-keywords={safe_keyword}&exp_level={exp}"
        page.get(search_url)
        time.sleep(4)
        
        # Check login
        if "login" in page.url or page.ele("text:Sign in"):
            print("⚠️ [Djinni] Warning: Not logged in. Results may be limited.")
            
        # Parse job cards (Djinni's standard UI)
        job_items = page.eles('css:.job-item')
        if not job_items:
            # Fallback for older Djinni layout
            job_items = page.eles('css:.list-jobs__item')
            
        print(f"✅ [Djinni] Found {len(job_items)} jobs on page 1.")
        
        for item in job_items:
            try:
                title_ele = item.ele('css:.job-item__position', timeout=1)
                link_ele = item.ele('tag:a@@class:job_item__header-link', timeout=1)
                
                if not title_ele:
                    title_ele = item.ele('css:.job-list-item__link', timeout=1)
                if not title_ele: continue
                
                title = title_ele.text
                link = link_ele.attr('href') if link_ele else item.ele('tag:a').attr('href')
                if link and not link.startswith('http'): link = "https://djinni.co" + link
                
                # Description usually inside id=job-description-XXXXX
                desc = item.text
                
                company = "Unknown"
                company_ele = item.ele('css:header > a', timeout=1)
                if not company_ele:
                    company_ele = item.ele('css:header span.text-gray-800', timeout=1)
                
                if company_ele:
                    company = company_ele.text
                else:
                    # Alternative company element
                    comp_alt = item.ele('css:.job-list-item__counts a', timeout=1)
                    if comp_alt: company = comp_alt.text
                
                jobs.append({
                    "title": title,
                    "company": company.strip(),
                    "link": link,
                    "description": desc,
                    "source": "Djinni"
                })
            except Exception as e:
                continue
    except Exception as e:
        print(f"⚠️ [Djinni] Error scraping: {e}")
    finally:
        page.quit()
        
    return jobs
