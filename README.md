# 💼 LinkedIn Profile AI Analyzer & Optimizer

An intelligent, full-stack AI application designed to audit, optimize, and elevate LinkedIn profiles like a top-tier executive recruiter.

Built with **Python**, **Streamlit**, **Plotly**, and a hybrid **Dual-Engine Architecture** (combining custom NLP heuristics with **Google Gemini AI**).

---

## 🌟 Key Features

### 1. 📊 Holistic Profile Scoring (0–100) & Radar Chart
- **Overall Score**: Weighted evaluation across all critical profile components.
- **Headline Hook (20%)**: Character count optimization, divider structure, value proposition, and search keyword density.
- **About / Summary Narrative (25%)**: Scans for first 3-line hook (before "see more"), quantifiable metrics, storytelling quality, and Call-to-Action (CTA).
- **Experience & Google XYZ Adherence (35%)**: Measures action-verb diversity, KPI density ($, %, scale), and flags passive buzzwords ("responsible for", "helped with").
- **ATS & Recruiter Search Fit (20%)**: Compares skills against real-world recruiter search benchmarks.
- **Interactive Plotly Radar Chart**: Multi-axis visualization showing strengths and blind spots at a glance.

### 2. ⏱️ Recruiter 10-Second Scan Simulation
Simulates the brutal reality of how recruiters review profiles:
- **0–3 Seconds**: Headline, role title, and immediate keyword positioning.
- **3–6 Seconds**: About section opening hook and narrative clarity.
- **6–10 Seconds**: Quick scan for quantifiable metrics, numbers, and impact verbs in work experience.

### 3. 🎯 Target Role & Keyword Gap Analysis
- Benchmarks against high-demand industry roles:
  - **AI & Machine Learning Engineer**
  - **Full-Stack Software Engineer**
  - **Data Scientist**
  - **Product Manager**
  - **DevOps & Cloud Engineer**
  - **Custom / General Tech**
- Identifies **Matching Skills (Green)** vs. **Missing High-Value Keywords (Orange)**.
- Recommends tailored power verbs for your target domain.

### 4. ✍️ 5 High-Converting AI Headline Variants
Generates 5 distinct headline styles (under LinkedIn's 220-character limit):
1. **The Recruiter Magnet**: Keyword-dense and search-optimized.
2. **The Metrics & Impact Driven**: Anchored in quantifiable results.
3. **The Value Proposition**: "Who you help + How you help them".
4. **The Storyteller / Thought Leader**: Focus on vision, craft, and mission.
5. **The Minimalist Authority**: High-status, concise executive positioning.

### 5. 📝 AI About Section Rewriter
Generates 3 full rewritten versions:
1. **Conversational & First-Person**: Relatable, engaging, and personal.
2. **Executive & Metric-Led**: Polished, structured, bulleted, and KPI-heavy.
3. **Story-Driven Narrative**: Hero's journey highlighting pivotal challenges and future vision.

### 6. 🚀 Google XYZ Formula Bullet Point Transformer
Transforms weak or passive bullets into Google's proven accomplishment formula:
> *"Accomplished [X], as measured by [Y], by doing [Z]"*
- Converts *"Worked on database speed"* ➡️ *"Refactored PostgreSQL indexing and query execution plans, reducing API p99 latency by 42% for 250K+ active users."*

### 7. 💡 LinkedIn Creator & Thought Leadership Generator
- Generates 5 scroll-stopping post concepts, opening hooks, and hashtags based on your actual experience to build inbound recruiter attraction.

### 8. 📥 One-Click Audit Report Export
- Download a structured, comprehensive Markdown audit report with an actionable checklist to review offline or share with mentors.

---

## 🏗️ Architecture

```
LinkedIn-AI-Optimizer/
│
├── app.py                      # Interactive Streamlit Web Dashboard
├── run.bat                     # 1-Click Windows Launcher Script
├── requirements.txt            # Python dependencies
├── .env.example                # API configuration template
│
├── analyzer/
│   ├── parser.py               # PDF parser for LinkedIn profile exports
│   ├── heuristics.py           # NLP rule-based scoring engine & 10s recruiter simulation
│   ├── role_benchmarks.py      # Industry role skills benchmarks & ATS matcher
│   └── ai_engine.py            # Dual AI engine (Google Gemini API + Smart Offline Heuristic Fallback)
│
└── sample_data/
    └── sample_profile.py       # Pre-loaded profiles for instant 1-click testing
```

---

## ⚡ Quick Start Guide

### 1. Run the App (1-Click)
On Windows, simply double-click **`run.bat`** or run:

```bash
streamlit run app.py
```

The application will automatically open in your default browser at `http://localhost:8501`.

### 2. Optional: Enable Live Google Gemini AI
The app comes with a **built-in intelligent offline NLP engine** that works 100% out of the box without any API keys.

If you want personalized generative AI rewrites powered by Gemini:
1. Obtain a free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
2. Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_actual_key_here
   ```
   *(Or enter your key directly in the app's sidebar under "AI Settings".)*

---

## 📄 How to Export Your LinkedIn Profile to PDF

1. Go to your **LinkedIn Profile** in your browser.
2. Click the **More** button in your profile header (next to "Open to" / "Add profile section").
3. Click **Save to PDF**.
4. Upload the downloaded PDF directly into the app's sidebar file uploader!

---

## 🛠️ Tech Stack
- **Frontend / UI**: Streamlit, Plotly Express & Graph Objects
- **Document Extraction**: PyPDF
- **NLP & Heuristics**: Custom regex tokenizers, action verb lexicons, metric extractors
- **AI / LLM**: `google-genai` / Google Gemini 2.5 Flash
