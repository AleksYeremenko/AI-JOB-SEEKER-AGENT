import sys
sys.stdout.reconfigure(encoding='utf-8')
from Scraping.djinni_scraper import scrape_djinni

jobs = scrape_djinni('python')
print("FOUND:", len(jobs))
if jobs:
    print(jobs[0])
