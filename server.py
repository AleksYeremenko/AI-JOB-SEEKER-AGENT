import os
import time
import base64
import requests
import threading
import customtkinter as ctk
from tkinter import filedialog
from playwright.sync_api import sync_playwright

# --- Цветовая палитра в стиле "Софи" ---
BG_COLOR = "#0D0D12"
FRAME_COLOR = "#15151B"
ACCENT_COLOR = "#1D4ED8"
ACCENT_HOVER = "#2563EB"
TEXT_MAIN = "#F8FAFC"
TEXT_MUTED = "#94A3B8"

ctk.set_appearance_mode("dark")


class AIJobSeekerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("MorphApp - AI Job Agent")
        self.geometry("700x850")
        self.minsize(600, 800)
        self.configure(fg_color=BG_COLOR)

        self.cv_file_path = None

        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=60, pady=50)

        self.create_widgets()

    def create_widgets(self):
        title_font = ctk.CTkFont(family="Helvetica", size=34, weight="bold")
        subtitle_font = ctk.CTkFont(family="Helvetica", size=16)
        input_font = ctk.CTkFont(family="Helvetica", size=16)
        main_btn_font = ctk.CTkFont(family="Helvetica", size=18, weight="bold")

        self.title_label = ctk.CTkLabel(self.main_frame, text="Automate your job search", font=title_font,
                                        text_color=TEXT_MAIN)
        self.title_label.pack(anchor="w", pady=(0, 8))

        self.subtitle_label = ctk.CTkLabel(self.main_frame, text="Set up your AI agent in seconds.", font=subtitle_font,
                                           text_color=TEXT_MUTED)
        self.subtitle_label.pack(anchor="w", pady=(0, 40))

        self.position_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Target Role (e.g. Python Backend)",
                                           height=50, fg_color=FRAME_COLOR, border_color=FRAME_COLOR,
                                           text_color=TEXT_MAIN, font=input_font, corner_radius=8)
        self.position_entry.pack(fill="x", pady=10)

        self.stack_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Tech Stack (e.g. Python, Docker, AWS)",
                                        height=50, fg_color=FRAME_COLOR, border_color=FRAME_COLOR, text_color=TEXT_MAIN,
                                        font=input_font, corner_radius=8)
        self.stack_entry.pack(fill="x", pady=10)

        self.email_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Contact Email", height=50,
                                        fg_color=FRAME_COLOR, border_color=FRAME_COLOR, text_color=TEXT_MAIN,
                                        font=input_font, corner_radius=8)
        self.email_entry.pack(fill="x", pady=10)

        self.row_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.row_frame.pack(fill="x", pady=10)

        self.city_combo = ctk.CTkComboBox(self.row_frame, values=["Warsaw", "Krakow", "Wroclaw", "Remote"], height=50,
                                          fg_color=FRAME_COLOR, border_color=FRAME_COLOR, button_color=FRAME_COLOR,
                                          button_hover_color=ACCENT_COLOR, dropdown_fg_color=FRAME_COLOR,
                                          font=input_font, corner_radius=8)
        self.city_combo.set("Select City")
        self.city_combo.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.job_type_combo = ctk.CTkComboBox(self.row_frame, values=["Backend", "Frontend", "Fullstack", "DevOps"],
                                              height=50, fg_color=FRAME_COLOR, border_color=FRAME_COLOR,
                                              button_color=FRAME_COLOR, button_hover_color=ACCENT_COLOR,
                                              dropdown_fg_color=FRAME_COLOR, font=input_font, corner_radius=8)
        self.job_type_combo.set("Job Type")
        self.job_type_combo.pack(side="right", fill="x", expand=True, padx=(8, 0))

        self.slider_label = ctk.CTkLabel(self.main_frame, text="Minimum Stack Match: 50%", font=subtitle_font,
                                         text_color=TEXT_MUTED)
        self.slider_label.pack(anchor="w", pady=(20, 5))

        self.match_slider = ctk.CTkSlider(self.main_frame, from_=10, to=100, number_of_steps=90,
                                          button_color=ACCENT_COLOR, button_hover_color=TEXT_MAIN,
                                          progress_color=ACCENT_COLOR, command=self.update_slider_label, height=20)
        self.match_slider.set(50)
        self.match_slider.pack(fill="x", pady=(5, 30))

        self.cv_frame = ctk.CTkFrame(self.main_frame, fg_color=FRAME_COLOR, corner_radius=8)
        self.cv_frame.pack(fill="x", pady=10, ipady=20)

        self.cv_label = ctk.CTkLabel(self.cv_frame, text="No resume uploaded", font=subtitle_font,
                                     text_color=TEXT_MUTED)
        self.cv_label.pack(pady=(15, 10))

        self.upload_btn = ctk.CTkButton(self.cv_frame, text="Upload CV (PDF)", command=self.upload_cv, height=40,
                                        width=180, fg_color="transparent", border_width=1.5, border_color=TEXT_MUTED,
                                        hover_color=FRAME_COLOR, text_color=TEXT_MAIN,
                                        font=ctk.CTkFont(size=14, weight="bold"))
        self.upload_btn.pack(pady=(0, 15))

        self.save_btn = ctk.CTkButton(self.main_frame, text="Launch Agent", command=self.save_settings, height=60,
                                      fg_color=ACCENT_COLOR, hover_color=ACCENT_HOVER, font=main_btn_font,
                                      corner_radius=8)
        self.save_btn.pack(fill="x", side="bottom", pady=(20, 0))

    def update_slider_label(self, value):
        self.slider_label.configure(text=f"Minimum Stack Match: {int(value)}%")

    def upload_cv(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.cv_file_path = file_path
            file_name = os.path.basename(file_path)
            self.cv_label.configure(text=f"Attached: {file_name}", text_color=ACCENT_COLOR)

    def save_settings(self):
        user_data = {
            "position": self.position_entry.get(),
            "tech_stack": self.stack_entry.get(),
            "stack_match_percent": int(self.match_slider.get()),
            "city": self.city_combo.get(),
            "job_type": self.job_type_combo.get(),
            "email": self.email_entry.get(),
            "cv_path": self.cv_file_path
        }

        self.save_btn.configure(text="Agent Running...", fg_color="#059669")

        # Запускаем браузер в фоновом потоке, чтобы UI не зависал
        threading.Thread(target=self.run_browser_agent, args=(user_data,), daemon=True).start()

    def run_browser_agent(self, user_data):
        """Запускает браузер и взаимодействует с удаленным сервером друга"""

        # 🔥 ВСТАВЬ СЮДА ССЫЛКУ НА СЕРВЕР ДРУГА (например: https://его-ip.ngrok.io/api/analyze_screen)
        SERVER_API_URL = "http://127.0.0.1:8000/api/analyze_screen"

        TEST_JOB_URL = "https://justjoin.it/offers/apius-technologies-sp-z-o-o-inzynier-systemowy-cyberbezpieczenstwo"

        try:
            with sync_playwright() as p:
                print("🌐 Запускаю браузер для демо...")

                # 🔥 СДЕЛАЛ HEADLESS=FALSE, ЧТОБЫ НА ПИТЧЕ ВСЕ ВИДЕЛИ МАГИЮ!
                browser = p.chromium.launch(headless=False)

                # Жестко фиксируем размер окна (FullHD), чтобы скрины всегда были одинаковыми для нейросети
                context = browser.new_context(viewport={'width': 1920, 'height': 1080})
                page = context.new_page()

                print("⏳ Загружаю страницу...")
                page.goto(TEST_JOB_URL, wait_until="networkidle")
                time.sleep(2)  # Даем время на динамический контент

                # 1. Делаем скриншот
                screenshot_bytes = page.screenshot(full_page=False)
                img_b64 = base64.b64encode(screenshot_bytes).decode('utf-8')

                print(f"📤 Отправляю скриншот на удаленный сервер ({SERVER_API_URL})...")
                response = requests.post(
                    SERVER_API_URL,
                    json={"image_b64": img_b64},
                    timeout=600  # Нейросети нужно время подумать
                )

                if response.status_code == 200:
                    result = response.json()
                    elements = result.get("data", {}).get("elements", [])
                    print(f"📥 Ответ получен. Найдено элементов: {len(elements)}")

                    # 2. Ищем кнопку Apply и кликаем
                    for elem in elements:
                        if elem.get("type") == "button_apply":
                            bbox = elem["bbox_norm"]

                            # Переводим масштаб 0-1000 в пиксели 1920x1080
                            y1 = int((bbox[0] / 1000) * 1080)
                            x1 = int((bbox[1] / 1000) * 1920)
                            y2 = int((bbox[2] / 1000) * 1080)
                            x2 = int((bbox[3] / 1000) * 1920)

                            center_x = (x1 + x2) / 2
                            center_y = (y1 + y2) / 2

                            print(f"🎯 Делаю клик по Apply ({center_x:.0f}, {center_y:.0f})")

                            # Двигаем мышку плавно, чтобы зрители видели процесс
                            page.mouse.move(center_x, center_y, steps=10)
                            time.sleep(0.5)
                            page.mouse.click(center_x, center_y)
                            time.sleep(2)

                            print("✅ Отклик отправлен!")
                            self.save_btn.configure(text="Application Sent!", fg_color="#10B981")
                            break
                else:
                    print(f"❌ Ошибка сервера: {response.status_code} - {response.text}")
                    self.save_btn.configure(text="Server Error", fg_color="#DC2626")

                # Не закрываем браузер сразу на демо, даем посмотреть пару секунд
                time.sleep(3)
                browser.close()

        except requests.exceptions.ConnectionError:
            print("❌ Не удалось подключиться к серверу друга! Проверь URL.")
            self.save_btn.configure(text="Connection Failed", fg_color="#DC2626")
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            self.save_btn.configure(text="Error Occurred", fg_color="#DC2626")
        finally:
            # Возвращаем кнопку в исходное состояние через 5 секунд
            time.sleep(5)
            self.save_btn.configure(text="Launch Agent", fg_color=ACCENT_COLOR)


if __name__ == "__main__":
    app = AIJobSeekerApp()
    app.mainloop()