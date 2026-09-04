import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

import time
import os
import sys
import random

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.append(project_root)

from DrissionPage import ChromiumPage, ChromiumOptions

class DjinniApplier:
    def __init__(self, profile_data):
        self.profile = profile_data

    def apply(self, page, job_link, cv_path):
        print(f"🌍 [Djinni] Opening: {job_link}")
        
        page.get(job_link)
        time.sleep(random.uniform(3, 5))

        # Handle Djinni location verification alert if present
        abroad_alert = page.ele('css:#ua_abroad_alert', timeout=2)
        if abroad_alert:
            print("⚠️ [Djinni] Location alert found. Attempting to dismiss...")
            change_btn = abroad_alert.ele('css:a[hx-post="/ajax/change_country"]', timeout=1)
            if change_btn:
                change_btn.click(by_js=True)
            else:
                keep_btn = abroad_alert.ele('css:a[hx-post="/ajax/keep_country"]', timeout=1)
                if keep_btn: keep_btn.click(by_js=True)
            print("⏳ [Djinni] Waiting for page reload after alert dismissal...")
            time.sleep(5)
            page.wait.load_start()

        # Look for Apply button
        print("🖱️ [Djinni] Looking for main Apply button...")
        apply_btn = page.ele('tag:button@@text():Відгукнутися', timeout=3)
        if not apply_btn: apply_btn = page.ele('tag:button@@text():Apply', timeout=1)
        if not apply_btn: apply_btn = page.ele('tag:a@@text():Відгукнутися', timeout=1)
        if not apply_btn: apply_btn = page.ele('text:Apply', timeout=1)
            
        if not apply_btn or apply_btn.attr('disabled') is not None:
            print("⚠️ [Djinni] Apply button not found or disabled! (Maybe already applied or not logged in?)")
            return "Failed - No Apply Button / Disabled / Not Logged In"

        try:
            apply_btn.click()
        except Exception:
            apply_btn.click(by_js=True)
            
        time.sleep(random.uniform(2, 4))

        # Окно с кавер-леттер (сообщением)
        message_box = page.ele('css:textarea[id="message"]', timeout=3)
        if not message_box:
            message_box = page.ele('css:textarea[name="message"]', timeout=2)
            
        if message_box:
            print("📝 [Djinni] Entering cover letter...")
            message_box.input(f"Hello,\n\nI am very interested in this position.\n\nBest regards,\n{self.profile.get('first_name', '')} {self.profile.get('last_name', '')}")
            time.sleep(1)
        
        # Отправляем
        print("🚀 [Djinni] Clicking Submit...")
        submit_btn = page.ele('tag:button@@text():Надіслати відгук', timeout=3)
        if not submit_btn: submit_btn = page.ele('tag:button@@id:job_apply', timeout=2)
        if not submit_btn: submit_btn = page.ele('css:.modal-content').ele('tag:button@@text():Apply', timeout=2)
        if not submit_btn: submit_btn = page.ele('tag:button@@type:submit@@text():Apply', timeout=2)
            
        if submit_btn:
            try:
                submit_btn.click()
            except Exception:
                submit_btn.click(by_js=True)
                
            time.sleep(random.uniform(2, 4))
            return "Success"
        else:
            print("⚠️ [Djinni] Could not find final Submit button.")
            return "Failed - No Submit Button"
