import time
from playwright.sync_api import Page
from Core.bulletproof_engine import BulletproofApplier

class InteractiveApplier(BulletproofApplier):
    """
    Advanced Deterministic Two-Pass Engine.
    Used as a fallback when BulletproofEngine fails.
    Physically clicks custom comboboxes to reveal options in DOM before asking LLM.
    """
    def __init__(self, profile_data, llm_handler=None):
        super().__init__(profile_data, llm_handler)
        self.profile = profile_data
        self.llm = llm_handler

    def apply(self, page: Page, context, job_link, cv_path, cover_letter=""):
        print(f"🌍 [INTERACTIVE FALLBACK] Initiating Deterministic Discovery on {job_link}")
        
        try:
            target_frame = page
            # Look for iframe if main page has no inputs
            if page.locator("input:not([type='hidden'])").count() == 0:
                for frame in page.frames:
                    if frame.locator("input:not([type='hidden'])").count() > 0:
                        target_frame = frame
                        break

            print("🔍 Phase 1: Physical Discovery of custom comboboxes...")
            # We target custom comboboxes that aren't native <select>
            comboboxes = target_frame.locator("[role='combobox']")
            questions = {}
            for i in range(comboboxes.count()):
                cb = comboboxes.nth(i)
                try:
                    if not cb.is_visible() or cb.is_disabled(): continue
                    
                    val = cb.input_value() if cb.evaluate("el => el.tagName === 'INPUT'") else cb.inner_text()
                    if val.strip() and val.strip().lower() not in ["select...", "select", "choose", "wybierz"]: 
                        continue # Skip already filled fields

                    # Find contextual label
                    js_label = """
                    (el) => {
                        let lbl = document.querySelector(`label[for='${el.id}']`);
                        if (lbl) return lbl.innerText.trim();
                        let p = el.closest('div, label, fieldset');
                        if (p) {
                            let l = p.querySelector('label, legend');
                            if (l) return l.innerText.trim();
                        }
                        return el.getAttribute('aria-label') || el.placeholder || "";
                    }
                    """
                    lbl = cb.evaluate(js_label)
                    
                    # Ensure we have a unique CSS selector to interact with it later
                    css = ""
                    el_id = cb.evaluate("el => el.id")
                    el_name = cb.evaluate("el => el.name")
                    if el_id: css = f"#{el_id}"
                    elif el_name: css = f"*[name='{el_name}']"
                    else: 
                        aria = cb.evaluate("el => el.getAttribute('aria-label')")
                        css = f"[aria-label='{aria}']"

                    # Physical click to reveal options in DOM
                    cb.scroll_into_view_if_needed()
                    cb.click(force=True)
                    time.sleep(0.5)
                    
                    # Extract revealed options (Greenhouse, Lever, etc. use these roles)
                    opts = target_frame.locator("[role='option'], [role='treeitem'], li").all_inner_texts()
                    opts = [o.strip() for o in opts if o.strip() and o.strip().lower() not in ["select...", "select", "choose", "wybierz"]]
                    
                    # Close the dropdown
                    target_frame.keyboard.press("Escape")
                    target_frame.keyboard.press("Tab") # Fallback to blur
                    time.sleep(0.3)
                    
                    if opts and css and css != "[]":
                        questions[css] = f"{lbl} (Options: {', '.join(opts[:15])}). Reply exactly with one of the options."
                except Exception as e:
                    print(f"⚠️ Error parsing a combobox: {e}")

            if questions and self.llm:
                print(f"🕵️ AI resolving {len(questions)} discovered comboboxes...")
                answers = self.llm.solve_form(questions, self.profile)
                for css, ans in answers.items():
                    if not ans: continue
                    try:
                        cb = target_frame.locator(css).first
                        cb.scroll_into_view_if_needed()
                        cb.click(force=True)
                        time.sleep(0.5)
                        
                        # Try to click the matching option
                        opt_loc = target_frame.locator("[role='option'], [role='treeitem'], li").filter(has_text=str(ans)).first
                        if opt_loc.is_visible():
                            opt_loc.click(force=True)
                            print(f"✅ AI selected [{css}] -> {ans}")
                        else:
                            # Fuzzy fallback
                            target_frame.keyboard.press("Escape")
                            print(f"⚠️ Could not click {ans} for {css}")
                    except Exception as e:
                        print(f"⚠️ Failed to select {ans} for {css}: {e}")
                        try: target_frame.keyboard.press("Escape")
                        except: pass

            # Enforce missing checkboxes
            print("☑️ Scanning and checking checkboxes in Interactive pass...")
            self._check_all_checkboxes(target_frame)

            # Re-submit logic
            print("🚀 Retrying Submit after Interactive fixes...")
            synonyms = ['submit', 'next', 'continue', 'wyślij', 'dalej', 'aplikuj', 'apply', 'send', 'submit application']
            btn = None
            elements = target_frame.locator("button, a, input[type='submit'], input[type='button']")
            for i in range(min(50, elements.count())):
                try:
                    el = elements.nth(i)
                    if el.is_visible():
                        text = (el.text_content() or el.get_attribute('value') or "").lower()
                        if any(syn in text for syn in synonyms) and len(text) < 30:
                            btn = el
                            break
                except: pass

            if btn:
                btn.scroll_into_view_if_needed()
                time.sleep(1)
                btn.click(force=True)
                time.sleep(5)
                
                print("📸 [POST-CHECK] Waiting for page response and verifying via Vision LLM...")
                status = self._verify_post_submit(target_frame)
                if status == "SUCCESS":
                    print("🎉 SUCCESS! Application completed (Interactive Pass).")
                    return "Applied"
                elif status == "NEXT_STEP":
                    print("➡️ Moving to next step...")
                    return "Manual" # To trigger loop or just Manual fallback
                elif status == "ERROR":
                    print("❌ Validation errors still present after Interactive pass.")
                    return "Failed"
                
                return "Applied"
            else:
                return "Manual"
            
        except Exception as e:
            print(f"⚠️ InteractiveApplier execution error: {e}")
            return "Failed"
