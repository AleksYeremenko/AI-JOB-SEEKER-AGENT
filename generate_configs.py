"""
Запусти этот скрипт ОДИН РАЗ:
    python generate_configs.py
Он создаст папку Appliers/site_configs/ и положит туда все 50 JSON-конфигов.
"""
import json
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "Appliers", "site_configs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# ШАБЛОН ПОЛЕЙ (используется почти везде)
# ============================================================
COMMON_FIELDS = {
    "first_name": ['input[name*="first" i]', 'input[autocomplete="given-name"]'],
    "last_name":  ['input[name*="last" i]',  'input[autocomplete="family-name"]'],
    "full_name":  ['input[name*="name" i]',  'input[formcontrolname*="name" i]'],
    "email":      ['input[type="email"]',    'input[name*="email" i]'],
    "phone":      ['input[type="tel"]',      'input[name*="phone" i]', 'input[name*="telefon" i]'],
    "linkedin":   ['input[name*="linkedin" i]', 'input[name*="github" i]', 'input[type="url"]'],
    "cv_file":    ['input[type="file"]'],
}

COMMON_LABELS = {000
    "full_name":  r"imię|imie|name|first",
    "first_name": r"imię|imie|first",
    "last_name":  r"nazwisko|last|surname",
    "email":      r"e-?mail",
    "phone":      r"telefon|phone|tel",
    "linkedin":   r"linkedin|github|url|portfolio",
}

COMMON_SUCCESS = {
    "url_contains": ["success", "thank", "dzieki", "confirmation", "applied"],
    "text_visible":  ["Dziękujemy", "Thank you", "Application sent", "Successfully applied", "Wysłano"]
}

ATS_BLACKLIST = [
    "workday", "taleo", "successfactors", "icims", "brassring",
    "myworkdayjobs", "smartrecruiters", "greenhouse.io", "lever.co",
    "breezy.hr", "ashbyhq.com", "workable.com", "bamboohr.com", "applytojob.com"
]

def make(site_name, base_url, url_patterns=None, search_url="", scraper_type="html",
         job_link_selector="a", title_selector="h3", company_selector="h4",
         apply_button="button:has-text('Apply'):visible, button:has-text('Aplikuj'):visible",
         opens_new_tab=False, special_handling=None,
         has_mat_checkboxes=False, use_form_scanner=True,
         extra_fields=None, extra_labels=None,
         submit_button=None, success=None,
         initial_wait=3, region="GLOBAL", active=True, note=""):
    fields = {**COMMON_FIELDS, **(extra_fields or {})}
    labels = {**COMMON_LABELS, **(extra_labels or {})}
    return {
        "site_name": site_name,
        "base_url": base_url,
        "url_patterns": url_patterns or [base_url.replace("https://", "")],
        "region": region,
        "active": active,
        "note": note,
        "scraper": {
            "type": scraper_type,
            "search_url": search_url,
            "job_link_selector": job_link_selector,
            "title_selector": title_selector,
            "company_selector": company_selector,
            "max_jobs": 150,
        },
        "applier": {
            "apply_button": apply_button,
            "opens_new_tab": opens_new_tab,
            "ats_blacklist": ATS_BLACKLIST,
            "special_handling": special_handling or [],
            "has_mat_checkboxes": has_mat_checkboxes,
            "use_form_scanner": use_form_scanner,
            "initial_wait": initial_wait,
            "fields": fields,
            "field_labels": labels,
            "submit_button": submit_button or "button[type='submit'], button:has-text('Wyślij'), button:has-text('Send'), button:has-text('Aplikuj'), button:has-text('Apply')",
            "success_signals": success or COMMON_SUCCESS,
        }
    }

# ============================================================
# ВСЕ 50 САЙТОВ
# ============================================================
SITES = [

    # ============================================================
    # ПОЛЬША (6 — уже работают)
    # ============================================================
    make(
        "JustJoin",
        "https://justjoin.it",
        search_url="https://justjoin.it/job-offers/all-locations/{keyword}",
        scraper_type="html",
        job_link_selector="a[href*='/job-offer/']",
        title_selector="h2",
        company_selector="span.css-1rlbqez",
        apply_button="button:has-text('Apply'):visible, button:has-text('Aplikuj'):visible",
        opens_new_tab=True,
        has_mat_checkboxes=True,
        region="PL", active=True,
        note="Если открывается новая вкладка — чаще всего внешняя ATS"
    ),

    make(
        "Pracuj",
        "https://www.pracuj.pl",
        url_patterns=["pracuj.pl"],
        search_url="https://www.pracuj.pl/praca/{keyword};kw",
        scraper_type="html",
        job_link_selector="[data-test='offer-link']",
        title_selector="[data-test='offer-title']",
        company_selector="[data-test='text-company-name']",
        apply_button="[data-test='button-apply'], button:has-text('Aplikuj')",
        opens_new_tab=True,
        special_handling=[
            {
                "type": "click_modal",
                "selector": "button:has-text('Kontynuuj aplikowanie'), a:has-text('Kontynuuj aplikowanie')",
                "label": "Kontynuuj aplikowanie"
            },
            {
                "type": "wait_login",
                "url_trigger": "login.pracuj.pl",
                "timeout_sec": 120
            },
            {
                "type": "replace_cv",
                "change_selector": "button:has-text('zmień lub odrzuć plik'), [data-test='button-change-cv']",
                "add_selector": "button:has-text('Dodaj nowe CV'), button:has-text('Wgraj nowy plik')"
            }
        ],
        region="PL", active=True,
    ),

    make(
        "NoFluffJobs",
        "https://nofluffjobs.com",
        search_url="https://nofluffjobs.com/pl/jobs?criteria=requirement%3D{keyword}",
        job_link_selector="a[href*='/pl/job/']",
        title_selector="h3",
        company_selector="[data-cy='company-name']",
        opens_new_tab=True,
        region="PL", active=True,
    ),

    make(
        "Bulldogjob",
        "https://bulldogjob.pl",
        search_url="https://bulldogjob.pl/companies/jobs?q={keyword}",
        job_link_selector="a.JobCard_container",
        title_selector="h2",
        company_selector=".JobCard_companyName",
        region="PL", active=True,
    ),

    make(
        "TheProtocol",
        "https://theprotocol.it",
        search_url="https://theprotocol.it/filtry/{keyword};kw?sort=date",
        job_link_selector="a[href*='/szczegoly/oferta/']",
        title_selector="h2",
        company_selector="[data-test='text-companyName']",
        region="PL", active=True,
    ),

    make(
        "SolidJobs",
        "https://solid.jobs",
        search_url="https://solid.jobs/offers/it;search={keyword}",
        job_link_selector="a.offer-title",
        title_selector="a.offer-title",
        company_selector="a.company-name",
        region="PL", active=True,
    ),

    # ============================================================
    # ГЛОБАЛЬНЫЕ API (уже работают)
    # ============================================================
    make(
        "Remotive",
        "https://remotive.com",
        search_url="https://remotive.com/api/remote-jobs?search={keyword}",
        scraper_type="api",
        region="GLOBAL", active=True,
    ),

    make(
        "RemoteOK",
        "https://remoteok.com",
        search_url="https://remoteok.com/api?tag={keyword}",
        scraper_type="api",
        region="GLOBAL", active=True,
    ),

    make(
        "WorkingNomads",
        "https://www.workingnomads.com",
        search_url="https://www.workingnomads.com/api/exposed_jobs/",
        scraper_type="api",
        region="GLOBAL", active=True,
    ),

    # ============================================================
    # ЕВРОПА — DACH
    # ============================================================
    make(
        "Stepstone",
        "https://www.stepstone.de",
        search_url="https://www.stepstone.de/jobs/{keyword}",
        job_link_selector="article.js-job-item a",
        title_selector=".listing-item__title",
        company_selector=".listing-item__company",
        opens_new_tab=True,
        region="DE", active=False,
        note="№1 в Германии. Требует аккаунт для подачи."
    ),

    make(
        "Xing",
        "https://www.xing.com",
        search_url="https://www.xing.com/jobs/search?keywords={keyword}",
        job_link_selector="a[data-xinglet='job-search-result-job-detail']",
        title_selector=".job-title",
        company_selector=".company-name",
        opens_new_tab=True,
        region="DACH", active=False,
        note="Главный конкурент LinkedIn в DACH. Требует аккаунт."
    ),

    make(
        "SwissDevJobs",
        "https://swissdevjobs.ch",
        search_url="https://swissdevjobs.ch/jobs/{keyword}",
        job_link_selector="a.job-title-link",
        title_selector="h2.job-title",
        company_selector=".company-name",
        region="CH", active=False,
        note="Швейцария, очень высокие ЗП."
    ),

    # ============================================================
    # ЕВРОПА — UK
    # ============================================================
    make(
        "Reed",
        "https://www.reed.co.uk",
        search_url="https://www.reed.co.uk/jobs/{keyword}-jobs",
        job_link_selector="article.job-result a.job-result-heading__title",
        title_selector=".job-result-heading__title",
        company_selector=".job-result-heading__employer",
        opens_new_tab=True,
        region="UK", active=False,
        note="Огромный борд в UK."
    ),

    make(
        "CWJobs",
        "https://www.cwjobs.co.uk",
        search_url="https://www.cwjobs.co.uk/jobs/{keyword}",
        job_link_selector="article a.job-title",
        title_selector=".job-title",
        company_selector=".company",
        region="UK", active=False,
    ),

    make(
        "TechnoJobs",
        "https://www.technojobs.co.uk",
        search_url="https://www.technojobs.co.uk/search-jobs/{keyword}.phtml",
        job_link_selector="a.job-link",
        title_selector="h2",
        company_selector=".company",
        region="UK", active=False,
    ),

    make(
        "DevITJobs",
        "https://devitjobs.com",
        search_url="https://devitjobs.com/jobs?search={keyword}",
        job_link_selector="a.job-item",
        title_selector="h3",
        company_selector=".company-name",
        region="UK/US", active=False,
    ),

    # ============================================================
    # ВОСТОЧНАЯ ЕВРОПА
    # ============================================================
    make(
        "Djinni",
        "https://djinni.co",
        search_url="https://djinni.co/jobs/?primary_keyword={keyword}",
        job_link_selector="a.job-list-item__link",
        title_selector=".job-list-item__title",
        company_selector=".company-name",
        region="UA/EU", active=False,
        note="№1 анонимный поиск Восточная Европа"
    ),

    make(
        "DOU",
        "https://jobs.dou.ua",
        search_url="https://jobs.dou.ua/vacancies/?category={keyword}",
        job_link_selector="a.vt",
        title_selector=".title",
        company_selector=".company",
        region="UA", active=False,
        note="Главный IT-портал Украины"
    ),

    # ============================================================
    # УДАЛЁНКА
    # ============================================================
    make(
        "WeWorkRemotely",
        "https://weworkremotely.com",
        search_url="https://weworkremotely.com/remote-jobs/search?term={keyword}",
        job_link_selector="article ul li a:not(.company)",
        title_selector="span.title",
        company_selector="span.company",
        opens_new_tab=True,
        region="GLOBAL", active=True,
    ),

    make(
        "Jobspresso",
        "https://jobspresso.co",
        search_url="https://jobspresso.co/remote-software-engineering-jobs/",
        job_link_selector="a.job_listing-clickbox",
        title_selector=".position",
        company_selector=".company",
        region="GLOBAL", active=True,
    ),

    make(
        "RemoteCo",
        "https://remote.co",
        search_url="https://remote.co/remote-jobs/developer/?search_keywords={keyword}",
        job_link_selector="a.card-title-link",
        title_selector=".card-title",
        company_selector=".card-subtitle",
        region="GLOBAL", active=False,
    ),

    make(
        "JustRemote",
        "https://justremote.co",
        search_url="https://justremote.co/remote-developer-jobs?search={keyword}",
        job_link_selector="a.position",
        title_selector=".position",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "DailyRemote",
        "https://dailyremote.com",
        search_url="https://dailyremote.com/remote-jobs?q={keyword}",
        job_link_selector="a.card",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "SkipTheDrive",
        "https://www.skipthedrive.com",
        search_url="https://www.skipthedrive.com/?s={keyword}",
        job_link_selector="a.job-title",
        title_selector="h2",
        company_selector=".company-name",
        region="GLOBAL", active=False,
    ),

    make(
        "Jobgether",
        "https://jobgether.com",
        search_url="https://jobgether.com/offer?search={keyword}",
        job_link_selector="a.job-title",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "Crossover",
        "https://www.crossover.com",
        search_url="https://www.crossover.com/jobs?q={keyword}",
        job_link_selector="a.job-card",
        title_selector="h3",
        company_selector=".company",
        scraper_type="api",
        region="GLOBAL", active=False,
        note="Специфичный найм топовых разрабов удалённо"
    ),

    make(
        "Flexiple",
        "https://flexiple.com",
        search_url="https://flexiple.com/developer/jobs",
        job_link_selector="a.job-link",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "Turing",
        "https://www.turing.com",
        search_url="https://www.turing.com/jobs",
        job_link_selector="a.job-card",
        title_selector="h3",
        company_selector=".company",
        scraper_type="api",
        region="GLOBAL", active=False,
        note="Удалёнка в Кремниевой долине"
    ),

    # ============================================================
    # TECH-ФОКУС И СТАРТАПЫ
    # ============================================================
    make(
        "BuiltIn",
        "https://builtin.com",
        url_patterns=["builtin.com"],
        search_url="https://builtin.com/jobs/dev-engineering?search={keyword}",
        job_link_selector="a[data-id='job-card-alias']",
        title_selector=".job-title",
        company_selector=".company-title",
        opens_new_tab=True,
        region="US", active=False,
        note="Сеть хабов: NYC, SF, Austin и т.д."
    ),

    make(
        "AngelList",
        "https://wellfound.com",
        url_patterns=["wellfound.com", "angel.co"],
        search_url="https://wellfound.com/jobs?q={keyword}",
        job_link_selector="a.job-link",
        title_selector="h2",
        company_selector=".company",
        opens_new_tab=True,
        region="GLOBAL", active=False,
        note="AngelList переехал на Wellfound"
    ),

    make(
        "AuthenticJobs",
        "https://authenticjobs.com",
        search_url="https://authenticjobs.com/?search={keyword}",
        job_link_selector="a.listing-title",
        title_selector=".listing-title",
        company_selector=".listing-company",
        region="GLOBAL", active=False,
        note="Дизайн и веб-разработка"
    ),

    make(
        "HoneypotEU",
        "https://www.honeypot.io",
        search_url="https://app.honeypot.io/profile/jobs",
        job_link_selector="a.JobCard",
        title_selector="h3",
        company_selector=".company",
        region="EU", active=False,
        note="Реверсивный поиск — компании пишут тебе"
    ),

    make(
        "Braintrust",
        "https://app.usebraintrust.com",
        search_url="https://app.usebraintrust.com/jobs/?search={keyword}",
        scraper_type="api",
        job_link_selector="a.job-card",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=False,
        note="Web3 фриланс/фуллтайм сеть"
    ),

    make(
        "GunIO",
        "https://www.gun.io",
        search_url="https://www.gun.io/find-work",
        scraper_type="api",
        job_link_selector="a.job",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=False,
        note="Элитные разработчики"
    ),

    make(
        "HackerRankJobs",
        "https://www.hackerrank.com",
        search_url="https://www.hackerrank.com/jobs/search?q={keyword}",
        scraper_type="api",
        job_link_selector="a.job-card",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    # ============================================================
    # КРУПНЫЕ АГРЕГАТОРЫ
    # ============================================================
    make(
        "Monster",
        "https://www.monster.com",
        search_url="https://www.monster.com/jobs/search?q={keyword}&where=remote",
        job_link_selector="a.job-cardstyle__JobCardComponent",
        title_selector=".job-cardstyle__JobCardTitle",
        company_selector=".job-cardstyle__CompanyName",
        opens_new_tab=True,
        region="US/GLOBAL", active=False,
    ),

    make(
        "ZipRecruiter",
        "https://www.ziprecruiter.com",
        search_url="https://www.ziprecruiter.com/jobs-search?search={keyword}&location=Remote",
        job_link_selector="article.job_result a.job_link",
        title_selector=".job_title",
        company_selector=".company_name",
        opens_new_tab=True,
        region="US", active=False,
    ),

    make(
        "CareerBuilder",
        "https://www.careerbuilder.com",
        search_url="https://www.careerbuilder.com/jobs?keywords={keyword}",
        job_link_selector="a.data-results-content",
        title_selector=".show-for-medium-up",
        company_selector=".data-results-company",
        opens_new_tab=True,
        region="US", active=False,
    ),

    make(
        "Jooble",
        "https://jooble.org",
        search_url="https://jooble.org/SearchResult?ukw={keyword}",
        job_link_selector="article a.vac_title",
        title_selector=".vac_title",
        company_selector=".company-name",
        opens_new_tab=True,
        region="GLOBAL", active=False,
        note="Агрегатор, работает в 70 странах"
    ),

    make(
        "Adzuna",
        "https://www.adzuna.co.uk",
        search_url="https://www.adzuna.co.uk/search?q={keyword}&w=remote",
        job_link_selector="article.result a",
        title_selector="h2",
        company_selector=".company",
        opens_new_tab=True,
        region="UK/GLOBAL", active=False,
    ),

    make(
        "SimplyHired",
        "https://www.simplyhired.com",
        search_url="https://www.simplyhired.com/search?q={keyword}&l=remote",
        job_link_selector="a[data-mdz='job']",
        title_selector=".SerpJob-title",
        company_selector=".SerpJob-company",
        opens_new_tab=True,
        region="US", active=False,
    ),

    make(
        "TalentCom",
        "https://www.talent.com",
        search_url="https://www.talent.com/jobs?k={keyword}&l=remote",
        job_link_selector="a.card__job-title",
        title_selector=".card__job-title",
        company_selector=".card__company-name",
        opens_new_tab=True,
        region="GLOBAL", active=False,
    ),

    # ============================================================
    # УЗКИЕ НИШИ
    # ============================================================
    make(
        "RubyNow",
        "https://jobs.rubynow.com",
        search_url="https://jobs.rubynow.com",
        job_link_selector="a.job-title",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=False,
        note="Ruby/Rails вакансии"
    ),

    make(
        "PythonOrg",
        "https://www.python.org/jobs",
        search_url="https://www.python.org/jobs/",
        job_link_selector="li.job-listing h2 a",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "VueJobs",
        "https://vuejobs.com",
        search_url="https://vuejobs.com/jobs?q={keyword}",
        job_link_selector="a.job",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "ReactJobs",
        "https://reactjobs.us",
        search_url="https://reactjobs.us",
        job_link_selector="a.job-title",
        title_selector="h3",
        company_selector=".company",
        region="US/GLOBAL", active=False,
    ),

    make(
        "LaraJobs",
        "https://larajobs.com",
        search_url="https://larajobs.com",
        job_link_selector="a.job-item",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=False,
        note="Laravel/PHP"
    ),

    make(
        "GolangProjects",
        "https://www.golangprojects.com",
        search_url="https://www.golangprojects.com/golang-go-jobs.html",
        job_link_selector="a.position-link",
        title_selector="h2",
        company_selector=".company-title",
        region="GLOBAL", active=False,
    ),

    make(
        "UXDesignJobs",
        "https://www.uxdesignjobs.net",
        search_url="https://www.uxdesignjobs.net",
        job_link_selector="a.job-title",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    # ============================================================
    # AI / ML / WEB3
    # ============================================================
    make(
        "AIjobs",
        "https://aijobs.net",
        search_url="https://aijobs.net/jobs/?q={keyword}",
        job_link_selector="a.job-title",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "MachineLearningJobs",
        "https://machinelearningjobs.com",
        search_url="https://machinelearningjobs.com",
        job_link_selector="a.listing",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=False,
    ),

    make(
        "Web3Career",
        "https://web3.career",
        search_url="https://web3.career/{keyword}-jobs",
        job_link_selector="a[href*='/web3-jobs/']",
        title_selector="h2",
        company_selector=".company-name",
        region="GLOBAL", active=False,
    ),

    make(
        "CryptoJobs",
        "https://crypto.jobs",
        search_url="https://crypto.jobs/?search={keyword}",
        job_link_selector="a.job-url",
        title_selector="h3",
        company_selector=".company",
        region="GLOBAL", active=True,
    ),

    # ============================================================
    # АЗИЯ / ИНДИЯ
    # ============================================================
    make(
        "Naukri",
        "https://www.naukri.com",
        search_url="https://www.naukri.com/{keyword}-jobs",
        job_link_selector="a.title",
        title_selector=".title",
        company_selector=".comp-name",
        opens_new_tab=True,
        region="IN", active=False,
        note="Монополист в Индии"
    ),

    make(
        "InstaHyre",
        "https://www.instahyre.com",
        search_url="https://www.instahyre.com/jobs/{keyword}/",
        job_link_selector="a.job-title",
        title_selector="h2",
        company_selector=".company-name",
        region="IN", active=False,
        note="Топовые IT стартапы Индии"
    ),

    # ============================================================
    # ЕЩЁ ГЛОБАЛЬНЫЕ БОРДЫ
    # ============================================================
    make(
        "BerlinStartupJobs",
        "https://berlinstartupjobs.com",
        search_url="https://berlinstartupjobs.com/engineering/",
        job_link_selector=".bjs-jl-title a",
        title_selector=".bjs-jl-title",
        company_selector=".bjs-jl-company",
        region="DE", active=True,
    ),

    make(
        "EuroTechJobs",
        "https://www.eurotechjobs.com",
        search_url="https://www.eurotechjobs.com/jobs/{keyword}",
        job_link_selector="a.jobTitle",
        title_selector=".jobTitle",
        company_selector=".company",
        region="EU", active=True,
    ),

    make(
        "SiliconCanals",
        "https://jobs.siliconcanals.com",
        search_url="https://jobs.siliconcanals.com/jobs?q={keyword}",
        job_link_selector="a.job-link",
        title_selector="h3",
        company_selector=".company",
        region="EU", active=True,
    ),

    make(
        "NoDesk",
        "https://nodesk.co",
        search_url="https://nodesk.co/remote-jobs/engineering/",
        job_link_selector="a.job-card",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=True,
    ),

    make(
        "TheHub",
        "https://thehub.io",
        search_url="https://thehub.io/jobs?roles=backenddeveloper",
        job_link_selector="a.card-job-find-list__link",
        title_selector="h3",
        company_selector=".company",
        region="EU", active=True,
    ),

    make(
        "Climatebase",
        "https://climatebase.org",
        search_url="https://climatebase.org/jobs?q={keyword}",
        job_link_selector="a.list_card",
        title_selector="h2",
        company_selector=".company",
        region="GLOBAL", active=True,
    ),

    make(
        "TechInAsia",
        "https://www.techinasia.com",
        search_url="https://www.techinasia.com/jobs/search?query={keyword}",
        job_link_selector="a.job-title",
        title_selector="h2",
        company_selector=".company",
        region="ASIA", active=False,
    ),
]

# ============================================================
# ЗАПИСЬ ФАЙЛОВ
# ============================================================
for site in SITES:
    fname = site["site_name"].lower().replace(" ", "_").replace(".", "_") + ".json"
    fpath = os.path.join(OUTPUT_DIR, fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(site, f, ensure_ascii=False, indent=2)

print(f"✅ Создано {len(SITES)} конфигов в {OUTPUT_DIR}")

# ============================================================
# ПЕЧАТАЕМ СВОДКУ
# ============================================================
active = [s for s in SITES if s["active"]]
inactive = [s for s in SITES if not s["active"]]
regions = {}
for s in SITES:
    r = s["region"]
    regions[r] = regions.get(r, 0) + 1

print(f"\n📊 ИТОГО:")
print(f"   Всего сайтов:   {len(SITES)}")
print(f"   Активных:       {len(active)}")
print(f"   Выключенных:    {len(inactive)}")
print(f"\n🌍 По регионам:")
for r, c in sorted(regions.items()):
    print(f"   {r}: {c}")

print(f"\n✅ Активные прямо сейчас:")
for s in active:
    print(f"   [{s['region']:8}] {s['site_name']}")

print(f"\n💤 Включить позже (активировать в JSON: active: true):")
for s in inactive:
    note = f"  — {s['note']}" if s.get("note") else ""
    print(f"   [{s['region']:8}] {s['site_name']}{note}")
