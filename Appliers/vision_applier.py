import time
import json
import re
from Appliers.base_applier import BaseApplier
from Core.vision_client import OmniParserClient

class VisionApplier(BaseApplier):
    def __init__(self, profile_data, llm_handler=None):
        super().__init__(profile_data, llm_handler)
        self.vision_client = OmniParserClient()

    def apply(self, page, context, job_link, cv_path, cover_letter):
        print(f"👁️ [VisionApplier] Начинаем работу с {job_link}")
        page.goto(job_link, wait_until="networkidle")
        time.sleep(3)
        self.kill_cookies(page)

        print("🔍 Пытаюсь найти и нажать первую кнопку 'Apply' (Aplikuj)...")
        page = self._open_apply_modal_if_needed(page)

        print("⚙️ Передаю управление детерминированному Vision Agent (без галлюцинаций LLM)...")
        
        self.interacted_ids = set()
        self.interacted_bboxes = []
        self.filled_labels = set()
        
        max_steps = 10
        for step in range(max_steps):
            print(f"\n--- Шаг {step+1}/{max_steps} ---")
            time.sleep(2)
            
            screenshot_path = self.take_screenshot_safe(page, suffix=f"vision_step_{step}")
            if not screenshot_path:
                time.sleep(3)
                continue

            raw_content, _ = self.vision_client.parse_screenshot(screenshot_path)
            if not raw_content:
                break

            import ast
            parsed_content = {}
            if isinstance(raw_content, str):
                for line in raw_content.strip().split('\n'):
                    if ': ' in line:
                        key, val_str = line.split(': ', 1)
                        try:
                            parsed_content[key.strip()] = ast.literal_eval(val_str.strip())
                        except:
                            pass

            action = self._deterministic_next_action(parsed_content)
            
            if not action:
                print("🛑 Не найдено явных полей или кнопок отправки. Пробуем микро-скролл вниз...")
                page.mouse.wheel(0, 150)
                self.interacted_bboxes = [] # Сбрасываем пространственную память при скролле!
                continue

            if action.get("action") == "done":
                print("✅ Форма успешно отправлена или больше нет действий!")
                break
            elif action.get("action") == "click":
                element_id = str(action.get("id"))
                print(f"🖱️ Кликаем по элементу ID {element_id} (Текст: '{action.get('reason')}')")
                self._execute_click_on_bbox(page, parsed_content, element_id)
                self.interacted_ids.add(element_id)
                if element_id in parsed_content and "bbox" in parsed_content[element_id]:
                    self.interacted_bboxes.append(parsed_content[element_id]["bbox"])
            elif action.get("action") == "type":
                element_id = str(action.get("id"))
                text_to_type = action.get("text", "")
                reason = action.get("reason", "")
                print(f"⌨️ Вводим текст '{text_to_type}' в элемент ID {element_id} (Поле: '{reason}')")
                self._execute_type_on_bbox(page, parsed_content, element_id, text_to_type)
                self.interacted_ids.add(element_id)
                self.filled_labels.add(reason)
                if element_id in parsed_content and "bbox" in parsed_content[element_id]:
                    self.interacted_bboxes.append(parsed_content[element_id]["bbox"])

        return True

    def _deterministic_next_action(self, parsed_content):
        texts = []
        inputs = []
        buttons = []
        
        print("\n--- [Debug] Что видит OmniParser (Интерактивные элементы) ---")
        
        for key, val in parsed_content.items():
            if key in self.interacted_ids:
                continue
                
            bbox = val.get("bbox")
            if not bbox: continue
            
            # ФИЛЬТРАЦИЯ 0: Пространственная память (защита от смены ID и от прочтения напечатанного текста)
            is_already_interacted = False
            for ibox in getattr(self, 'interacted_bboxes', []):
                icenter_x = (ibox[0] + ibox[2]) / 2
                icenter_y = (ibox[1] + ibox[3]) / 2
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                
                # Если центры совпадают с погрешностью 3% от экрана — это тот же самый элемент!
                if abs(center_x - icenter_x) < 0.03 and abs(center_y - icenter_y) < 0.03:
                    is_already_interacted = True
                    break
            
            if is_already_interacted:
                continue
                
            content = val.get("content", "").strip().lower()
            
            _, y_min, _, y_max = bbox
            if y_max < 0.15: # Игнорируем шапку
                continue
                
            is_yolo_input = content in ["full screen mode.", "a text box or label.", "a document or file.", ""]
            
            # Избегаем ложных срабатываний: если это явно кнопка, это не плейсхолдер
            button_kws = ['apply', 'aplikuj', 'submit', 'wyślij', 'send', 'dodaj', 'next', 'dalej', 'akceptuj', 'zgadzam', 'zapisz', 'upload', 'wybierz', 'choose']
            is_button = any(k in content for k in button_kws)
            
            placeholder_kws = [
                'name', 'email', 'message', 'tell ', 'type ', 'enter ', 'write ', 'cover letter', 
                'phone', 'salary', 'experience', 'url', 'link', 'portfolio', 'github', 'cv', 'resume', 
                'years', 'city', 'location', 'imię', 'nazwisko', 'telefon', 'wiadomość', 'miasto', 
                'oczekiwania', 'wynagrodzenie'
            ]
            # Плейсхолдеры всегда короткие. Если текста больше 60 символов — это уже наш напечатанный ответ, а не плейсхолдер!
            is_placeholder_input = (not is_button) and (len(content) < 60) and any(kw in content for kw in placeholder_kws)
            
            is_interactive = val.get('interactivity', False)
            
            if is_interactive:
                print(f"ID: {key} | Текст: '{content}' | is_input: {is_yolo_input or is_placeholder_input}")
            
            if val.get('type') == 'text' and not is_interactive:
                texts.append({"id": key, "bbox": bbox, "content": content})
            elif is_interactive:
                if is_yolo_input or is_placeholder_input:
                    # Если внутри есть плейсхолдер, используем его как label
                    inputs.append({"id": key, "bbox": bbox, "content": content, "label": content if is_placeholder_input else "unknown"})
                else:
                    buttons.append({"id": key, "bbox": bbox, "content": content})
                    
        print("----------------------------------------------------------\n")

        # Ищем ближайший текст для каждого пустого поля (только если плейсхолдера нет)
        for inp in inputs:
            if inp.get("label") and inp["label"] != "unknown":
                continue
                
            ix_min, iy_min, ix_max, iy_max = inp["bbox"]
            icenter_x = (ix_min + ix_max) / 2
            icenter_y = (iy_min + iy_max) / 2
            
            closest_label = None
            min_dist = 999.0
            
            for txt in texts:
                tx_min, ty_min, tx_max, ty_max = txt["bbox"]
                tcenter_x = (tx_min + tx_max) / 2
                tcenter_y = (ty_min + ty_max) / 2
                
                is_above = (ty_max <= iy_min + 0.05) and (tx_max >= ix_min - 0.1) and (tx_min <= ix_max + 0.1)
                is_left = (tx_max <= ix_min + 0.05) and (ty_max >= iy_min - 0.05) and (ty_min <= iy_max + 0.05)
                is_inside = (tx_min >= ix_min - 0.02) and (tx_max <= ix_max + 0.02) and (ty_min >= iy_min - 0.02) and (ty_max <= iy_max + 0.02)
                
                if is_above or is_left or is_inside:
                    dist = ((icenter_x - tcenter_x)**2 + (icenter_y - tcenter_y)**2)**0.5
                    if dist < min_dist and dist < 0.2:
                        min_dist = dist
                        closest_label = txt["content"]
            inp["label"] = closest_label if closest_label else "unknown"

        # ЭВРИСТИКА 2 (Идея пользователя): Если OmniParser вообще не увидел визуальную рамку пустого поля,
        # но мы видим текст-заголовок (например, "Email", "Name"), мы математически догадываемся, 
        # что поле ввода находится прямо под ним, и создаем "виртуальное" поле!
        import re
        for txt in texts:
            content = txt["content"].lower()
            
            # Ищем строго по словам, чтобы "center " не сработало на "enter "
            has_kw = False
            for kw in placeholder_kws:
                kw_clean = kw.strip()
                if re.search(r'\b' + re.escape(kw_clean) + r'\b', content):
                    has_kw = True
                    break
                    
            if has_kw and len(content) <= 25:
                tx_min, ty_min, tx_max, ty_max = txt["bbox"]
                tcenter_x = (tx_min + tx_max) / 2
                
                # Проверяем, не нашел ли OmniParser уже какое-то поле рядом (под ним или справа)
                has_input_nearby = False
                for inp in inputs:
                    ix_min, iy_min, ix_max, iy_max = inp["bbox"]
                    icenter_x = (ix_min + ix_max) / 2
                    
                    is_below = (iy_min >= ty_min - 0.02) and (iy_min <= ty_max + 0.1) and abs(icenter_x - tcenter_x) < 0.2
                    is_right = (ix_min >= tx_max - 0.02) and (ix_min <= tx_max + 0.2) and abs((iy_min+iy_max)/2 - (ty_min+ty_max)/2) < 0.05
                    
                    if is_below or is_right:
                        has_input_nearby = True
                        break
                        
                if not has_input_nearby:
                    # Рамки нет, но заголовок есть! Создаем виртуальную рамку прямо ПОД текстом.
                    # По статистике веб-форм, поле начинается сразу под ярлыком.
                    virtual_bbox = [tx_min, ty_max, tx_max + 0.1, ty_max + 0.05]
                    print(f"🪄 [Vision] Нашел заголовок '{txt['content']}', но не вижу рамки! Создаю виртуальное поле под ним.")
                    virt = {
                        "id": f"virtual_{txt['id']}",
                        "bbox": virtual_bbox,
                        "content": "",
                        "label": txt["content"]
                    }
                    inputs.append(virt)
                    # КРИТИЧНО: Добавляем в parsed_content, иначе _execute_type_on_bbox его проигнорирует!
                    parsed_content[virt["id"]] = virt

        # ПРАВИЛО 0: Чекбоксы (часто обязательны для согласия с правилами, OmniParser может помечать их как is_input: False)
        for k, val in parsed_content.items():
            if k in getattr(self, 'interacted_ids', set()):
                continue
            if "checkbox" in val.get("content", "").lower():
                return {"action": "click", "id": k, "reason": "checkbox"}

        # ПРАВИЛО 1: Если есть незаполненные поля, заполняем их первыми (по одному за шаг)
        if inputs:
            for inp in inputs:
                label = inp["label"]
                # Если мы уже заполняли поле с таким лейблом на этой странице - пропускаем!
                if label in getattr(self, 'filled_labels', set()) and label != "unknown":
                    continue
                    
                print(f"🧠 Спрашиваем Ollama, что написать в поле с вопросом: '{label}'...")
                prompt = f"""
Ты — AI-ассистент, помогающий кандидату откликнуться на вакансию.

ПРОФИЛЬ КАНДИДАТА:
- First Name: {self.profile.get('first_name', 'Aleks')}
- Last Name: {self.profile.get('last_name', 'Yeremenko')}
- Email: {self.profile.get('email', 'yeremenkoaleks1@gmail.com')}
- Phone: {self.profile.get('phone', '516478223')}
- Role: Senior Python/AI Engineer
- City: Warsaw / Warszawa
- Expected Salary: 25000 PLN
- English level: B2/C1
- GitHub: https://github.com/aleksyeremenko
- LinkedIn: https://linkedin.com/in/aleksyeremenko

ТЕКУЩЕЕ ПОЛЕ НА САЙТЕ: "{label}"

ЗАДАЧА:
Опираясь на профиль, напиши ТОЛЬКО текст, который нужно вставить в это поле. 
Без пояснений. Если это зарплата — напиши число. Если не знаешь ответ — напиши "N/A".
"""
                response = self.llm.ask(prompt, model_type="fast")
                
                text_to_type = response.strip() if response and response != "REJECT" else "N/A"
                if text_to_type.startswith('"') and text_to_type.endswith('"'):
                    text_to_type = text_to_type[1:-1]
                    
                return {"action": "type", "id": inp["id"], "text": text_to_type, "reason": label}

        # ПРАВИЛО 2: Если все поля заполнены, ищем кнопку отправки
        submit_keywords = ['apply', 'aplikuj', 'submit', 'wyślij', 'send', 'dodaj', 'next', 'dalej', 'akceptuj', 'zgadzam', 'zapisz']
        for btn in buttons:
            if any(k in btn["content"] for k in submit_keywords) and len(btn["content"]) < 30:
                return {"action": "click", "id": btn["id"], "reason": btn["content"]}

        # ПРАВИЛО 3: Если есть чекбоксы без текста (часто YOLO помечает их как пустые поля)
        for inp in inputs:
            if inp["label"] != "unknown" and any(k in inp["label"] for k in ['agree', 'zgadzam', 'akceptuj', 'policy', 'terms', 'regulamin']):
                return {"action": "click", "id": inp["id"], "reason": f"Checkbox for {inp['label']}"}

        return None

    def _execute_click_on_bbox(self, page, parsed_content, element_id):
        val = parsed_content.get(element_id)
        if not val or "bbox" not in val: return
        bbox = val["bbox"]
        viewport = page.evaluate("({width: window.innerWidth, height: window.innerHeight})")
        x_min, y_min, x_max, y_max = bbox
        
        # Кликаем в центр по умолчанию
        center_x = (x_min + x_max) / 2 * viewport['width']
        center_y = (y_min + y_max) / 2 * viewport['height']
        
        page.mouse.click(center_x, center_y)

    def _execute_type_on_bbox(self, page, parsed_content, element_id, text_to_type):
        val = parsed_content.get(element_id)
        if not val or "bbox" not in val: return
        bbox = val["bbox"]
        viewport = page.evaluate("({width: window.innerWidth, height: window.innerHeight})")
        x_min, y_min, x_max, y_max = bbox
        
        # Для полей ввода кликаем в геометрический центр
        center_x = (x_min + x_max) / 2 * viewport['width']
        center_y = (y_min + y_max) / 2 * viewport['height']
        
        # Тройной клик выделяет весь текст в поле без Ctrl+A
        page.mouse.click(center_x, center_y, click_count=3)
        time.sleep(0.5)
        page.keyboard.press("Backspace")
        time.sleep(0.5)
        page.keyboard.type(text_to_type, delay=50)
        time.sleep(0.5)

    def _open_apply_modal_if_needed(self, page):
        apply_btn = page.locator("button:has-text('Aplikuj'), button:has-text('Apply'), a:has-text('Aplikuj'), a:has-text('Apply')").first
        if apply_btn.is_visible(timeout=3000):
            try: apply_btn.click(timeout=3000)
            except: apply_btn.click(force=True)
            time.sleep(3)
        return page
