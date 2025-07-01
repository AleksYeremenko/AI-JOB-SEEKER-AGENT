"""
scraper_registry.py
Читает site_configs/ и запускает только активные скраперы нужного региона.
В main.py заменяет цикл `for skill in search_keywords`.

Использование в main.py:
    from Scraping.scraper_registry import SiteRegistry
    registry = SiteRegistry(seen_jobs=seen_jobs)
    all_new_jobs = registry.run_all(keywords=search_keywords, regions=["PL","GLOBAL","EU"])
"""
import json
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import concurrent.futures


class SiteRegistry:
    def __init__(self, seen_jobs=None):
        self.seen_jobs = seen_jobs if seen_jobs else set()
        self.configs = self._load_configs()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        print(f"📚 [SiteRegistry] Загружено {len(self.configs)} конфигов")

    def _load_configs(self):
        config_dir = os.path.join(os.path.dirname(__file__), "..", "Appliers", "site_configs")
        configs = []
        if not os.path.exists(config_dir):
            print(f"⚠️ [SiteRegistry] Папка конфигов не найдена: {config_dir}")
            return configs
        for fname in os.listdir(config_dir):
            if fname.endswith(".json"):
                with open(os.path.join(config_dir, fname), encoding="utf-8") as f:
                    cfg = json.load(f)
                if cfg.get("active", False):
                    configs.append(cfg)
        return configs

    def run_all(self, keywords=None, regions=None):
        """
        Запускает все активные скраперы для заданных ключевых слов.
        keywords: list[str] — поисковые запросы
        regions: list[str] или None — фильтр по регионам (None = все)
        """
        if keywords is None:
            keywords = ["Python", "Java", "React", "DevOps"]

        target_configs = [
            c for c in self.configs
            if regions is None or c.get("region") in regions
        ]

        print(f"\n🌍 [SiteRegistry] Запускаю {len(target_configs)} активных сайтов × {len(keywords)} ключевых слов...")

        all_jobs = []
        pending_html = []

        for cfg in target_configs:
            site = cfg["site_name"]
            scraper_cfg = cfg["scraper"]

            for keyword in keywords:
                safe_kw = urllib.parse.quote_plus(keyword)
                search_url = scraper_cfg["search_url"].replace("{keyword}", safe_kw)

                print(f"  📡 [{site}] {keyword}...")

                try:
                    if scraper_cfg["type"] == "api":
                        jobs = self._scrape_api(cfg, search_url, keyword)
                        all_jobs.extend(jobs)

                    elif scraper_cfg["type"] == "html":
                        links = self._collect_html_links(cfg, search_url, keyword)
                        pending_html.extend(links)

                except Exception as e:
                    print(f"  ⚠️ [{site}] Ошибка: {e}")

        # Параллельная загрузка HTML страниц
        if pending_html:
            print(f"\n⚡ [SiteRegistry] {len(pending_html)} ссылок → загружаю в 20 потоков...")
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
                    futures = [executor.submit(self._fetch_job_page, job) for job in pending_html]
                    for future in concurrent.futures.as_completed(futures):
                        result = future.result()
                        if result:
                            self.seen_jobs.add(result["link"])
                            all_jobs.append(result)
            except KeyboardInterrupt:
                print("\n🛑 Прервано пользователем")

        all_jobs.sort(key=lambda x: x.get("priority", 0), reverse=True)
        print(f"✅ [SiteRegistry] Итого найдено: {len(all_jobs)} вакансий")
        return all_jobs

    # ------------------------------------------------------------------
    # ВНУТРЕННИЕ МЕТОДЫ
    # ------------------------------------------------------------------

    def _scrape_api(self, cfg, search_url, keyword):
        sc = cfg["scraper"]
        site = cfg["site_name"]
        jobs = []

        res = requests.get(search_url, headers=self.headers, timeout=10)
        data = res.json()

        # Разные форматы API
        if isinstance(data, list):
            items = data
        elif "jobs" in data:
            items = data["jobs"]
        elif "job-data" in data:
            items = data["job-data"]
        else:
            items = []

        for item in items[:200]:
            link = item.get("url") or item.get("job_url") or item.get("link")
            title = item.get("title") or item.get("position") or "Developer"
            company = item.get("company_name") or item.get("company") or "Company"
            if isinstance(company, dict):
                company = company.get("name", "Company")
            desc = item.get("description", "")

            if not link or link in self.seen_jobs:
                continue
            if not self._is_valid(title, link):
                continue

            self.seen_jobs.add(link)
            jobs.append({
                "title": title,
                "company": str(company),
                "details": desc[:4000],
                "link": link,
                "source": site,
                "priority": 3,
            })

        return jobs

    def _collect_html_links(self, cfg, search_url, keyword):
        sc = cfg["scraper"]
        site = cfg["site_name"]
        pending = []

        res = requests.get(search_url, headers=self.headers, timeout=10)
        soup = BeautifulSoup(res.text, "lxml")

        for el in soup.select(sc["job_link_selector"]):
            href = el.get("href")
            title_el = el.find(sc.get("title_selector", "h3")) or el
            title = title_el.get_text(strip=True) if title_el else "Developer"

            if not href:
                continue
            if href.startswith("/"):
                href = cfg["base_url"].rstrip("/") + href

            if href in self.seen_jobs:
                continue
            if not self._is_valid(title, href):
                self.seen_jobs.add(href)
                continue

            pending.append({
                "title": title,
                "company": "Unknown",
                "link": href,
                "source": site,
            })
            if len(pending) >= sc.get("max_jobs", 150):
                break

        return pending

    def _fetch_job_page(self, job_dict):
        url = job_dict["link"]
        try:
            res = requests.get(url, headers=self.headers, timeout=7)
            if res.status_code != 200:
                return None

            raw = res.text.lower()
            # Фильтр "обязательный немецкий"
            if re.search(r'\b(niemiecki|german|deutsch)\b', raw) and \
               re.search(r'\b(c1|c2|b2|native)\s*(german|deutsch)\b', raw):
                return None

            soup = BeautifulSoup(res.text, "lxml")
            text = soup.get_text(separator=" | ", strip=True)
            priority = self._freshness(text)

            job_dict["details"] = text[:4000]
            job_dict["priority"] = priority
            return job_dict
        except:
            return None

    # ------------------------------------------------------------------
    # УТИЛИТЫ
    # ------------------------------------------------------------------

    STOP_WORDS = re.compile(
        r'\b(senior|sr\.?|snr|lead|principal|manager|architect|head|vp|director|cto|intern|trainee|'
        r'php|ruby|ios|android|shopify|firmware|c\+\+|wordpress|magento)\b|-sr-|/sr-',
        re.IGNORECASE
    )
    MUST_HAVE = re.compile(
        r'\b(java|mid|regular|developer|engineer|software|backend|python|react|devops|security|analyst)\b',
        re.IGNORECASE
    )

    def _is_valid(self, title, url, desc=""):
        text = f"{title} {url} {desc}"
        if self.STOP_WORDS.search(text):
            return False
        if not self.MUST_HAVE.search(f"{title} {url}"):
            return False
        return True

    def _freshness(self, text):
        t = text.lower()
        if any(re.search(m, t) for m in [r'\bnowa\b', r'\bdzisiaj\b', r'\btoday\b', r'\b[1-9]h\b']):
            return 3
        if any(re.search(m, t) for m in [r'\bwczoraj\b', r'\byesterday\b']):
            return 3
        m = re.search(r'(\d+)\s*(dni|d|days?)', t)
        if m:
            days = int(re.findall(r'\d+', m.group(0))[0])
            return 1 if days >= 15 else 2
        return 2
