import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import json
import sys
import re
import time
from pathlib import Path

# Добавляем текущую директорию в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from utils.llm_handler import LLMHandler
from Core.bulletproof_engine import BulletproofApplier
from Appliers.justjoin_applier import JustJoinApplier
from utils.resume_manager import ResumeManager
from db_manager import db
from email_checker import EmailChecker

# Импорты скрейперов
try:
    from Scraping.multi_scraper import MultiScraper
    from Scraping.universal_scraper import scrape_polish_sites
    from Scraping.djinni_scraper import scrape_djinni
except ImportError:
    pass


class UserSettings:
    """Глобальное хранилище настроек пользователя"""

    def __init__(self):
        self.first_name = ""
        self.last_name = ""
        self.email = ""
        self.phone = ""
        self.cv_path = ""
        self.stack = ""
        self.city = ""
        self.job_type = "Remote"
        self.match_threshold = 30
        self.seniority_level = "Junior"
        self.cv_template = "Classic_ATS.html"
        self.work_speed = self.auto_detect_speed()
        self.non_tech_mode = False
        self.autonomous_mode = False

    def auto_detect_speed(self):
        try:
            import ctypes
            class MemoryStatusEx(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MemoryStatusEx()
            stat.dwLength = ctypes.sizeof(MemoryStatusEx)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            # Смотрим на СВОБОДНУЮ память, а не на общую
            avail_ram_gb = stat.ullAvailPhys / (1024**3)
            
            if avail_ram_gb < 2:
                return 10  # 10% - еле живой комп
            elif avail_ram_gb < 6:
                return 30  # 30% - мало места
            elif avail_ram_gb < 12:
                return 50  # 50% - норм
            else:
                return 80  # 80% - много свободной памяти
        except Exception:
            return 50

    def to_dict(self):
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": f"{self.first_name} {self.last_name}",
            "email": self.email,
            "phone": self.phone,
            "cv_path": self.cv_path,
            "stack": self.stack,
            "city": self.city,
            "job_type": self.job_type,
            "match_threshold": self.match_threshold,
            "seniority_level": self.seniority_level,
            "work_speed": self.work_speed,
            "non_tech_mode": self.non_tech_mode,
            "autonomous_mode": getattr(self, 'autonomous_mode', False),
            "github": ""
        }

    def save(self, filepath="Data/user_settings.json"):
        os.makedirs("Data", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath="Data/user_settings.json"):
        settings = cls()
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                settings.first_name = data.get("first_name", "")
                settings.last_name = data.get("last_name", "")
                settings.email = data.get("email", "")
                settings.phone = data.get("phone", "")
                settings.cv_path = data.get("cv_path", "")
                settings.stack = data.get("stack", "")
                settings.city = data.get("city", "")
                settings.job_type = data.get("job_type", "Remote")
                settings.match_threshold = data.get("match_threshold", 30)
                settings.seniority_level = data.get("seniority_level", "Junior")
                settings.work_speed = data.get("work_speed", settings.auto_detect_speed())
                settings.non_tech_mode = data.get("non_tech_mode", False)
                settings.autonomous_mode = data.get("autonomous_mode", False)
        return settings

class LoginWindow(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("MorphApp - Login")
        self.geometry("400x550")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.update_idletasks()
        
        # --- Language Selector ---
        lang_frame = ctk.CTkFrame(self, fg_color="transparent")
        lang_frame.pack(fill="x", pady=(20, 10), padx=20)
        
        self.lang_var = ctk.StringVar(value="EN")
        lang_seg = ctk.CTkSegmentedButton(
            lang_frame, 
            values=["EN", "UK", "RU", "PL"],
            variable=self.lang_var,
            command=self.change_language
        )
        lang_seg.pack(side="right")
        
        # --- Title ---
        self.title_lbl = ctk.CTkLabel(self, text="Welcome Back", font=ctk.CTkFont(size=28, weight="bold"))
        self.title_lbl.pack(pady=(20, 30))
        
        # --- Inputs ---
        self.email_entry = ctk.CTkEntry(self, placeholder_text="Email", width=300, height=45)
        self.email_entry.pack(pady=10)
        
        self.pass_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=300, height=45)
        self.pass_entry.pack(pady=10)
        
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_cb = ctk.CTkCheckBox(self, text="Remember me", variable=self.remember_var)
        self.remember_cb.pack(pady=(5, 20), padx=50, anchor="w")
        
        # --- Buttons ---
        self.login_btn = ctk.CTkButton(self, text="Login", width=300, height=45, command=self.do_login)
        self.login_btn.pack(pady=10)
        
        self.register_btn = ctk.CTkButton(
            self, text="Don't have an account? Register", 
            fg_color="transparent", text_color="#3b82f6", hover_color="#1f2937", 
            command=self.do_register
        )
        self.register_btn.pack(pady=(10, 0))

        # Check for saved login
        self.check_saved_login()

    def check_saved_login(self):
        login_file = "Data/saved_login.json"
        if os.path.exists(login_file):
            try:
                with open(login_file, "r") as f:
                    data = json.load(f)
                    if data.get("remember"):
                        self.email_entry.insert(0, data.get("email", ""))
                        self.pass_entry.insert(0, data.get("password", ""))
                        self.remember_var.set(True)
            except:
                pass

    def on_close(self):
        self.master.destroy()
        import os
        os._exit(0)
        
    def do_login(self):
        email = self.email_entry.get().strip()
        pwd = self.pass_entry.get()
        if not email or not pwd:
            messagebox.showwarning("Error", "Please enter email and password.")
            return
            
        # --- Authentication Check ---
        os.makedirs("Data", exist_ok=True)
        users_file = "Data/users.json"
        
        # Create a default user if file doesn't exist
        if not os.path.exists(users_file):
            with open(users_file, "w") as f:
                json.dump({"test@test.com": "12345"}, f)
                
        with open(users_file, "r") as f:
            try:
                valid_users = json.load(f)
            except:
                valid_users = {}
                
        if email not in valid_users or valid_users[email] != pwd:
            messagebox.showerror("Access Denied", "Invalid email or password.")
            return
            
        # Save login if remember me is checked
        login_file = "Data/saved_login.json"
        if self.remember_var.get():
            with open(login_file, "w") as f:
                json.dump({"email": email, "password": pwd, "remember": True}, f)
        else:
            if os.path.exists(login_file):
                os.remove(login_file)
                
        # Move to main app
        self.master.deiconify()
        self.destroy()
        
    def do_register(self):
        messagebox.showinfo("Register", "Registration is currently closed for beta.")
        
    def change_language(self, lang):
        texts = {
            "EN": {"title": "Welcome Back", "email": "Email", "pass": "Password", "rem": "Remember me", "log": "Login", "reg": "Don't have an account? Register"},
            "UK": {"title": "З поверненням", "email": "Електронна пошта", "pass": "Пароль", "rem": "Запам'ятати мене", "log": "Увійти", "reg": "Немає акаунту? Зареєструватися"},
            "RU": {"title": "С возвращением", "email": "Электронная почта", "pass": "Пароль", "rem": "Запомнить меня", "log": "Войти", "reg": "Нет аккаунта? Регистрация"},
            "PL": {"title": "Witaj ponownie", "email": "E-mail", "pass": "Hasło", "rem": "Zapamiętaj mnie", "log": "Zaloguj się", "reg": "Nie masz konta? Zarejestruj się"}
        }
        t = texts.get(lang, texts["EN"])
        self.title_lbl.configure(text=t["title"])
        self.email_entry.configure(placeholder_text=t["email"])
        self.pass_entry.configure(placeholder_text=t["pass"])
        self.remember_cb.configure(text=t["rem"])
        self.login_btn.configure(text=t["log"])
        self.register_btn.configure(text=t["reg"])
class MultiSelectComboBox(ctk.CTkFrame):
    def __init__(self, master, options, vars_dict, width=320, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.options = options
        self.vars_dict = vars_dict
        
        self.btn = ctk.CTkButton(self, text="Select...", width=width, fg_color="#1e293b", hover_color="#334155", 
                                 border_color="#334155", border_width=1, anchor="w", command=self.toggle_dropdown)
        self.btn.pack(fill="x")
        
        self.dropdown = None
        self.update_text()
        
    def toggle_dropdown(self):
        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None
        else:
            self.dropdown = ctk.CTkToplevel(self)
            self.dropdown.overrideredirect(True)
            self.dropdown.configure(fg_color="#0f172a")
            self.dropdown.attributes('-topmost', True)
            
            x = self.btn.winfo_rootx()
            y = self.btn.winfo_rooty() + self.btn.winfo_height()
            self.dropdown.geometry(f"{self.btn.winfo_width()}x{min(200, len(self.options)*35 + 10)}+{x}+{y}")
            
            frame = ctk.CTkFrame(self.dropdown, fg_color="#0f172a", border_color="#38bdf8", border_width=1)
            frame.pack(fill="both", expand=True)
            
            for opt in self.options:
                cb = ctk.CTkCheckBox(frame, text=opt, variable=self.vars_dict[opt], command=self.update_text,
                                     text_color="#e2e8f0", fg_color="#38bdf8", hover_color="#7dd3fc")
                cb.pack(anchor="w", padx=10, pady=5)
                
            self.dropdown.bind("<FocusOut>", lambda e: self.close_dropdown())
            self.dropdown.focus_set()

    def close_dropdown(self):
        if self.dropdown and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None

    def update_text(self, *args):
        selected = [opt for opt in self.options if self.vars_dict[opt].get()]
        text = ", ".join(selected) if selected else "None"
        self.btn.configure(text=text)


class AIJobSeekerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("AI Job Seeker Agent")
        self.geometry("1200x900")

        self.settings = UserSettings.load()
        self.llm = LLMHandler()
        self.resume_manager = ResumeManager()
        self.is_paused = False

        self.setup_ui()
        self.load_saved_settings()
        
        # Window closing handler
        self.protocol("WM_DELETE_WINDOW", self.on_app_close)
        
        # Hide main window and show login
        self.withdraw()
        self.login_window = LoginWindow(self)
        
    def on_app_close(self):
        try:
            self.cleanup_chromium()
        except:
            pass
        self.destroy()
        import os
        os._exit(0)
        
    def open_faq(self, lang="RU"):
        try:
            import webbrowser
            filename = "FAQ.html"
            faq_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            if os.path.exists(faq_path):
                webbrowser.open(f"file:///{faq_path.replace(chr(92), '/')}")
            else:
                messagebox.showerror("Error", f"{filename} not found.")
        except Exception as e:
            print(f"Error opening FAQ: {e}")

    def handle_file_menu(self, choice):
        self.file_menu.set("File")
        if choice == "Save":
            self.save_settings()
            messagebox.showinfo("Success", "Settings saved!")
        elif choice == "Save and Exit":
            self.save_settings()
            self.on_app_close()
        elif choice == "Export to PDF":
            messagebox.showinfo("Info", "Export to PDF is not yet implemented.")
        elif choice == "Import from CV":
            cv_path = getattr(self.settings, 'cv_path', '')
            if cv_path and os.path.exists(cv_path) and cv_path.endswith('.pdf'):
                try:
                    text = self.resume_manager.extract_text_from_pdf(cv_path)
                    if not text:
                        raise ValueError("Could not extract text from PDF.")
                    
                    import threading
                    def parse_cv():
                        print("🤖 [SYSTEM] Parsing CV to auto-fill fields...")
                        prompt = (
                            "Extract the following info from the CV text. Return ONLY a valid JSON object with the exact keys: "
                            "'first_name', 'last_name', 'email', 'phone', 'stack', 'city'.\n"
                            f"CV Text:\n{text[:3000]}"
                        )
                        res = self.llm.ask(prompt, model_type="fast")
                        try:
                            import json, re
                            match = re.search(r'\{.*\}', res, re.DOTALL)
                            if match:
                                data = json.loads(match.group(0))
                            else:
                                data = json.loads(res)
                                
                            # Fill fields in UI thread
                            self.after(0, lambda d=data: self.fill_ui_from_dict(d))
                            print("✅ [SYSTEM] Auto-fill complete!")
                        except Exception as e:
                            print(f"❌ [SYSTEM] Failed to parse JSON from LLM: {e}")
                    
                    threading.Thread(target=parse_cv, daemon=True).start()
                    messagebox.showinfo("Import", "Reading CV...\nPlease wait a few seconds. Ensure all Personal Info fields are correct before starting the agent!")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to read CV: {e}")
            else:
                messagebox.showerror("Error", "Please select a valid PDF CV first using Browse.")
                
    def fill_ui_from_dict(self, data):
        if data.get("first_name"): self.first_name_entry.delete(0, 'end'); self.first_name_entry.insert(0, data["first_name"])
        if data.get("last_name"): self.last_name_entry.delete(0, 'end'); self.last_name_entry.insert(0, data["last_name"])
        if data.get("email"): self.email_entry.delete(0, 'end'); self.email_entry.insert(0, data["email"])
        if data.get("phone"): self.phone_entry.delete(0, 'end'); self.phone_entry.insert(0, data["phone"])
        if data.get("stack"): self.stack_entry.delete(0, 'end'); self.stack_entry.insert(0, data["stack"])
        if data.get("city"): self.city_entry.delete(0, 'end'); self.city_entry.insert(0, data["city"])

    def handle_clear_menu(self, choice):
        self.clear_menu.set("Clear")
        if choice == "Dashboard":
            self.clear_dashboard()
        elif choice == "Seen Jobs":
            self.clear_seen_jobs()
        elif choice == "CV":
            self.settings.cv_path = ""
            self.cv_label.configure(text="No file selected")
        elif choice == "Logins":
            if os.path.exists("Data/users.json"):
                os.remove("Data/users.json")
            if os.path.exists("Data/saved_login.json"):
                os.remove("Data/saved_login.json")
            messagebox.showinfo("Success", "Logins cleared! Restart app to take effect.")
        elif choice == "Data for CV":
            self.first_name_entry.delete(0, 'end')
            self.last_name_entry.delete(0, 'end')
            self.email_entry.delete(0, 'end')
            self.phone_entry.delete(0, 'end')
            self.stack_entry.delete(0, 'end')
            self.city_entry.delete(0, 'end')
        elif choice == "Logs":
            if hasattr(self, 'log_textbox'):
                self.log_textbox.configure(state='normal')
                self.log_textbox.delete("1.0", "end")
                self.log_textbox.configure(state='disabled')

    def handle_dash_menu(self, choice):
        self.dash_menu.set("Dashboard")
        if choice == "Open":
            if os.path.exists("dashboard.html"):
                import webbrowser
                webbrowser.open("file://" + os.path.abspath("dashboard.html"))
            else:
                messagebox.showerror("Error", "dashboard.html not found.")
        elif choice == "Edit (ReWrite)":
            self.open_native_dashboard_editor()
            
    def open_native_dashboard_editor(self):
        editor = ctk.CTkToplevel(self.root)
        editor.title("Job Dashboard Manager")
        editor.geometry("900x600")
        editor.configure(fg_color=self.glass_bg)
        editor.attributes("-topmost", True)
        
        lbl = ctk.CTkLabel(editor, text="Manage Job Applications", font=("Inter", 24, "bold"), text_color="#60A5FA")
        lbl.pack(pady=20)
        
        scroll = ctk.CTkScrollableFrame(editor, width=850, height=500, fg_color=self.glass_panel)
        scroll.pack(pady=10, padx=20, fill="both", expand=True)
        
        try:
            from db_manager import db
            jobs = db._read_db()
            for job in jobs:
                row = ctk.CTkFrame(scroll, fg_color="transparent")
                row.pack(fill="x", pady=5)
                
                title_lbl = ctk.CTkLabel(row, text=f"{job.get('company', 'Unknown')} - {job.get('title', 'Unknown')}", width=400, anchor="w", font=("Inter", 14))
                title_lbl.pack(side="left", padx=10)
                
                status_var = ctk.StringVar(value=job.get('status', 'Seen'))
                def make_update_cmd(j_link, s_var):
                    return lambda val: db.update_job_status(j_link, val)
                    
                status_menu = ctk.CTkOptionMenu(
                    row, values=["Seen", "Applied", "Failed", "Manual", "Interview", "Rejected", "Offer"],
                    variable=status_var,
                    command=make_update_cmd(job.get('link'), status_var),
                    width=150
                )
                status_menu.pack(side="right", padx=10)
                
        except Exception as e:
            ctk.CTkLabel(scroll, text=f"Error loading jobs: {e}").pack()

    def handle_help_menu(self, choice):
        self.help_menu.set("Help / FAQ")
        if choice == "FAQ (English)":
            self.open_faq("EN")
        elif choice == "FAQ (Russian)":
            self.open_faq("RU")
        elif choice == "Change Language":
            messagebox.showinfo("Language", "Language switching will be available in the next update!")

    def setup_ui(self):
        # Dark Modern Dashboard Theme Colors
        self.glass_bg = "#12141A"          # Main background
        self.glass_panel = "#22252E"       # Cards/Panels
        self.glass_border = "#2A2D35"      # Card borders
        self.glass_input = "#12141A"       # Inputs and Dropdowns
        
        self.neon_cyan = "#2D8CFF"         # Neon Blue
        self.neon_amber = "#FF7A45"        # Neon Orange
        
        self.text_primary = "#FFFFFF"
        self.text_secondary = "#8A8D93"
        
        # Fonts
        self.font_main = ctk.CTkFont(family="Segoe UI", size=13)
        self.font_title = ctk.CTkFont(family="Segoe UI", size=18, weight="bold")
        self.font_label = ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        self.font_mono = ctk.CTkFont(family="Consolas", size=12)
        
        self.configure(fg_color=self.glass_bg)

        # === TOP MENU BAR ===
        menu_bar = ctk.CTkFrame(self, height=40, fg_color=self.glass_panel, corner_radius=0, border_width=0)
        menu_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        menu_kwargs = {
            "fg_color": self.glass_panel,
            "text_color": self.neon_cyan,
            "button_color": self.glass_panel,
            "button_hover_color": self.glass_border,
            "dropdown_fg_color": self.glass_panel,
            "dropdown_text_color": self.neon_cyan,
            "dropdown_hover_color": self.glass_border,
            "font": ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        }

        self.file_menu = ctk.CTkOptionMenu(menu_bar, values=["Save", "Save and Exit", "Export to PDF", "Import from CV"], command=self.handle_file_menu, **menu_kwargs)
        self.file_menu.set("File")
        self.file_menu.pack(side="left", padx=(20, 5), pady=5)
        
        self.clear_menu = ctk.CTkOptionMenu(menu_bar, values=["Dashboard", "Seen Jobs", "CV", "Logins", "Data for CV", "Logs"], command=self.handle_clear_menu, **menu_kwargs)
        self.clear_menu.set("Clear")
        self.clear_menu.pack(side="left", padx=5, pady=5)
        
        self.dash_menu = ctk.CTkOptionMenu(menu_bar, values=["Open", "Edit (ReWrite)"], command=self.handle_dash_menu, **menu_kwargs)
        self.dash_menu.set("Dashboard")
        self.dash_menu.pack(side="left", padx=5, pady=5)
        
        self.help_menu = ctk.CTkOptionMenu(menu_bar, values=["FAQ (English)", "FAQ (Russian)", "Change Language"], command=self.handle_help_menu, **menu_kwargs)
        self.help_menu.set("Help / FAQ")
        self.help_menu.pack(side="left", padx=5, pady=5)

        self.logout_btn = ctk.CTkButton(
            menu_bar, text="Logout", width=80, command=self.do_logout, 
            fg_color="transparent", text_color=self.neon_amber, hover_color=self.glass_border, 
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")
        )
        self.logout_btn.pack(side="right", padx=20, pady=5)

        # Обертка для двух колонок: левая (настройки) и правая (логи+график)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=20)

        right_panel = ctk.CTkFrame(
            self, fg_color=self.glass_panel, border_width=1, border_color=self.glass_border, corner_radius=12
        )
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=20)

        # ЛЕВАЯ ПАНЕЛЬ
        main_frame = ctk.CTkFrame(
            left_panel, fg_color=self.glass_panel, border_width=1, border_color=self.glass_border, corner_radius=12
        )
        main_frame.pack(fill="both", expand=True)

        input_kwargs = {
            "fg_color": self.glass_input,
            "border_color": self.glass_border,
            "text_color": self.text_primary,
            "corner_radius": 8,
            "font": self.font_main
        }
        
        label_kwargs = {
            "text_color": self.text_secondary,
            "font": self.font_label
        }

        ctk.CTkLabel(main_frame, text="Personal Information", text_color=self.text_primary, font=self.font_title).grid(row=0, column=0, columnspan=2, pady=(20, 10), sticky="w", padx=20)

        ctk.CTkLabel(main_frame, text="First Name:", **label_kwargs).grid(row=1, column=0, pady=8, padx=20, sticky="w")
        self.first_name_entry = ctk.CTkEntry(main_frame, width=320, **input_kwargs)
        self.first_name_entry.grid(row=1, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="Last Name:", **label_kwargs).grid(row=2, column=0, pady=8, padx=20, sticky="w")
        self.last_name_entry = ctk.CTkEntry(main_frame, width=320, **input_kwargs)
        self.last_name_entry.grid(row=2, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="Email:", **label_kwargs).grid(row=3, column=0, pady=8, padx=20, sticky="w")
        self.email_entry = ctk.CTkEntry(main_frame, width=320, **input_kwargs)
        self.email_entry.grid(row=3, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="Email Login:", **label_kwargs).grid(row=4, column=0, pady=8, padx=20, sticky="w")
        self.email_login_btn = ctk.CTkButton(
            main_frame, text="AUTHENTICATE EMAIL", width=320, 
            fg_color=self.glass_input, hover_color=self.glass_border, 
            text_color=self.neon_cyan, border_color=self.neon_cyan, border_width=1,
            corner_radius=8, font=self.font_label, command=self.login_email
        )
        self.email_login_btn.grid(row=4, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="Phone:", **label_kwargs).grid(row=5, column=0, pady=8, padx=20, sticky="w")
        self.phone_entry = ctk.CTkEntry(main_frame, width=320, **input_kwargs)
        self.phone_entry.grid(row=5, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="CV (PDF/DOCX):", **label_kwargs).grid(row=6, column=0, pady=8, padx=20, sticky="w")
        cv_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        cv_frame.grid(row=6, column=1, pady=8, padx=20, sticky="w")

        self.cv_label = ctk.CTkLabel(cv_frame, text="No file selected", width=220, text_color=self.text_secondary, font=self.font_main)
        self.cv_label.pack(side="left", padx=(0, 10))

        self.cv_button = ctk.CTkButton(
            cv_frame, text="BROWSE", width=90, 
            fg_color=self.glass_input, hover_color=self.glass_border, 
            text_color=self.text_primary, border_color=self.glass_border, border_width=1,
            corner_radius=8, font=self.font_label, command=self.browse_cv
        )
        self.cv_button.pack(side="left")

        ctk.CTkLabel(main_frame, text="Job Preferences", text_color=self.text_primary, font=self.font_title).grid(row=7, column=0, columnspan=2, pady=(25, 10), sticky="w", padx=20)

        ctk.CTkLabel(main_frame, text="Tech Stack:", **label_kwargs).grid(row=8, column=0, pady=8, padx=20, sticky="w")
        self.stack_entry = ctk.CTkEntry(main_frame, width=320, placeholder_text="e.g., Python, Django, React", **input_kwargs)
        self.stack_entry.grid(row=8, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="Seniority Level:", **label_kwargs).grid(row=9, column=0, pady=8, padx=20, sticky="w")
        
        combo_kwargs = {
            "fg_color": self.glass_input,
            "border_color": self.glass_border,
            "text_color": self.text_primary,
            "button_color": self.glass_border,
            "button_hover_color": self.neon_cyan,
            "dropdown_fg_color": self.glass_panel,
            "dropdown_text_color": self.text_primary,
            "dropdown_hover_color": self.glass_border,
            "corner_radius": 8,
            "font": self.font_main
        }
        self.seniority_vars = {
            "Junior": ctk.BooleanVar(value=True),
            "Mid": ctk.BooleanVar(value=False),
            "Senior": ctk.BooleanVar(value=False),
            "Lead": ctk.BooleanVar(value=False)
        }
        self.seniority_combo = MultiSelectComboBox(main_frame, options=list(self.seniority_vars.keys()), vars_dict=self.seniority_vars, width=320)
        self.seniority_combo.grid(row=9, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="City:", **label_kwargs).grid(row=10, column=0, pady=8, padx=20, sticky="w")
        self.city_entry = ctk.CTkEntry(main_frame, width=320, placeholder_text="e.g., Warsaw, Krakow", **input_kwargs)
        self.city_entry.grid(row=10, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="CV Template:", **label_kwargs).grid(row=11, column=0, pady=8, padx=20, sticky="w")
        self.template_combo = ctk.CTkComboBox(main_frame, width=320, values=["Classic_ATS.html", "Modern_Tech.html", "Creative_Startup.html"], state="readonly", **combo_kwargs)
        self.template_combo.grid(row=11, column=1, pady=8, padx=20, sticky="w")
        self.template_combo.set("Classic_ATS.html")

        ctk.CTkLabel(main_frame, text="Job Type:", **label_kwargs).grid(row=12, column=0, pady=8, padx=20, sticky="w")
        self.job_type_vars = {
            "Remote": ctk.BooleanVar(value=True),
            "Hybrid": ctk.BooleanVar(value=False),
            "Onsite": ctk.BooleanVar(value=False)
        }
        self.job_type_combo = MultiSelectComboBox(main_frame, options=list(self.job_type_vars.keys()), vars_dict=self.job_type_vars, width=320)
        self.job_type_combo.grid(row=12, column=1, pady=8, padx=20, sticky="w")

        ctk.CTkLabel(main_frame, text="Match Threshold (%):", **label_kwargs).grid(row=13, column=0, pady=8, padx=20, sticky="w")
        self.match_slider = ctk.CTkSlider(
            main_frame, from_=30, to=100, width=250, 
            fg_color=self.glass_input, progress_color=self.neon_cyan, button_color=self.neon_cyan, button_hover_color="#1a6ccc"
        )
        self.match_slider.grid(row=13, column=1, pady=8, padx=20, sticky="w")
        self.match_slider.set(30)

        self.match_value_label = ctk.CTkLabel(main_frame, text="30%", text_color=self.neon_cyan, font=self.font_label)
        self.match_value_label.grid(row=13, column=1, pady=8, padx=(290, 0), sticky="w")
        self.match_slider.configure(command=self.update_match_label)

        ctk.CTkLabel(main_frame, text="Work Speed (% CPU):", **label_kwargs).grid(row=14, column=0, pady=8, padx=20, sticky="w")
        self.speed_slider = ctk.CTkSlider(
            main_frame, from_=1, to=100, number_of_steps=99, width=250, 
            fg_color=self.glass_input, progress_color=self.neon_amber, button_color=self.neon_amber, button_hover_color="#D95A2B"
        )
        self.speed_slider.grid(row=14, column=1, pady=8, padx=20, sticky="w")

        self.speed_value_label = ctk.CTkLabel(main_frame, text="50%", text_color=self.neon_amber, font=self.font_label)
        self.speed_value_label.grid(row=14, column=1, pady=8, padx=(290, 0), sticky="w")
        self.speed_slider.configure(command=self.update_speed_label)

        cb_kwargs = {
            "text_color": self.text_primary,
            "font": self.font_main,
            "fg_color": self.neon_cyan,
            "hover_color": "#1a6ccc",
            "border_color": self.glass_border,
            "border_width": 1
        }

        self.non_tech_var = ctk.BooleanVar(value=False)
        self.non_tech_cb = ctk.CTkCheckBox(main_frame, text="Non-Tech Job (Fast Apply, No LLM Checks)", variable=self.non_tech_var, **cb_kwargs)
        self.non_tech_cb.grid(row=15, column=0, columnspan=2, pady=(15, 5), padx=20, sticky="w")

        self.ignore_faang_var = ctk.BooleanVar(value=True)
        self.ignore_faang_cb = ctk.CTkCheckBox(main_frame, text="Ignore Large Companies (FAANG & Banks)", variable=self.ignore_faang_var, **cb_kwargs)
        self.ignore_faang_cb.grid(row=16, column=0, columnspan=2, pady=5, padx=20, sticky="w")

        self.autonomous_var = ctk.BooleanVar(value=False)
        self.autonomous_cb = ctk.CTkCheckBox(main_frame, text="Autonomous Mode (Loop every 30 mins)", variable=self.autonomous_var, **cb_kwargs)
        self.autonomous_cb.grid(row=17, column=0, columnspan=2, pady=5, padx=20, sticky="w")

        self.first_in_var = ctk.BooleanVar(value=False)
        self.first_in_cb = ctk.CTkCheckBox(main_frame, text="First In Mode (Sleep & Snipe Newest Jobs)", variable=self.first_in_var, **cb_kwargs)
        self.first_in_cb.grid(row=18, column=0, columnspan=2, pady=(5, 20), padx=20, sticky="w")

        btn_frame = ctk.CTkFrame(left_panel, fg_color="transparent")
        btn_frame.pack(pady=(20, 0), padx=0, fill="x")

        btn_row_1 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_row_1.pack(fill="x", pady=(0, 15))

        self.launch_button = ctk.CTkButton(
            btn_row_1, text="INITIALIZE SEQUENCE", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=50, corner_radius=8, 
            fg_color=self.neon_cyan, hover_color="#1a6ccc", text_color="#FFFFFF", command=self.save_and_launch
        )
        self.launch_button.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.pause_button = ctk.CTkButton(
            btn_row_1, text="PAUSE", font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
            height=50, width=120, corner_radius=8,
            fg_color=self.glass_input, hover_color=self.glass_border, text_color=self.neon_amber,
            border_color=self.neon_amber, border_width=1, command=self.toggle_pause
        )
        self.pause_button.pack(side="right")

        btn_row_2 = ctk.CTkFrame(btn_frame, fg_color="transparent")
        btn_row_2.pack(fill="x")
        
        self.login_boards_btn = ctk.CTkButton(
            btn_row_2, text="AUTHENTICATE BOARDS", font=self.font_label,
            height=40, corner_radius=8,
            fg_color=self.glass_input, hover_color=self.glass_border, text_color=self.text_secondary,
            border_color=self.glass_border, border_width=1, command=self.login_job_boards
        )
        self.login_boards_btn.pack(side="left", fill="x", expand=True)

        # === ПРАВАЯ ПАНЕЛЬ (График + Логи) ===
        ctk.CTkLabel(
            right_panel, text="Bot Activity Overview", text_color=self.text_primary, font=self.font_title
        ).pack(pady=(20, 0), padx=20, anchor="w")

        self.graph_frame = ctk.CTkFrame(right_panel, fg_color="transparent", height=150)
        self.graph_frame.pack(fill="x", padx=20, pady=(10, 20))
        
        self.setup_live_graph()

        ctk.CTkLabel(
            right_panel, text="Activity Logs", text_color=self.text_primary, font=self.font_title
        ).pack(pady=(0, 10), padx=20, anchor="w")

        self.log_textbox = ctk.CTkTextbox(
            right_panel, font=self.font_mono, text_color=self.text_primary,
            fg_color=self.glass_input, border_color=self.glass_border, border_width=1, corner_radius=8, state="disabled"
        )
        self.log_textbox.pack(pady=(0, 20), padx=20, fill="both", expand=True)
        self.setup_print_redirector()
        
    def setup_live_graph(self):
        import numpy as np
        import matplotlib
        matplotlib.use("TkAgg")
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self.fig = Figure(figsize=(5, 1.5), dpi=100, facecolor=self.glass_panel)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor(self.glass_panel)
        self.fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Remove borders and axes
        for spine in self.ax.spines.values():
            spine.set_visible(False)
        self.ax.get_xaxis().set_visible(False)
        self.ax.get_yaxis().set_visible(False)

        # Initial data arrays
        self.x_data = np.linspace(0, 10, 100)
        self.y_data1 = np.sin(self.x_data) + 2.0
        self.y_data2 = np.cos(self.x_data * 0.8) * 0.8 + 1.5

        # Plot smooth anti-aliased lines
        self.line1, = self.ax.plot(self.x_data, self.y_data1, color=self.neon_cyan, lw=2, antialiased=True)
        self.line2, = self.ax.plot(self.x_data, self.y_data2, color=self.neon_amber, lw=2, antialiased=True)

        # Fill under lines
        self.fill1 = self.ax.fill_between(self.x_data, self.y_data1, 0, color=self.neon_cyan, alpha=0.15, antialiased=True)
        self.fill2 = self.ax.fill_between(self.x_data, self.y_data2, 0, color=self.neon_amber, alpha=0.15, antialiased=True)

        self.ax.set_ylim(0, 4)
        self.ax.set_xlim(0, 10)
        
        # Faint Gridlines
        for i in range(1, 4):
            self.ax.axhline(i, color="#2A2D35", linestyle="--", linewidth=1, alpha=0.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        widget = self.canvas.get_tk_widget()
        widget.pack(fill="both", expand=True)

        self.phase = 0
        self.update_live_graph()

    def update_live_graph(self):
        import numpy as np
        
        self.phase += 0.1
        
        # Shift existing data to the left
        self.y_data1[:-1] = self.y_data1[1:]
        self.y_data2[:-1] = self.y_data2[1:]
        
        # Generate new data points with smooth sine waves + slight noise
        if getattr(self, "is_paused", False):
            # If paused, lines still move but become flat/inactive
            self.y_data1[-1] = 2.0 + (np.random.rand() * 0.05)
            self.y_data2[-1] = 1.5 + (np.random.rand() * 0.05)
        else:
            self.y_data1[-1] = np.sin(self.phase) * 0.8 + 2.0 + (np.random.rand() * 0.15)
            self.y_data2[-1] = np.cos(self.phase * 0.7) * 0.6 + 1.5 + (np.random.rand() * 0.15)
        
        self.line1.set_ydata(self.y_data1)
        self.line2.set_ydata(self.y_data2)
        
        # Matplotlib requires removing and redrawing fill_between objects for animation
        self.fill1.remove()
        self.fill2.remove()
        self.fill1 = self.ax.fill_between(self.x_data, self.y_data1, 0, color=self.neon_cyan, alpha=0.15, antialiased=True)
        self.fill2 = self.ax.fill_between(self.x_data, self.y_data2, 0, color=self.neon_amber, alpha=0.15, antialiased=True)
        
        self.canvas.draw_idle()
        
        # Loop every 50ms for smooth live scrolling
        self.after(50, self.update_live_graph)

    def setup_print_redirector(self):
        # Перехват принтов
        import threading
        import sys
        class PrintRedirector:
            def __init__(self, textbox):
                self.textbox = textbox
                self.lock = threading.Lock()

            def write(self, text):
                with self.lock:
                    self.textbox.configure(state="normal")
                    self.textbox.insert("end", text)
                    self.textbox.see("end")
                    self.textbox.configure(state="disabled")
                    sys.__stdout__.write(text)  # дублируем в консоль IDE

            def flush(self):
                sys.__stdout__.flush()
                
            def reconfigure(self, *args, **kwargs):
                pass
                
            def isatty(self):
                return False

        sys.stdout = PrintRedirector(self.log_textbox)
        sys.stderr = PrintRedirector(self.log_textbox)

    def cleanup_chromium(self):
        import psutil
        print("🧹 Cleaning up headless browser instances...")
        try:
            for p in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'chrome' in (p.info['name'] or '').lower() or 'chromium' in (p.info['name'] or '').lower():
                    cmd = " ".join(p.info['cmdline'] or [])
                    if 'job_boards_profile' in cmd or 'email_profile' in cmd or 'headless' in cmd:
                        p.kill()
        except Exception as e:
            print(f"Cleanup error: {e}")

    def do_logout(self):
        self.cleanup_chromium()
        self.withdraw()
        from AIJobSeekerApp import LoginWindow # Since it might be needed
        self.login_window = LoginWindow(self)
        
    def clear_all_data(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all CVs, User Data, and Logs?"):
            import shutil
            try:
                for d in ["Data/job_boards_profile", "Data"]:
                    if os.path.exists(d):
                        for f in os.listdir(d):
                            if f.startswith("CV_") or f.startswith("job_boards_profile"):
                                path = os.path.join(d, f)
                                if os.path.isdir(path): shutil.rmtree(path)
                                else: os.remove(path)
                
                self.first_name_entry.delete(0, 'end')
                self.last_name_entry.delete(0, 'end')
                self.email_entry.delete(0, 'end')
                self.phone_entry.delete(0, 'end')
                self.stack_entry.delete(0, 'end')
                self.cv_label.configure(text="No file selected")
                self.settings.cv_path = ""
                messagebox.showinfo("Success", "Data cleared!")
            except Exception as e:
                messagebox.showerror("Error", f"Could not clear completely: {e}")

    def toggle_pause(self):
        self.is_paused = not getattr(self, 'is_paused', False)
        if self.is_paused:
            self.pause_button.configure(
                text="RESUME", 
                fg_color=self.glass_input, text_color=self.neon_cyan, border_color=self.neon_cyan
            )
            print("⏸️ [SYSTEM] Agent paused. Waiting to resume...")
        else:
            self.pause_button.configure(
                text="PAUSE", 
                fg_color=self.glass_input, text_color=self.neon_amber, border_color=self.neon_amber
            )
            print("▶️ [SYSTEM] Agent resumed. Continuing work...")

    def clear_dashboard(self):
        if messagebox.askyesno("Clear Dashboard", "Are you sure you want to delete ALL applied jobs history? This cannot be undone."):
            try:
                from db_manager import db
                db._write_db([])
                print("🗑️ [SYSTEM] Dashboard history cleared.")
                messagebox.showinfo("Success", "Dashboard history has been cleared.")
            except Exception as e:
                print(f"⚠️ Failed to clear dashboard: {e}")

    def clear_seen_jobs(self):
        if messagebox.askyesno("Clear Seen Jobs", "Are you sure you want to delete only 'Seen' jobs history? This allows you to apply to them again."):
            try:
                from db_manager import db
                db.clear_seen_jobs()
                print("🗑️ [SYSTEM] Seen jobs history cleared.")
                messagebox.showinfo("Success", "Seen jobs have been cleared.")
            except Exception as e:
                print(f"⚠️ Failed to clear seen jobs: {e}")

    def login_email(self):
        email = self.email_entry.get().strip()
        if not email:
            return messagebox.showerror("Error", "Please enter your email address first.")
        import threading
        def _login():
            checker = EmailChecker(email)
            checker.login_to_email()
            messagebox.showinfo("Success", "Email session saved! The bot can now check confirmations.")
        threading.Thread(target=_login, daemon=True).start()

    def login_job_boards(self):
        import threading
        def _login_boards():
            from DrissionPage import ChromiumOptions, ChromiumPage
            import os, time
            print("🌍 Launching browser for Job Boards login...")
            co = ChromiumOptions()
            co.set_user_data_path(os.path.abspath("Data/job_boards_profile"))
            co.headless(False)
            co.set_argument('--disable-blink-features=AutomationControlled')
            
            try:
                page = ChromiumPage(co)
                page.get("https://www.pracuj.pl/")
                page.new_tab("https://justjoin.it/")
                page.new_tab("https://djinni.co/login")
                print("⏳ Please log in to Pracuj.pl, JustJoin.it and Djinni.")
                print("⏳ Once you are done, simply close the browser window.")
                while True:
                    time.sleep(1)
                    _ = page.title
            except Exception:
                print("✅ Job boards session saved and browser closed.")
                messagebox.showinfo("Success", "Job boards session saved! Cloudflare blocks will be minimized.")
                
        threading.Thread(target=_login_boards, daemon=True).start()

    def browse_cv(self):
        filetypes = (
            ("CV files", "*.pdf *.docx"),
            ("PDF files", "*.pdf"),
            ("Word files", "*.docx"),
            ("All files", "*.*")
        )

        filename = filedialog.askopenfilename(title="Select your CV", filetypes=filetypes)
        if filename:
            self.settings.cv_path = filename
            self.cv_label.configure(text=Path(filename).name)

    def update_match_label(self, value):
        self.match_value_label.configure(text=f"{int(value)}%")

    def update_speed_label(self, value):
        self.speed_value_label.configure(text=f"{int(value)}%")
        # Мгновенно обновляем настройку прямо во время работы
        self.settings.work_speed = int(value)

    def load_saved_settings(self):
        if self.settings.first_name: self.first_name_entry.insert(0, self.settings.first_name)
        if self.settings.last_name: self.last_name_entry.insert(0, self.settings.last_name)
        if self.settings.email: self.email_entry.insert(0, self.settings.email)
        if self.settings.phone: self.phone_entry.insert(0, self.settings.phone)
        if self.settings.cv_path: self.cv_label.configure(text=Path(self.settings.cv_path).name)
        if self.settings.stack: self.stack_entry.insert(0, self.settings.stack)
        if self.settings.city: self.city_entry.insert(0, self.settings.city)
        if hasattr(self.settings, 'cv_template') and self.settings.cv_template: self.template_combo.set(self.settings.cv_template)
        if self.settings.job_type:
            jt_list = [j.strip() for j in self.settings.job_type.split(',')]
            for jt, var in self.job_type_vars.items():
                var.set(jt in jt_list)
        if self.settings.seniority_level:
            sen_list = [s.strip() for s in self.settings.seniority_level.split(',')]
            for sen, var in self.seniority_vars.items():
                var.set(sen in sen_list)
        self.match_slider.set(self.settings.match_threshold)
        self.update_match_label(self.settings.match_threshold)
        self.speed_slider.set(self.settings.work_speed)
        self.update_speed_label(self.settings.work_speed)
        self.non_tech_var.set(self.settings.non_tech_mode)
        self.ignore_faang_var.set(getattr(self.settings, 'ignore_faang', True))
        self.autonomous_var.set(getattr(self.settings, 'autonomous_mode', False))
        self.first_in_var.set(getattr(self.settings, 'first_in_mode', False))

    def save_settings(self):
        if not self.first_name_entry.get().strip(): messagebox.showerror("Error", "Please enter your first name"); return False
        if not self.last_name_entry.get().strip(): messagebox.showerror("Error", "Please enter your last name"); return False
        if not self.email_entry.get().strip(): messagebox.showerror("Error", "Please enter your email"); return False
        if getattr(self, 'settings', None) and not getattr(self.settings, 'cv_path', ''): messagebox.showerror("Error", "Please upload your CV"); return False
        if not self.stack_entry.get().strip(): messagebox.showerror("Error", "Please enter your tech stack"); return False

        self.settings.first_name = self.first_name_entry.get().strip()
        self.settings.last_name = self.last_name_entry.get().strip()
        self.settings.email = self.email_entry.get().strip()
        self.settings.phone = self.phone_entry.get().strip()
        self.settings.stack = self.stack_entry.get().strip()
        self.settings.city = self.city_entry.get().strip()
        self.settings.cv_template = self.template_combo.get()
        self.settings.job_type = ", ".join([jt for jt, var in self.job_type_vars.items() if var.get()])
        self.settings.match_threshold = int(self.match_slider.get())
        self.settings.seniority_level = ", ".join([sen for sen, var in self.seniority_vars.items() if var.get()])
        self.settings.work_speed = int(self.speed_slider.get())
        self.settings.non_tech_mode = self.non_tech_var.get()
        self.settings.ignore_faang = self.ignore_faang_var.get()
        self.settings.autonomous_mode = self.autonomous_var.get()
        self.settings.first_in_mode = self.first_in_var.get()
        self.settings.save()
        return True

    def save_and_launch(self):
        if not self.save_settings():
            return
        messagebox.showinfo("Success", "Settings saved! Starting job search...")

        import threading
        threading.Thread(target=self.run_agent, daemon=True).start()

    def run_agent(self):
        while True:
            self._run_agent_once()
            
            if not self.settings.autonomous_mode:
                break
                
            print(f"\n⏳ [AUTONOMOUS MODE] Sleeping for 30 minutes before next scan...")
            for _ in range(1800):
                while getattr(self, 'is_paused', False):
                    time.sleep(1)
                time.sleep(1)

    def _run_agent_once(self):
        """Основной цикл: Scraping → Matching (Batched) → CV Gen → Apply (Batched) → Log"""
        print("🚀 Starting agent loop...")
        
        # Очистка отклоненных вакансий если поменялись настройки
        current_hash = f"{self.settings.stack}_{self.settings.match_threshold}_{self.settings.seniority_level}_{self.settings.city}".lower()
        last_hash_file = "Data/last_settings_hash.txt"
        
        try:
            with open(last_hash_file, "r") as f:
                last_hash = f.read().strip()
        except:
            last_hash = ""
            
        if last_hash != current_hash:
            print("🔄 Settings changed! Clearing rejected jobs cache to re-evaluate them...")
            db.clear_rejected_jobs()
            with open(last_hash_file, "w") as f:
                f.write(current_hash)

        # Вспомогательная функция проверки дубликатов (через твой pandas логгер)
        def is_already_applied(link):
            # 1. Проверка по JSON базе (если уже подавались или отклонили)
            status = db.get_job_status(link)
            if status == "Applied" or status == "Success" or status == "Rejected":
                # Если настройки изменились, мы должны были бы очистить Rejected
                # Но пока просто скипаем все Rejected, так как при смене настроек юзер может вручную удалить базу
                # (Ниже добавим очистку при старте если настройки поменялись)
                return True
                
            # 2. Проверка по Excel (на всякий случай)
            file_name = "Data/my_applications.xlsx"
            if not os.path.exists(file_name):
                return False
            try:
                import pandas as pd
                df = pd.read_excel(file_name)
                if "link" in df.columns:
                    return link in df['link'].values
            except Exception:
                pass
            return False

        # Извлекаем базовый CV для LLM
        base_cv_text = ""
        if self.settings.cv_path.endswith(".pdf"):
            base_cv_text = self.resume_manager.extract_text_from_pdf(self.settings.cv_path)
        elif self.settings.cv_path.endswith(".docx"):
            try:
                import docx
                doc = docx.Document(self.settings.cv_path)
                base_cv_text = "\n".join([p.text for p in doc.paragraphs])
            except Exception as e:
                print(f"⚠️   DOCX: {e}")

        if getattr(self, 'is_paused', False):
            print("\n⏸️ [SYSTEM] Agent is PAUSED. Click 'Resume' in the UI to start Phase 1 (Scraping)...")
            while getattr(self, 'is_paused', False):
                time.sleep(1)
            print("▶️ [SYSTEM] Resuming...\n")
            
        # 1. Scraping
        print("🔍 Phase 1: Searching for jobs...")
        all_jobs = []
        seen_jobs = set()

        try:
            skills = [s.strip() for s in self.settings.stack.lower().split(",") if s.strip()]
            scraper = MultiScraper(skills=skills, seniority_filter=self.settings.seniority_level, seen_jobs=seen_jobs, settings=self.settings)
            global_jobs = scraper.run() if hasattr(scraper, 'run') else scraper.scrape()
            all_jobs.extend(global_jobs)
            print(f"✅ Found {len(global_jobs)} jobs on international sites")
        except Exception as e:
            print(f"⚠️ Error scraping international sites: {e}")

        try:
            polish_jobs = scrape_polish_sites(
                tech_stack=[s.strip() for s in self.settings.stack.lower().split(",") if s.strip()],
                seniority_filter=self.settings.seniority_level,
                city=self.settings.city,
                settings=self.settings
            )
            all_jobs.extend(polish_jobs)
            print(f"✅ Found {len(polish_jobs)} jobs on Polish sites")
        except Exception as e:
            print(f"⚠️ Error scraping Polish sites: {e}")

        try:
            djinni_jobs = scrape_djinni(
                keyword=self.settings.stack.split(",")[0].strip(),
                seniority_filter=self.settings.seniority_level,
                settings=self.settings
            )
            all_jobs.extend(djinni_jobs)
            print(f"✅ Found {len(djinni_jobs)} jobs on Djinni")
        except Exception as e:
            print(f"⚠️ Error scraping Djinni: {e}")

        # Нормализация: скраперы возвращают 'details', а матчинг ожидает 'description'
        for job in all_jobs:
            if "description" not in job and "details" in job:
                job["description"] = job["details"]
            db.add_job(job.get("title", "Unknown"), job.get("company", "Unknown"), job.get("link", job.get("url", "")), job.get("source", "Unknown"))

        if not all_jobs:
            print("⚠️ No matching jobs found.")
            return

        print(f"📊 Total jobs found: {len(all_jobs)}")

        # Фильтруем уже обработанные вакансии и дубликаты
        new_jobs = []
        seen_urls_this_run = set()
        for job in all_jobs:
            job_url = job.get("link", "")
            if not job_url or job_url in seen_urls_this_run:
                continue
                
            seen_urls_this_run.add(job_url)
            
            company_name = job.get("company", "").lower()
            big_corps = ['google', 'amazon', 'facebook', 'meta', 'apple', 'netflix', 'microsoft', 'jpmorgan', 'goldman sachs', 'morgan stanley', 'citi bank', 'citibank', 'bank of america', 'ubs', 'barclays', 'deutsche bank', 'epam', 'luxoft', 'capgemini', 'accenture', 'ibm']
            is_big_corp = any(b in company_name for b in big_corps)
            
            if getattr(self.settings, 'ignore_faang', True) and is_big_corp:
                print(f"⏭️ Skipping (Big Corp / FAANG filtered): {job.get('company', 'Unknown')}")
                continue
            
            if not is_already_applied(job_url):
                new_jobs.append(job)
            else:
                print(f"⏭️ Skipping (already applied): {job.get('title', 'N/A')}")

        print(f"🆕 New jobs to process: {len(new_jobs)}")
        if not new_jobs:
            print("⚠️ All found jobs have already been processed.")
            return

        # 2. Matching (Batches of 50)
        if getattr(self, 'is_paused', False):
            print("\n⏸️ [SYSTEM] Agent is PAUSED. Click 'Resume' in the UI to start Phase 2 (Matching)...")
            while getattr(self, 'is_paused', False):
                time.sleep(1)
            print("▶️ [SYSTEM] Resuming...\n")
            
        print("🎯 Phase 2: Resume Matching (LLM Analysis)...")
        matched_jobs = []

        BATCH_SIZE = 50
        total_batches = (len(new_jobs) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_num in range(total_batches):
            start_idx = batch_num * BATCH_SIZE
            end_idx = min(start_idx + BATCH_SIZE, len(new_jobs))
            batch_jobs = new_jobs[start_idx:end_idx]

            print(f"\n📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch_jobs)} jobs)...")

            for job in batch_jobs:
                if self.settings.non_tech_mode:
                    job["match_score"] = 100
                    matched_jobs.append(job)
                    print(f"✅ {job.get('title', 'N/A')[:50]} (Non-Tech Mode Auto-Match)")
                    continue

                try:
                    job_desc = job.get("description", "")

                    if job_desc.strip():
                        # Есть описание — используем LLM (точный анализ)
                        match_score = self.llm.calculate_match_score(
                            job_title=job.get("title", ""),
                            job_description=job_desc,
                            user_stack=self.settings.stack,
                            user_seniority=self.settings.seniority_level
                        )
                    else:
                        # Нет описания — быстрый keyword match по title + source
                        job_text = job.get("title", "").lower()
                        stack_keywords = [s.strip().lower() for s in self.settings.stack.split(",") if s.strip()]
                        matches = sum(1 for kw in stack_keywords if kw in job_text)
                        match_score = int((matches / max(len(stack_keywords), 1)) * 100)
                        # Бонус: польские сайты (JustJoin, Pracuj) получают +20% за релевантность источника
                        source = job.get("source", "").lower()
                        if any(s in source for s in ["justjoin", "pracuj", "nofluff", "bulldogjob", "theprotocol"]):
                            match_score = min(match_score + 20, 100)

                    if match_score >= self.settings.match_threshold:
                        job["match_score"] = match_score
                        matched_jobs.append(job)
                        print(f"✅ {job.get('title', 'N/A')[:50]} ({job.get('company', '?')}) - {match_score}%")
                    else:
                        print(f"⏭️ {job.get('title', 'N/A')[:50]} - {match_score}% (below threshold)")

                except Exception as e:
                    print(f"⚠️ Error analyzing job: {e}")
                    continue

            print(
                f"✅ Batch {batch_num + 1} completed. Matches found: {len([j for j in batch_jobs if 'match_score' in j])}")

        matched_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        print(f"\n🎯 Total suitable jobs selected: {len(matched_jobs)}")

        if not matched_jobs:
            print("⚠️ No new jobs with the required match percentage.")
            return

        # 3. Apply (МНОГОПОТОЧНОСТЬ С ДИНАМИЧЕСКИМ ЛИМИТОМ)
        print("\n📝 Phase 3: CV Generation and Applying (Multithreaded)...")

        applied_count = 0
        MAX_APPLY = 50
        jobs_to_apply = matched_jobs[:MAX_APPLY]

        from utils.thread_manager import ThreadManager
        tm = ThreadManager(self.settings)

        import threading
        class Counter:
            def __init__(self):
                self.val = 0
                self.lock = threading.Lock()
            def increment(self):
                with self.lock:
                    self.val += 1
        
        applied_counter = Counter()

        def process_job(job_tuple):
            idx, job = job_tuple
            job_url = job.get("url", "")
            if not job_url: job_url = job.get("link", "")
            original_job_url = job_url
            
            job_title = job.get("title", "Unknown")
            company = job.get("company", "Unknown")
            source = job.get("source", "").lower()
            recommendations = job.get("recommendations", "")

            print(f"[{idx}/{len(jobs_to_apply)}] 🚀 Processing {company} - {job_title} ({source})")
            
            import copy
            import os
            import re
            profile_data = copy.deepcopy(self.settings.to_dict())

            # 1. Генерация CV
            try:
                ai_reco = self.llm.generate_cv_json(job_title, job.get("description", ""), profile_data, self.settings.stack, base_cv_text)
                if not ai_reco:
                    raise ValueError("LLM returned empty CV JSON")

                safe_comp = "".join([c for c in company if c.isalpha() or c.isdigit()]).rstrip()
                if not safe_comp: safe_comp = "Unknown_Company"

                out_path = f"Data/CV_{safe_comp}.pdf"

                from utils.cv_generator import generate_custom_cv
                custom_cv_path = generate_custom_cv(safe_comp, ai_reco, profile_data, output_path=out_path, template_name=self.settings.cv_template)

                if custom_cv_path:
                    profile_data["cv_path"] = custom_cv_path
                    print(f"✅ CV created: {custom_cv_path}")

            except Exception as e:
                print(f"⚠️ Failed to create custom CV: {e}")
                print("📎 Using original CV")
                profile_data["cv_path"] = self.settings.cv_path

            status = "Failed"

            if "remoteok" in job_url.lower() or "remoteok" in source:
                print(f"⏭️ Skipping {source} — RemoteOK requires Premium to apply.")
                status = "Skipped"
            elif "justjoin.it" in job_url or source == "justjoin.it":
                from DrissionPage import ChromiumOptions, ChromiumPage
                import random
                import os
                import shutil
                import threading
                
                speed = getattr(self.settings, 'work_speed', 100)
                is_single_thread = speed <= 25  # 1 thread
                
                base_dir = os.path.abspath("Data/job_boards_profile")
                if is_single_thread:
                    user_data_dir = base_dir
                else:
                    thread_id = threading.get_ident()
                    user_data_dir = os.path.abspath(f"Data/job_boards_profile_{thread_id}")
                    if os.path.exists(base_dir) and not os.path.exists(user_data_dir):
                        try:
                            shutil.copytree(base_dir, user_data_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns('Singleton*', 'lock'))
                        except Exception as e:
                            print(f"⚠️ Profile copy warning: {e}")

                if is_single_thread:
                    global_profile_lock = getattr(self, 'global_profile_lock', None)
                    if not global_profile_lock:
                        import threading
                        self.global_profile_lock = threading.Lock()
                        global_profile_lock = self.global_profile_lock
                    global_profile_lock.acquire()

                port = random.randint(9300, 9900)
                co = ChromiumOptions().set_local_port(port)
                co.set_user_data_path(user_data_dir)
                co.set_argument('--disable-blink-features=AutomationControlled')
                co.headless(False)
                
                try:
                    page = ChromiumPage(co)
                    from Appliers.justjoin_applier_drission import JustJoinApplier
                    local_jj = JustJoinApplier(profile_data)
                    result = local_jj.apply(page, job_url, profile_data["cv_path"])
                    
                    if result and result.startswith("ExternalATS:"):
                        print(f"🔄 JustJoin redirected to external ATS. Passing to Universal Applier...")
                        job_url = result.split("ExternalATS:")[1]
                        status = "ExternalATS"
                    elif result == "Success":
                        status = "Applied"
                        applied_counter.increment()
                    else:
                        status = "Failed"
                        
                except Exception as e:
                    print(f"❌ JustJoin apply error: {e}")
                    status = "Failed"
                finally:
                    try:
                        page.quit()
                    except:
                        pass

                    if is_single_thread:
                        try:
                            global_profile_lock.release()
                        except:
                            pass
            
            elif "djinni.co" in job_url or source == "Djinni":
                from DrissionPage import ChromiumOptions, ChromiumPage
                import random
                import os
                import shutil
                import threading
                
                speed = getattr(self.settings, 'work_speed', 100)
                is_single_thread = speed <= 25  # 1 thread
                
                base_dir = os.path.abspath("Data/job_boards_profile")
                if is_single_thread:
                    user_data_dir = base_dir
                else:
                    thread_id = threading.get_ident()
                    user_data_dir = os.path.abspath(f"Data/job_boards_profile_{thread_id}")
                    if os.path.exists(base_dir) and not os.path.exists(user_data_dir):
                        try:
                            shutil.copytree(base_dir, user_data_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns('Singleton*', 'lock'))
                        except Exception as e:
                            print(f"⚠️ Profile copy warning: {e}")

                if is_single_thread:
                    global_profile_lock = getattr(self, 'global_profile_lock', None)
                    if not global_profile_lock:
                        import threading
                        self.global_profile_lock = threading.Lock()
                        global_profile_lock = self.global_profile_lock
                    global_profile_lock.acquire()

                port = random.randint(9300, 9900)
                co = ChromiumOptions().set_local_port(port)
                co.set_user_data_path(user_data_dir)
                co.set_argument('--disable-blink-features=AutomationControlled')
                co.headless(False)
                
                try:
                    page = ChromiumPage(co)
                    from Appliers.djinni_applier import DjinniApplier
                    local_djinni = DjinniApplier(self.settings.to_dict())
                    result = local_djinni.apply(page, job_url, profile_data["cv_path"])
                    if result == "Success":
                        status = "Applied"
                        applied_counter.increment()
                    else:
                        status = "Failed"
                except Exception as e:
                    print(f"❌ Djinni apply error: {e}")
                    status = "Failed"
                finally:
                    try:
                        page.quit()
                    except:
                        pass
                        
                    if is_single_thread:
                        try:
                            global_profile_lock.release()
                        except:
                            pass
                        
            if status == "ExternalATS" or (status == "Failed" and not ("remoteok" in job_url.lower() or "justjoin.it" in job_url or "djinni.co" in job_url)):
                from playwright.sync_api import sync_playwright
                with sync_playwright() as p:
                    import os
                    import shutil
                    import threading
                    
                    speed = getattr(self.settings, 'work_speed', 100)
                    is_single_thread = speed <= 25  # 1 thread
                    
                    base_dir = os.path.abspath("Data/job_boards_profile")
                    if is_single_thread:
                        user_data_dir = base_dir
                    else:
                        thread_id = threading.get_ident()
                        user_data_dir = os.path.abspath(f"Data/job_boards_profile_{thread_id}")
                        if os.path.exists(base_dir) and not os.path.exists(user_data_dir):
                            try:
                                shutil.copytree(base_dir, user_data_dir, dirs_exist_ok=True, ignore=shutil.ignore_patterns('Singleton*', 'lock'))
                            except Exception as e:
                                print(f"⚠️ Profile copy warning: {e}")

                    if is_single_thread:
                        global_profile_lock = getattr(self, 'global_profile_lock', None)
                        if not global_profile_lock:
                            import threading
                            self.global_profile_lock = threading.Lock()
                            global_profile_lock = self.global_profile_lock
                        global_profile_lock.acquire()

                    try:
                        context = p.chromium.launch_persistent_context(
                            user_data_dir=user_data_dir,
                            channel="chrome",
                            headless=False,
                            slow_mo=200,
                            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-gpu", "--disable-software-rasterizer"],
                            no_viewport=True
                        )
                    except Exception as e:
                        if is_single_thread:
                            global_profile_lock.release()
                        raise e

                    
                    page = context.pages[0] if context.pages else context.new_page()
                    
                    # Применяем Stealth-режим, чтобы Cloudflare не блокировал нас
                    try:
                        from playwright_stealth import Stealth
                        stealth = Stealth()
                        stealth.apply_stealth_sync(context)
                    except ImportError:
                        print("⚠️ playwright-stealth is not installed. Cloudflare might block the page.")


                    try:
                        from Core.bulletproof_engine import BulletproofApplier
                        local_sandbox = BulletproofApplier(profile_data, getattr(self, 'llm', None))
                        sandbox_status = local_sandbox.apply(page, context, job_url, profile_data.get("cv_path", ""))
                        if sandbox_status == "Manual":
                            status = "Manual Apply Required"
                        elif sandbox_status == "Applied" or sandbox_status == "Success":
                            status = "Applied"
                            applied_counter.increment()
                        else:
                            print("⚠️ Bulletproof engine failed. Launching Deterministic Discovery Fallback...")
                            from Core.interactive_engine import InteractiveApplier
                            fallback_applier = InteractiveApplier(profile_data, getattr(self, 'llm', None))
                            fallback_status = fallback_applier.apply(page, context, job_url, profile_data.get("cv_path", ""))
                            if fallback_status == "Applied" or fallback_status == "Success":
                                status = "Applied"
                                applied_counter.increment()
                            elif fallback_status == "Manual":
                                status = "Manual Apply Required"
                            else:
                                status = "Failed"
                    except Exception as e:
                        print(f"❌ Universal applier error: {e}")
                        status = "Failed"
                    finally:
                        try:
                            context.close()
                        except:
                            pass
                        
                        if is_single_thread:
                            try:
                                global_profile_lock.release()
                            except:
                                pass

            try:
                from excel_logger import log_application
                log_data = {
                    "company": company,
                    "title": job_title,
                    "stack": self.settings.stack,
                    "status": status,
                    "link": original_job_url
                }
                log_application(log_data)
            except Exception as e:
                print(f"[Error] Excel logging failed: {e}")
                
            if status in ["Applied", "Applied (Unconfirmed)", "Success"]:
                db.update_job_status(original_job_url, "Applied")
                
                if self.settings.email:
                    checker = EmailChecker(self.settings.email)
                    print(f"📧 Checking email for confirmation from {company}...")
                    time.sleep(5) 
                    if checker.check_for_confirmation(company, job_title):
                        print(f"✅ Confirmation email received from {company}!")
                        db.set_email_confirmed(company)
                    else:
                        print(f"⚠️ No confirmation email found yet.")
            else:
                db.update_job_status(original_job_url, "Failed")
                
            return status

        import queue
        jobs_queue = queue.Queue()
        for idx, job in enumerate(jobs_to_apply, 1):
            jobs_queue.put((idx, job))
            
        active_threads_state = [0]
        threads_lock = threading.Lock()
        
        print(f"\n🚀 [MULTITHREADING] Dispatcher started with {len(jobs_to_apply)} jobs.")
        print("💡 You can adjust the Speed slider in real-time to control concurrent browsers!")
        
        while not jobs_queue.empty():
            if getattr(self, 'is_paused', False):
                print("\n⏸️ [SYSTEM] Application process is PAUSED. Click 'Resume' in the UI to continue...")
                while getattr(self, 'is_paused', False):
                    time.sleep(1)
                print("▶️ [SYSTEM] Resuming application process...\n")
            # Максимальное количество параллельных браузеров 
            # 100% = 4 браузера, 1% = 1 браузер
            MAX_CONCURRENT = 4
            desired_threads = max(1, int((self.settings.work_speed / 100.0) * MAX_CONCURRENT))
            
            with threads_lock:
                current_active = active_threads_state[0]
                
            if current_active < desired_threads:
                job_tuple = jobs_queue.get()
                
                with threads_lock:
                    active_threads_state[0] += 1
                    
                def worker(jt):
                    try:
                        process_job(jt)
                    finally:
                        with threads_lock:
                            active_threads_state[0] -= 1
                        jobs_queue.task_done()
                        
                threading.Thread(target=worker, args=(job_tuple,), daemon=True).start()
                time.sleep(1.5) # Небольшая пауза между запусками потоков, чтобы избежать лагов CPU при старте браузеров
            else:
                time.sleep(1) # Ждем пока освободится поток
                
        # Ждем завершения всех отправленных задач
        jobs_queue.join()
        
        self.cleanup_chromium()

        print(f"\n🎉 [Done] Process finished! Applications sent: {applied_counter.val}")


if __name__ == "__main__":
    app = AIJobSeekerApp()
    app.mainloop()