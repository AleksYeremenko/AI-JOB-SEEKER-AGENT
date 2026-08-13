import os
import pandas as pd
from datetime import datetime
import time

FILE_NAME = "Data/my_applications.xlsx"

def log_application(data):
    # ВАЖНО: Используем английские ключи, так как main.py ищет 'status', 'link' и 'company'
    columns = ["date", "company", "title", "stack", "status", "link"]

    if os.path.exists(FILE_NAME):
        try:
            df = pd.read_excel(FILE_NAME)
            # Защита от старых файлов с русскими колонками
            if "status" not in df.columns:
                df = pd.DataFrame(columns=columns)
        except Exception:
            df = pd.DataFrame(columns=columns)
    else:
        df = pd.DataFrame(columns=columns)

    new_row = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "company": data.get("company", "Unknown"),
        "title": data.get("title", ""),
        "stack": data.get("stack", ""),
        "status": data.get("status", "Found"),
        "link": data.get("link", "")
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Твоя шикарная защита от открытого файла
    while True:
        try:
            df.to_excel(FILE_NAME, index=False)
            break
        except PermissionError:
            print(f"⏳ Файл {FILE_NAME} открыт! Закрой Excel, жду 10 секунд...")
            time.sleep(10)