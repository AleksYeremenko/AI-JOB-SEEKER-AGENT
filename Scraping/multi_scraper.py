import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import concurrent.futures

class MultiScraper:
    def __init__(self, skills, seniority_filter="Junior", seen_jobs=None, settings=None):
        self.settings = settings
        self.seen_jobs = seen_jobs if seen_jobs else set()
        self.keyword = skills[0] if skills else "Developer"
        self.safe_keyword = urllib.parse.quote_plus(self.keyword)
        self.seniority_filter = seniority_filter
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
        }

        self.target_sites = {
            "RemotiveAPI": {"type": "api", "search_url": f"https://remotive.com/api/remote-jobs?search={self.keyword}",
                            "jobs_array_key": "jobs", "url_key": "url", "active": True},
            "RemoteOK": {"type": "api", "search_url": f"https://remoteok.com/api?tag={self.keyword}",
                         "jobs_array_key": "", "url_key": "url", "active": False},
            "WorkingNomads": {"type": "api", "search_url": "https://www.workingnomads.com/api/exposed_jobs/",
                              "jobs_array_key": "jobs", "url_key": "url", "active": True},
            "BerlinStartupJobs": {"type": "html", "search_url": "https://berlinstartupjobs.com/engineering/",
                                  "base_url": "", "link_selector": ".bjs-jl-title a", "active": True},
            "EuroTechJobs": {"type": "html", "search_url": f"https://www.eurotechjobs.com/jobs/{self.keyword}",
                             "base_url": "https://www.eurotechjobs.com", "link_selector": "a.jobTitle", "active": True},
            "TheHub": {"type": "html", "search_url": "https://thehub.io/jobs?roles=backenddeveloper",
                       "base_url": "https://thehub.io", "link_selector": "a.card-job-find-list__link", "active": True},
            "SiliconCanals": {"type": "html", "search_url": f"https://jobs.siliconcanals.com/jobs?q={self.keyword}",
                              "base_url": "https://jobs.siliconcanals.com", "link_selector": "a.job-link",
                              "active": True},
            "WeWorkRemotely": {"type": "html",
                               "search_url": "https://weworkremotely.com/categories/remote-back-end-programming-jobs",
                               "base_url": "https://weworkremotely.com",
                               "link_selector": "article ul li a:not(.company)", "active": True},
            "Jobspresso": {"type": "html", "search_url": "https://jobspresso.co/remote-software-engineering-jobs/",
                           "base_url": "", "link_selector": "a.job_listing-clickbox", "active": True},
            "NoDesk": {"type": "html", "search_url": "https://nodesk.co/remote-jobs/engineering/",
                       "base_url": "https://nodesk.co", "link_selector": "a.job-card", "active": True},
            "CryptoJobs": {"type": "html", "search_url": f"https://crypto.jobs/?search={self.keyword}", "base_url": "",
                           "link_selector": "a.job-url", "active": True},
            "Climatebase": {"type": "html", "search_url": f"https://climatebase.org/jobs?l=&q={self.keyword}",
                            "base_url": "https://climatebase.org", "link_selector": "a.list_card", "active": True},
            "TechInAsia": {"type": "html", "search_url": f"https://www.techinasia.com/jobs/search?query={self.keyword}",
                           "base_url": "https://www.techinasia.com", "link_selector": "a.job-title", "active": True}
        }

    def is_fresh_enough(self, text):
        text = text.lower()
        if any(re.search(m, text) for m in [r'\bnowa\b', r'\bdzisiaj\b', r'\btoday\b', r'\b[1-9]h\b']): return 3
        if any(re.search(m, text) for m in [r'\bwczoraj\b', r'\byesterday\b']): return 3
        match = re.search(r'(\d+)\s*(dni|d|days?)', text)
        if match:
            nums = re.findall(r'\d+', match.group(0))
            if nums and int(nums[0]) >= 15:
                return 2
            elif nums:
                return 1
        return 2

    def is_valid_global_job(self, title, url, description=""):
        """Фильтрует senior/lead позиции (Твоя обновленная логика)"""
        text_to_check = f"{title} {url} {description}".lower()

        # Если юзер ищет Junior/Mid - исключаем Senior/Lead
        if "Junior" in self.seniority_filter or "Mid" in self.seniority_filter:
            senior_patterns = [
                r'\bsenior\b', r'\bsr\.?\b', r'\blead\b', r'\bprincipal\b',
                r'\barchitect\b', r'\bhead of\b', r'\bteam lead\b', r'\bstaff\b'
            ]
            for pattern in senior_patterns:
                if re.search(pattern, text_to_check):
                    return False

        must_have_pattern = r"\b(java|mid|regular|developer|engineer|software|backend)\b"
        if not re.search(must_have_pattern, f"{title} {url}".lower()): return False
        return True

    def fetch_full_job_page(self, job_dict):
        url = job_dict['link']
        try:
            res = requests.get(url, headers=self.headers, timeout=7)
            if res.status_code != 200: return None
            raw_html = res.text.lower()
            if re.search(r'\b(niemiecki|german|deutsch)\b', raw_html) and re.search(
                    r'\b(c1|c2|b2|native)\s*(niemiecki|german|deutsch)\b', raw_html):
                return None
            soup = BeautifulSoup(res.text, 'lxml')
            full_text = soup.get_text(separator=" | ", strip=True)
            if not self.is_valid_global_job(job_dict['title'], url, description=full_text):
                return None
            job_dict['details'] = full_text[:4000]
            job_dict['priority'] = self.is_fresh_enough(full_text)
            return job_dict
        except Exception:
            pass
        return None

    def run(self):
        print(f"\n🌍 [MultiScraper] Starting global search (Level: {self.seniority_filter}) for: {self.keyword}...")
        global_jobs = []
        pending_html_jobs = []

        for site_name, config in self.target_sites.items():
            if not config["active"]: continue
            print(f"📡 Checking international board: {site_name}...")
            try:
                res = requests.get(config["search_url"], headers=self.headers, timeout=10)

                if config["type"] == "api":
                    data = res.json()
                    jobs_array = data if isinstance(data, list) else data.get(config["jobs_array_key"], [])

                    for job in jobs_array[:200]:
                        link = job.get(config["url_key"])
                        title = job.get("title", job.get("position", "Developer"))
                        desc = job.get("description", "")

                        comp = job.get("company_name") or job.get("company") or job.get("employer")
                        if isinstance(comp, dict):
                            comp = comp.get("name")

                        if not comp or str(comp).lower() == "unknown":
                            if link:
                                parts = [p for p in link.split('/') if p]
                                if parts: comp = parts[-1].split('-')[0].capitalize()
                            else:
                                comp = "Tech Company"
                        else:
                            comp = str(comp).strip()

                        if link and link not in self.seen_jobs and self.is_valid_global_job(title, link, description=desc):
                            self.seen_jobs.add(link)
                            global_jobs.append({
                                "title": title, "company": comp,
                                "details": desc[:4000], "link": link, "source": site_name, "priority": 3
                            })

                elif config["type"] == "html":
                    soup = BeautifulSoup(res.text, 'lxml')
                    links = soup.select(config["link_selector"])
                    fetches = 0

                    for link_el in links:
                        href = link_el.get("href")
                        title = link_el.get_text(strip=True)
                        if not href: continue
                        if href.startswith('/'): href = config["base_url"] + href

                        if href in self.seen_jobs: continue
                        if not self.is_valid_global_job(title, href):
                            self.seen_jobs.add(href)
                            continue

                        fetches += 1
                        if fetches > 150: break

                        pending_html_jobs.append({
                            "title": title, "company": "GlobalCompany",
                            "link": href, "source": site_name
                        })
            except Exception:
                pass

        if pending_html_jobs:
            print(f"⚡ Found {len(pending_html_jobs)} HTML links. Fetching texts...")
            try:
                from utils.thread_manager import ThreadManager
                import threading
                
                tm = ThreadManager(self.settings) if self.settings else None
                
                def process_job(job):
                    return self.fetch_full_job_page(job)
                    
                if tm:
                    lock = threading.Lock()
                    def worker_wrapper(job):
                        res = process_job(job)
                        if res:
                            with lock:
                                self.seen_jobs.add(res['link'])
                                global_jobs.append(res)
                    tm.run_tasks(pending_html_jobs, worker_wrapper)
                else:
                    workers = max(1, min(5, int(10 * getattr(self.settings, 'work_speed', 100) / 100.0)))
                    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                        futures = [executor.submit(process_job, job) for job in pending_html_jobs]
                        for future in concurrent.futures.as_completed(futures):
                            result = future.result()
                            if result:
                                self.seen_jobs.add(result['link'])
                                global_jobs.append(result)
            except KeyboardInterrupt:
                print("\n🛑 Download interrupted by user. Returning collected jobs.")
            except Exception as e:
                print(f"⚠️ Error in MultiScraper threads: {e}")

        global_jobs.sort(key=lambda x: x['priority'], reverse=True)
        return global_jobs


# === Обертка для интеграции с AIJobSeekerApp.py ===
def scrape_all_sites(search_keywords=None, seniority_filter="Junior", settings=None):
    """Wrapper for international scraper"""
    if search_keywords is None:
        search_keywords = ["Developer"]
    scraper = MultiScraper(skills=search_keywords, seniority_filter=seniority_filter, settings=settings)
    return scraper.run()