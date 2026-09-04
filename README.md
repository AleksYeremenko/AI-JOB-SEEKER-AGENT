# 🤖 JOB SEARCHER AI — Automated CV-Based Job Hunting Agent

A fully automated AI agent built with **LangChain**, **LangGraph**, **Streamlit**, that takes your **CV (PDF)** as input, intelligently parses it, finds **matching job listings from LinkedIn**, and sends them directly to your.

> 🎯 “Upload your CV. Get jobs. Instantly. Anywhere.”

---

## 🚀 Features

- 📄 **CV Parsing** — Extracts your job title and skills automatically from a PDF resume.
- 🔍 **Live LinkedIn Scraping** — Searches LinkedIn in real-time for jobs that match your profile.
- 🤖 **LangGraph Agent Workflow** — Fully modular graph-based pipeline with nodes for CV parsing, job search, and messaging.
- 🧠 **Skill Matching** — Identifies relevant technologies (Python, ML, AI, etc.) to tailor job queries.
- ⚡ **1-Click Streamlit UI** — Clean web interface to upload your CV and launch the agent.

---

## 🧠 Tech Stack

| Tool        | Purpose                                      |
|-------------|----------------------------------------------|
| 🦜 LangChain | Language modeling & pipeline orchestration   |
| 🧩 LangGraph | Multi-agent execution and state transitions  |
| 🐍 Python    | Core backend logic                           |
| 🕸 Selenium  | Real-time LinkedIn job scraping              |
| 🧾 PyMuPDF   | PDF parsing and text extraction              |
| 🌐 Streamlit | Interactive web UI for file upload           |
| 🔐 dotenv    | Secure API key and credentials management    |

---

---

---

## 🚦 Usage

```bash
streamlit run main.py
```

Then:

1. Upload your **PDF CV**
2. Click **“Start Job Search”**
3. Check your **Gmail** for job listings 📱

---

## 📁 Folder Structure

```
JOB-SEARCHER/
│
├── main.py                # Streamlit app
├── graph.py               # LangGraph agent
├── cv_parser.py           # CV text extraction + skill matching
├── linkedin_scraper.py    # Job scraping via Selenium
├── notify_agent.py        # WhatsApp message sender via Twilio
├── .env                   # API keys & phone config
```

---

## ✅ Example Output 

```
🧠 Jobs Matched to Your CV:

🔹 Machine Learning Engineer at Google
📍 Mountain View, CA
🔗 https://linkedin.com/jobs/view/...

🔹 Data Scientist at Meta
📍 Remote
🔗 https://linkedin.com/jobs/view/...
```

---

## ✨ Future Upgrades

- 📍 Location-based filtering
- 🧾 Export job results to PDF
- ⏱️ Scheduled daily/weekly job scans
- 📧 Email fallback for job results
- 🗣️ Chat-based interface

---


---



If you found this useful:

- 🌟 Star the repo
- 🍴 Fork it
- 🧵 Share with friends
