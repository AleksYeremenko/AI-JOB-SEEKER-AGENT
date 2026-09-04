from playwright.sync_api import sync_playwright
import time
import os
from utils.llm_handler import LLMHandler
from Appliers.vision_applier import VisionApplier

# Если у тебя установлен playwright-stealth, раскомментируй импорт ниже:
# from playwright_stealth import Stealth

def main():
    print("🤖 Загрузка профиля...")
    profile_data = {
        "first_name": "Aleks",
        "last_name": "Yeremenko",
        "email": "yeremenkoaleks1@gmail.com",
        "phone": "516478223"
    }
    
    print("🧠 Инициализация Ollama LLM...")
    llm = LLMHandler()
    
    print("👁️ Инициализация VisionApplier...")
    applier = VisionApplier(profile_data, llm_handler=llm)
    
    cv_path = "Data/my_cv.pdf" 
    
    # Проверка, запущен ли сервер OmniParser
    try:
        import requests
        requests.get("http://localhost:8000/docs", timeout=2)
    except:
        print("\n⚠️ ВНИМАНИЕ: Кажется, сервер OmniParser (server.py) не запущен!")
        print("Сначала запусти `python server.py` в отдельном терминале, прежде чем тестировать.\n")
        return

    # Читаем тестовые ссылки
    links = []
    try:
        with open("test_links.json.txt", "r", encoding="utf-8") as f:
            for line in f:
                parts = line.split(" - ")
                if parts[0].strip().startswith("http"):
                    links.append(parts[0].strip())
    except Exception as e:
        print(f"⚠️ Ошибка чтения test_links.json.txt: {e}")
        return

    print(f"\n🚀 Запуск браузера для тестирования {len(links)} ссылок...")
    
    for idx, job_link in enumerate(links):
        print(f"\n=======================================================")
        print(f"🔗 ТЕСТ {idx+1}/{len(links)}: {job_link}")
        print(f"=======================================================\n")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False, 
                args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
            )
            
            context = browser.new_context(
                no_viewport=True,
                color_scheme='light'
            )
            
            page = context.new_page()
            
            print("⚡ Передаю управление VisionApplier...")
            try:
                applier.apply(page, context, job_link, cv_path, "")
            except Exception as e:
                print(f"❌ Ошибка в процессе отклика: {e}")
            
            print(f"\n🏁 Тест {idx+1} завершен. Закрываю браузер...")
            time.sleep(2)
            browser.close()

if __name__ == "__main__":
    main()

