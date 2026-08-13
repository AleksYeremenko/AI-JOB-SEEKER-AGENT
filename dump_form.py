import time
import sys
from DrissionPage import ChromiumPage, ChromiumOptions

sys.stdout.reconfigure(encoding='utf-8')

def dump_form():
    print("Открываю страницу для дампа...")
    co = ChromiumOptions()
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_user_data_path(r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\Chrome_Profile")
    page = ChromiumPage(co)
    
    page.get("https://justjoin.it/job-offer/wavestone-poland-ifs-technical-consultant-gliwice-erp")
    time.sleep(4)
    
    # Кликаем Аплай
    apply_btn = page.ele('@@data-test-id=button-apply', timeout=5)
    if not apply_btn:
        apply_btn = page.ele('tag:button@@text():Aplikuj', timeout=3)
    if not apply_btn:
        apply_btn = page.ele('tag:button@@text():Apply', timeout=3)
    if apply_btn:
        try:
            apply_btn.click()
        except:
            apply_btn.click(by_js=True)
        time.sleep(3)
        
        # Дампим все инпуты
        inputs = page.eles('tag:input')
        textareas = page.eles('tag:textarea')
        
        with open("justjoin_form_dump.txt", "w", encoding="utf-8") as f:
            f.write("=== INPUTS ===\n")
            for inp in inputs:
                f.write(f"Type: {inp.attr('type')} | Name: {inp.attr('name')} | Placeholder: {inp.attr('placeholder')} | Class: {inp.attr('class')}\n")
            f.write("\n=== TEXTAREAS ===\n")
            for txt in textareas:
                f.write(f"Name: {txt.attr('name')} | Placeholder: {txt.attr('placeholder')} | Class: {txt.attr('class')}\n")
                
        print("✅ Форма сдамплена в justjoin_form_dump.txt")
    else:
        print("❌ Кнопка Apply не найдена")
    
    page.quit()

if __name__ == "__main__":
    dump_form()
