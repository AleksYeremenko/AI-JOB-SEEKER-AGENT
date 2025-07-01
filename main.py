import os
import time
from datetime import datetime
import pandas as pd
import re
import gc  # Сборщик мусора Python
import psutil

from dotenv import load_dotenv
from smart_hybrid_applier import SmartHybridApplier

load_dotenv("Data/.env")

from utils.llm_handler import LLMHandler
from utils.comfy_connector import send_to_comfy
from Scraping.multi_scraper import MultiScraper
from Scraping.universal_scraper import UniversalScraper
from Core.resume_manager import ResumeManager
from Core.job_analyzer import JobAnalyzer

from excel_logger import log_application
from osint_module import OSINTAgent

# 🔥 ИМПОРТЫ НАШЕГО ЗАВОДА И ТЕЛЕГРАМА 🔥
from pipeline_processor import PipelineProcessor
from telegram_bot import TelegramApprovalBot

try:
    from universal_applier import UniversalApplier

    HAS_APPLIER = True
except ImportError:
    HAS_APPLIER = False

try:
    from email_listener import get_links_from_email
    from mailer import send_to_hr
except ImportError:
    def get_links_from_email():
        return []


    def send_to_hr(*args, **kwargs):
        return False

# ==============================================================
# КОНФИГИ И ПУТИ
# ==============================================================
MY_PROFILE = {
    "first_name": "Oleksandr",
    "last_name": "Yeremenko",
    "email": "yeremenkoaleks1@gmail.com",
    "phone": "+48516478223",
    "linkedin": "",
    "github": "https://github.com/AleksYeremenko"
}

CV_FILE_NAME = "my_cv.pdf"
SEEN_JOBS_FILE = "seen_jobs.txt"
EXCEL_DB_FILE = "Data/my_applications.xlsx"
ATS_DB_FILE = "Data/ats_database.json"
APPLICATIONS_DIR = "Applications"

seen_jobs = set()
if os.path.exists(SEEN_JOBS_FILE):
    with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
        seen_jobs.update(line.strip() for line in f if line.strip())

resume_mgr = ResumeManager()

# Делаем бота глобальным, чтобы колбэки могли отправлять сообщения
tg_bot = None


# ==============================================================
# КОЛБЭКИ ТЕЛЕГРАМ-БОТА (Реакция на кнопки ✅ и ❌)
# ==============================================================
def on_approve(job_id, job):
    print(f"✅ [TG] Одобрено: {job['company']}")
    try:
        # Гибридный апплаер сам решает: Playwright или Ollama
        status = hybrid_applier.apply(
            job_link     = job["link"],
            cv_path      = job["cv_path"],
            cover_letter = job.get("cover_letter", ""),
        )

        if tg_bot:
            tg_bot.send_message(f"📨 {job['company']}: {status}")

        if os.path.exists(EXCEL_DB_FILE):
            df = pd.read_excel(EXCEL_DB_FILE)
            df.loc[df["link"] == job["link"], "status"] = status
            df.to_excel(EXCEL_DB_FILE, index=False)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        if tg_bot:
            tg_bot.send_message(f"❌ {job['company']}: {e}")

def on_reject(job_id, reason):
    print(f"❌ [TG] Вакансия отклонена юзером: {job_id}")
    send_to_comfy("REJECTED BY USER")


# ==============================================================
# ОЧИСТКА ПАМЯТИ
# ==============================================================
def kill_zombie_browsers():
    """Убивает зависшие процессы Playwright (Chromium/Node), не трогая основной браузер юзера"""
    print("🧹 [RAM] Запускаю очистку оперативной памяти от зомби-процессов...")
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
            print(f"♻️ [RAM] Убито {killed_count} зависших скрытых процессов. Память освобождена!")
        else:
            print("♻️ [RAM] Зомби не найдено, память чистая.")
    except Exception as e:
        pass


# ==============================================================
# ГЛАВНЫЙ ЦИКЛ
# ==============================================================
def run_daemon():
    global tg_bot
    print("🚀 AI-Агент (Конвейерная Версия) запущен!")

    llm = LLMHandler()
    hunter_key = os.getenv("HUNTER_API_KEY")
    osint_agent = OSINTAgent(hunter_key)

    if os.path.exists(EXCEL_DB_FILE):
        try:
            df_history = pd.read_excel(EXCEL_DB_FILE)
            if 'link' in df_history.columns:
                seen_jobs.update(df_history["link"].dropna().tolist())
        except Exception as e:
            pass

    cv_raw_text = resume_mgr.extract_text_from_pdf(CV_FILE_NAME)
    my_real_stack = resume_mgr.analyze_my_cv(llm, cv_raw_text)
    print(f"🎯 Мой полный арсенал: {my_real_stack}")

    try:
        with open(ATS_DB_FILE, "r", encoding="utf-8") as f:
            ats_db = f.read()
    except:
        ats_db = "{}"

    analyzer = JobAnalyzer(llm, ats_db, my_real_stack)
    search_keywords = ["Java", ".NET", "Python", "React", "CyberSecurity", "DevOps"]

    # Создаем гибридный апплаер для обхода сложных ATS-систем
    hybrid_applier = SmartHybridApplier(
        profile_data=MY_PROFILE,
        llm_handler=llm,  # Твой Groq — используется только для CV
        config_dir=os.path.join(os.path.dirname(__file__), "Appliers", "site_configs")
    )

    # Инициализация Telegram Бота и Конвейера
    tg_bot = TelegramApprovalBot(on_approve=on_approve, on_reject=on_reject)
    # Запускаем конвейер, передавая в него наш новый hybrid_applier
    pipeline = PipelineProcessor(
        groq_llm=llm,
        analyzer=analyzer,
        resume_mgr=resume_mgr,
        osint_agent=osint_agent,
        telegram_bot=tg_bot,
        profile=MY_PROFILE,
        excel_logger=log_application,
        hybrid_applier=hybrid_applier,  # <-- Вот это самое важное добавление
    )

    while True:
        all_new_jobs = []

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 📬 Проверяю почту...")
        email_links = get_links_from_email()
        if email_links:
            direct_scraper = UniversalScraper(["Developer"], seen_jobs=seen_jobs)
            for link in email_links:
                if link not in seen_jobs:
                    job_data = direct_scraper.scrape_direct_link(link)
                    if job_data: all_new_jobs.append(job_data)

        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 Начинаю сканирование джоб-бордов...")
        for skill in search_keywords:
            multi_scraper = MultiScraper([skill], seen_jobs=seen_jobs)
            heavy_scraper = UniversalScraper([skill], seen_jobs=seen_jobs)

            jobs = multi_scraper.run() + heavy_scraper.get_all_jobs()

            for j in jobs:
                if not any(existing['link'] == j['link'] for existing in all_new_jobs):
                    all_new_jobs.append(j)
            time.sleep(3)

        if not all_new_jobs:
            print("📭 По ВСЕМ направлениям пусто. Рынок спит. Ухожу в спячку на 15 минут...")
            time.sleep(900)
            continue

        all_new_jobs.sort(key=lambda x: x.get('priority', 0), reverse=True)
        print(f"✅ Найдено {len(all_new_jobs)} уникальных вакансий! Отдаю в ЦЕХ НА ОБРАБОТКУ...")

        # 🔥 МАГИЯ КОНВЕЙЕРА: вместо зависания на одном потоке, мы отдаем всё на наш "завод"
        pipeline.run(all_new_jobs, my_real_stack, ats_db, seen_jobs)

        # Сохраняем все увиденные ссылки, чтобы не парсить их снова
        with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
            for link in seen_jobs: f.write(link + "\n")

        # Чистим память перед сном
        kill_zombie_browsers()

        print("💤 Цикл завершен. Ухожу в спячку на 20 минут...")
        time.sleep(1200)


if __name__ == "__main__":
    run_daemon()