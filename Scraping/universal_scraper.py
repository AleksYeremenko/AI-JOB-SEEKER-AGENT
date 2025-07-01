import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import concurrent.futures


class UniversalScraper:
    """Тяжелая артиллерия: 6 польских гигантов (Многопоточная версия)"""

    def __init__(self, skills, seen_jobs=None):
        self.seen_jobs = seen_jobs if seen_jobs else set()
        self.keyword = skills[0] if skills else "Developer"
        self.safe_keyword = urllib.parse.quote_plus(self.keyword)
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
        title_stops = ['senior', 'sr', 'sr.', 'lead', 'manager', 'head', 'principal', 'expert', 'architect', 'staff',
                       'cto', 'director', 'vp']
        if any(re.search(r'\b' + word + r'\b', title.lower()) for word in title_stops): return False

        bad_badges = {'senior', 'expert', 'lead', 'principal', 'staff', 'sr', 'cto', 'manager', 'head', 'architect'}
        good_badges = {'junior', 'trainee', 'intern', 'młodszy', 'mid', 'regular', 'middle', 'mid / regular',
                       'regular / mid'}

        if card_elem and hasattr(card_elem, 'stripped_strings'):
            text_blocks = [text.lower() for text in card_elem.stripped_strings]
            for block in text_blocks:
                if block in bad_badges: return False
                if block in good_badges: return True
        return True

    def fetch_full_job_page(self, job_dict):
        """Скачивает текст вакансии (работает в отдельном потоке)"""
        url = job_dict['link']
        try:
            res = requests.get(url, headers=self.headers, timeout=7)  # Жесткий таймаут 7 сек
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
            pass  # Глушитель ошибок (таймауты, разрывы соединения)
        return None

    def scrape_direct_link(self, link):
        try:
            job_dict = {"title": "Developer (Direct)", "company": "Direct Email", "link": link, "source": "Email"}
            return self.fetch_full_job_page(job_dict)
        except Exception:
            return None

    # ==========================================
    # ПАРСЕРЫ (Только собирают ссылки)
    # ==========================================
    def scrape_justjoin(self):
        print(f"🔍 [JustJoin.it] Собираю карточки: {self.keyword}...")
        pending = []
        cat = {"qa automation": "testing", "security analyst": "security", "cybersecurity": "security",
               "cloud engineer": "devops", "system administrator": "admin", "linux": "admin",
               "support engineer": "support"}.get(self.keyword.lower(), self.keyword.lower().replace(' ', '-'))
        try:
            res = requests.get(f"https://justjoin.it/job-offers/all-locations/{cat}", headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a_tag in soup.find_all('a', href=True):
                if '/job-offer/' in a_tag['href']:
                    link = f"https://justjoin.it{a_tag['href']}"
                    if link in self.seen_jobs: continue
                    title_elem = a_tag.find('h2')
                    title = title_elem.text.strip() if title_elem else "Developer"
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
        print(f"🔍 [Pracuj.pl] Собираю карточки: {self.keyword}...")
        pending = []
        url = f"https://www.pracuj.pl/praca/{self.safe_keyword};kw"
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for offer in soup.find_all('div', attrs={'data-test': 'default-offer'}):
                link_elem = offer.find(attrs={'data-test': 'offer-link'})
                if not link_elem: continue
                link = link_elem['href'] if link_elem['href'].startswith('http') else url
                if link in self.seen_jobs: continue
                title_elem = offer.find(attrs={'data-test': 'offer-title'})
                title = title_elem.text.strip() if title_elem else "Developer"
                if self.is_junior_card(title, offer):
                    comp_elem = offer.find(attrs={'data-test': 'text-company-name'})
                    comp = comp_elem.text.strip() if comp_elem else "Unknown"
                    pending.append({"title": title, "company": comp, "link": link, "source": "Pracuj.pl"})
                    if len(pending) >= 150: break
        except Exception:
            pass
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
        print("\n⚙️ [UniversalScraper] Запускаю сбор базы (Польша)...")
        pending_jobs = []
        pending_jobs.extend(self.scrape_pracuj())
        pending_jobs.extend(self.scrape_justjoin())
        pending_jobs.extend(self.scrape_nofluffjobs())
        pending_jobs.extend(self.scrape_bulldogjob())
        pending_jobs.extend(self.scrape_theprotocol())
        pending_jobs.extend(self.scrape_solidjobs())

        if not pending_jobs: return []

        print(f"⚡ Собрано {len(pending_jobs)} ссылок. Скачиваю тексты в 20 потоков...")
        all_jobs = []

        # МАГИЯ МНОГОПОТОЧНОСТИ (Скачиваем всё одновременно)
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                futures = [executor.submit(self.fetch_full_job_page, job) for job in pending_jobs]
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        self.seen_jobs.add(result['link'])
                        all_jobs.append(result)
        except KeyboardInterrupt:
            print("\n🛑 Скачивание прервано пользователем. Возвращаю то, что успел собрать.")
        except Exception as e:
            print(f"⚠️ Ошибка пула потоков: {e}")

        all_jobs.sort(key=lambda x: x.get('priority', 0), reverse=True)
        return all_jobs