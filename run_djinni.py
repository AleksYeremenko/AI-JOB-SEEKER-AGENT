import time; import os; from DrissionPage import ChromiumPage, ChromiumOptions
co = ChromiumOptions()
co.set_user_data_path(os.path.abspath('Data/job_boards_profile'))
co.headless(True)
page = ChromiumPage(co)
page.get('https://djinni.co/jobs/843124-lead-support/')
time.sleep(3)
alert=page.ele('#ua_abroad_alert')
if alert:
    alert.ele('tag:a').click(by_js=True)
time.sleep(3)
btn=page.ele('text:Apply')
if btn:
    btn.click(by_js=True)
time.sleep(3)
open('djinni_modal2.html', 'w', encoding='utf-8').write(page.html)
page.quit()
