import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

from playwright.sync_api import sync_playwright
import time
import os
import re
import sys
from dotenv import load_dotenv

load_dotenv("Data/.env")

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from utils.llm_handler import LLMHandler

TEST_CV_PATH = os.path.abspath("Data/my_cv.pdf")
MY_PROFILE = {
    "first_name": "Oleksandr",
    "last_name": "Yeremenko",
    "full_name": "Oleksandr Yeremenko",
    "email": "yeremenkoaleks1@gmail.com",
    "phone": "+48516478223",
    "github": "https://github.com/AleksYeremenko"
}


class SandboxApplier:
    def __init__(self, profile_data, llm_handler=None):
        self.profile = profile_data
        self.llm = llm_handler
        self.manual_domains = [
            'workday', 'taleo', 'successfactors', 'icims', 'brassring',
            'myworkdayjobs', 'breezy.hr', 'applytojob.com', 'ashbyhq.com', 
            'workable.com', 'bamboohr.com'
        ]

    def check_all_checkboxes(self, target_page):
        try:
            checkboxes = target_page.locator('input[type="checkbox"]')
            for i in range(checkboxes.count()):
                try:
                    cb = checkboxes.nth(i)
                    if cb.is_checked(): continue
                    cb.check(force=True)
                    if not cb.is_visible():
                        parent_label = cb.locator("xpath=ancestor::label").first
                        if parent_label.is_visible():
                            parent_label.click(force=True)
                        else:
                            checkbox_icon = cb.locator("xpath=..//span[contains(@class, 'checkbox')]").first
                            if checkbox_icon.is_visible():
                                checkbox_icon.click(force=True)
                except Exception:
                    pass
        except:
            pass

    def kill_cookies(self, page):
        print("🍪 Killing cookies...")
        try:
            accept_texts = ['Accept', 'Accept All', 'Akceptuj', 'Akceptuję', 'Zaakceptuj', 'Zgadzam', 'Allow', 'Got it', 'Rozumiem', 'Przejdź', 'Zamknij', 'Zezwól', 'Zezwol', 'Approve', 'Przejdź do serwisu', 'Rozumiem i akceptuję']
            selectors = ", ".join([f"button:has-text('{text}'), span:has-text('{text}'), div:has-text('{text}')" for text in accept_texts])
            pracuj_selectors = ", [data-test='button-submitCookie'], [data-test='system-message-close'], [data-test='button-close'], .rodo-popup-agree"
            full_selectors = selectors + pracuj_selectors
            cookie_buttons = page.locator(full_selectors)
            for i in range(cookie_buttons.count()):
                if cookie_buttons.nth(i).is_visible(timeout=1000):
                    cookie_buttons.nth(i).click(force=True)
                    time.sleep(0.5)
        except:
            pass
            
        # Hardcore DOM nuking for sticky cookie banners
        try:
            page.evaluate('''
                document.querySelectorAll('div, section, aside, footer').forEach(el => {
                    if (el.innerText && /cookie|akceptuj|zezw|zgadzam|accept|allow|agree/i.test(el.innerText)) {
                        const style = window.getComputedStyle(el);
                        if (style.position === 'fixed' || style.position === 'sticky' || style.zIndex > 100) {
                            el.remove();
                        }
                    }
                });
            ''')
        except:
            pass

    def fill_custom_dropdown(self, page, question_text, target_answer):
        """Универсальный заполнитель нестандартных выпадающих списков (React/Vue pseudo-selects)"""
        print(f"🔄 Trying custom dropdown: '{question_text}' -> '{target_answer}'")
        try:
            # Ищем лейбл или блок с текстом вопроса
            # Берем родительский элемент (контейнер вопроса)
            container = page.locator(f"xpath=//*[contains(text(), '{question_text}')]/ancestor::div[contains(@class, 'form') or contains(@class, 'field') or contains(@class, 'group') or contains(@class, 'wrapper')]").first
            
            if not container.is_visible(timeout=1000):
                # Fallback: просто ищем родительский div ближайшего уровня
                container = page.locator(f"xpath=//*[contains(text(), '{question_text}')]/..").first
                
            if not container.is_visible(timeout=1000):
                raise Exception("Контейнер вопроса не найден")

            # Ищем триггер списка (кнопку или div с текстом "Wybierz" или aria-expanded)
            trigger = container.locator("button, div[role='combobox'], div[role='listbox'], div[role='button'], :has-text('Wybierz')").last
            
            if not trigger.is_visible(timeout=1000):
                 trigger = container.locator("input[readonly]").first # иногда это инпут
                 trigger = container.locator("input[readonly]").first 

            trigger.scroll_into_view_if_needed()
            trigger.click(force=True)
            page.wait_for_timeout(500) 

            option = page.locator(f"xpath=//body//div[contains(@class, 'option') or contains(@class, 'menu') or @role='option']//*[contains(text(), '{target_answer}')]").first
            
            if not option.is_visible(timeout=1000):
                 option = page.locator(f"text='{target_answer}'").last

            if option.is_visible(timeout=2000):
                option.click(force=True)
                print(f"✅ Successfully selected '{target_answer}' for '{question_text}'")
                page.wait_for_timeout(300)
                return True
            else:
                raise Exception("Option did not appear in DOM")
                
        except Exception as e:
            print(f"⚠️ Failed to fill custom dropdown: {e}")
            
            try:
                print("🔄 Trying super-fallback click on nearest 'Wybierz'...")
                fallback_trigger = page.locator(f"xpath=//*[contains(text(), '{question_text}')]/following::*[contains(text(), 'Wybierz') or contains(text(), 'Select')][1]")
                fallback_trigger.click(force=True, timeout=2000)
                page.wait_for_timeout(500)
                page.locator(f"text='{target_answer}'").last.click(force=True, timeout=2000)
                print(f"✅ Fallback worked!")
                return True
            except:
                print("❌ Super-fallback also failed.")
                return False

    def fill_dynamic_questions(self, page):
        print("🧠 Looking for dynamic questions (Traffit/Custom ATS)...")
        if getattr(self, 'llm', None) is None:
            print("⚠️ LLM not connected, skipping dynamic questions.")
            return

        js_code = """
        () => {
            function isVisible(e) {
                return !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length) && window.getComputedStyle(e).visibility !== 'hidden';
            }
            
            function getLabel(e) {
                // 1. Native HTML labels
                if (e.labels && e.labels.length > 0) return e.labels[0].innerText.trim();
                
                // 2. ARIA labels
                let ariaLabel = e.getAttribute('aria-label');
                if (ariaLabel) return ariaLabel.trim();
                let ariaLabelledBy = e.getAttribute('aria-labelledby');
                if (ariaLabelledBy) {
                    let el = document.getElementById(ariaLabelledBy);
                    if (el && el.innerText) return el.innerText.trim();
                }

                // 3. Parent wrapper's label or text
                let parent = e.closest('.form-group, .field, .wrapper, .input-container, label');
                if (parent) {
                    let label = parent.querySelector('label');
                    if (label) return label.innerText.trim();
                    let text = parent.innerText.trim();
                    if (text && text.length > 0) return text.split('\\n')[0].trim();
                }
                
                // 4. Previous sibling text (e.g. <div>Name</div><input>)
                let sibling = e.previousElementSibling;
                while (sibling) {
                    let text = sibling.innerText;
                    if (text && text.trim().length > 0) return text.trim().split('\\n').pop();
                    sibling = sibling.previousElementSibling;
                }
                
                // 5. Parent's previous sibling
                if (e.parentElement && e.parentElement.previousElementSibling) {
                    let text = e.parentElement.previousElementSibling.innerText;
                    if (text && text.trim().length > 0) return text.trim().split('\\n').pop();
                }

                // 6. Fallbacks
                return e.placeholder || e.name || e.id || 'Unknown Field';
            }

            let fields = [];
            let index = 0;
            
            // Collect all typical input types including date, email, tel, url
            let elements = document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="checkbox"]):not([type="radio"]):not([type="file"]), textarea, select');
            
            for (let e of elements) {
                if (!isVisible(e)) continue;
                if (e.type === 'hidden' || e.readOnly || e.disabled) continue;
                
                // Exclude search inputs and location filters
                let name = (e.name || '').toLowerCase();
                let id = (e.id || '').toLowerCase();
                let placeholder = (e.placeholder || '').toLowerCase();
                if (name.includes('search') || id.includes('search') || placeholder.includes('szukaj') ||
                    name.includes('location') || id.includes('location') || placeholder.includes('miasto')) {
                    continue;
                }
                
                let val = e.value;
                if (e.tagName.toLowerCase() === 'select') {
                    if (e.selectedIndex > 0 && e.options[e.selectedIndex].value) val = e.options[e.selectedIndex].value;
                }
                
                if (!val || val.trim() === '') {
                    let uniqId = 'dyn_field_' + index;
                    e.setAttribute('data-ai-dyn-id', uniqId);
                    
                    fields.push({
                        id: uniqId,
                        tag: e.tagName.toLowerCase(),
                        type: e.type || '',
                        label: getLabel(e),
                        options: e.tagName.toLowerCase() === 'select' ? Array.from(e.options).map(o => o.innerText.trim()).filter(o => o) : []
                    });
                    index++;
                }
            }
            return fields;
        }
        """
        
        try:
            fields = page.evaluate(js_code)
            if not fields:
                print("✅ No empty dynamic fields found.")
                return
                
            print(f"🧐 Found {len(fields)} custom fields. Asking LLM...")
            
            questions_text = ""
            for f in fields:
                if f['tag'] == 'select':
                    opts = ", ".join(f['options'][:10])
                    questions_text += f"- ID: {f['id']} | QUESTION: {f['label']} | OPTIONS: {opts}\n"
                else:
                    questions_text += f"- ID: {f['id']} | QUESTION: {f['label']}\n"
            
            prompt = f"""
You are an AI assistant filling out a job application form.
The applicant's profile is:
Name: {self.profile.get('first_name', 'AI')} {self.profile.get('last_name', 'User')}
Email: {self.profile.get('email', '')}
Phone: {self.profile.get('phone', '')}
Stack: {self.profile.get('stack', 'Software Engineer')}
Seniority: {self.profile.get('seniority_level', 'Mid')}
City: {self.profile.get('city', 'Remote')}

Default logic to use if asked:
- Salary expectations (B2B/Net): 60-120 PLN/h depending on seniority.
- Notice period / Availability: ASAP or 1 month.
- Location: {self.profile.get('city', 'Remote')}.

Here are the empty fields found on the page:
{questions_text}

For each field, generate an appropriate answer based on the candidate's profile.
If it's a 'select' field, you MUST choose exactly one of the provided OPTIONS (the exact string).
Return ONLY a valid JSON object where keys are the field IDs and values are your generated answers.
Example: {{"dyn_field_0": "ASAP", "dyn_field_1": "Remote"}}
"""
            
            response = self.llm.ask(prompt)
            import json
            import re
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                answers = json.loads(json_match.group(0))
                for field_id, answer in answers.items():
                    print(f"🤖 LLM decided for {field_id}: {answer}")
                    selector = f"[data-ai-dyn-id='{field_id}']"
                    try:
                        field_info = next((f for f in fields if f['id'] == field_id), None)
                        if field_info:
                            if field_info['tag'] == 'select':
                                page.select_option(selector, label=str(answer), timeout=2000)
                            else:
                                loc = page.locator(selector).first
                                self.robust_fill_field(loc, str(answer))
                    except Exception as e:
                        print(f"⚠️ Failed to fill {field_id}: {e}")
            else:
                print("⚠️ LLM did not return valid JSON.")
                
        except Exception as e:
            print(f"❌ Error in fill_dynamic_questions: {e}")

    def find_main_apply_button(self, page):
        """COMBO: DOM selectors + JS filtering + positioning"""
        print("🔍 Searching for main Apply button (MULTI-STRATEGY)...")
        
        try:
            page.wait_for_selector("a:has-text('Aplikuj'), button:has-text('Aplikuj'), a:has-text('Apply'), button:has-text('Apply'), [data-test='button-apply']", timeout=5000)
        except:
            pass

        direct_selectors = [
            "[data-test='button-apply']",
            "[data-test='button-apply-quick']",
            "div[data-test='section-offer-header'] button:has-text('Aplikuj')",
            "div[data-test='section-offer-header'] a:has-text('Aplikuj')",
            "div[data-test='section-offer-action'] button:has-text('Aplikuj')",
            "a.postings-btn",  # Lever
            "#apply_button",   # Greenhouse
            ".application-button",
            "button:has-text('Apply for this job')",
            "a:has-text('Apply for this job')"
        ]

        for sel in direct_selectors:
            try:
                # Iterate through all elements matching the selector
                elements = page.locator(sel).all()
                for btn in elements:
                    if btn.is_visible(timeout=500):
                        print(f"✅ STRATEGY 1: Found visible button by selector [{sel}]")
                        return btn
            except:
                pass

        print("⚙️ STRATEGY 2: Filtering by parent...")
        try:
            buttons = page.locator("button:has-text('Aplikuj'), button:has-text('Apply'), a:has-text('Aplikuj'), a:has-text('Apply'), div[role='button']:has-text('Apply'), span[role='button']:has-text('Apply')")

            main_button = buttons.filter(
                has_not=page.locator(":has-text('Sprawdź podobne')")
            ).first

            if main_button.is_visible(timeout=2000):
                print("✅ STRATEGY 2: Found via filter (excluded 'Sprawdź podobne')")
                return main_button
        except Exception as e:
            print(f"⚠️ Strategy 2 failed: {e}")

        print("⚙️ STRATEGY 3: Search by position (Y coordinate)...")
        try:
            all_buttons = page.locator("button:has-text('Aplikuj'), button:has-text('Apply'), a:has-text('Aplikuj'), a:has-text('Apply'), div[role='button']:has-text('Apply'), a:has-text('Apply Now'), button:has-text('Apply Now')").all()

            main_button = None
            min_y = 9999

            for btn in all_buttons:
                try:
                    if not btn.is_visible():
                        continue

                    box = btn.bounding_box()
                    if not box:
                        continue

                    # Adjust for potentially huge buttons or small buttons
                    if box['y'] < 2000 and box['height'] > 20 and box['width'] > 40:
                        if box['y'] < min_y:
                            min_y = box['y']
                            main_button = btn
                            print(f"📍 Candidate: Y={int(box['y'])}, size {int(box['width'])}x{int(box['height'])}")
                except:
                    continue

            if main_button:
                print(f"✅ STRATEGY 3: Selected top button (Y={int(min_y)})")
                return main_button
        except Exception as e:
            print(f"⚠️ Strategy 3 failed: {e}")

        print("⚙️ STRATEGY 4: JS-filtering 'similar' block...")
        try:
            js_code = """
            () => {
                const elements = Array.from(document.querySelectorAll('button, a'));
                for (let el of elements) {
                    const text = (el.innerText || '').toLowerCase();
                    if (text.includes('aplikuj') || text.includes('apply')) {
                        const rect = el.getBoundingClientRect();
                        if (rect.width === 0 || rect.height === 0) continue;

                        const isSimilar = el.closest('[data-test*="similar"], [class*="similar"], [id*="similar"], [data-test*="recommend"], [class*="podobne"]');
                        if (!isSimilar) {
                            el.setAttribute('data-ai-target-btn', 'true');
                            return true;
                        }
                    }
                }
                return false;
            }
            """
            if page.evaluate(js_code):
                btn = page.locator("[data-ai-target-btn='true']").first
                print("✅ STRATEGY 4: JS found button (excluded 'similar' block)")
                return btn
        except Exception as e:
            print(f"⚠️ Strategy 4 failed: {e}")

        print("❌ ALL STRATEGIES FAILED! Apply button not found!")
        return None

    def robust_fill_field(self, element, value):
        if not value: return False
        value = str(value)
        try:
            # Level 1: Standard Fill
            element.fill(value, force=True, timeout=2000)
            return True
        except:
            try:
                # Level 2: Click, Clear, Type
                element.click(force=True, timeout=1000)
                element.press("Control+A")
                element.press("Backspace")
                element.type(value, delay=50)
                return True
            except:
                try:
                    # Level 3: JS Evaluation
                    js_code = """
                    (el, val) => {
                        el.value = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                        el.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Enter' }));
                    }
                    """
                    element.evaluate(js_code, value)
                    return True
                except:
                    return False

    def test_pracuj(self, page, context, job_link):
        print(f"🌍 [PRACUJ TEST] {job_link}")

        if any(domain in job_link.lower() for domain in self.manual_domains):
            print(f"🛑 Complex ATS. Skip!")
            return "Manual"

        page.goto(job_link, timeout=30000)
        time.sleep(3)
        self.kill_cookies(page)

        apply_button = self.find_main_apply_button(page)
        target_page = page

        if not apply_button:
            if page.locator("input[type='email'], input[name*='email' i], input[name*='first' i]").count() > 0:
                print("✅ Apply button not found, but form inputs detected! Proceeding to fill...")
            else:
                print("❌ Test cancelled: Apply button not found and no form inputs detected.")
                return "Failed"
        else:
            try:
                apply_button.scroll_into_view_if_needed()
                time.sleep(1)
                print(f"🖱️ Clicking...")

                with context.expect_page(timeout=5000) as new_page_info:
                    apply_button.click(force=True)

                target_page = new_page_info.value
                print(f"✅ New tab: {target_page.url}")

                if any(domain in target_page.url.lower() for domain in self.manual_domains):
                    print(f"🛑 Monster-ATS. Skip! Requires Manual Registration.")
                    return "Manual"

                time.sleep(3)
                self.kill_cookies(target_page)

            except:
                print("✅ Form on the same page")
                try:
                    apply_button.click(force=True)
                    time.sleep(2)
                except:
                    pass
                self.kill_cookies(target_page)

        try:
            kontynuuj_btn = target_page.locator("button:has-text('Kontynuuj aplikowanie'), a:has-text('Kontynuuj aplikowanie')").first
            if kontynuuj_btn.is_visible(timeout=2000):
                print("🚧 Modal. Clicking 'Kontynuuj'...")
                old_pages = len(context.pages)
                kontynuuj_btn.click(force=True)
                time.sleep(4)
                
                if len(context.pages) > old_pages:
                    target_page = context.pages[-1]
                    print(f"✅ Navigated: {target_page.url}")
                else:
                    print(f"✅ Clicked Kontynuuj, stayed on same page.")
                    if target_page.locator("text=/Dzi.kujemy/i").count() > 0 or target_page.locator("text=/Thank you/i").count() > 0 or target_page.locator("text=/Aplikacja wys.ana/i").count() > 0:
                        print("🎉 1-Click Apply Successful!")
                        return "Success"

                if any(domain in target_page.url.lower() for domain in self.manual_domains):
                    print(f"🛑 Monster-ATS. Skip! Requires Manual Registration.")
                    return "Manual"
                time.sleep(3)
                self.kill_cookies(target_page)
        except Exception as e:
            print(f"⚠️ Warning with Kontynuuj: {e}")

        if "login.pracuj.pl" in target_page.url:
            print("🛑 Login required. Waiting 2 minutes...")
            try:
                target_page.wait_for_url(lambda url: "login" not in url.lower(), timeout=120000)
                context.storage_state(path="Data/my_session.json")
                time.sleep(3)
            except:
                print("❌ Timed out")
                return

        print("⏳ Waiting for form...")
        try:
            target_page.wait_for_selector("input:not([type='hidden'])", timeout=10000)
            time.sleep(2)
        except:
            print("⚠️ Form did not appear")

        print("📝 Filling...")
        os.makedirs("Data/screenshots", exist_ok=True)
        session_id = int(time.time())
        try: target_page.screenshot(path=f"Data/screenshots/{session_id}_1_before_fill.png")
        except: pass

        smart_fields = {
            "First Name": {"val": self.profile["first_name"], "css": ['input[name*="first" i]', 'input[autocomplete="given-name"]']},
            "Last Name": {"val": self.profile["last_name"], "css": ['input[name*="last" i]', 'input[autocomplete="family-name"]']},
            "Email": {"val": self.profile["email"], "css": ['input[type="email"]', 'input[name*="email" i]']},
            "Phone": {"val": self.profile["phone"], "css": ['input[type="tel"]', 'input[name*="phone" i]']},
            "GitHub": {"val": self.profile["github"], "css": ['input[type="url"]', 'input[name*="github" i]', 'input[name*="linkedin" i]']}
        }

        for field_name, data in smart_fields.items():
            filled = False
            regex_map = {
                "First Name": r"imię|imie|first",
                "Last Name": r"nazwisko|last",
                "Email": r"e-?mail",
                "Phone": r"telefon|phone|tel",
                "GitHub": r"linkedin|github|url"
            }
            rx = re.compile(regex_map[field_name], re.IGNORECASE)

            for method in [target_page.get_by_placeholder, target_page.get_by_label]:
                if filled: break
                try:
                    loc = method(rx)
                    for i in range(loc.count()):
                        el = loc.nth(i)
                        if el.is_editable() and el.is_visible():
                            self.robust_fill_field(el, data["val"])
                            print(f"✅ {field_name}")
                            filled = True
                            break
                except:
                    pass

            if not filled:
                for css in data["css"]:
                    try:
                        elements = target_page.locator(css)
                        for i in range(elements.count()):
                            el = elements.nth(i)
                            if el.is_editable() and el.is_visible():
                                self.robust_fill_field(el, data["val"])
                                print(f"✅ {field_name}")
                                filled = True
                                break
                        if filled: break
                    except:
                        pass

        print("📎 CV...")
        try:
            file_inputs = target_page.locator('input[type="file"]')
            for i in range(file_inputs.count()):
                try:
                    file_input = file_inputs.nth(i)
                    cv_to_upload = self.profile.get("cv_path", TEST_CV_PATH)
                    if os.path.exists(cv_to_upload):
                        file_input.set_input_files(cv_to_upload)
                        print("✅ Uploaded")
                        time.sleep(2)
                        break
                except:
                    continue
        except:
            pass

        print("☑️ Checkboxes...")
        self.check_all_checkboxes(target_page)

        self.fill_dynamic_questions(target_page)
        
        try: target_page.screenshot(path=f"Data/screenshots/{session_id}_2_after_fill.png")
        except: pass

        for attempt in range(2):
            print(f"🚀 Submit (Attempt {attempt+1})...")
            try:
                submit_button = target_page.locator(
                    "button[type='submit'], "
                    "input[type='submit'], "
                    "button:has-text('Wyślij'), "
                    "button:has-text('Wyślij aplikację'), "
                    "button:has-text('Send'), "
                    "input[value='Wyślij'], "
                    "input[value='Send'], "
                    "[data-test='button-submit']"
                ).last

                if submit_button.count() == 0:
                    print("⚠️ Could not find a submit button matching the selectors.")
                    break

                try: submit_button.scroll_into_view_if_needed(timeout=2000)
                except: pass
                time.sleep(1)
                
                try:
                    submit_button.click(force=True, timeout=5000)
                except Exception as click_err:
                    print(f"⚠️ Playwright click failed, trying JS click... {click_err}")
                    try:
                        submit_button.evaluate("el => el.click()")
                    except Exception as eval_err:
                        print(f"⚠️ Submit JS evaluation error: {eval_err}")
                        raise
                    
                print("✅ SUBMITTED!")
                time.sleep(5)
                
                try: target_page.screenshot(path=f"Data/screenshots/{session_id}_3_after_submit_{attempt}.png")
                except: pass
                
                if self.llm:
                    try:
                        import base64
                        screenshot_bytes = target_page.screenshot()
                        b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                        prompt = "I just clicked the submit button on this job application form. Are there any validation error messages (like 'To pole jest wymagane', 'Required', red text) or missed required fields? Answer ONLY 'YES' if there are errors preventing submission. Answer 'NO' if it looks successful, if there's a thank you message, or if there are no visible error messages."
                        res = self.llm.ask_with_image(prompt, b64).strip().upper()
                        print(f"🔍 Post-submit check: {res}")
                        if "YES" in res:
                            print("⚠️ Found validation errors. Trying to fill missing fields again...")
                            self.check_all_checkboxes(target_page)
                            self.fill_dynamic_questions(target_page)
                            continue
                    except Exception as e:
                        print(f"⚠️ Could not check post-submit status (probably page closed/redirected): {e}")
                
                return "Applied"
            except Exception as e:
                print(f"⚠️ Submit error: {e}")
                if attempt == 0:
                    time.sleep(2)
                    continue
                return "Failed"
                
        return "Failed"


def run_sandbox():
    CURRENT_TEST_URL = "https://www.pracuj.pl/praca/full-stack-java-angular-developer-warszawa,oferta,1004906918?s=c693da39&searchId=MTc4MTY1NzA4NTQ0Ny4zMjUy"
    print("🧪 RUNNING MULTI-STRATEGY...")

    llm = LLMHandler()
    sandbox = SandboxApplier(MY_PROFILE, llm)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            slow_mo=200,
            args=["--disable-blink-features=AutomationControlled", "--disable-infobars"]
        )

        session_file = "Data/my_session.json"
        if os.path.exists(session_file):
            print("🔑  OK")
            context = browser.new_context(viewport={"width": 1920, "height": 1080}, storage_state=session_file)
        else:
            print("⚠️")
            context = browser.new_context(viewport={"width": 1920, "height": 1080})

        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            sandbox.test_pracuj(page, context, CURRENT_TEST_URL)
            print("\n🏁  30 ...")
            time.sleep(30)
        except Exception as e:
            print(f"💥 : {e}")
            import traceback
            traceback.print_exc()
            time.sleep(30)
        finally:
            browser.close()


if __name__ == "__main__":
    run_sandbox()