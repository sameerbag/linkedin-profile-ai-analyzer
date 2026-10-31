# 🚀 AI Job Search, Matcher & Consent-Based Auto-Apply Assistant

An end-to-end, open-source AI job discovery and application platform inspired by [`ai-job-search`](https://github.com/ai-job-search-dev/ai-job-search).

It audits your LinkedIn profile, aggregates live job postings from major portals (**LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, RemoteOK**), ranks positions by **AI Fit Score**, and with **explicit user consent**, automatically fills and applies your candidate details and tailored cover letter in one click!

Built with **Python**, **Streamlit**, **JobSpy**, **Playwright**, and a **Dual AI Engine** (custom NLP heuristics + **Google Gemini AI**).

---

## 🌟 Key Capabilities

### 1. 🔍 Multi-Portal Job Scraping & Aggregation
- **Cross-Portal Discovery**: Concurrently searches across:
  - **LinkedIn**
  - **Indeed**
  - **Glassdoor**
  - **ZipRecruiter**
  - **Google Jobs**
  - **RemoteOK**
- **Deep Geographic & Country Filtering**:
  - Filter by Country (**USA, India, United Kingdom, Canada, Germany, Australia, Global/Remote**).
  - Filter by City / State / Area (e.g. *San Francisco, CA*, *Bengaluru*, *London*, *Toronto*, *Berlin*).
  - Filter by Work Mode: **Remote Only**, **Hybrid**, or **On-site**.
  - Filter by Freshness: Past 24 hours, past 3 days, past 7 days, past 30 days.

### 2. 🎯 AI Fit Scorer & Best-Fit Suggestions
- Analyzes each discovered job description against your candidate profile (skills, title, experience).
- Computes:
  - **Fit Score (0–100%)**
  - **Match Tier**: 🔥 Top Fit (82%+), ✨ Strong Match (68–81%), ⚖️ Moderate (50–67%), ⚠️ Low (<50%).
  - **Matching Skills Breakdown** (Green pills) vs **Missing Skill Gaps** (Orange pills).
  - **Recruiter Verdict**: Actionable AI summary explaining why the role fits your background and what to emphasize.
  - Automatically sorts search results so the **Best Fit** jobs are surfaced first!

### 3. 🔒 Human-in-the-Loop Consent Gate
- Complete privacy & safety: No application is ever submitted without your explicit knowledge.
- Clear consent verification checkbox before auto-fill tools are unlocked.

### 4. ⚡ Multi-Engine Auto-Fill & Auto-Apply
- **🌐 1-Click Universal Browser Auto-Fill Bookmarklet**:
  - Drag the bookmarklet to your browser bar.
  - Open ANY job application page (**Greenhouse, Lever, LinkedIn Easy Apply, Workday, Indeed, Ashby, BambooHR, Taleo**).
  - Click the bookmarklet to auto-fill First Name, Last Name, Email, Phone, LinkedIn, GitHub, Location, and Cover Letter in under 1 second!
- **🤖 Automated Browser Mode (Playwright)**:
  - Launches an automated browser window, navigates to the job portal, and injects your profile into form fields so you can inspect and submit.
- **📋 1-Click Quick-Fill Field Matrix**:
  - Individual 1-click copy inputs for all common application questions.

### 5. ✍️ AI-Tailored Application Kit
- **Tailored Cover Letter**: Generates a 3-paragraph tailored cover letter referencing the company's name, role title, and matching technical achievements.
- **Form Q&A Answers**: Pre-drafts responses for standard application questions (*"Why do you want to work here?"*, *"Summary of relevant experience"*, Notice period, Work authorization, Expected salary).

### 6. 💼 LinkedIn Profile Audit & Heuristics
- Upload your LinkedIn profile PDF (`More > Save to PDF`) or enter details manually.
- 10-Second recruiter scan simulation (`0–3s`, `3–6s`, `6–10s`).
- 5 AI Headline variants & Google XYZ experience bullet optimizer (`"Accomplished [X] as measured by [Y], by doing [Z]"`).

### 7. 📋 Application Pipeline & Tracker
- Tracks every application through the lifecycle: `Shortlisted` ➡️ `Consented` ➡️ `Applied` ➡️ `Interviewing` ➡️ `Offer / Rejected`.
- Local JSON database (`data/applications.json`), persisted across runs.
- 1-Click export to JSON.

---

## 🏗️ Architecture

```
Antigravity/
│
├── app.py                      # Streamlit Multi-Page Web Platform
├── run.bat                     # Windows 1-Click Launcher Script
├── requirements.txt            # Python dependencies
├── .env.example                # API configuration template
│
├── jobs/                       # Job Search, Matcher & Auto-Apply Engine
│   ├── models.py               # Data models (JobPosting, ApplicantProfile, ApplicationRecord)
│   ├── job_searcher.py         # Multi-portal scraper (JobSpy + Remote aggregators)
│   ├── job_matcher.py          # AI Fit Scorer, Skill overlap analyzer & Ranker
│   ├── application_generator.py# Tailored cover letters & form Q&A generator
│   ├── auto_apply.py           # Browser bookmarklet & Playwright form auto-fillers
│   ├── tracker.py              # Application pipeline tracker (data/applications.json)
│   └── sample_jobs.py          # Curated multi-country benchmark postings
│
├── analyzer/                   # LinkedIn Profile Analysis Engine
│   ├── parser.py               # PDF parser for LinkedIn profile exports
│   ├── heuristics.py           # NLP rule-based scoring engine & 10s recruiter simulation
│   ├── role_benchmarks.py      # Industry role skills benchmarks & ATS matcher
│   └── ai_engine.py            # Dual AI engine (Google Gemini API + Heuristic Fallback)
│
└── sample_data/
    └── sample_profile.py       # Pre-loaded profiles for instant testing
```

---

## ⚡ Quick Start Guide

### 1. Launch the Application
Simply double-click **`run.bat`** on Windows, or run in your terminal:

```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`.

### 2. How to Search & Auto-Apply in 3 Steps:
1. **Set Up Your Profile**: In **💼 LinkedIn Profile & Applicant Setup**, upload your LinkedIn PDF (or load a demo profile) and fill your contact info.
2. **Find & Rank Jobs**: In **🔍 Job Search & Best-Fit Matches**, enter your target role, pick your country & city, and click **🚀 Find & Rank Jobs**. The top matches will appear with fit scores and skill gaps.
3. **Consent & Auto-Apply**: Click **⚡ Apply** on any job. Review the tailored cover letter, check the **Consent Box**, and click the **1-Click Auto-Fill Bookmarklet** or launch Playwright!

---

## 🔒 Security & Privacy
- **Local-First**: All personal data and resumes stay on your local computer.
- **Zero Involuntary Submissions**: Human-in-the-loop consent gate ensures no form is ever submitted without your explicit confirmation.
- **Works 100% Offline**: Includes built-in intelligent NLP engines that require zero external API keys.
