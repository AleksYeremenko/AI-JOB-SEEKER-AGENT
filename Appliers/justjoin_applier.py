import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except:
    pass

import time
import re
import sys
import os
import random
from faker import Faker

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from base_applier import BaseApplier
except ImportError:
    from Appliers.base_applier import BaseApplier


class JustJoinApplier(BaseApplier):

    def apply_advanced_stealth(self, page):
        """Продвинутая маскировка - имитация реального браузера"""
        fake = Faker()

        page.add_init_script("""
            // Удаляем все следы автоматизации
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Чистим playwright/puppeteer следы
            delete window.__playwright;
            delete window.__puppeteer;
            delete window.playwright;
            delete window.puppeteer;
            delete window.__firefox__;
            delete window.__nightmare;
            delete window._Selenium_IDE_Recorder;
            delete window._phantom;
            delete window.callPhantom;
            delete window.__webdriver_script_fn;

            // Chrome API
            window.chrome = {
                app: {
                    isInstalled: false,
                    InstallState: {
                        DISABLED: 'disabled',
                        INSTALLED: 'installed',
                        NOT_INSTALLED: 'not_installed'
                    },
                    RunningState: {
                        CANNOT_RUN: 'cannot_run',
                        READY_TO_RUN: 'ready_to_run',
                        RUNNING: 'running'
                    }
                },
                runtime: {
                    OnInstalledReason: {
                        CHROME_UPDATE: 'chrome_update',
                        INSTALL: 'install',
                        SHARED_MODULE_UPDATE: 'shared_module_update',
                        UPDATE: 'update'
                    },
                    OnRestartRequiredReason: {
                        APP_UPDATE: 'app_update',
                        OS_UPDATE: 'os_update',
                        PERIODIC: 'periodic'
                    },
                    PlatformArch: {
                        ARM: 'arm',
                        ARM64: 'arm64',
                        MIPS: 'mips',
                        MIPS64: 'mips64',
                        X86_32: 'x86-32',
                        X86_64: 'x86-64'
                    },
                    PlatformNaclArch: {
                        ARM: 'arm',
                        MIPS: 'mips',
                        MIPS64: 'mips64',
                        X86_32: 'x86-32',
                        X86_64: 'x86-64'
                    },
                    PlatformOs: {
                        ANDROID: 'android',
                        CROS: 'cros',
                        LINUX: 'linux',
                        MAC: 'mac',
                        OPENBSD: 'openbsd',
                        WIN: 'win'
                    },
                    RequestUpdateCheckStatus: {
                        NO_UPDATE: 'no_update',
                        THROTTLED: 'throttled',
                        UPDATE_AVAILABLE: 'update_available'
                    }
                },
                loadTimes: function() {
                    return {
                        commitLoadTime: Date.now() / 1000 - Math.random() * 2,
                        connectionInfo: 'h2',
                        finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
                        finishLoadTime: Date.now() / 1000 - Math.random() * 0.5,
                        firstPaintAfterLoadTime: 0,
                        firstPaintTime: Date.now() / 1000 - Math.random() * 2,
                        navigationType: 'Other',
                        npnNegotiatedProtocol: 'h2',
                        requestTime: Date.now() / 1000 - Math.random() * 3,
                        startLoadTime: Date.now() / 1000 - Math.random() * 2.5,
                        wasAlternateProtocolAvailable: false,
                        wasFetchedViaSpdy: true,
                        wasNpnNegotiated: true
                    };
                },
                csi: function() {
                    return {
                        startE: Date.now() - Math.random() * 1000,
                        onloadT: Date.now() - Math.random() * 500,
                        pageT: Date.now() - Math.random() * 300
                    };
                }
            };

            // Vendor
            Object.defineProperty(navigator, 'vendor', {
                get: () => 'Google Inc.'
            });

            // Languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en', 'pl-PL', 'pl']
            });

            // Platform
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32'
            });

            // Hardware Concurrency (реальное значение)
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => 8
            });

            // Device Memory
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => 8
            });

            // WebGL - реальный рендерер
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) return 'Intel Inc.';
                if (parameter === 37446) return 'Intel(R) UHD Graphics 620';
                return getParameter.apply(this, arguments);
            };

            // Permissions API
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // Plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    {
                        0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                        description: "Portable Document Format",
                        filename: "internal-pdf-viewer",
                        length: 1,
                        name: "Chrome PDF Plugin"
                    },
                    {
                        0: {type: "application/pdf", suffixes: "pdf", description: ""},
                        description: "",
                        filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                        length: 1,
                        name: "Chrome PDF Viewer"
                    },
                    {
                        0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                        1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                        description: "",
                        filename: "internal-nacl-plugin",
                        length: 2,
                        name: "Native Client"
                    }
                ]
            });

            // Battery API
            Object.defineProperty(navigator, 'getBattery', {
                get: () => () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 0.85 + Math.random() * 0.14,
                    addEventListener: () => {},
                    removeEventListener: () => {},
                    dispatchEvent: () => true
                })
            });

            // Max Touch Points
            Object.defineProperty(navigator, 'maxTouchPoints', {
                get: () => 0
            });

            // Connection (реалистичный)
            Object.defineProperty(navigator, 'connection', {
                get: () => ({
                    effectiveType: '4g',
                    rtt: 50,
                    downlink: 10,
                    saveData: false
                })
            });

            // Screen (реальные значения)
            Object.defineProperty(window.screen, 'width', {
                get: () => 1920
            });
            Object.defineProperty(window.screen, 'height', {
                get: () => 1080
            });
            Object.defineProperty(window.screen, 'availWidth', {
                get: () => 1920
            });
            Object.defineProperty(window.screen, 'availHeight', {
                get: () => 1040
            });
            Object.defineProperty(window.screen, 'colorDepth', {
                get: () => 24
            });
            Object.defineProperty(window.screen, 'pixelDepth', {
                get: () => 24
            });

            // Замена Date для реалистичности
            const originalDate = Date;
            Date = class extends originalDate {
                getTimezoneOffset() {
                    return -120; // UTC+2 (Poland)
                }
            };
            Date.prototype = originalDate.prototype;

            // Canvas fingerprinting protection
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {
                const context = this.getContext('2d');
                if (context) {
                    const imageData = context.getImageData(0, 0, this.width, this.height);
                    // Добавляем микро-шум в пиксели
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.floor(Math.random() * 2);
                    }
                    context.putImageData(imageData, 0, 0);
                }
                return originalToDataURL.apply(this, arguments);
            };

            // WebRTC IP leak protection
            const originalRTCPeerConnection = window.RTCPeerConnection;
            window.RTCPeerConnection = function(...args) {
                const pc = new originalRTCPeerConnection(...args);
                const originalCreateDataChannel = pc.createDataChannel;
                pc.createDataChannel = function() {
                    return originalCreateDataChannel.apply(this, arguments);
                };
                return pc;
            };

            // Mouse/Touch event timing (реалистичность)
            let lastEventTime = Date.now();
            ['mousedown', 'mouseup', 'click', 'touchstart', 'touchend'].forEach(eventType => {
                document.addEventListener(eventType, () => {
                    const now = Date.now();
                    const timeDiff = now - lastEventTime;
                    if (timeDiff < 10) {
                        console.warn('Suspiciously fast events');
                    }
                    lastEventTime = now;
                }, true);
            });

            console.log('✅ Advanced stealth applied');
        """)

    def human_type(self, element, text, min_delay=100, max_delay=250):
        """Более реалистичный набор текста"""
        for char in text:
            delay = random.randint(min_delay, max_delay)
            # Иногда делаем паузы как будто думаем
            if random.random() < 0.08:
                delay = random.randint(400, 900)
            element.type(char, delay=delay)

    def human_click(self, element):
        """Более реалистичный клик с микро-паузами"""
        box = element.bounding_box()
        if box:
            # Клик в случайную точку внутри элемента (не в центр)
            x = box['x'] + random.uniform(box['width'] * 0.2, box['width'] * 0.8)
            y = box['y'] + random.uniform(box['height'] * 0.2, box['height'] * 0.8)
            element.hover()
            time.sleep(random.uniform(0.2, 0.5))
            element.click(position={'x': box['width'] * 0.5, 'y': box['height'] * 0.5})
            time.sleep(random.uniform(0.3, 0.7))
        else:
            element.click()
            time.sleep(random.uniform(0.2, 0.5))

    def natural_scroll(self, page):
        """Естественный скроллинг как человек"""
        for _ in range(random.randint(2, 4)):
            scroll_amount = random.randint(150, 400)
            page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            time.sleep(random.uniform(0.8, 1.5))
            # Иногда скроллим назад
            if random.random() < 0.3:
                page.evaluate(f"window.scrollBy(0, -{random.randint(50, 150)})")
                time.sleep(random.uniform(0.5, 1.0))

    def natural_mouse_movement(self, page):
        """Естественные движения мыши"""
        for _ in range(random.randint(3, 6)):
            x = random.randint(100, 1800)
            y = random.randint(100, 900)
            page.mouse.move(x, y)
            time.sleep(random.uniform(0.3, 0.8))

    def apply(self, page, context, job_link, cv_path, cover_letter):
        print(f"🌍 [JustJoin] : {job_link}")

        self.apply_advanced_stealth(page)
        page.goto(job_link, timeout=40000, wait_until="domcontentloaded")

        # Имитируем чтение страницы
        time.sleep(random.uniform(4, 7))
        self.natural_mouse_movement(page)
        self.natural_scroll(page)
        time.sleep(random.uniform(2, 4))

        self.kill_cookies(page)

        print("🖱️ [JustJoin]    Apply...")
        
        apply_button = None
        selectors = "button:has-text('Apply'), button:has-text('Aplikuj'), a:has-text('Apply'), a:has-text('Aplikuj'), [data-test='button-apply']"
        
        for _ in range(20): # Ждем до 10 секунд
            buttons = page.locator(selectors)
            for i in range(buttons.count()):
                btn = buttons.nth(i)
                if btn.is_visible():
                    apply_button = btn
                    break
            if apply_button:
                break
            time.sleep(0.5)

        if not apply_button:
            print("⚠️ [JustJoin]  Apply    10 !")

        target_page = page
        is_external = False

        try:
            with context.expect_page(timeout=3000) as new_page_info:
                self.human_click(apply_button)

            target_page = new_page_info.value
            is_external = True
            print(f"🛑 [JustJoin] :  ATS! ({target_page.url})")

            self.apply_advanced_stealth(target_page)

            MONSTER_ATS = ['workday', 'taleo', 'successfactors', 'icims', 'brassring', 'myworkdayjobs']
            if any(monster in target_page.url.lower() for monster in MONSTER_ATS):
                print("☠️ [JustJoin]  ATS. .")
                return "Manual Apply Required"

            target_page.wait_for_load_state("domcontentloaded", timeout=20000)
            time.sleep(random.uniform(3, 5))
            self.natural_mouse_movement(target_page)

        except:
            print("✅ [JustJoin]   ,  ...")

        time.sleep(random.uniform(2, 3))
        self.kill_cookies(target_page)

        if is_external:
            try:
                secondary_apply = target_page.locator(
                    "button:has-text('Aplikuj'), a:has-text('Aplikuj'), button:has-text('Apply')"
                ).first
                if secondary_apply.is_visible(timeout=3000):
                    print("🖱️ [JustJoin]    Apply!")
                    self.human_click(secondary_apply)
                    time.sleep(random.uniform(2, 4))
                    self.kill_cookies(target_page)
            except:
                pass

        time.sleep(random.uniform(1, 3))
        print("📝 [JustJoin]  ...")

        my_first = self.profile.get("first_name", "Oleksandr")
        my_last = self.profile.get("last_name", "Yeremenko")
        my_full = f"{my_first} {my_last}"
        my_email = self.profile.get("email", "yeremenkoaleks1@gmail.com")
        my_phone = self.profile.get("phone", "+48516478223")
        my_linkedin = self.profile.get("linkedin", "https://github.com/AleksYeremenko")

        smart_fields = {
            "Имя / Full Name": {
                "val": my_full,
                "css": [
                    'input[name*="first" i]',
                    'input[name*="name" i]',
                    'input[formcontrolname*="name" i]',
                    'input[autocomplete="given-name"]',
                    'input[placeholder*="imię" i]',
                    'input[placeholder*="name" i]',
                    'xpath=//label[contains(translate(text(), "IMIĘ", "imię"), "imię")]/following::input[1]',
                    'input[type="text"]:not([readonly])'
                ]
            },
            "Email": {
                "val": my_email,
                "css": [
                    'input[type="email"]',
                    'input[name*="email" i]',
                    'input[formcontrolname*="email" i]',
                    'input[placeholder*="email" i]'
                ]
            },
            "Телефон": {
                "val": my_phone,
                "css": [
                    'input[type="tel"]',
                    'input[name*="phone" i]',
                    'input[name*="telefon" i]',
                    'input[formcontrolname*="phone" i]',
                    'input[placeholder*="phone" i]',
                    'input[placeholder*="telefon" i]',
                    'xpath=//*[contains(translate(text(), "TELEFON", "telefon"), "telefon")]/following::input[1]'
                ]
            },
            "LinkedIn/GitHub": {
                "val": my_linkedin,
                "css": [
                    'input[type="url"]',
                    'input[name*="linkedin" i]',
                    'input[name*="github" i]',
                    'input[name*="url" i]',
                    'input[placeholder*="portfolio" i]'
                ]
            },
            "Message": {
                "val": f"Hi! I'm {my_full}. Check my work: {my_linkedin}",
                "css": ['textarea', '[contenteditable="true"]']
            }
        }

        for field_name, data in smart_fields.items():
            filled = False
            regex_map = {
                "Имя / Full Name": r"imię|imie|name|first.*name",
                "Email": r"e-?mail",
                "Телефон": r"telefon|phone|tel",
                "LinkedIn/GitHub": r"linkedin|github|url|portfolio",
                "Message": r"message|wiadomość|introduce"
            }
            rx = re.compile(regex_map.get(field_name, ""), re.IGNORECASE)

            for method in [target_page.get_by_placeholder, target_page.get_by_label]:
                if filled: break
                try:
                    loc = method(rx)
                    for i in range(loc.count()):
                        el = loc.nth(i)
                        if el.is_editable() and el.is_visible():
                            el.click()
                            time.sleep(random.uniform(0.3, 0.8))
                            el.fill("")
                            time.sleep(random.uniform(0.1, 0.3))
                            self.human_type(el, data["val"])
                            print(f"✅ {field_name}")
                            filled = True
                            break
                except:
                    pass

            if filled: continue
            for css in data["css"]:
                try:
                    elements = target_page.locator(css)
                    for i in range(elements.count()):
                        el = elements.nth(i)
                        if el.is_editable() and el.is_visible():
                            el.click()
                            time.sleep(random.uniform(0.3, 0.8))
                            el.fill("")
                            time.sleep(random.uniform(0.1, 0.3))
                            self.human_type(el, data["val"])
                            print(f"✅ {field_name}")
                            filled = True
                            break
                    if filled: break
                except:
                    pass

        print("📎 [JustJoin]  CV...")
        try:
            file_inputs = target_page.locator('input[type="file"]')
            for i in range(file_inputs.count()):
                try:
                    file_input = file_inputs.nth(i)
                    if os.path.exists(cv_path):
                        file_input.set_input_files(cv_path)
                        print(f"✅")
                        time.sleep(random.uniform(1, 2))
                        break
                except:
                    continue
        except Exception as e:
            print(f"⚠️ {e}")

        print("☑️ [JustJoin] ...")
        try:
            checkboxes = target_page.locator('input[type="checkbox"]:not([checked])')
            for i in range(checkboxes.count()):
                try:
                    cb = checkboxes.nth(i)
                    if cb.is_visible():
                        time.sleep(random.uniform(0.3, 0.7))
                        cb.check(force=True, timeout=1000)
                except:
                    pass
        except:
            pass

        try:
            mat_checkboxes = target_page.locator('mat-checkbox:not(.mat-checkbox-checked)')
            for i in range(mat_checkboxes.count()):
                try:
                    time.sleep(random.uniform(0.4, 0.9))
                    mat_checkboxes.nth(i).click(force=True, timeout=1000)
                except:
                    pass
        except:
            pass

        # Пробуем открыть поле 'Message', если оно спрятано под кнопкой
        try:
            msg_btn = target_page.locator("button:has-text('Wiadomość'), button:has-text('Message'), button:has-text('Introduce')").first
            if msg_btn.is_visible(timeout=1000):
                self.human_click(msg_btn)
                time.sleep(1)
        except:
            pass

        print("📝 [JustJoin]  Message/LinkedIn ( )...")
        # Повторно пробуем заполнить поля, так как форма могла расшириться
        for field_name, data in smart_fields.items():
            if field_name not in ["Message", "LinkedIn/GitHub"]: continue
            filled = False
            for css in data["css"]:
                try:
                    elements = target_page.locator(css)
                    for i in range(elements.count()):
                        el = elements.nth(i)
                        if el.is_editable() and el.is_visible():
                            el.click()
                            time.sleep(random.uniform(0.3, 0.8))
                            el.fill("")
                            time.sleep(random.uniform(0.1, 0.3))
                            self.human_type(el, data["val"])
                            print(f"✅ {field_name}")
                            filled = True
                            break
                    if filled: break
                except:
                    pass

        # Финальные естественные движения
        self.natural_mouse_movement(target_page)
        self.natural_scroll(target_page)
        time.sleep(random.uniform(1, 2))

        def check_for_captcha():
            # Cloudflare Turnstile или reCAPTCHA
            captcha_iframe = target_page.locator("iframe[src*='challenges.cloudflare.com'], iframe[src*='recaptcha'], iframe[title*='recaptcha'], iframe[title*='cloudflare']").first
            if captcha_iframe.is_visible(timeout=2000):
                print("🤖 :  !  60        ...")
                try:
                    captcha_iframe.wait_for(state="hidden", timeout=60000)
                    print("✅   !")
                    time.sleep(2)
                except:
                    print("❌     !")

        print("🚀 [JustJoin] ...")
        try:
            submit_selectors = [
                "button[type='submit']:visible",
                "button:has-text('Wyślij'):visible",
                "button:has-text('Aplikuj'):visible",
                "button:has-text('Apply'):visible",
                "button:has-text('Send'):visible",
            ]

            submit_button = None
            for sel in submit_selectors:
                try:
                    btn = target_page.locator(sel).last
                    if btn.is_visible(timeout=1000):
                        submit_button = btn
                        break
                except:
                    pass

            check_for_captcha() # Проверка капчи ДО нажатия

            if submit_button:
                submit_button.scroll_into_view_if_needed()
                time.sleep(random.uniform(1, 2))
                self.human_click(submit_button)
                print("✅     !")
                
                check_for_captcha() # Проверка капчи ПОСЛЕ нажатия

                time.sleep(5)

                url_lower = target_page.url.lower()
                if "success" in url_lower or "thank" in url_lower:
                    return "Applied"

                for keyword in ['Dziękujemy', 'Thank you', 'Application sent', 'Successfully']:
                    try:
                        if target_page.locator(f"text={keyword}").is_visible(timeout=2000):
                            return "Applied"
                    except:
                        pass

                return "Applied (Unconfirmed)"
            else:
                return "Failed - No Submit Button"

        except Exception as e:
            print(f"⚠️ {e}")
            return "Failed - Submit Error"



if __name__ == "__main__":
    from playwright.sync_api import sync_playwright

    TEST_URL = "https://justjoin.it/job-offer/wavestone-poland-ifs-technical-consultant-gliwice-erp"
    TEST_CV = r"C:\Users\yerem\AI-JOB-SEEKER-AGENT\Data\my_cv.pdf"

    MY_PROFILE = {
        "first_name": "Oleksandr",
        "last_name": "Yeremenko",
        "email": "yeremenkoaleks1@gmail.com",
        "phone": "+48516478223",
        "linkedin": "https://github.com/AleksYeremenko"
    }

    print("🧪   JustJoinApplier...")
    print("=" * 60)

    user_data_dir = os.path.join(project_root, "Data", "Chrome_Profile")

    if not os.path.exists(user_data_dir):
        print(f"❌ :  Chrome  !")
        print(f"📁 : {user_data_dir}")
        print("\n💡  : python save_login.py")
        exit(1)

    print(f"✅  : {user_data_dir}")
    print("🔐  ...")

    with sync_playwright() as p:
        # КРИТИЧНО: максимально близко к реальному Chrome
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            viewport={"width": 1920, "height": 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            locale='en-US,pl-PL',
            timezone_id='Europe/Warsaw',
            geolocation={'latitude': 52.2297, 'longitude': 21.0122},  # Warsaw
            permissions=['geolocation'],
            color_scheme='light',
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-popup-blocking',
                '--disable-notifications',
                '--disable-extensions-except',
                '--load-extension',
            ],
            ignore_default_args=['--enable-automation', '--enable-blink-features=AutomationControlled'],
            java_script_enabled=True,
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1.0
        )

        page = context.pages[0] if context.pages else context.new_page()

        applier = JustJoinApplier(MY_PROFILE)
        status = applier.apply(page, context, TEST_URL, TEST_CV, "")

        print("\n" + "=" * 60)
        print(f"✅ : {status}")
        print("=" * 60)
        time.sleep(10)
        context.close()