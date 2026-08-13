import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import concurrent.futures


class UniversalScraper:
    """Heavy scraper: 6 Polish job boards"""

    def __init__(self, skills, seniority_filter="Junior", city="", seen_jobs=None, settings=None):
        self.settings = settings
        self.seen_jobs = seen_jobs if seen_jobs else set()
        self.keyword = skills[0] if skills else "Developer"
        self.safe_keyword = urllib.parse.quote_plus(self.keyword)
        self.seniority_filter = seniority_filter
        self.city = city
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def is_fresh_enough(self, text):
        text = text.lower()
        if any(re.search(m, text) for m in
               [r'\bnowa\b', r'\bdzisiaj\b', r'\btoday\b', r'\b[1-9]h\b', r'\bjust now\b']): return 3
        if any(re.search(m, text) for m in [r'\bwczoraj\b', r'\byesterday\b', r'\b1 d\b', r'\b2 d\b']): return 3
        match = re.search(r'(\d+)\s*(dni|d|days?)\s*(left|zostało)', text)
        if not match: match = re.search(r'(zostało|left)\s*(\d+)\s*(dni|d|days?)', text)
        if match:
            nums = re.findall(r'\d+', match.group(0))
            if nums:
                days_left = int(nums[0])
                if days_left >= 28: return 3
                if days_left >= 15: return 2
                return 1
        return 2

    def is_junior_card(self, title, card_elem):
        """Фильтрует позиции по seniority уровню (Твоя обновленная логика)"""
        text_lower = title.lower()

        if card_elem and hasattr(card_elem, 'stripped_strings'):
            text_blocks = [text.lower() for text in card_elem.stripped_strings]
            text_lower += " " + " ".join(text_blocks)

        # Если ищем Junior/Mid - исключаем Senior+
        if "Junior" in self.seniority_filter or "Mid" in self.seniority_filter:
            exclude_words = ['senior', 'lead', 'architect', 'head', 'principal', 'staff', 'manager', 'director', 'vp',
                             'sr', 'sr.']
            for word in exclude_words:
                if re.search(r'\b' + word + r'\b', text_lower):
                    return False

        # Если ищем Senior/Lead - показываем все (или можешь добавить фильтр на 'junior')
        return True

    def fetch_full_job_page(self, job_dict):
        """Скачивает текст вакансии (работает в отдельном потоке)"""
        url = job_dict['link']
        try:
            res = requests.get(url, headers=self.headers, timeout=7)
            if res.status_code != 200: return None

            raw_html = res.text.lower()
            if re.search(r'\b(niemiecki|german|deutsch)\b', raw_html) and re.search(
                    r'\b(c1|c2|b2|native)\s*(niemiecki|german|deutsch)\b', raw_html):
                return None

            soup = BeautifulSoup(res.text, 'html.parser')
            full_text = soup.get_text(separator=" | ", strip=True)

            priority = self.is_fresh_enough(full_text)
            if priority > 0:
                job_dict['details'] = full_text[:4000]
                job_dict['priority'] = priority
                return job_dict
        except Exception:
            pass
        return None

    def scrape_direct_link(self, link):
        try:
            job_dict = {"title": "Developer (Direct)", "company": "Direct Email", "link": link, "source": "Email"}
            return self.fetch_full_job_page(job_dict)
        except Exception:
            return None

    def scrape_justjoin(self):
        print(f"🔍 [JustJoin.it] Собираю карточки: {self.keyword}...")
        pending = []

        # JustJoin.it — SPA (React), requests.get() не получает HTML с вакансиями
        # Используем их JSON API напрямую
        api_urls = [
            f"https://api.justjoin.it/v2/user-panel/offers?categories[]={self.keyword.lower()}&page=1&sortBy=published&orderBy=DESC&perPage=100",
            "https://justjoin.it/api/offers",
        ]

        for api_url in api_urls:
            try:
                api_headers = {**self.headers, "Accept": "application/json", "Version": "2"}
                res = requests.get(api_url, headers=api_headers, timeout=15)
                if res.status_code != 200:
                    continue

                data = res.json()

                # API v2 возвращает {"data": [...], "meta": {...}}
                # Старый API возвращает просто [...]
                offers = data.get("data", data) if isinstance(data, dict) else data
                if not isinstance(offers, list):
                    continue

                keyword_lower = self.keyword.lower()

                # Дебаг: показываем структуру первого оффера
                if offers:
                    first = offers[0]
                    print(f"  🔑 [JustJoin.it API] Ключи первого оффера: {list(first.keys())[:15]}")

                for offer in offers:
                    try:
                        # Пробуем все возможные ключи для title
                        title = (offer.get("title")
                                 or offer.get("jobTitle")
                                 or offer.get("name")
                                 or offer.get("position")
                                 or "Developer")

                        # Пробуем все возможные ключи для company
                        company = (offer.get("companyName")
                                   or offer.get("company_name")
                                   or offer.get("company")
                                   or offer.get("employer")
                                   or "Unknown")
                        if isinstance(company, dict):
                            company = company.get("name", "Unknown")

                        # Строим ссылку — API может возвращать полный URL или slug
                        slug = (offer.get("slug")
                                or offer.get("id")
                                or offer.get("url")
                                or offer.get("offerUrl")
                                or offer.get("offer_url")
                                or "")

                        if not slug:
                            continue

                        # Если slug уже полный URL — используем как есть
                        if slug.startswith("http"):
                            link = slug
                        elif slug.startswith("/"):
                            link = f"https://justjoin.it{slug}"
                        else:
                            link = f"https://justjoin.it/job-offer/{slug}"

                        if link in self.seen_jobs:
                            continue

                        # Фильтр по seniority
                        if not self.is_junior_card(title, None):
                            continue

                        # Фильтр по ключевому слову (в title или skills)
                        skills_list = offer.get("skills", offer.get("requiredSkills", []))
                        skills_text = " ".join([
                            s.get("name", s) if isinstance(s, dict) else str(s) for s in skills_list
                        ]).lower()
                        search_text = f"{title} {skills_text}".lower()

                        if keyword_lower not in search_text and keyword_lower not in title.lower():
                            category = offer.get("marker_icon", offer.get("category", "")).lower()
                            if keyword_lower not in category:
                                continue

                        # Описание из API (если есть)
                        description = offer.get("body", offer.get("description", ""))

                        pending.append({
                            "title": title,
                            "company": company,
                            "link": link,
                            "source": "JustJoin.it",
                            "description": description[:4000] if description else "",
                            "details": description[:4000] if description else "",
                            "priority": 3
                        })

                        if len(pending) >= 150:
                            break
                    except Exception:
                        continue

                if pending:
                    print(f"  ✅ [JustJoin.it API] Найдено {len(pending)} вакансий")
                    return pending

            except Exception as e:
                print(f"  ⚠️ [JustJoin.it API] Ошибка: {e}")
                continue

        print("  ⚠️ [JustJoin.it] Переход на запасной HTML-парсер...")
        # Fallback: старый HTML-парсинг (может сработать если API умрёт)
        cat = {"qa automation": "testing", "security analyst": "security", "cybersecurity": "security",
               "cloud engineer": "devops", "system administrator": "admin", "linux": "admin",
               "support engineer": "support"}.get(self.keyword.lower(), self.keyword.lower().replace(' ', '-'))
        try:
            res = requests.get(f"https://justjoin.it/job-offers/all-locations/{cat}", headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                if '/job-offer/' in a_tag['href']:
                    href = a_tag['href']
                    if href.startswith('http'):
                        link = href
                    else:
                        link = f"https://justjoin.it{href}" if href.startswith('/') else f"https://justjoin.it/{href}"
                    if link in self.seen_jobs: continue
                    title_elem = a_tag.find('h2')
                    
                    if title_elem:
                        title = title_elem.text.strip()
                    else:
                        # Достаём title из slug (например, /job-offer/company-name-junior-java-developer)
                        try:
                            slug = link.split('/')[-1]
                            title = slug.replace('-', ' ').title()
                        except:
                            title = "Developer"

                    if self.is_junior_card(title, a_tag):
                        try:
                            comp = link.split('/')[4].split('-')[0].capitalize()
                        except:
                            comp = "Unknown"
                        pending.append({"title": title, "company": comp, "link": link, "source": "JustJoin.it"})
                        if len(pending) >= 150: break
        except Exception:
            pass
        return pending

    def scrape_pracuj(self):
        print(f"🔍 [Pracuj.pl] Собираю карточки (через Playwright): {self.keyword}...")
        pending = []
        url = f"https://www.pracuj.pl/praca/{self.safe_keyword};kw"
        
        try:
            from playwright.sync_api import sync_playwright
            import time
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
                context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                page = context.new_page()
                try:
                    from playwright_stealth import Stealth
                    stealth = Stealth()
                    stealth.apply_stealth_sync(page)
                except ImportError:
                    pass

                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                print("  ⏳ [Pracuj.pl] Ждем прогрузки...")
                time.sleep(3)
                
                try:
                    page.wait_for_selector('div[data-test="default-offer"]', timeout=10000)
                except Exception:
                    print("  ⚠️ [Pracuj.pl] Карточки не прогрузились (возможно, капча Cloudflare).")
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(page.content(), 'html.parser')
                browser.close()
                
            for offer in soup.find_all('div', attrs={'data-test': 'default-offer'}):
                link_elem = offer.find(attrs={'data-test': 'offer-link'})
                href = ""
                if link_elem:
                    href = link_elem.get('href', '')
                else:
                    for a_tag in offer.find_all('a'):
                        h = a_tag.get('href', '')
                        if 'oferta,' in h or ('/praca/' in h and 'pracodawcy' not in h):
                            href = h
                            break
                
                if not href: continue
                
                if href.startswith('http'):
                    link = href
                else:
                    link = f"https://www.pracuj.pl{href}" if href.startswith('/') else f"https://www.pracuj.pl/{href}"
                
                if link in self.seen_jobs: continue
                
                title_elem = offer.find(attrs={'data-test': 'offer-title'})
                if title_elem:
                    title = title_elem.text.strip()
                else:
                    try:
                        slug = link.split('/praca/')[1].split(',')[0]
                        title = slug.replace('-', ' ').title()
                    except:
                        title = "Developer"
                        
                if self.is_junior_card(title, offer):
                    comp_elem = offer.find(attrs={'data-test': 'text-company-name'})
                    comp = comp_elem.text.strip() if comp_elem else "Unknown"
                    pending.append({"title": title, "company": comp, "link": link, "source": "Pracuj.pl"})
                    if len(pending) >= 150: break
                    
            print(f"  ✅ [Pracuj.pl] Собрано {len(pending)} ссылок.")
        except Exception as e:
            print(f"  ⚠️ [Pracuj.pl] Ошибка Playwright: {e}")

        return pending

    def scrape_nofluffjobs(self):
        print(f"🔍 [NoFluffJobs] Собираю карточки: {self.keyword}...")
        pending = []
        try:
            res = requests.get(f"https://nofluffjobs.com/pl/jobs?criteria=requirement%3D{self.safe_keyword}",
                               headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for item in soup.find_all('a', href=re.compile(r'/pl/job/')):
                link = "https://nofluffjobs.com" + item['href']
                if link in self.seen_jobs: continue
                title_elem = item.find('h3')
                title = title_elem.text.strip() if title_elem else "Developer"
                if self.is_junior_card(title, item):
                    comp_elem = item.find(attrs={'data-cy': 'company-name'}) or item.find('span', class_=re.compile(
                        r'truncate'))
                    comp = comp_elem.text.strip() if comp_elem else "Unknown"
                    pending.append({"title": title, "company": comp, "link": link, "source": "NoFluffJobs"})
                    if len(pending) >= 150: break
        except Exception:
            pass
        return pending

    def scrape_bulldogjob(self):
        print(f"🔍 [Bulldogjob] Собираю карточки: {self.keyword}...")
        pending = []
        try:
            res = requests.get(f"https://bulldogjob.pl/companies/jobs?q={self.safe_keyword}", headers=self.headers,
                               timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for card in soup.find_all('a', class_=re.compile(r'JobCard_container')):
                link = card['href']
                if link in self.seen_jobs: continue
                title_elem = card.find('h2')
                title = title_elem.text.strip() if title_elem else "Developer"
                if self.is_junior_card(title, card):
                    comp_div = card.find('div', class_=re.compile(r'JobCard_companyName'))
                    comp = comp_div.text.strip() if comp_div else "Company"
                    pending.append({"title": title, "company": comp, "link": link, "source": "Bulldogjob"})
                    if len(pending) >= 150: break
        except Exception:
            pass
        return pending

    def scrape_theprotocol(self):
        print(f"🔍 [TheProtocol.it] Собираю карточки: {self.keyword}...")
        pending = []
        try:
            res = requests.get(f"https://theprotocol.it/filtry/{self.safe_keyword};kw?sort=date", headers=self.headers,
                               timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for offer in soup.find_all('a', href=re.compile(r'/szczegoly/oferta/')):
                link = "https://theprotocol.it" + offer['href']
                if link in self.seen_jobs: continue
                title_elem = offer.find('h2')
                title = title_elem.text.strip() if title_elem else "Developer"
                if self.is_junior_card(title, offer):
                    comp_elem = offer.find('div', attrs={'data-test': 'text-companyName'})
                    comp = comp_elem.text.strip() if comp_elem else "TheProtocol"
                    pending.append({"title": title, "company": comp, "link": link, "source": "TheProtocol"})
                    if len(pending) >= 150: break
        except Exception:
            pass
        return pending

    def scrape_solidjobs(self):
        print(f"🔍 [SolidJobs] Собираю карточки: {self.keyword}...")
        pending = []
        try:
            res = requests.get(f"https://solid.jobs/offers/it;search={self.safe_keyword}", headers=self.headers,
                               timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for offer in soup.find_all('div', class_='offer-container'):
                link_elem = offer.find('a', class_='offer-title')
                if not link_elem: continue
                link = "https://solid.jobs" + link_elem['href']
                if link in self.seen_jobs: continue
                title = link_elem.text.strip() if link_elem else "Developer"
                if self.is_junior_card(title, offer):
                    comp_elem = offer.find('a', class_='company-name')
                    comp = comp_elem.text.strip() if comp_elem else "SolidJobs"
                    pending.append({"title": title, "company": comp, "link": link, "source": "SolidJobs"})
                    if len(pending) >= 150: break
        except Exception:
            pass
        return pending

    def get_all_jobs(self):
        print(f"\n⚙️ [UniversalScraper] Starting Polish boards scraping | Level: {self.seniority_filter}...")
        pending_jobs = []
        pending_jobs.extend(self.scrape_pracuj())
        pending_jobs.extend(self.scrape_justjoin())
        pending_jobs.extend(self.scrape_nofluffjobs())
        pending_jobs.extend(self.scrape_bulldogjob())
        pending_jobs.extend(self.scrape_theprotocol())
        pending_jobs.extend(self.scrape_solidjobs())

        if not pending_jobs: return []

        print(f"⚡ Collected {len(pending_jobs)} links. Fetching texts...")
        all_jobs = []
        fetched_links = set()

        try:
            from utils.thread_manager import ThreadManager
            import threading
            
            # Using ThreadManager for real-time speed control
            tm = ThreadManager(self.settings) if self.settings else None
            
            def process_job(job):
                res = self.fetch_full_job_page(job)
                if res:
                    return res
                return None
                
            if tm:
                # Use ThreadManager
                lock = threading.Lock()
                def worker_wrapper(job):
                    res = process_job(job)
                    if res:
                        with lock:
                            self.seen_jobs.add(res['link'])
                            fetched_links.add(res['link'])
                            all_jobs.append(res)
                            
                tm.run_tasks(pending_jobs, worker_wrapper)
            else:
                # Fallback to ThreadPoolExecutor
                workers = max(1, int(20 * getattr(self.settings, 'work_speed', 100) / 100.0))
                with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = {executor.submit(process_job, job): job for job in pending_jobs}
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result:
                            self.seen_jobs.add(result['link'])
                            fetched_links.add(result['link'])
                            all_jobs.append(result)
                            
        except KeyboardInterrupt:
            print("\n🛑 Download interrupted by user. Returning what was collected.")
        except Exception as e:
            print(f"⚠️ Thread pool error: {e}")

        # Вакансии, для которых не удалось скачать полную страницу (JS-рендеринг, бот-защита)
        # Карточка уже содержит title, company, link, source — этого достаточно для apply
        unfetched_count = 0
        for job in pending_jobs:
            if job['link'] not in fetched_links and job['link'] not in self.seen_jobs:
                job['details'] = ''
                job['description'] = ''
                job['priority'] = 1
                self.seen_jobs.add(job['link'])
                all_jobs.append(job)
                unfetched_count += 1

        if unfetched_count > 0:
            print(f"📋 Added {unfetched_count} jobs without description (pages failed to load)")

        all_jobs.sort(key=lambda x: x.get('priority', 0), reverse=True)
        return all_jobs


# === Обертка для интеграции с AIJobSeekerApp.py ===
def scrape_polish_sites(tech_stack=None, seniority_filter="Junior", city="", settings=None):
    """Обертка для запуска польского парсера"""
    if tech_stack is None:
        tech_stack = ["Developer"]
    scraper = UniversalScraper(skills=tech_stack, seniority_filter=seniority_filter, city=city, settings=settings)
    return scraper.get_all_jobs()