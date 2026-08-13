from playwright.sync_api import sync_playwright
import time
import os


def save_my_session():
    with sync_playwright() as p:
        print("🕵️‍♂️ Запускаю браузер в режиме 'Ниндзя'...")

        # Ensure the Data directory exists
        if not os.path.exists("Data"):
            os.makedirs("Data")

        # Create or connect to the persistent Chrome profile
        context = p.chromium.launch_persistent_context(
            user_data_dir="Data/Chrome_Profile",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars"
            ]
        )

        # ==========================================
        # 🌍 TAB 1: Pracuj.pl
        # ==========================================
        page1 = context.pages[0] if context.pages else context.new_page()
        page1.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("🌍 Открываю страницу входа Pracuj.pl...")
        page1.goto("https://login.pracuj.pl/")

        # ==========================================
        # 🌍 TAB 2: JustJoinIT
        # ==========================================
        page2 = context.new_page()
        page2.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("🌍 Открываю страницу входа JustJoinIT...")
        page2.goto("https://justjoin.it/")
        time.sleep(2)

        # Пытаемся найти кнопку логина на JustJoinIT
        try:
            login_btn = page2.locator("button:has-text('Sign in'), a:has-text('Sign in'), button:has-text('Log in')").first
            if login_btn.is_visible(timeout=3000):
                login_btn.click()
                print("   ✅ Кликнул на кнопку логина JustJoinIT")
                time.sleep(2)
        except:
            print("   ⚠️ Кнопка логина не найдена, возможно уже залогинен")

        # ==========================================
        # 🌍 TAB 3: RemoteOK
        # ==========================================
        page3 = context.new_page()
        page3.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("🌍 Открываю RemoteOK...")
        page3.goto("https://remoteok.com")

        print("\n" + "="*60)
        print("⏳ У тебя есть 5 минут (300 секунд)!")
        print("="*60)
        print("🔥 ЗАЛОГИНЬСЯ НА ВСЕХ ВКЛАДКАХ:")
        print("   1️⃣  Pracuj.pl (через Google или Email)")
        print("   2️⃣  JustJoinIT (через Google или LinkedIn)")
        print("   3️⃣  RemoteOK (если нужно)")
        print("\n💡 СОВЕТЫ:")
        print("   • Используй Google Sign-In везде где можно")
        print("   • Не закрывай браузер!")
        print("   • Я сам сохраню все сессии через 5 минут")
        print("="*60 + "\n")

        # Wait for 5 minutes
        time.sleep(300)

        # Save the unified cookie snapshot
        context.storage_state(path="Data/my_session.json")

        print("\n" + "="*60)
        print("✅ СЕССИЯ СОХРАНЕНА!")
        print("="*60)
        print(f"📁 Файл: Data/my_session.json")
        print("🎯 Теперь бот может:")
        print("   ✅ Работать на Pracuj.pl без логина")
        print("   ✅ Работать на JustJoinIT без логина")
        print("   ✅ Работать на RemoteOK без логина")
        print("="*60)

        context.close()


if __name__ == "__main__":
    save_my_session()