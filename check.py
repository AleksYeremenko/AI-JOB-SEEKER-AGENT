from DrissionPage import ChromiumPage, ChromiumOptions
import time

co = ChromiumOptions()
co.headless(True)
co.set_argument('--disable-blink-features=AutomationControlled')

try:
    page = ChromiumPage(co)
    page.get('https://djinni.co/jobs/?all-keywords=python&exp_level=1y')
    time.sleep(5)
    
    # print inner HTML of the first job item
    inner_html = page.run_js("return document.querySelector('.job-item').innerHTML;")
    with open('output.txt', 'w', encoding='utf-8') as f:
        f.write(inner_html)

except Exception as e:
    print(e)
finally:
    try:
        page.quit()
    except:
        pass
