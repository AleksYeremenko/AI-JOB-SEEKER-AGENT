import os
import time
from datetime import datetime
import gc
import psutil
import json

from dotenv import load_dotenv
load_dotenv("Data/.env")

from utils.llm_handler import LLMHandler
from Scraping.multi_scraper import MultiScraper
from Scraping.universal_scraper import UniversalScraper

# Заглушки для отсутствующих модулей
def get_links_from_email():
    print("📭 [EMAIL] Email listener отключен")
    return []

def log_application(job, status):
    print(f"📋 [LOG] {job.get('company', 'Unknown')} - {status}")

# ==========================================
# КОНФИГИ (ИЗ UI ИЛИ ФАЙЛА)
# ==========================================
USER_SETTINGS_FILE = "Data/user_settings.json"

def load_user_settings():
    """Читает настройки из UI (сохраненные в файле)"""
    if os.path.exists(USER_SETTINGS_FILE):
        with open(USER_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Дефолтные значения если UI еще не запускали
        return {
            "position": "Python Developer",
            "tech_stack": "Python, Django, PostgreSQL, Docker",
            "stack_match_percent": 50,
            "city": "Warsaw",
            "job_type": "Backend",
            "email": "yeremenkoaleks1@gmail.com",
            "cv_path": "Data/my_cv.pdf"
        }

USER_SETTINGS = load_user_settings()

MY_PROFILE = {
    "first_name": "Oleksandr",
    "last_name": "Yeremenko",
    "email": USER_SETTINGS["email"],
    "phone": "+48516478223",
    "linkedin": "",
    "github": "https://github.com/AleksYeremenko"
}

CV_FILE_NAME = USER_SETTINGS.get("cv_path", "Data/my_cv.pdf")
SEEN_JOBS_FILE = "seen_jobs.txt"

seen_jobs = set()
if os.path.exists(SEEN_JOBS_FILE):
    with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
        seen_jobs.update(line.strip() for line in f if line.strip())

# ==============================================================
# ФИЛЬТРЫ (ПРОСТЫЕ, БЕЗ LLM)
# ==============================================================
def is_junior_or_mid(job):
    """Простой фильтр: убираем Senior/Lead"""
    title = job.get("title", "").lower()
    bad_words = ["senior", "sr.", "sr ", "lead", "principal", "manager", "architect", "head", "director", "cto"]
    return not any(word in title for word in bad_words)

def stack_match_simple(job, target_stack):
    """Простое совпадение стека (без LLM)"""
    job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    stack_keywords = [s.strip().lower() for s in target_stack.split(",")]

    matches = sum(1 for keyword in stack_keywords if keyword in job_text)
    total = len(stack_keywords)

    if total == 0:
        return 0

    match_percent = int((matches / total) * 100)
    return match_percent

# ==========================================
# ОЧИСТКА ПАМЯТИ
# ==========================================
def kill_zombie_browsers():
    """Убивает зависшие процессы Playwright"""
    killed_count = 0
    gc.collect()

    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                name = proc.info['name'].lower()
                cmdline = proc.info.get('cmdline', [])
                cmd_str = " ".join(cmdline).lower() if cmdline else ""

                is_playwright_node = "node" in name and "playwright" in cmd_str
                is_playwright_chrome = ("chrome" in name or "chromium" in name) and "--headless" in cmd_str

                if is_playwright_node or is_playwright_chrome:
                    proc.kill()
                    killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        if killed_count > 0:
            print(f"♻️ [RAM] Убито {killed_count} зависших процессов")
    except Exception:
        pass

# ==============================================================
# ГЛАВНЫЙ ЦИКЛ
# ==============================================================
def run_daemon():
    print("🚀 AI Job Seeker Agent (MVP) запущен!")
    print("=" * 60)
    print(f"🎯 Должность: {USER_SETTINGS['position']}")
    print(f"🛠️  Стек: {USER_SETTINGS['tech_stack']}")
    print(f"📊 Min Match: {USER_SETTINGS['stack_match_percent']}%")
    print(f"📍 Город: {USER_SETTINGS['city']}")
    print(f"📧 Email: {USER_SETTINGS['email']}")
    print("=" * 60)

    llm = LLMHandler()

    # Извлекаем ключевые слова для парсинга
    search_keywords = [s.strip() for s in USER_SETTINGS['tech_stack'].split(",")]
    min_match = USER_SETTINGS['stack_match_percent']

    cycle_count = 0

    while True:
        cycle_count += 1
        print(f"\n{'=' * 60}")
        print(f"🔄 ЦИКЛ #{cycle_count} [{datetime.now().strftime('%H:%M:%S')}]")
        print(f"{'=' * 60}")

        all_new_jobs = []

        # 1. Проверяем почту
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📬 Проверяю почту...")
        email_links = get_links_from_email()

        # 2. ПАРСИМ ВАКАНСИИ (польские сайты)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔍 Сканирую польские сайты...")
        for keyword in search_keywords[:2]: # Берем только первые 2 слова (экономим время)
            print(f"   🔎 Ключевое слово: {keyword}")

            # UniversalScraper (JustJoin, Pracuj, NoFluff и т.д.)
            polish_scraper = UniversalScraper([keyword], seen_jobs=seen_jobs)
            polish_jobs = polish_scraper.get_all_jobs()

            all_new_jobs.extend(polish_jobs)
            time.sleep(2)

        # 3. ПАРСИМ ГЛОБАЛЬНЫЕ САЙТЫ (опционально)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🌍 Сканирую глобальные сайты...")
        for keyword in search_keywords[:1]: # Берем только 1 слово для глобала
            global_scraper = MultiScraper([keyword], seen_jobs=seen_jobs)
            global_jobs = global_scraper.run()

            all_new_jobs.extend(global_jobs)
            time.sleep(2)

        if not all_new_jobs:
            print("\n📭 Новых вакансий нет.")
            time.sleep(900)  # 15 минут
            continue

        print(f"\n✅ Найдено {len(all_new_jobs)} уникальных вакансий!")
        print("=" * 60)

        # 4. ФИЛЬТРУЕМ ВАКАНСИИ
        filtered_jobs = []

        for job in all_new_jobs:
            # Фильтр 1: Junior/Mid only
            if not is_junior_or_mid(job):
                print(f"   ⏭️  {job['company']} - {job['title']} (Senior/Lead)")
                continue

            # Фильтр 2: Stack Match
            match_percent = stack_match_simple(job, USER_SETTINGS['tech_stack'])

            if match_percent < min_match:
                print(f"   ⏭️  {job['company']} - {job['title']} (Low match: {match_percent}%)")
                continue

            job['match_percent'] = match_percent
            filtered_jobs.append(job)
            print(f"   ✅ {job['company']} - {job['title']} (Match: {match_percent}%)")

        print(f"\n📊 Прошли фильтр: {len(filtered_jobs)} из {len(all_new_jobs)}")

        # 5. СОРТИРУЕМ ПО ПРИОРИТЕТУ
        filtered_jobs.sort(key=lambda x: (x.get('priority', 0), x.get('match_percent', 0)), reverse=True)

        # 6. ПРИМЕНЯЕМСЯ (пока заглушка)
        for idx, job in enumerate(filtered_jobs[:10], 1):  # Топ-10 вакансий
            print(f"\n📋 [{idx}/{len(filtered_jobs)}] {job['company']} - {job['title']}")
            print(f"   🔗 {job['link']}")
            print(f"   📊 Match: {job['match_percent']}%, Priority: {job.get('priority', 0)}")

            # Реальный applier
            try:
                from Appliers.justjoin_applier_drission import JustJoinApplier
                from DrissionPage import ChromiumPage, ChromiumOptions
                
                print(f"   ⏳ Запускаю DrissionPage для отклика...")
                co = ChromiumOptions()
                co.set_argument('--disable-blink-features=AutomationControlled')
                co.set_argument('--disable-infobars')
                co.set_user_data_path(r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\Chrome_Profile")
                
                # Запускаем браузер для апплая
                page = ChromiumPage(co)
                
                applier = JustJoinApplier(USER_SETTINGS)
                # TODO: Нужно передавать правильный путь к CV, пока берем дефолтный
                cv_path = r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\my_cv.pdf"
                status = applier.apply(page, job['link'], cv_path)
                
                log_application(job, status)
                page.quit()
            except Exception as e:
                print(f"   ❌ Ошибка авто-отклика: {e}")
                log_application(job, "Error")

            seen_jobs.add(job['link'])
            time.sleep(3)

        # 7. Сохраняем seen_jobs
        print(f"\n💾 Сохраняю просмотренные вакансии...")
        with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
            for link in seen_jobs:
                f.write(link + "\n")

        # 8. Чистим память
        kill_zombie_browsers()

        print("\n" + "=" * 60)
        print("💤 Цикл завершен. Ухожу в спячку на 20 минут...")
        print("=" * 60)
        time.sleep(1200)  # 20 минут


if __name__ == "__main__":
    try:
        run_daemon()
    except KeyboardInterrupt:
        print("\n\n⏹️  Агент остановлен пользователем.")
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()