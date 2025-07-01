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
        # 🌍 TAB 1: RemoteOK
        # ==========================================
        page1 = context.pages[0] if context.pages else context.new_page()
        page1.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("🌍 Открываю RemoteOK...")
        page1.goto("https://remoteok.com")

        # ==========================================
        # 🌍 TAB 2: Pracuj.pl
        # ==========================================
        page2 = context.new_page()
        page2.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("🌍 Открываю страницу входа Pracuj.pl...")
        # Go directly to their login page
        page2.goto("https://login.pracuj.pl/")

        print("\n⏳ У тебя есть 5 минут (300 секунд)! Залогинься везде (Гугл, почта, пароли).")
        print("Оставь браузер открытым, я сам сохраню слепок ВСЕХ сессий после истечения времени.")

        # Wait for 5 minutes
        time.sleep(300)

        # Save the unified cookie snapshot
        context.storage_state(path="Data/my_session.json")
        print("✅ Сессия сохранена в Data/my_session.json! Бот готов к работе на всех вкладках.")

        context.close()


if __name__ == "__main__":
    save_my_session()