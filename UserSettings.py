import os
import json

class UserSettings:
    """Глобальное хранилище настроек пользователя"""
    def __init__(self):
        self.first_name = ""
        self.last_name = ""
        self.email = ""
        self.phone = ""
        self.github = ""
        self.position = ""
        self.tech_stack = ""
        self.stack_match_percent = 50
        self.city = ""
        self.job_type = ""
        self.cv_path = None
        self.license_key = ""

    def to_dict(self):
        """Конвертирует в словарь для сохранения"""
        return {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "github": self.github,
            "position": self.position,
            "tech_stack": self.tech_stack,
            "stack_match_percent": self.stack_match_percent,
            "city": self.city,
            "job_type": self.job_type,
            "cv_path": self.cv_path,
            "license_key": self.license_key
        }

    def save_to_file(self, path="UserData/user_settings.json"):
        """Сохраняет настройки в JSON"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=4, ensure_ascii=False)

    def load_from_file(self, path="UserData/user_settings.json"):
        """Загружает настройки из JSON"""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
            except Exception as e:
                print(f"⚠️ Error loading settings: {e}")