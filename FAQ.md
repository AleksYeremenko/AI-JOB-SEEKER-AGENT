# AI Job Seeker Agent - FAQ & User Guide

Welcome to the AI Job Seeker Agent! This tool fully automates your job search by scraping job boards, tailoring your CV using AI, and applying to jobs on your behalf.

## How to Get Started

1. **Personal Information:** 
   Fill in your contact details (First Name, Last Name, Email, Phone). Make sure your email is accurate as the agent will use it to apply for jobs and check for interview invitations.

2. **Upload Your CV:** 
   Click `Browse` and select your base CV (PDF or DOCX). The agent uses this to understand your real work history. Don't worry about formatting; the AI will read the text and generate a beautiful, ATS-friendly PDF tailored to each job.

3. **Job Preferences:** 
   - **Tech Stack:** Enter your key technologies (e.g., Python, React, AWS).
   - **Seniority & City:** Select the roles you are targeting.
   - **Job Type:** Choose between Remote, Hybrid, or Onsite.

4. **Match Threshold (%):** 
   The AI evaluates how well your skills match a job description. 
   - Set to **30-40%** to apply to a large volume of jobs (recommended for Junior/Mid).
   - Set to **70-80%** to only apply for jobs where you are a perfect fit.

5. **Work Speed:** 
   Adjusts how fast the agent runs. Lower speed uses less CPU and RAM.

6. **Email Login (Optional but Recommended):**
   Click `Login to Email` to authenticate. This allows the agent to monitor your inbox for interview invitations and update your dashboard statistics!

## Modes of Operation

- **Non-Tech Mode:** Enable this if you are applying for non-technical roles (e.g., Marketing, Sales, HR).
- **Autonomous Mode:** The agent will continuously run in the background, searching for new jobs every few hours.

## Where to view my applications?
A beautiful HTML dashboard is generated automatically! Open `dashboard.html` in your browser to see a detailed report of all applied jobs, conversion rates, and interview invitations.

## Troubleshooting
- **Playwright Errors / Chrome not found:** Run `playwright install` in your terminal.
- **Empty CVs generated:** Ensure your base CV is text-readable (not a scanned image).
- **Agent stops applying:** Some websites may block automated applications. The agent will log these as failures and skip them.

## Disclaimer
The AI will NEVER invent fake companies or fake experience. It only reorganizes and highlights your existing experience to bypass ATS filters.
