import time
import os
import random
import sys
from DrissionPage import ChromiumPage, ChromiumOptions

sys.stdout.reconfigure(encoding='utf-8')

class JustJoinApplier:
    def __init__(self, profile_data):
        self.profile = profile_data

    def apply(self, page, job_link, cv_path):
        print(f"🌍 [JustJoin Drission] Opening: {job_link}")
        
        page.get(job_link)
        time.sleep(random.uniform(3, 5))

        try:
            cookie_btn = page.ele('text:Akceptuj', timeout=2)
            if not cookie_btn:
                cookie_btn = page.ele('text:Accept All', timeout=1)
            if cookie_btn:
                cookie_btn.click()
                time.sleep(1)
        except:
            pass

        print("🖱️ [JustJoin Drission] Looking for main Apply button...")
        
        apply_btn = page.ele('@@data-test-id=button-apply', timeout=5)
        if not apply_btn:
            apply_btn = page.ele('tag:button@@text():Aplikuj', timeout=3)
        if not apply_btn:
            apply_btn = page.ele('tag:button@@text():Apply', timeout=3)

        if not apply_btn:
            print("⚠️ [JustJoin Drission] Apply button not found!")
            return "Failed - No Apply Button"

        try:
            apply_btn.click()
        except Exception:
            apply_btn.click(by_js=True)
            
        time.sleep(random.uniform(2, 4))
        
        if len(page.tab_ids) > 1:
            page = page.get_tab(page.latest_tab)
            print(f"✅ Switched to new tab: {page.url}")

        if "justjoin.it" not in page.url:
            print(f"🛑 [JustJoin Drission] External ATS ({page.url}). Passing back to Universal Applier...")
            return f"ExternalATS:{page.url}"

        print("📝 [JustJoin Drission] Filling Name and Email...")
        
        # Ищем инпут для имени (максимально универсально)
        name_input = None
        for sel in ['css:input[name="name"]', 'css:input[name*="first"]', 'css:input[id*="name"]', 'css:input[name="first_name"]']:
            name_input = page.ele(sel, timeout=1)
            if name_input: break
            
        if name_input:
            # Если есть поле last_name (часто бывает на внешних ATS)
            last_name_input = page.ele('css:input[name*="last"]', timeout=1)
            if last_name_input:
                name_input.input(self.profile.get("first_name", "AI"), clear=True)
                last_name_input.input(self.profile.get("last_name", "User"), clear=True)
            else:
                full_name = f"{self.profile.get('first_name', 'AI')} {self.profile.get('last_name', '')}".strip()
                name_input.input(full_name, clear=True)
            print("  ✅ Name entered")
            
        # Ищем инпут для Email
        email_input = None
        for sel in ['css:input[type="email"]', 'css:input[name*="email"]', 'css:input[id*="email"]']:
            email_input = page.ele(sel, timeout=1)
            if email_input: break
            
        if email_input:
            email_input.input(self.profile.get("email", ""), clear=True)
            print("  ✅ Email entered")
            time.sleep(0.5)

        # Открываем сообщение (если есть ползунок)
        print("☑️ [JustJoin Drission] Looking for message switch...")
        try:
            switch_root = page.ele('css:.MuiSwitch-root', timeout=2)
            if switch_root:
                switch_root.click()
                time.sleep(1)
                print("  ✅ Clicked on MuiSwitch-root!")
                
                # Ищем текстарею по имени
                msg_area = page.ele('css:textarea[name="message"]', timeout=3)
                if msg_area:
                    msg = f"Hi! I'm {self.profile.get('first_name', 'User')}. Check my work: {self.profile.get('linkedin', '')}"
                    msg_area.clear()
                    msg_area.input(msg)
                    print("  ✅ Message written (GitHub link inserted!)")
                    time.sleep(0.5)
                else:
                    print("  ⚠️ Textarea for message did not appear after click.")
            else:
                print("  ⚠️ Message switch not found on page.")
        except Exception as e:
            print(f"  ⚠️ Error with message field: {e}")

        # Загрузка CV
        print("📎 [JustJoin Drission] Attaching CV...")
        try:
            file_input = page.ele('tag:input@@type=file')
            if file_input and os.path.exists(cv_path):
                file_input.input(cv_path)
                time.sleep(random.uniform(1, 2))
                print("  ✅ File uploaded")
        except Exception as e:
            print(f"  ⚠️ Error uploading CV: {e}")

        # Чекбоксы согласий (только обязательные RODO, пропускаем ползунок аккаунта)
        print("☑️ [JustJoin Drission] Checking consents (RODO)...")
        try:
            checkboxes = page.eles('css:input[type="checkbox"]')
            for cb in checkboxes:
                name_attr = str(cb.attr("name") or "")
                class_attr = str(cb.attr("class") or "")
                
                # Пропускаем маркетинговую рассылку
                if name_attr == "marketing_consent_accepted":
                    continue
                
                # Пропускаем ползунок сообщения (чтобы не отжать его случайно)
                if "MuiSwitch-input" in class_attr:
                    continue
                
                status = cb.attr("checked")
                if status is None:
                    try:
                        cb.click(by_js=True)
                        time.sleep(0.2)
                    except: pass
        except Exception as e:
            pass

        print("🚀 [JustJoin Drission] Clicking Submit...")
        try:
            submit_btn = None
            for selector in ['css:form#apply-form button[type="submit"]', 'css:button[type="submit"]', 'tag:button@@text():Wyślij', 'tag:button@@text():Aplikuj', 'tag:button@@text():Apply']:
                btn = page.ele(selector, timeout=1)
                if btn:
                    submit_btn = btn
                    break
                
            if submit_btn:
                try:
                    # Фокусируемся на кнопке и эмулируем реальный клик мышью
                    submit_btn.scroll.to_see()
                    time.sleep(0.5)
                    submit_btn.click()
                except Exception as e:
                    print(f"⚠️ Normal click failed: {e}, trying JS...")
                    submit_btn.click(by_js=True)
                    
                print("✅ Submit clicked! Waiting for site response...")
                time.sleep(2)
                
                # Check for errors on page
                try:
                    errors = page.eles('.Mui-error')
                    if errors:
                        err_texts = [e.text for e in errors if e.text]
                        if err_texts:
                            print(f"❌ JustJoin form validation error: {err_texts}")
                            return "Failed - Form Validation Error"
                except:
                    pass

                time.sleep(3)
                
                try:
                    url_lower = page.url.lower()
                    if "success" in url_lower or "thank" in url_lower:
                        return "Applied"
                    if page.ele('text:Dziękujemy') or page.ele('text:Thank you'):
                        return "Applied"
                except:
                    print("✅ Connection closed by site after Submit (Success!)")
                    return "Applied"
                    
                return "Applied (Unconfirmed)"
            else:
                return "Failed - No Submit Button"
        except Exception as e:
            if "连接已断开" in str(e) or "disconnected" in str(e).lower():
                print("✅ Success! Site closed window after submit.")
                return "Applied"
            print(f"⚠️ Submit error: {e}")
            return "Failed - Submit Error"


if __name__ == "__main__":
    TEST_URL = "https://justjoin.it/job-offer/wavestone-poland-ifs-technical-consultant-gliwice-erp"
    TEST_CV = r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\my_cv.pdf"
    MY_PROFILE = {
        "first_name": "Oleksandr",
        "last_name": "Yeremenko",
        "email": "yeremenkoaleks1@gmail.com",
        "phone": "+48516478223",
        "linkedin": "https://github.com/AleksYeremenko"
    }

    print("🧪 Starting DrissionPage JustJoinApplier...")
    
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--disable-infobars')
    co.set_user_data_path(r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\Chrome_Profile")

    page = ChromiumPage(co)
    applier = JustJoinApplier(MY_PROFILE)
    status = applier.apply(page, TEST_URL, TEST_CV)

    print("\n" + "=" * 60)
    print(f"✅ STATUS: {status}")
    print("=" * 60)
    
    time.sleep(10)
    page.quit()
