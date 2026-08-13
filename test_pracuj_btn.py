from DrissionPage import ChromiumOptions, ChromiumPage
import time

co = ChromiumOptions()
co.headless(False)
co.set_argument('--disable-blink-features=AutomationControlled')

page = ChromiumPage(co)
page.get('https://www.pracuj.pl/praca/junior-java-developer-warszawa-zwirki-i-wigury-16a,oferta,1004966592')
time.sleep(5)

buttons = page.eles('tag:button')
links = page.eles('tag:a')
print("--- BUTTONS ---")
for b in buttons:
    try:
        if b.text.strip(): print(f"BTN: {b.text.strip()}")
    except: pass
print("--- LINKS ---")
for l in links:
    try:
        text = l.text.strip()
        if "aplikuj" in text.lower() or "apply" in text.lower() or "kontynuuj" in text.lower():
            print(f"LINK MATCH: {text}")
    except: pass

page.quit()
