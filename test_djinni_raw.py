import os
from DrissionPage import ChromiumPage, ChromiumOptions
import time

def main():
    co = ChromiumOptions()
    co.set_user_data_path(os.path.abspath("Data/job_boards_profile"))
    co.headless(True)
    page = ChromiumPage(co)
    page.get("https://djinni.co/jobs/?all-keywords=Python")
    time.sleep(3)
    
    html = page.html
    with open("djinni_dump.html", "w", encoding="utf-8") as f:
        f.write(html)
        
    print("HTML saved to djinni_dump.html")
    page.quit()

if __name__ == "__main__":
    main()
