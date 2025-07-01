import json
import os
import re
import time
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from Appliers.base_applier import BaseApplier


class ConfigDrivenApplier(BaseApplier):
    """
    Один класс вместо 50.
    Читает JSON-конфиги из Appliers/site_configs/ и применяет нужный по URL.
    """

    def __init__(self, profile_data, llm_handler=None):
        super().__init__(profile_data, llm_handler)
        self.configs = self._load_all_configs()
        print(f"✅ [ConfigDrivenApplier] Загружено конфигов: {len(self.configs)}")

    def _load_all_configs(self):
        configs = {}
        config_dir = os.path.join(os.path.dirname(__file__), "site_configs")
        if not os.path.exists(config_dir):
            print(f"⚠️ Папка {config_dir} не найдена!")
            return configs
        for fname in os.listdir(config_dir):
            if fname.endswith(".json"):
                fpath = os.path.join(config_dir, fname)
                try:
                    with open(fpath, encoding="utf-8") as f:
                        cfg = json.load(f)
                    configs[cfg["site_name"]] = cfg
                except Exception as e:
                    print(f"⚠️ Ошибка загрузки {fname}: {e}")
        return configs

    def get_config_for_url(self, url):
        url_lower = url.lower()
        for name, cfg in self.configs.items():
            patterns = cfg.get("url_patterns", [cfg.get("base_url", "").replace("https://", "")])
            if any(p and p in url_lower for p in patterns):
                return cfg
        return None

    # ------------------------------------------------------------------
    # ГЛАВНЫЙ МЕТОД
    # ------------------------------------------------------------------
    def apply(self, page, context, job_link, cv_path, cover_letter=""):
        cfg = self.get_config_for_url(job_link)

        if not cfg:
            print(f"🔮 [ConfigDrivenApplier] Нет конфига для {job_link} — универсальный режим")
            return self._universal_fallback(page, context, job_link, cv_path, cover_letter)

        site = cfg["site_name"]
        ac = cfg["applier"]
        print(f"\n🎯 [{site}] Конфиг найден! Начинаю подачу...")

        # 1. Пре-фильтр ATS по ссылке
        if any(d in job_link.lower() for d in ac.get("ats_blacklist", [])):
            print(f"🛑 [{site}] Ссылка ведёт на ATS-монстра. Пропускаю.")
            return "Manual Apply Required"

        # 2. Открываем страницу
        page.goto(job_link, timeout=30000)
        time.sleep(ac.get("initial_wait", 3))
        self.kill_cookies(page)

        # 3. Клик на Apply
        target_page = self._click_apply(page, context, ac, site, cfg)
        if target_page is None:
            return "Manual Apply Required"

        # 4. Спец-обработка
        target_page = self._special_handling(target_page, context, ac, site)

        self.kill_cookies(target_page)
        time.sleep(2)

        # 5. Ждём форму
        try:
            target_page.wait_for_selector("input:not([type='hidden'])", timeout=8000)
        except:
            print(f"  ⚠️ [{site}] Поля ввода не появились")

        # 6. Заполняем поля
        self._fill_fields(target_page, ac)

        # 7. Form scanner + LLM
        if ac.get("use_form_scanner", True) and self.llm:
            self._run_form_scanner(target_page)

        # 8. Загружаем CV (с поддержкой drag-and-drop зон)
        self._upload_cv(target_page, ac, cv_path, site)

        # 9. Чекбоксы
        self._check_checkboxes(target_page, ac)

        # 10. Submit
        return self._submit(target_page, ac, site)

    # ------------------------------------------------------------------
    # КЛИК Apply — С УМНЫМ ОПРЕДЕЛЕНИЕМ ВНЕШНЕГО ДОМЕНА
    # ------------------------------------------------------------------
    def _click_apply(self, page, context, ac, site, cfg):
        btn_selector = ac.get("apply_button",
                               "button:has-text('Apply'):visible, button:has-text('Aplikuj'):visible")
        try:
            apply_btn = page.locator(btn_selector).first
            apply_btn.wait_for(state="attached", timeout=5000)
        except:
            print(f"  ⚠️ [{site}] Кнопка Apply не найдена")
            return page

        opens_new_tab     = ac.get("opens_new_tab", False)
        skip_external     = ac.get("skip_external_domains", False)
        base_domain       = cfg.get("base_url", "").replace("https://", "").replace("www.", "").split("/")[0]

        if opens_new_tab:
            try:
                with context.expect_page(timeout=4000) as new_page_info:
                    apply_btn.click(force=True)

                new_page = new_page_info.value
                new_url  = new_page.url.lower()
                print(f"  🔗 [{site}] Новая вкладка: {new_page.url}")

                # ✅ ГЛАВНЫЙ ФИКС: если ушли на внешний домен — скипаем
                if skip_external and base_domain and base_domain not in new_url:
                    print(f"  🛑 [{site}] Внешний домен ({new_page.url}) — не наша форма. Пропускаю.")
                    return None

                # Проверяем ATS монстров
                if any(d in new_url for d in ac.get("ats_blacklist", [])):
                    print(f"  🛑 [{site}] Редирект на ATS-монстра!")
                    return None

                new_page.wait_for_load_state("networkidle", timeout=10000)
                time.sleep(2)
                return new_page

            except:
                # Новая вкладка не открылась — значит форма прямо на странице
                print(f"  ℹ️ [{site}] Новая вкладка не открылась, остаёмся")
                apply_btn.click(force=True)
                time.sleep(2)
                return page
        else:
            apply_btn.click(force=True)
            time.sleep(2)
            return page

    # ------------------------------------------------------------------
    # СПЕЦ-ОБРАБОТКА
    # ------------------------------------------------------------------
    def _special_handling(self, target_page, context, ac, site):
        for spec in ac.get("special_handling", []):
            kind = spec.get("type")

            if kind == "click_modal":
                try:
                    btn = target_page.locator(spec["selector"]).first
                    if btn.is_visible(timeout=3000):
                        print(f"  🚧 [{site}] Жму модалку: {spec.get('label','')}")
                        try:
                            with context.expect_page(timeout=5000) as p_info:
                                btn.evaluate("node => node.click()")
                            target_page = p_info.value
                            time.sleep(3)
                        except:
                            btn.click(force=True)
                            time.sleep(2)
                except:
                    pass

            elif kind == "wait_login":
                if spec.get("url_trigger", "") in target_page.url:
                    print(f"  🔑 [{site}] Нужен логин! Жду {spec.get('timeout_sec', 120)} сек...")
                    try:
                        target_page.wait_for_url(
                            lambda url: spec["url_trigger"] not in url.lower(),
                            timeout=spec.get("timeout_sec", 120) * 1000
                        )
                        context.storage_state(path="Data/my_session.json")
                        time.sleep(3)
                    except:
                        print(f"  ❌ [{site}] Время логина вышло")

            elif kind == "secondary_apply":
                try:
                    sec_btn = target_page.locator(spec["selector"]).first
                    if sec_btn.is_visible(timeout=3000):
                        print(f"  🖱️ [{site}] Вторичная кнопка Apply найдена")
                        sec_btn.click(force=True)
                        time.sleep(3)
                        self.kill_cookies(target_page)
                except:
                    pass

            elif kind == "replace_cv":
                try:
                    change_btn = target_page.locator(spec["change_selector"]).first
                    if change_btn.is_visible(timeout=3000):
                        print(f"  ♻️ [{site}] Заменяю старое CV...")
                        change_btn.click(force=True)
                        time.sleep(1)
                        add_btn = target_page.locator(spec.get("add_selector", "")).first
                        if add_btn.is_visible(timeout=1000):
                            add_btn.click(force=True)
                            time.sleep(1)
                except:
                    pass

        return target_page

    # ------------------------------------------------------------------
    # ЗАПОЛНЕНИЕ ПОЛЕЙ
    # ------------------------------------------------------------------
    def _fill_fields(self, page, ac):
        field_values = {
            "first_name": self.profile.get("first_name", ""),
            "last_name":  self.profile.get("last_name", ""),
            "full_name":  f"{self.profile.get('first_name','')} {self.profile.get('last_name','')}",
            "email":      self.profile.get("email", ""),
            "phone":      self.profile.get("phone", ""),
            "linkedin":   self.profile.get("linkedin", "") or self.profile.get("github", ""),
            "github":     self.profile.get("github", ""),
        }

        for field_key, selectors in ac.get("fields", {}).items():
            if field_key == "cv_file":
                continue

            value = field_values.get(field_key, "")
            if not value:
                continue

            filled = False

            # Сначала по label/placeholder
            regex_str = ac.get("field_labels", {}).get(field_key)
            if regex_str:
                rx = re.compile(regex_str, re.IGNORECASE)
                for method in [page.get_by_placeholder, page.get_by_label]:
                    if filled: break
                    try:
                        loc = method(rx)
                        for i in range(loc.count()):
                            el = loc.nth(i)
                            if el.is_editable():
                                el.fill(value, force=True)
                                print(f"  ✅ {field_key} (по label)")
                                filled = True
                                break
                    except:
                        pass

            if filled:
                continue

            # Затем по CSS/XPath
            for css in selectors:
                try:
                    els = page.locator(css)
                    for i in range(els.count()):
                        el = els.nth(i)
                        if el.is_editable() and el.is_visible():
                            el.fill(value, force=True)
                            print(f"  ✅ {field_key} (по CSS)")
                            filled = True
                            break
                except:
                    pass
                if filled:
                    break

            if not filled:
                print(f"  ⚠️ {field_key} не найдено")

    # ------------------------------------------------------------------
    # FORM SCANNER + LLM
    # ------------------------------------------------------------------
    def _run_form_scanner(self, page):
        scanner_script = """
        () => {
            const result = {};
            const elements = document.querySelectorAll(
                'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="file"]):not([type="checkbox"]):not([type="radio"]), textarea, select'
            );
            elements.forEach((el, index) => {
                if ((el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') && el.value.trim() !== '') return;
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;

                let questionText = el.getAttribute('aria-label') || '';
                if (!questionText && el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) questionText = label.innerText;
                }
                if (!questionText) {
                    const wrapper = el.closest('div, li, fieldset, .form-group');
                    if (wrapper) {
                        const lbl = wrapper.querySelector('label, span, legend, p');
                        if (lbl) questionText = lbl.innerText;
                    }
                }
                let optionsText = '';
                if (el.tagName === 'SELECT') {
                    const opts = Array.from(el.querySelectorAll('option'))
                        .map(o => o.innerText.trim())
                        .filter(t => t && t.toLowerCase() !== 'wybierz' && t.toLowerCase() !== 'select' && t !== '-');
                    if (opts.length) optionsText = ' [Options: ' + opts.join(' | ') + ']';
                }
                if (questionText && questionText.trim()) {
                    let selector = el.id ? `${el.tagName.toLowerCase()}#${el.id}`
                                        : el.name ? `${el.tagName.toLowerCase()}[name="${el.name}"]` : '';
                    if (!selector) {
                        const uid = `ai_target_${index}`;
                        el.setAttribute('data-ai-target', uid);
                        selector = `${el.tagName.toLowerCase()}[data-ai-target="${uid}"]`;
                    }
                    result[selector] = questionText.replace(/\\n/g,' ').replace(/\\s+/g,' ').trim() + optionsText;
                }
            });
            return result;
        }
        """
        try:
            questions = page.evaluate(scanner_script)
            if not questions:
                return
            print(f"  🔍 FormScanner: {len(questions)} незаполненных полей")
            answers = self.llm.solve_form(questions, self.profile)
            for selector, answer in answers.items():
                try:
                    el = page.locator(selector).first
                    if el.is_visible():
                        tag = el.evaluate("node => node.tagName").lower()
                        if tag == "select":
                            try:
                                el.select_option(label=str(answer))
                            except:
                                # Частичное совпадение
                                opts = el.locator("option")
                                for i in range(opts.count()):
                                    if str(answer).lower() in (opts.nth(i).text_content() or "").lower():
                                        el.select_option(index=i)
                                        break
                        else:
                            el.fill(str(answer), force=True)
                        print(f"  ✅ LLM заполнил [{field_key}]: {answer}")
                except:
                    pass
        except Exception as e:
            print(f"  ⚠️ FormScanner ошибка: {e}")

    # ------------------------------------------------------------------
    # ✅ УМНАЯ ЗАГРУЗКА CV — обычный input + drag-and-drop зона
    # ------------------------------------------------------------------
    def _upload_cv(self, page, ac, cv_path, site):
        cv_selectors = ac.get("fields", {}).get("cv_file", ['input[type="file"]'])

        # Способ 1: стандартный input[type=file]
        for css in cv_selectors:
            try:
                fi = page.locator(css).first
                if fi.count() > 0:
                    # Даже если input скрыт — set_input_files работает
                    fi.set_input_files(cv_path)
                    print(f"  ✅ [{site}] CV загружен (стандартный input)")
                    time.sleep(1)
                    return
            except:
                pass

        # Способ 2: drag-and-drop зона (как на eleadergroup.com)
        # Ищем скрытый input внутри зоны перетаскивания
        print(f"  🔄 [{site}] Стандартный input не найден, пробую drag-and-drop зону...")
        try:
            # Ищем любой скрытый file input через JS
            file_input = page.evaluate_handle("""
                () => {
                    const inputs = document.querySelectorAll('input[type="file"]');
                    return inputs.length > 0 ? inputs[0] : null;
                }
            """)

            if file_input:
                page.evaluate("""
                    (input) => {
                        input.style.display = 'block';
                        input.style.visibility = 'visible';
                        input.style.opacity = '1';
                        input.style.position = 'fixed';
                        input.style.top = '0';
                        input.style.left = '0';
                        input.style.width = '100px';
                        input.style.height = '100px';
                        input.style.zIndex = '999999';
                    }
                """, file_input)
                time.sleep(0.5)

                # Теперь пробуем снова
                fi = page.locator('input[type="file"]').first
                fi.set_input_files(cv_path)
                print(f"  ✅ [{site}] CV загружен (drag-and-drop зона)")
                time.sleep(1)
                return
        except Exception as e:
            print(f"  ⚠️ [{site}] Drag-and-drop тоже не сработал: {e}")

        # Способ 3: эмулируем dataTransfer через JS
        print(f"  🔄 [{site}] Пробую JS dataTransfer эмуляцию...")
        try:
            with open(cv_path, "rb") as f:
                import base64
                file_content = base64.b64encode(f.read()).decode()
                file_name = os.path.basename(cv_path)

            page.evaluate(f"""
                () => {{
                    const b64 = '{file_content}';
                    const byteChars = atob(b64);
                    const byteNums = new Array(byteChars.length);
                    for (let i = 0; i < byteChars.length; i++) {{
                        byteNums[i] = byteChars.charCodeAt(i);
                    }}
                    const byteArr = new Uint8Array(byteNums);
                    const file = new File([byteArr], '{file_name}', {{
                        type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    }});
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    const input = document.querySelector('input[type="file"]');
                    if (input) {{
                        Object.defineProperty(input, 'files', {{ value: dt.files }});
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                }}
            """)
            print(f"  ✅ [{site}] CV загружен (JS DataTransfer)")
            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ [{site}] Все способы загрузки CV не сработали: {e}")

    # ------------------------------------------------------------------
    # ЧЕКБОКСЫ
    # ------------------------------------------------------------------
    def _check_checkboxes(self, page, ac):
        for cb in page.locator('input[type="checkbox"]').all():
            try:
                cb.check(force=True)
            except:
                try:
                    cb.evaluate("node => { if (!node.checked) node.click(); }")
                except:
                    pass

        if ac.get("has_mat_checkboxes", False):
            try:
                mats = page.locator('mat-checkbox:not(.mat-checkbox-checked)')
                for i in range(mats.count()):
                    mats.nth(i).click(force=True)
            except:
                pass
        print("  ✅ Чекбоксы проставлены")

    # ------------------------------------------------------------------
    # SUBMIT
    # ------------------------------------------------------------------
    def _submit(self, page, ac, site):
        submit_sel = ac.get("submit_button",
                             "button[type='submit'], button:has-text('Wyślij'), button:has-text('Send'), button:has-text('Apply')")
        try:
            btn = page.locator(submit_sel).last
            btn.scroll_into_view_if_needed()
            btn.click(force=True, timeout=5000)
            print(f"  🚀 [{site}] Submit нажат!")
            time.sleep(5)
        except Exception as e:
            print(f"  ⚠️ [{site}] Ошибка Submit: {e}")
            return "Failed - Submit Error"

        # Проверяем успех
        signals = ac.get("success_signals", {})
        for word in signals.get("url_contains", ["success", "thank", "confirmation"]):
            if word in page.url.lower():
                print(f"  🎉 [{site}] УСПЕХ по URL!")
                return "Applied"
        for text in signals.get("text_visible", ["Dziękujemy", "Thank you"]):
            try:
                if page.locator(f"text={text}").is_visible(timeout=2000):
                    print(f"  🎉 [{site}] УСПЕХ по тексту: {text}")
                    return "Applied"
            except:
                pass

        # Проверяем ошибки
        try:
            err = page.locator(".error, .invalid, [aria-invalid='true']").first
            if err.is_visible(timeout=2000):
                return "Failed - Validation Error"
        except:
            pass

        print(f"  🤔 [{site}] Submit прошёл без явного подтверждения")
        return "Applied (Unconfirmed)"

    # ------------------------------------------------------------------
    # УНИВЕРСАЛЬНЫЙ FALLBACK
    # ------------------------------------------------------------------
    def _universal_fallback(self, page, context, job_link, cv_path, cover_letter=""):
        print("🔮 Универсальный режим без конфига...")
        page.goto(job_link, timeout=30000)
        time.sleep(3)
        self.kill_cookies(page)

        apply_btn = page.locator(
            "button:has-text('Apply'):visible, button:has-text('Aplikuj'):visible"
        ).first
        try:
            apply_btn.click(force=True)
            time.sleep(2)
        except:
            return "Failed - Apply Button Not Found"

        fallback_ac = {
            "fields": {
                "full_name": ['input[name*="first" i]', 'input[type="text"]:not([readonly])'],
                "email":     ['input[type="email"]'],
                "phone":     ['input[type="tel"]'],
                "linkedin":  ['input[type="url"]', 'input[name*="linkedin" i]'],
                "cv_file":   ['input[type="file"]'],
            },
            "field_labels": {
                "full_name": r"imię|name|first",
                "email":     r"e-?mail",
                "phone":     r"telefon|phone",
                "linkedin":  r"linkedin|github|url",
            },
            "has_mat_checkboxes": False,
        }
        self._fill_fields(page, fallback_ac)
        self._upload_cv(page, fallback_ac, cv_path, "Universal")
        self._check_checkboxes(page, fallback_ac)
        return self._submit(page, fallback_ac, "Universal")
