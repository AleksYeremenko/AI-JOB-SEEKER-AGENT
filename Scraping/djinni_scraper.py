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
        if "login" in page.url or page.ele("text:Sign in") or page.ele("text:Увійти") or page.ele("text:Войти"):
            print("⚠️ [Djinni] Warning: Not logged in. Djinni hides results for unauthorized users.")
            print("🔄 [Djinni] Перезапускаю браузер в видимом режиме для ручной авторизации...")
            page.quit()
            
            co.headless(False)
            page = ChromiumPage(co)
            page.get("https://djinni.co/login")
            print("⏳ У вас есть 60 секунд, чтобы войти в аккаунт...")
            
            for _ in range(30):
                time.sleep(2)
                if "login" not in page.url and not page.ele("text:Sign in") and not page.ele("text:Увійти"):
                    print("✅ Успешная авторизация! Продолжаем парсинг.")
                    break
            else:
                print("⚠️ Время вышло. Парсинг может выдать 0 результатов.")
                
            page.get(search_url)
            time.sleep(4)
            
        # Parse job cards using BeautifulSoup for robustness
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(page.html, 'html.parser')
        job_links = soup.find_all('a', href=re.compile(r'/jobs/\d+-'))
        
        print(f"✅ [Djinni] Found {len(job_links)} jobs on page 1.")
        
        for l in job_links:
            try:
                # The new Djinni layout wraps the whole header in an 'a' tag
                href = l.get('href')
                link = "https://djinni.co" + href if href and not href.startswith('http') else href
                
                title_ele = l.find('h2')
                if not title_ele:
                    # Fallback if h2 is missing, just use the first text line
                    title = l.text.strip().split('\n')[0]
                else:
                    title = title_ele.text.strip()
                    
                company = "Unknown"
                company_span = l.find('span', class_='text-gray-800')
                if company_span:
                    company = company_span.text.strip()
                
                # Description usually in the parent card
                desc = ""
                parent_card = l.find_parent('div', class_=re.compile(r'job-item'))
                if parent_card:
                    desc = parent_card.text.strip()
                
                jobs.append({
                    "title": title,
                    "company": company,
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
