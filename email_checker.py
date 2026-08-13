import os
import time

class EmailChecker:
    def __init__(self, email_address):
        self.email_address = email_address.lower()
        self.profile_path = os.path.abspath("Data/email_profile")
        
        self.provider = "gmail"
        if "outlook.com" in self.email_address or "hotmail.com" in self.email_address:
            self.provider = "outlook"
        elif "yahoo.com" in self.email_address:
            self.provider = "yahoo"

    def login_to_email(self):
        """Launches DrissionPage to bypass Google automation checks."""
        from DrissionPage import ChromiumOptions, ChromiumPage
        print(f"🌍 Launching browser for {self.provider.capitalize()} login...")
        
        co = ChromiumOptions()
        co.set_user_data_path(self.profile_path)
        co.headless(False)
        co.set_argument('--disable-blink-features=AutomationControlled')
        
        try:
            page = ChromiumPage(co)
            
            if self.provider == "gmail":
                page.get("https://mail.google.com")
            elif self.provider == "outlook":
                page.get("https://outlook.live.com/mail/")
            elif self.provider == "yahoo":
                page.get("https://mail.yahoo.com")
                
            print("⏳ Please log in to your email in the opened browser.")
            print("⏳ Once you see your inbox, you can close the browser window.")
            
            # Keep script alive until the user closes the browser
            while True:
                time.sleep(1)
                _ = page.title  # this will throw an exception when the browser is closed
                
            print("✅ Email session saved successfully!")
        except Exception:
            # When closed manually, it throws an error which we catch cleanly
            print("✅ Email session saved and browser closed.")

    def check_for_confirmation(self, company_name, job_title=""):
        """Checks if a confirmation email was received."""
        if not os.path.exists(self.profile_path):
            print("⚠️ No email session found. Please login first.")
            return False

        try:
            from DrissionPage import ChromiumOptions, ChromiumPage
            
            co = ChromiumOptions()
            co.set_user_data_path(self.profile_path)
            co.headless(True)
            co.set_argument('--disable-blink-features=AutomationControlled')
            
            page = ChromiumPage(co)
            
            # Clean company name
            clean_company = company_name.split('sp. z')[0].split('Sp. z')[0].strip() if company_name else ""
            safe_company = clean_company.replace(' ', '+') if clean_company else ""
            
            # Clean job title (take first 2 words for broader match)
            clean_title = " ".join(job_title.split()[:2]) if job_title else ""
            safe_title = clean_title.replace(' ', '+') if clean_title else ""
            
            keywords = "(aplikacja OR aplikowania OR aplikację OR application OR applied OR thank OR otrzymaliśmy OR received OR traffit OR erecruiter OR potwierdź OR dziękujemy OR złożenie OR powiązaną)"
            exclude = "-from:justjoin.it -from:pracuj.pl -from:nofluffjobs.com -from:djinni.co"
            
            if self.provider == "gmail":
                search_query = f"newer_than:1d {keywords} {exclude}"
                if safe_company and safe_title:
                    search_query += f" ({safe_company} OR {safe_title})"
                elif safe_company:
                    search_query += f" {safe_company}"
                    
                search_url = f'https://mail.google.com/mail/u/0/#search/{search_query.replace(" ", "+")}'
                page.get(search_url)
                time.sleep(4)
                
                # Check rows
                rows = page.eles('tag:tr@class:zA')
                found = len(rows) > 0
                page.quit()
                return found
                
            elif self.provider == "outlook":
                page.get("https://outlook.live.com/mail/0/inbox")
                time.sleep(5)
                content = page.html.lower()
                found = (company_name.lower() in content or "traffit" in content or "erecruiter" in content or job_title.lower() in content) and ("thank" in content or "received" in content or "aplikacj" in content or "otrzymaliśmy" in content or "potwierdź" in content or "złożenie" in content)
                page.quit()
                return found
                
            elif self.provider == "yahoo":
                page.get(f"https://mail.yahoo.com/d/search/keyword={safe_company}+application")
                time.sleep(5)
                content = page.html.lower()
                found = company_name.lower() in content or "traffit" in content
                page.quit()
                return found

            page.quit()
            return False
            
        except Exception as e:
            print(f"⚠️ Email check failed: {e}")
            try:
                page.quit()
            except:
                pass
            return False
