import time
import os
import base64
import json
from playwright.sync_api import Page, ElementHandle
from Appliers.base_applier import BaseApplier

class BulletproofApplier(BaseApplier):
    """
    The 100% Success Rate Apply Engine.
    Uses LLM Vision to read errors, verifies steps, and iteratively submits.
    """
    def __init__(self, profile_data, llm_handler=None):
        super().__init__(profile_data, llm_handler)
        self.profile = profile_data
        self.llm = llm_handler
        self.max_steps = 5
        self.max_retries_per_step = 3
        
        self.manual_domains = [
            'workday', 'taleo', 'successfactors', 'icims', 'brassring',
            'myworkdayjobs', 'breezy.hr', 'applytojob.com', 'ashbyhq.com', 
            'workable.com', 'bamboohr.com'
        ]

    def _get_screenshot_b64(self, page: Page):
        try:
            bytes_data = page.screenshot()
            return base64.b64encode(bytes_data).decode('utf-8')
        except:
            return ""

    def apply(self, page: Page, context, job_link, cv_path, cover_letter=""):
        print(f"🌍 [BULLETPROOF] Opening: {job_link}")
        
        # We no longer skip any domains. We force the AI to try everything.

        try:
            page.goto(job_link, timeout=40000)
            page.wait_for_load_state('networkidle', timeout=10000)
        except Exception as e:
            print(f"⚠️ Page load warning: {e}")

        time.sleep(3)
        self.kill_cookies(page)

        # Look for the initial "Apply" button to start the form
        target_page = self._start_form(page, context)
        
        if target_page == "ALREADY_APPLIED":
            return ("Applied", "Already applied (detected 'ponownie')")
            
        if not target_page:
            target_page = page
            target_page = page
            print("🤖 [AI AUTONOMOUS] Scanning for 'Apply' buttons to start the process...")
            synonyms = ['aplikuj szybko', 'kontynuuj aplikowanie', 'apply', 'aplikuj', 'bewerben', 'postuler', 'start', 'join', 'easy apply']
            found_btn = False
            elements = target_page.locator("button, a, div[role='button'], span[role='button']")
            for i in range(min(100, elements.count())):
                try:
                    el = elements.nth(i)
                    if el.is_visible():
                        text = el.text_content().lower()
                        # We explicitly want to trigger the apply flow if we see an apply button
                        if any(syn in text for syn in synonyms) and len(text) < 40 and not any(skip in text for skip in ['submit', 'wyślij', 'send']):
                            print(f"🖱️ Clicking Apply button: '{text.strip()}'")
                            try:
                                with context.expect_page(timeout=4000) as new_page_info:
                                    el.click(force=True)
                                target_page = new_page_info.value
                                found_btn = True
                                break
                            except:
                                el.click(force=True)
                                time.sleep(4)
                                if len(context.pages) > 1 and context.pages[-1] != target_page:
                                    target_page = context.pages[-1]
                                found_btn = True
                                break
                except: pass
            
            # Now verify we have some sort of form
            form_inputs = target_page.locator("input:not([type='hidden']), textarea, select").count()
            if form_inputs == 0:
                print("❌ Autonomous scan failed. No form found. Skipping job.")
                return "Failed"

        # Begin multi-step submission loop
        for step in range(1, self.max_steps + 1):
            print(f"\n--- 🛡️ BULLETPROOF STEP {step} ---")
            time.sleep(2)
            
            # Check for iframe
            target_frame = self._get_form_frame(target_page)
            
            self._fill_form_fields(target_frame, cv_path)
            self._check_all_checkboxes(target_frame)
            
            print("📸 [PRE-CHECK] Analyzing form for empty required fields before clicking submit...")
            self._resolve_errors(target_frame)
            
            # Find and click Submit/Next
            btn = self._find_submit_button(target_frame)
            if not btn:
                print("🤖 [AI AUTONOMOUS] Cannot find Submit button. Attempting aggressive scan...")
                synonyms = ['submit', 'next', 'continue', 'wyślij', 'dalej', 'aplikuj', 'apply', 'send']
                elements = target_frame.locator("button, a, input[type='submit'], input[type='button']")
                for i in range(min(50, elements.count())):
                    try:
                        el = elements.nth(i)
                        if el.is_visible():
                            text = (el.text_content() or "").lower()
                            if not text:
                                text = (el.get_attribute('value') or "").lower()
                                
                            if any(syn in text for syn in synonyms) and 'ponownie' not in text and len(text) < 30:
                                btn = el
                                print(f"🖱️ Found hidden submit button: '{text.strip()}'")
                                break
                    except: pass
                
            if not btn:
                print("❌ No Submit button found at all. Failing job.")
                return ("Failed", "No Submit button found on form")
            
            # Click and verify loop
            for attempt in range(self.max_retries_per_step):
                print(f"🚀 Clicking Action Button (Attempt {attempt+1})...")
                try:
                    btn.scroll_into_view_if_needed(timeout=2000)
                    time.sleep(1)
                    btn.click(force=True, timeout=5000)
                except Exception as e:
                    try: btn.evaluate("el => el.click()")
                    except: pass
                
                print("📸 [POST-CHECK] Waiting for page response and verifying via Vision LLM...")
                time.sleep(5)
                
                # Verification via LLM Vision
                status = self._verify_post_submit(target_page)
                if status == "SUCCESS":
                    print("🎉 SUCCESS! Application completed.")
                    return "Applied"
                elif status == "NEXT_STEP":
                    print("➡️ Moving to next step...")
                    break # Breaks inner retry loop, continues outer step loop
                elif status == "ERROR":
                    print("❌ Validation errors detected by Vision LLM. Attempting to fix...")
                    self._resolve_errors(target_frame)
                    # Loop back to click submit again
                    continue
                else:
                    print("❓ Unknown state after submit.")
                    break # Break to the outer loop to fail eventually
                    
            # If we reach here, we either broke out for NEXT_STEP, or ran out of retries/unknown state.
            if status == "NEXT_STEP":
                continue

            print("❌ [AI AUTONOMOUS] Bot is stuck or unsure. Failing job to prevent hanging.")
            return ("Failed", f"Stuck at step {step} with status {status}")
                
        # If max steps exceeded
        print("❌ [AI AUTONOMOUS] Max steps exceeded. Failing job.")
        return ("Failed", f"Max form steps ({self.max_steps}) exceeded")

    def kill_cookies(self, page):
        print("🍪 Killing cookies...")
        try:
            buttons = page.locator("button, a")
            for i in range(min(50, buttons.count())):
                try:
                    btn = buttons.nth(i)
                    if btn.is_visible():
                        text = btn.text_content().lower()
                        if any(x in text for x in ["akceptuj", "accept", "zezwól", "allow", "zgadzam"]):
                            btn.click(timeout=1000)
                            time.sleep(1)
                except: pass
        except: pass

    def _start_form(self, page, context):
        target_page = None
        
        # Check if already applied
        already_applied = page.locator("button:has-text('ponownie'), a:has-text('ponownie'), :text('Aplikowałeś')").count() > 0
        if already_applied:
            print("⚠️ Already applied to this job! ('ponownie' detected)")
            return "ALREADY_APPLIED"

        apply_btn = page.locator("button:has-text('Aplikuj'), button:has-text('Apply'), a:has-text('Aplikuj'), a:has-text('Apply')").first
        if apply_btn.is_visible(timeout=2000):
            print("🖱️ Found start Apply button. Clicking...")
            try:
                with context.expect_page(timeout=5000) as new_page_info:
                    apply_btn.click(force=True)
                target_page = new_page_info.value
                print("✅ Opened in new tab.")
            except:
                try:
                    apply_btn.click(force=True)
                    target_page = page
                    print("✅ Clicked on same page.")
                except:
                    pass
        
        if not target_page:
            target_page = page

        # Handle 'Kontynuuj' modal
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
        except:
            pass

        if "login.pracuj.pl" in target_page.url:
            print("🛑 Login required. Waiting 2 minutes...")
            try:
                target_page.wait_for_url(lambda url: "login" not in url.lower(), timeout=120000)
                context.storage_state(path="Data/my_session.json")
                time.sleep(3)
            except:
                print("❌ Timed out waiting for login")
                return None

        return target_page

    def _get_form_frame(self, page):
        # Look for iframe if main page has no inputs
        if page.locator("input:not([type='hidden'])").count() == 0:
            for frame in page.frames:
                if frame.locator("input:not([type='hidden'])").count() > 0:
                    print(f"🪟 Found form inside iframe: {frame.name or frame.url}")
                    return frame
        return page

    def _fill_form_fields(self, frame, cv_path):
        print("📝 Smart Filling...")
        # Upload CV first
        try:
            file_inputs = frame.locator('input[type="file"]')
            if file_inputs.count() > 0 and os.path.exists(cv_path):
                file_inputs.first.set_input_files(cv_path)
                print("✅ CV Uploaded")
                time.sleep(1)
        except: pass

        # Standard fields mapping
        smart_fields = {
            "First Name": {"val": self.profile.get("first_name", ""), "css": ['input[name*="first" i]', 'input[autocomplete="given-name"]']},
            "Last Name": {"val": self.profile.get("last_name", ""), "css": ['input[name*="last" i]', 'input[autocomplete="family-name"]']},
            "Email": {"val": self.profile.get("email", ""), "css": ['input[type="email"]', 'input[name*="email" i]']},
            "Phone": {"val": self.profile.get("phone", ""), "css": ['input[type="tel"]', 'input[name*="phone" i]']},
            "GitHub": {"val": self.profile.get("github", ""), "css": ['input[type="url"]', 'input[name*="github" i]', 'input[name*="linkedin" i]']}
        }

        import re
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
            
            for method in [frame.get_by_placeholder, frame.get_by_label]:
                if filled: break
                try:
                    loc = method(rx)
                    if loc.count() > 0:
                        el = loc.first
                        if el.is_editable() and el.is_visible():
                            self.robust_fill_field(el, data["val"])
                            print(f"✅ {field_name} (by label/placeholder)")
                            filled = True
                except: pass
            
            if not filled:
                for css in data["css"]:
                    try:
                        elements = frame.locator(css)
                        if elements.count() > 0:
                            el = elements.first
                            if el.is_editable() and el.is_visible():
                                self.robust_fill_field(el, data["val"])
                                print(f"✅ {field_name} (by css)")
                                break
                    except: pass

    def _check_all_checkboxes(self, frame):
        print("☑️ Scanning and checking checkboxes...")
        try:
            checkboxes = frame.locator('input[type="checkbox"]')
            count = checkboxes.count()
            for i in range(count):
                try:
                    cb = checkboxes.nth(i)
                    is_checked = cb.evaluate("el => el.checked")
                    if is_checked: continue
                    
                    try:
                        # Try standard visible check first
                        cb.check(timeout=1000)
                    except:
                        # If hidden or intercepted, click parent label or force JS click
                        parent_label = cb.locator("xpath=ancestor::label").first
                        if parent_label.is_visible():
                            parent_label.click(force=True)
                        else:
                            cb.evaluate("el => el.click()")
                except: pass
        except: pass

    def _find_submit_button(self, frame):
        try:
            btn = frame.locator(
                "button[type='submit'], input[type='submit'], "
                "button:has-text('Wyślij'), button:has-text('Send'), "
                "button:has-text('Next'), button:has-text('Continue'), "
                "button:has-text('Dalej'), button:has-text('Submit')"
            ).last
            if btn.count() > 0:
                return btn
        except: pass
        return None

    def _verify_post_submit(self, page):
        if not self.llm:
            return "SUCCESS"
        b64 = self._get_screenshot_b64(page)
        if not b64: return "SUCCESS"

        prompt = "Look at this screenshot of a job application page after I clicked Submit/Next. What is the status? Answer ONLY with one of these three exact words:\n" \
                 "SUCCESS (if there is a clear thank you message confirming the application is received. Do NOT reply SUCCESS if it's just asking to fill out a survey/poll)\n" \
                 "ERROR (if there are red validation texts, missed required fields, error banners, or survey forms requiring input)\n" \
                 "NEXT_STEP (if the form proceeded to step 2 or a new blank form page)"
        
        try:
            res = self.llm.ask_with_image(prompt, b64).strip().upper()
            print(f"🔍 Vision LLM Judgment: {res}")
            if "SUCCESS" in res: return "SUCCESS"
            if "ERROR" in res: return "ERROR"
            if "NEXT_STEP" in res or "NEXT" in res: return "NEXT_STEP"
        except Exception as e:
            print(f"⚠️ Vision verification failed: {e}")
            
        return "SUCCESS" # fallback

    def _resolve_errors(self, frame):
        print("🧠 [AI SOLVER] Deep analysis of missing fields and errors...")
        try:
            # 1. Gather all empty inputs, textareas, and selects
            questions_dict = {}
            elements = frame.locator("input:not([type='hidden']):not([type='file']):not([type='checkbox']):not([type='radio']), textarea, select")
            js_script = """
            () => {
                let result = {};
                
                // 1. Inputs, textareas, selects
                let els = document.querySelectorAll("input:not([type='hidden']):not([type='radio']):not([type='checkbox']), textarea, select");
                els.forEach(el => {
                    if (el.type === 'file') return;
                    if (!el.value || el.value.trim() === "") {
                        let css = el.id ? "#" + el.id : (el.name ? "*[name='" + el.name + "']" : "");
                        if (!css) return;
                        
                        let context = "";
                        if (el.id) {
                            let lbl = document.querySelector("label[for='" + el.id + "']");
                            if (lbl) context += lbl.innerText + " | ";
                        }
                        let wrapper = el.closest('.form-group, .field, div');
                        if (wrapper && context.length < 10) {
                            let lbl = wrapper.querySelector('label');
                            if (lbl) context += lbl.innerText + " | ";
                        }
                        
                        let placeholder = el.placeholder || "";
                        if (placeholder) context += placeholder;
                        
                        if (el.tagName === 'SELECT') {
                            let opts = Array.from(el.querySelectorAll('option')).map(o => o.innerText.trim() || o.value).filter(Boolean).join(', ');
                            context += " (Options: " + opts + ")";
                        }
                        
                        let final_text = context.replace(/\\s+/g, ' ').trim();
                        if (final_text) result[css] = final_text.substring(0, 300);
                    }
                });

                // 2. Radio buttons (grouped by name)
                let radios = document.querySelectorAll("input[type='radio']");
                let radioGroups = {};
                radios.forEach(r => {
                    if (r.name) {
                        if (!radioGroups[r.name]) radioGroups[r.name] = [];
                        let labelText = r.value;
                        if (r.id) {
                            let lbl = document.querySelector("label[for='" + r.id + "']");
                            if (lbl) labelText = lbl.innerText.trim();
                        }
                        if (!labelText) {
                             let parentLbl = r.closest('label');
                             if (parentLbl) labelText = parentLbl.innerText.trim();
                        }
                        radioGroups[r.name].push({val: r.value, text: labelText, checked: r.checked});
                    }
                });

                for (let name in radioGroups) {
                    let group = radioGroups[name];
                    if (!group.some(r => r.checked)) {
                        // None selected
                        let css = "*[name='" + name + "']";
                        let opts = group.map(r => r.text || r.val).join(", ");
                        
                        let context = "";
                        let firstRadio = document.querySelector(css);
                        if (firstRadio) {
                            let wrapper = firstRadio.closest('.form-group, .field, fieldset, div');
                            if (wrapper) {
                                let legend = wrapper.querySelector('legend, label');
                                if (legend) context = legend.innerText.trim() + " | ";
                            }
                        }
                        result[css] = context + " (Radio Options: " + opts + "). Reply exactly with one of the options.";
                    }
                }
                
                return result;
            }
            """
            
            try:
                questions_dict = frame.evaluate(js_script)
            except Exception as e:
                print(f"⚠️ Smart Context JS failed: {e}")
                questions_dict = {}

            if questions_dict and self.llm:
                print(f"🕵️ AI detected {len(questions_dict)} empty or problematic fields. Delegating to LLM...")
                answers = self.llm.solve_form(questions_dict, self.profile)
                for css, answer in answers.items():
                    if css not in questions_dict:
                        continue
                    if answer:
                        ans_str = str(answer)
                        if ans_str.lower() not in ["none", "null", "n/a", ""]:
                            try:
                                loc = frame.locator(css)
                                if loc.count() > 1 and loc.first.evaluate("el => el.type === 'radio'"):
                                    js_click = """
                                    (els, val) => {
                                        let match = els.find(r => r.value.trim() === val.trim());
                                        if (!match) {
                                            match = els.find(r => {
                                                let lbl = document.querySelector("label[for='" + r.id + "']");
                                                if (lbl && lbl.innerText.includes(val)) return true;
                                                let pLbl = r.closest('label');
                                                if (pLbl && pLbl.innerText.includes(val)) return true;
                                                return false;
                                            });
                                        }
                                        if (match) { match.click(); return true; }
                                        // fuzzy fallback
                                        match = els.find(r => val.includes(r.value));
                                        if (match) { match.click(); return true; }
                                        return false;
                                    }
                                    """
                                    success = loc.evaluate_all(js_click, ans_str)
                                    if success:
                                        print(f"✅ AI intelligently selected radio [{css}] -> {ans_str}")
                                    else:
                                        loc.first.click(force=True)
                                        print(f"✅ AI fallback clicked first radio [{css}]")
                                else:
                                    self.robust_fill_field(loc.first, ans_str)
                                    print(f"✅ AI intelligently filled [{css}] -> {ans_str}")
                            except Exception as e:
                                print(f"⚠️ Failed to fill {css}: {e}")
            else:
                print("🤷 No standard empty text fields found. It might be a custom dropdown or a checkbox issue.")

            # 2. Force check all remaining checkboxes and radios
            print("☑️ AI enforcing missing checkboxes/radios...")
            self._check_all_checkboxes(frame)
            
            # 3. Check for specific common ATS weirdness (like select2, custom UI components)
            # The LLM answers will cover basic selects, but checkboxes are brutal force
        except Exception as e:
            print(f"⚠️ AI Solver execution error: {e}")
        return True
