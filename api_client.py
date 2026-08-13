import customtkinter as ctk
from tkinter import filedialog
import json
import os
import threading
import requests
import time
from playwright.sync_api import sync_playwright

# --- Цветовая палитра ---
BG_COLOR = "#0D0D12"
FRAME_COLOR = "#15151B"
ACCENT_COLOR = "#1D4ED8"
ACCENT_HOVER = "#2563EB"
TEXT_MAIN = "#F8FAFC"
TEXT_MUTED = "#94A3B8"

ctk.set_appearance_mode("dark")

# --- Конфиг лицензий ---
BASE_URL = "http://127.0.0.1:8000"

def validate_license(license_key: str) -> bool:
    """Проверяет ключ перед запуском"""
    if not license_key:
        return False
    try:
        response = requests.post(
            f"{BASE_URL}/agent/validate",
            json={"license_key": license_key},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False

def register_application(license_key: str):
    """Списывает 1 лимит после успешного отклика"""
    if not license_key:
        return
    try:
        requests.post(
            f"{BASE_URL}/agent/application",
            json={"license_key": license_key},
            timeout=5
        )
        print("✅ License server updated: -1 application")
    except:
        print("⚠️ Failed to update license server")