import requests
from bs4 import BeautifulSoup
import re
import time


class OSINTAgent:
    def __init__(self, hunter_api_key=None):
        self.api_key = hunter_api_key
        self.base_url = "https://api.hunter.io/v2/domain-search"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }

    def clean_company_name(self, company_name):
        name = re.sub(r'\b(sp\. z o\.o\.|llc|inc|ltd|gmbh|s\.a\.)\b', '', company_name, flags=re.IGNORECASE)
        return name.strip()

    def find_linkedin_hr(self, company_name):
        """Хакерский поиск HR через ПРЯМОЙ парсинг DuckDuckGo HTML"""
        if company_name in ["Unknown", "Tech Company", "Direct Email", "GlobalCompany"]:
            return []  # Не ищем HR для пустых компаний

        clean_name = self.clean_company_name(company_name)
        query = f'site:pl.linkedin.com/in ("HR" OR "Recruiter" OR "Talent" OR "IT Sourcer" OR "Rekruter") "{clean_name}"'

        print(f"🕵️‍♂️ [OSINT] Ищу LinkedIn HR для: {clean_name}...")
        results = []

        try:
            # Бьем напрямую по HTML версии поисковика
            url = "https://html.duckduckgo.com/html/"
            res = requests.post(url, headers=self.headers, data={'q': query}, timeout=10)

            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')

                # Ищем все блоки с результатами
                for result_block in soup.find_all('div', class_='result__body'):
                    a_tag = result_block.find('a', class_='result__url')
                    if not a_tag: continue

                    link = a_tag.get('href', '')
                    if "linkedin.com/in" in link:
                        title_tag = result_block.find('a', class_='result__snippet')
                        title = title_tag.text if title_tag else "HR Profile"

                        clean_title = title.split('-')[0].split('|')[0].strip()
                        results.append({"name": clean_title, "link": link})

                        if len(results) >= 3:  # Берем топ-3
                            break
            time.sleep(2)  # Защита от бана
        except Exception as e:
            print(f"⚠️ Ошибка парсинга DuckDuckGo: {e}")

        if not results:
            print("⚠️ Ошибка поиска LinkedIn: No results found.")

        return results

    def find_hr_emails(self, company_name):
        """Сначала ищем LinkedIn, если не нашли - пробуем Hunter"""
        linkedin_results = self.find_linkedin_hr(company_name)

        if linkedin_results:
            return [{"type": "linkedin", "data": linkedin_results}]

        # Фолбэк на Hunter.io
        if not self.api_key:
            return []

        clean_name = self.clean_company_name(company_name).lower()
        domain = f"{clean_name.replace(' ', '')}.com"

        try:
            res = requests.get(f"{self.base_url}?domain={domain}&type=personal&api_key={self.api_key}")
            if res.status_code == 200:
                data = res.json()
                emails = []
                for email_data in data.get('data', {}).get('emails', []):
                    position = email_data.get('position', '').lower()
                    if any(hr_word in position for hr_word in ['hr', 'recruiter', 'talent', 'people']):
                        emails.append({
                            "type": "email",
                            "email": email_data['value'],
                            "first_name": email_data.get('first_name', 'HR'),
                            "position": position
                        })
                return emails
            return []
        except Exception:
            return []