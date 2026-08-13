import os
import imaplib
import email
from email.header import decode_header
import re
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("Data/.env")

EMAIL_ACCOUNT = os.getenv("EMAIL_ACCOUNT")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


def get_links_from_email():
    if not EMAIL_ACCOUNT or not EMAIL_PASSWORD:
        print("⚠️ Учетные данные почты не найдены в .env!")
        return []

    links = []
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_ACCOUNT, EMAIL_PASSWORD)
        mail.select("inbox")

        # 🔥 1. ИЩЕМ ТОЛЬКО ЗА ПОСЛЕДНИЕ СУТКИ 🔥
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        status, messages = mail.search(None, "UNSEEN", "SINCE", yesterday)

        if status != "OK":
            return []

        email_ids = messages[0].split()
        if not email_ids:
            print("📭 В почте за последние сутки тихо. Новых писем нет.")
            return []

        print(f"📧 [ПОЧТА] Найдено {len(email_ids)} новых писем за сутки. Фильтрую по ключевым словам...")

        links = []
        invites_found = []
        interview_keywords = ['interview', 'rozmowa', 'собеседование', 'spotkanie', 'zaproszenie', 'invitation']

        # 🔥 2. СЛОВАРЬ КЛЮЧЕВЫХ СЛОВ 🔥
        job_keywords = [
            'job', 'work', 'interview', 'offer', 'application', 'status', 'vacancy', 'career', 'opportunity',
            'praca', 'rozmowa', 'spotkanie', 'oferta', 'aplikacja', 'wakat', 'kariera',
            'работа', 'вакансия', 'собеседование', 'отклик'
        ]

        for e_id in email_ids:
            # Получаем письмо
            status, msg_data = mail.fetch(e_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])

                    subject_data = decode_header(msg.get("Subject", ""))[0]
                    subject = subject_data[0]
                    encoding = subject_data[1]
                    if isinstance(subject, bytes):
                        try:
                            subject = subject.decode(encoding if encoding else "utf-8")
                        except:
                            subject = str(subject)

                    sender = str(msg.get("From", ""))

                    subject_lower = subject.lower()
                    sender_lower = sender.lower()

                    # Проверяем, есть ли ключевые слова в теме или отправителе
                    is_job_related = any(kw in subject_lower for kw in job_keywords) or any(
                        kw in sender_lower for kw in ['pracuj', 'justjoin', 'hr', 'recruiter', 'talent', 'jobs', 'ats'])
                    non_it_words = ['barista', 'kelner', 'kelnerka', 'kucharz', 'sprzątacz',
                                    'kasjer', 'magazynier', 'kierowca', 'ochroniarz']
                    if any(w in subject_lower for w in non_it_words):
                        continue

                    if not is_job_related:

                        continue  # Пропускаем спам, игры и т.д.

                    print(f"   📨 Целевое рабочее письмо! От: {sender} | Тема: {subject}")

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))

                            if content_type in ["text/plain", "text/html"] and "attachment" not in content_disposition:
                                try:
                                    body += part.get_payload(decode=True).decode()
                                except:
                                    pass
                    else:
                        try:
                            body = msg.get_payload(decode=True).decode()
                        except:
                            pass

                    # Вытаскиваем ссылки
                    found = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', body)
                    links.extend(found)

                    # 🔥 ИЩЕМ ПРИГЛАШЕНИЯ НА СОБЕСЕДОВАНИЕ 🔥
                    if any(kw in subject_lower or kw in body.lower() for kw in interview_keywords):
                        if "rejection" not in subject_lower and "unfortunately" not in body.lower():
                            invites_found.append({
                                "sender": sender,
                                "subject": subject,
                                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            })

        mail.logout()

        valid_domains = ['pracuj.pl', 'justjoin.it', 'nofluffjobs', 'linkedin', 'bank', 'oferta', 'job', 'career']
        valid_links = []

        for l in links:
            l_lower = l.lower()
            if any(domain in l_lower for domain in valid_domains) and not l_lower.endswith(
                    ('.png', '.jpg', '.gif', '.jpeg', '.css', '.js')):
                valid_links.append(l)

        valid_links = list(set(valid_links))
        
        if invites_found:
            stats_path = "Data/interview_stats.json"
            try:
                stats = {"invites": []}
                if os.path.exists(stats_path):
                    with open(stats_path, "r", encoding="utf-8") as f:
                        stats = json.load(f)
                
                # Check for duplicates by subject
                existing_subjects = [i.get('subject') for i in stats.get('invites', [])]
                new_invites = [i for i in invites_found if i['subject'] not in existing_subjects]
                
                if new_invites:
                    stats["invites"].extend(new_invites)
                    with open(stats_path, "w", encoding="utf-8") as f:
                        json.dump(stats, f, ensure_ascii=False, indent=4)
                    print(f"🎉 [УРА!] Найдено {len(new_invites)} новых приглашений на собеседование!")
            except Exception as e:
                print(f"⚠️ Ошибка сохранения статистики собесов: {e}")

        if valid_links:
            print(f"🔗 [ПОЧТА] БИНГО! Вытащил {len(valid_links)} ссылок на вакансии/статусы! Закидываю в парсер.")
        else:
            print("🔗 [ПОЧТА] Рабочие письма проверил, но целевых ссылок внутри не нашел.")

        return valid_links

    except Exception as e:
        print(f"❌ Ошибка при чтении почты: {e}")
        return []
