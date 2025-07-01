from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


def search_jobs(profile: dict) -> list:
    title = profile.get("title", "")
    skills = " ".join(profile.get("skills", []))
    # Формируем поисковый запрос
    query = f"{title} {skills}".strip() or "Python Developer"
    print(f"🔍 Начинаю поиск на LinkedIn по запросу: {query}")

    options = Options()
    # options.add_argument("--headless=new") # Раскомментируй, если не хочешь видеть окно браузера
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # Добавляем User-Agent, чтобы LinkedIn нас не забанил сразу
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

    driver = webdriver.Chrome(options=options)

    # URL для поиска (используем публичную страницу вакансий)
    url = f"https://www.linkedin.com/jobs/search/?keywords={query.replace(' ', '%20')}"

    try:
        driver.get(url)
        # Ждем загрузки карточек вакансий (до 10 секунд)
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "base-search-card")))

        # Прокручиваем немного вниз, чтобы подгрузились данные
        driver.execute_script("window.scrollTo(0, 500);")
        time.sleep(2)

        jobs = []
        # Находим все карточки вакансий
        job_cards = driver.find_elements(By.CLASS_NAME, "base-search-card")
        print(f"📦 Вижу карточек на странице: {len(job_cards)}")

        for card in job_cards[:7]:  # Берем первые 7 для стабильности
            try:
                # 1. Извлекаем Заголовок (пробуем разные селекторы)
                title_selectors = [
                    "h3.base-search-card__title",
                    ".base-search-card__title",
                    "h3"
                ]
                job_title = ""
                for selector in title_selectors:
                    try:
                        job_title = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                        if job_title: break
                    except:
                        continue

                # 2. Извлекаем Компанию
                company_selectors = [
                    "h4.base-search-card__subtitle",
                    ".base-search-card__subtitle",
                    "h4"
                ]
                company_name = ""
                for selector in company_selectors:
                    try:
                        company_name = card.find_element(By.CSS_SELECTOR, selector).text.strip()
                        if company_name: break
                    except:
                        continue

                # 3. Извлекаем Ссылку
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")

                if job_title and company_name:
                    jobs.append({
                        "title": job_title,
                        "company": company_name,
                        "link": link
                    })
                    print(f"✅ Нашел: {job_title} в {company_name}")

            except Exception as e:
                # print(f"⚠️ Ошибка парсинга карточки: {e}")
                continue

        return jobs

    except Exception as e:
        print(f"❌ Ошибка скрапера: {e}")
        return []
    finally:
        driver.quit()