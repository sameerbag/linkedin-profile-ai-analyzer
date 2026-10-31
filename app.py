import os
import json
import re
import urllib.parse
from datetime import datetime
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

# Profile & Heuristic Analyzers
from analyzer.parser import extract_text_from_pdf, parse_linkedin_text
from analyzer.heuristics import (
    score_headline,
    score_about,
    score_experience,
    compute_overall_profile_score,
    recruiter_10_second_audit
)
from analyzer.role_benchmarks import ROLE_BENCHMARKS, analyze_role_fit
from analyzer.ai_engine import (
    generate_headlines,
    generate_about_rewrites,
    transform_bullet_points,
    generate_linkedin_post_ideas
)
from sample_data.sample_profile import SAMPLE_PROFILES

# Jobs Engine
from jobs.models import JobPosting, ApplicantProfile, ApplicationRecord
from jobs.job_searcher import search_jobs_multi_portal
from jobs.job_matcher import rank_jobs_for_applicant
from jobs.application_generator import generate_tailored_cover_letter, generate_application_answers
from jobs.auto_apply import generate_browser_autofill_script, launch_playwright_autofill
from jobs.tracker import (
    save_application,
    get_all_applications,
    update_application_status,
    delete_application,
    get_pipeline_stats
)
from jobs.utils import clean_html_text, clean_text_field

# Page configuration
st.set_page_config(
    page_title="AI Job Search, Matcher & Auto-Apply Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #0A66C2;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #555;
        margin-bottom: 1.2rem;
    }
    .score-card {
        background: #f8fafd;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .score-val {
        font-size: 2.0rem;
        font-weight: 800;
        margin: 4px 0;
    }
    .score-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        margin: 2px;
    }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-warning { background: #fef3c7; color: #92400e; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .badge-info { background: #e0f2fe; color: #075985; }
    .badge-purple { background: #f3e8ff; color: #6b21a8; }
    
    .job-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-left: 6px solid #0A66C2;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        transition: transform 0.2s ease;
    }
    .job-card:hover {
        border-color: #0A66C2;
        box-shadow: 0 4px 12px rgba(10,102,194,0.12);
    }
    .recruiter-scan-box {
        background: #ffffff;
        border-left: 5px solid #0A66C2;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .consent-box {
        background: #f0fdf4;
        border: 2px dashed #16a34a;
        padding: 16px 20px;
        border-radius: 10px;
        margin: 15px 0;
    }
    .bookmarklet-btn {
        display: inline-block;
        background: #0A66C2;
        color: #ffffff !important;
        font-weight: 700;
        padding: 10px 18px;
        border-radius: 8px;
        text-decoration: none;
        box-shadow: 0 2px 6px rgba(10,102,194,0.3);
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "applicant_profile" not in st.session_state:
    st.session_state.applicant_profile = ApplicantProfile()
else:
    # Ensure backward-compatibility for active sessions during hot-reload
    for field_name in ["location", "current_location", "country", "city", "state_province", "postal_code", "email", "phone", "headline", "about", "experience"]:
        if not hasattr(st.session_state.applicant_profile, field_name):
            setattr(st.session_state.applicant_profile, field_name, "")
    if not hasattr(st.session_state.applicant_profile, "skills"):
        st.session_state.applicant_profile.skills = []

if "profile_loaded" not in st.session_state:
    st.session_state.profile_loaded = False

if "last_processed_pdf_name" not in st.session_state:
    st.session_state.last_processed_pdf_name = ""

if "location_configured" not in st.session_state:
    st.session_state.location_configured = False

if "target_role_query" not in st.session_state:
    st.session_state.target_role_query = ""

if "discovered_jobs" not in st.session_state:
    st.session_state.discovered_jobs = []

if "selected_job" not in st.session_state:
    st.session_state.selected_job = None

if "tailored_cover_letter" not in st.session_state:
    st.session_state.tailored_cover_letter = ""

if "user_consent" not in st.session_state:
    st.session_state.user_consent = False


# SIDEBAR
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3536/3536505.png", width=55)
st.sidebar.title("AI Job Navigator")

app_mode = st.sidebar.radio(
    "Choose Platform Section:",
    [
        "🔍 Job Search & Best-Fit Matches",
        "⚡ Consent & Auto-Apply Center",
        "💼 LinkedIn Profile & Applicant Setup",
        "📋 Application Pipeline Tracker"
    ],
    index=0
)

st.sidebar.markdown("---")

with st.sidebar.expander("🔑 AI Settings (Gemini API)", expanded=False):
    api_key_input = st.text_input(
        "Google Gemini API Key (Optional):",
        value=os.getenv("GEMINI_API_KEY", ""),
        type="password",
        help="Leave blank to use the built-in offline NLP engine. Provide a key for personalized generative AI rewrites."
    )
    if api_key_input:
        st.caption("🟢 Live Gemini AI Engine Enabled")
    else:
        st.caption("⚡ Offline Intelligent NLP Engine Active")

prof = st.session_state.applicant_profile
if prof.full_name or prof.headline:
    loc_display = f"{prof.city}, {prof.country}".strip(", ") if (prof.city or prof.country) else (getattr(prof, "location", "") or "Location not set")
    st.sidebar.markdown(f"**Current Applicant:**  \n👤 **{prof.full_name or 'Uploaded Applicant'}**  \n📍 **{loc_display}**")
else:
    st.sidebar.markdown("**Current Applicant:**  \n👤 *No PDF attached yet*  \n📍 *Attach LinkedIn PDF below*")

if st.sidebar.button("📄 Attach / Switch LinkedIn PDF", use_container_width=True):
    st.session_state.location_configured = False
    st.session_state.profile_loaded = False
    st.session_state.last_processed_pdf_name = ""
    st.rerun()


# ==============================================================================
# SECTION 1: JOB SEARCH & BEST-FIT MATCHES
# ==============================================================================
if app_mode == "🔍 Job Search & Best-Fit Matches":
    st.markdown('<div class="main-title">🔍 Multi-Portal Job Finder & Best-Fit Matcher</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Scrapes and aggregates postings from LinkedIn, Indeed, Glassdoor, ZipRecruiter, and Google Jobs. Analyzes and ranks each role against your profile to find your best fit.</div>', unsafe_allow_html=True)

    # Launch Onboarding / Setup Box if profile is not loaded or user wants to switch PDF
    if not st.session_state.get("profile_loaded", False) or not st.session_state.get("location_configured", False):
        with st.container(border=True):
            st.markdown("### 📄 Step 1: Attach Your LinkedIn Profile PDF")
            st.markdown("Upload your LinkedIn Profile PDF. Your **Name, Headline, Location (City & Country), Skills, Experience, and Contact Details** will be extracted directly from your PDF—with no mock or default values.")
            st.caption("💡 *How to download your LinkedIn PDF:* Open your profile on LinkedIn ➔ Click the **More** button ➔ Click **Save to PDF**.")

            col_pdf_setup, col_manual_setup = st.columns([1.4, 1.2])
            with col_pdf_setup:
                st.markdown("##### 📥 Attach PDF File")
                launch_pdf = st.file_uploader("Upload LinkedIn Profile PDF:", type=["pdf"], key="launch_pdf_uploader")
                if launch_pdf is not None:
                    # Auto-extract immediately when PDF is attached or button clicked
                    should_parse = (st.session_state.get("last_processed_pdf_name") != launch_pdf.name)
                    btn_clicked = st.button("🚀 Parse & Extract from Attached PDF", type="primary", use_container_width=True)
                    if should_parse or btn_clicked:
                        with st.spinner("Extracting details & detecting location directly from your PDF..."):
                            raw_text = extract_text_from_pdf(launch_pdf)
                            parsed = parse_linkedin_text(raw_text)
                            p = st.session_state.applicant_profile
                            p.full_name = parsed.get("name", "")
                            p.first_name = p.full_name.split()[0] if p.full_name else ""
                            p.last_name = p.full_name.split()[-1] if len(p.full_name.split()) > 1 else ""
                            p.headline = parsed.get("headline", "")
                            p.location = parsed.get("location", "")
                            p.country = parsed.get("country", "")
                            p.city = parsed.get("city", "")
                            p.current_location = p.location or f"{p.city}, {p.country}".strip(", ")
                            p.email = parsed.get("email", "")
                            p.phone = parsed.get("phone", "")
                            p.linkedin_url = parsed.get("linkedin_url", "")
                            p.about = parsed.get("about", "")
                            p.experience = parsed.get("experience", "")
                            p.skills = parsed.get("skills", [])
                            p.education = parsed.get("education", "")
                            st.session_state.profile_loaded = True
                            st.session_state.location_configured = True
                            st.session_state.last_processed_pdf_name = launch_pdf.name
                            if p.headline:
                                st.session_state.target_role_query = p.headline.split("|")[0].split("-")[0].strip()
                            st.session_state.discovered_jobs = []
                            loc_str = f"{p.city}, {p.country}".strip(", ") or p.location or "Location Detected"
                            st.success(f"✅ Loaded profile from PDF: **{p.full_name or 'Candidate'}** | 📍 Location: **{loc_str}** | 🎯 Role: **{st.session_state.target_role_query}**")
                            st.rerun()

            with col_manual_setup:
                st.markdown("##### ✏️ Or Enter Details Manually")
                c_opt1, c_opt2 = st.columns(2)
                with c_opt1:
                    setup_country_list = ["India", "USA", "United Kingdom", "Canada", "Germany", "Australia", "Singapore", "Global / Remote", "All Countries"]
                    default_c_idx = setup_country_list.index(prof.country) if prof.country in setup_country_list else 0
                    chosen_setup_country = st.selectbox("Your Country:", setup_country_list, index=default_c_idx, key="setup_country_select")
                with c_opt2:
                    chosen_setup_city = st.text_input("City / Area:", value=prof.city or "", placeholder="e.g. Pune, Bengaluru, London", key="setup_city_input")

                chosen_setup_role = st.text_input("Target Job Title:", value=st.session_state.get("target_role_query", ""), placeholder="e.g. Software Engineer, AI Engineer", key="setup_role_input")

                if st.button("💾 Continue with Manual Details", use_container_width=True):
                    p = st.session_state.applicant_profile
                    p.country = chosen_setup_country
                    p.city = chosen_setup_city
                    p.current_location = f"{chosen_setup_city}, {chosen_setup_country}".strip(", ")
                    st.session_state.target_role_query = chosen_setup_role
                    st.session_state.profile_loaded = True
                    st.session_state.location_configured = True
                    st.session_state.discovered_jobs = []
                    st.rerun()

        st.markdown("---")

    # Search Filters (Dynamic to User's Profile)
    with st.expander("🎯 Search Filters & Country Selection", expanded=st.session_state.get("profile_loaded", False)):
        f1, f2, f3, f4 = st.columns([1.5, 1, 1, 1])
        with f1:
            default_role = st.session_state.get("target_role_query", "")
            search_query = st.text_input("Job Title / Keywords:", value=default_role, placeholder="e.g. Machine Learning Engineer, Full Stack")
        with f2:
            country_options = ["India", "USA", "United Kingdom", "Canada", "Germany", "Australia", "Singapore", "Global / Remote", "All Countries"]
            active_country = prof.country if prof.country in country_options else "India"
            country_idx = country_options.index(active_country)
            selected_country = st.selectbox("Country:", country_options, index=country_idx)
        with f3:
            active_city = prof.city or getattr(prof, "location", "") or ""
            location_query = st.text_input("City / Area (Optional):", value=active_city, placeholder="e.g. Pune, Bengaluru, Remote")
        with f4:
            work_mode = st.selectbox("Work Type:", ["Remote or Any", "Remote Only", "Hybrid / On-site"], index=0)

        f_portals, f_freshness, f_results, f_btn = st.columns([2, 1, 1, 1.2])
        with f_portals:
            chosen_portals = st.multiselect(
                "Portals to Search:",
                ["LinkedIn", "Indeed", "Glassdoor", "ZipRecruiter", "Google", "RemoteOK"],
                default=["LinkedIn", "Indeed", "Glassdoor", "ZipRecruiter"]
            )
        with f_freshness:
            hours_map = {"Last 24 Hours": 24, "Last 3 Days": 72, "Last 7 Days": 168, "Last 30 Days": 720}
            freshness_label = st.selectbox("Date Posted:", list(hours_map.keys()), index=1)
            hours_val = hours_map[freshness_label]
        with f_results:
            results_count = st.slider("Max Results:", min_value=5, max_value=25, value=12)
        with f_btn:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            search_clicked = st.button("🚀 Find & Rank Jobs", use_container_width=True, type="primary")

    # If no profile attached yet and search not explicitly requested
    if not st.session_state.get("profile_loaded", False) and not search_clicked and not st.session_state.discovered_jobs:
        st.info("👆 **Please attach your LinkedIn Profile PDF in Step 1 above.** All details (skills, experience, headline, contact info, and location) will be extracted from your PDF only.")
    else:
        # Perform Search
        if search_clicked or (not st.session_state.discovered_jobs and st.session_state.get("profile_loaded", False)):
            search_term_to_use = search_query or st.session_state.get("target_role_query", "Software Engineer")
            with st.spinner(f"Scanning portals for '{search_term_to_use}' in {selected_country}..."):
                is_remote_flag = (work_mode == "Remote Only")
                raw_jobs = search_jobs_multi_portal(
                    search_term=search_term_to_use,
                    country=selected_country,
                    location=location_query,
                    is_remote=is_remote_flag,
                    selected_portals=chosen_portals,
                    results_wanted=results_count,
                    hours_old=hours_val,
                    use_live_scraper=True
                )
                # Rank with AI Matcher against current applicant profile
                ranked_jobs = rank_jobs_for_applicant(raw_jobs, st.session_state.applicant_profile, api_key=api_key_input)
                st.session_state.discovered_jobs = ranked_jobs

        jobs = st.session_state.discovered_jobs

        # Search Results Header
        if jobs:
            st.markdown(f"### 🎯 Found & Ranked {len(jobs)} Opportunities for Your Profile")
            st.caption("Roles are automatically sorted in descending order of **Fit Score** based on your skills, experience, and title alignment.")

            # Render Ranked Jobs
            for idx, job in enumerate(jobs):
                with st.container(border=True):
                    score = job.fit_score
                    tier = job.match_tier
                    badge_class = "badge-success" if score >= 80 else ("badge-info" if score >= 65 else "badge-warning")

                    c_header_left, c_header_right = st.columns([3.5, 1.2])
                    with c_header_left:
                        st.markdown(f"### {job.title}")
                        sal_part = f" &nbsp;•&nbsp; 💰 **{job.salary}**" if job.salary else ""
                        st.markdown(f"🏢 **{job.company}** &nbsp;•&nbsp; 📍 {job.location} &nbsp;•&nbsp; 🌐 **{job.source}**{sal_part}")
                    with c_header_right:
                        st.markdown(f'<div style="text-align: right;"><span class="badge-pill {badge_class}" style="font-size: 0.95rem;">{tier} ({score}%)</span></div>', unsafe_allow_html=True)

                    st.info(f"💡 **AI Fit Summary:** {job.match_summary}")

                    col_skills, col_actions = st.columns([2.8, 1.4])
                    with col_skills:
                        matching_pills = " ".join([f'<span class="badge-pill badge-success">✓ {s}</span>' for s in job.matching_skills[:5]])
                        missing_pills = " ".join([f'<span class="badge-pill badge-warning">⚠ {s}</span>' for s in job.missing_skills[:3]])
                        st.markdown(f"**Matching Skills:** {matching_pills if matching_pills else 'Core skills identified'} &nbsp; {missing_pills}", unsafe_allow_html=True)

                    with col_actions:
                        btn_c1, btn_c2 = st.columns([1, 1])
                        with btn_c1:
                            if st.button("⚡ Apply", key=f"apply_{job.id}_{idx}", type="primary", use_container_width=True):
                                st.session_state.selected_job = job
                                st.session_state.tailored_cover_letter = generate_tailored_cover_letter(job, st.session_state.applicant_profile, api_key_input)
                                st.session_state.user_consent = False
                                st.query_params["tab"] = "apply"
                                st.rerun()
                        with btn_c2:
                            if st.button("⭐ Save", key=f"save_{job.id}_{idx}", use_container_width=True):
                                rec = ApplicationRecord(
                                    job_id=job.id,
                                    job_title=job.title,
                                    company=job.company,
                                    location=job.location,
                                    job_url=job.job_url,
                                    source=job.source,
                                    fit_score=job.fit_score,
                                    status="Shortlisted"
                                )
                                save_application(rec)
                                st.toast(f"Saved {job.title} at {job.company} to Pipeline!", icon="⭐")

                    with st.expander("📖 View Cleaned Job Description", expanded=False):
                        st.markdown(clean_html_text(job.description))


# ==============================================================================
# SECTION 2: CONSENT & AUTO-APPLY CENTER
# ==============================================================================
elif app_mode == "⚡ Consent & Auto-Apply Center":
    st.markdown('<div class="main-title">⚡ Consent & Auto-Apply Control Center</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Review the job details, customize your AI-tailored cover letter, grant explicit consent, and auto-fill your application in one click.</div>', unsafe_allow_html=True)

    selected_job = st.session_state.selected_job

    if not selected_job:
        st.info("👋 No job currently selected! Please search for a role in **Job Search & Best-Fit Matches** and click **⚡ Apply** on any posting.")
        if st.session_state.discovered_jobs:
            st.markdown("##### Or pick from your recent search results:")
            for j in st.session_state.discovered_jobs[:4]:
                if st.button(f"Select: {j.title} at {j.company} ({j.fit_score}% match)", key=f"pick_{j.id}"):
                    st.session_state.selected_job = j
                    st.session_state.tailored_cover_letter = generate_tailored_cover_letter(j, st.session_state.applicant_profile, api_key_input)
                    st.rerun()
        st.stop()

    # Render Selected Job Info
    c_job1, c_job2 = st.columns([2.5, 1])
    with c_job1:
        st.markdown(f"### 💼 {selected_job.title}")
        st.markdown(f"**Company:** {selected_job.company} &nbsp;•&nbsp; **Location:** {selected_job.location} &nbsp;•&nbsp; **Portal:** {selected_job.source}")
    with c_job2:
        st.metric("AI Fit Score", f"{selected_job.fit_score}%", selected_job.match_tier)

    with st.expander("📄 Full Job Description & Requirements", expanded=False):
        cleaned_desc = clean_html_text(selected_job.description)
        st.markdown(cleaned_desc)
        if selected_job.job_url:
            st.markdown(f"🔗 [Direct Posting URL]({selected_job.job_url})")

    st.markdown("---")

    # Tailored Application Kit
    st.markdown("### 📝 Tailored Application Kit")
    t1, t2 = st.tabs(["✉️ AI Tailored Cover Letter", "📋 Application Form Q&A"])

    with t1:
        st.caption("Custom-crafted for this specific company and role, highlighting your matching background:")
        cover_text = st.text_area(
            "Cover Letter (Editable):",
            value=st.session_state.tailored_cover_letter,
            height=260
        )
        st.session_state.tailored_cover_letter = cover_text

        col_regen, col_copy = st.columns([1, 1])
        with col_regen:
            if st.button("🔄 Regenerate Cover Letter with AI"):
                with st.spinner("Re-crafting tailored cover letter..."):
                    st.session_state.tailored_cover_letter = generate_tailored_cover_letter(selected_job, st.session_state.applicant_profile, api_key_input)
                    st.rerun()

    with t2:
        qa_answers = generate_application_answers(selected_job, st.session_state.applicant_profile, api_key_input)
        st.caption("Standard application questions pre-filled for portals like Greenhouse, Lever, Workday:")
        for q, a in qa_answers.items():
            st.text_input(q, value=a, key=f"qa_{q}")

    st.markdown("---")

    # ==========================================================================
    # USER CONSENT GATE
    # ==========================================================================
    st.markdown("### 🔒 Step 1: User Consent Verification")
    st.warning("⚠️ **Security & Consent Requirement:** To prevent accidental submissions, this assistant operates with **human-in-the-loop consent**. You must review the tailored application materials and check the consent box below before auto-fill tools are unlocked.")

    consent_given = st.checkbox(
        f"✅ I have reviewed the application materials and give my consent to auto-fill my details for '{selected_job.title}' at {selected_job.company}.",
        value=st.session_state.user_consent,
        key="chk_consent"
    )
    st.session_state.user_consent = consent_given

    if not consent_given:
        st.warning("Please check the consent box above to unlock auto-fill and submission tools.")
    else:
        st.success("🎉 Consent granted! You can now use any of the auto-fill and application tools below:")

        st.markdown("### 🚀 Step 2: Auto-Fill & Apply Tools")

        a1, a2, a3 = st.tabs([
            "🌐 1-Click Universal Browser Auto-Fill",
            "🤖 Automated Browser (Playwright)",
            "📋 Quick-Fill Clipboard Assistant"
        ])

        scripts = generate_browser_autofill_script(
            selected_job,
            st.session_state.applicant_profile,
            st.session_state.tailored_cover_letter
        )

        with a1:
            st.markdown("#### 🌟 1-Click Browser Auto-Fill Bookmarklet")
            st.write("""
            **How to use:**
            1. Drag the blue button below into your browser's Bookmarks bar (or copy the script).
            2. Open the job application page (Greenhouse, Lever, LinkedIn, Workday, Indeed, etc.).
            3. Click the bookmark in your browser! It instantly auto-fills First Name, Last Name, Email, Phone, LinkedIn, GitHub, Location, and Cover Letter!
            """)

            st.markdown(f"""
            <div style="margin: 20px 0;">
                <a href="{scripts['bookmarklet_url']}" class="bookmarklet-btn">⚡ AI Auto-Fill Bookmarklet (Drag to Bookmarks Bar)</a>
            </div>
            """, unsafe_allow_html=True)

            if selected_job.job_url:
                st.link_button(f"↗️ Open Job Posting Page ({selected_job.company})", selected_job.job_url, type="primary")

            with st.expander("View Raw JavaScript Snippet (For Browser Console)"):
                st.code(scripts["raw_js"], language="javascript")

        with a2:
            st.markdown("#### 🤖 Automated Browser Mode (Playwright)")
            st.write("Launches a local browser window, navigates to the job portal, and auto-fills all matching form inputs so you can inspect and submit.")
            
            target_url = st.text_input("Application URL to launch:", value=selected_job.job_url or "https://www.linkedin.com/jobs")
            
            if st.button("🚀 Launch Playwright Auto-Fill Browser"):
                with st.spinner("Launching headed Chromium browser & auto-filling form..."):
                    result = launch_playwright_autofill(
                        target_url,
                        st.session_state.applicant_profile,
                        st.session_state.tailored_cover_letter
                    )
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.info(result["message"])

        with a3:
            st.markdown("#### 📋 1-Click Quick-Fill Field Matrix")
            st.caption("Quickly copy individual pre-formatted answers to your clipboard:")
            
            q_cols = st.columns(2)
            with q_cols[0]:
                st.text_input("Full Name:", value=st.session_state.applicant_profile.full_name, key="c_name")
                st.text_input("Email:", value=st.session_state.applicant_profile.email, key="c_email")
                st.text_input("Phone:", value=st.session_state.applicant_profile.phone, key="c_phone")
                st.text_input("LinkedIn:", value=st.session_state.applicant_profile.linkedin_url, key="c_in")
            with q_cols[1]:
                st.text_input("GitHub:", value=st.session_state.applicant_profile.github_url, key="c_gh")
                st.text_input("Portfolio:", value=st.session_state.applicant_profile.portfolio_url, key="c_port")
                st.text_input("Work Authorization:", value=st.session_state.applicant_profile.work_authorization, key="c_auth")
                st.text_input("Notice Period:", value=st.session_state.applicant_profile.notice_period, key="c_not")

        # Mark as Applied
        st.markdown("---")
        st.markdown("#### 💾 Save Application to Tracker")
        track_col1, track_col2 = st.columns([1.5, 1])
        with track_col1:
            app_status = st.selectbox("Set Application Status:", ["Applied", "Consented", "Interviewing", "Shortlisted"], index=0)
            app_notes = st.text_input("Notes (e.g. Applied via LinkedIn Easy Apply):", value="Applied via 1-click auto-fill assistant")
        with track_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("💾 Record in Application Pipeline", type="primary", use_container_width=True):
                rec = ApplicationRecord(
                    job_id=selected_job.id,
                    job_title=selected_job.title,
                    company=selected_job.company,
                    location=selected_job.location,
                    job_url=selected_job.job_url,
                    source=selected_job.source,
                    fit_score=selected_job.fit_score,
                    status=app_status,
                    tailored_cover_letter=st.session_state.tailored_cover_letter,
                    notes=app_notes
                )
                save_application(rec)
                st.success(f"Recorded application for {selected_job.title} at {selected_job.company} as '{app_status}'!")


# ==============================================================================
# SECTION 3: LINKEDIN PROFILE & APPLICANT SETUP
# ==============================================================================
elif app_mode == "💼 LinkedIn Profile & Applicant Setup":
    st.markdown('<div class="main-title">💼 LinkedIn Profile & Applicant Setup</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Audit your LinkedIn profile like an executive recruiter, discover keyword gaps, and configure your applicant auto-fill details.</div>', unsafe_allow_html=True)

    input_mode = st.radio("Choose Input Method:", ["Upload LinkedIn PDF", "Manual Inputs & Auto-Fill Details", "Demo Profiles"], horizontal=True)

    if input_mode == "Demo Profiles":
        demo_choice = st.selectbox("Select a Demo Profile:", list(SAMPLE_PROFILES.keys()))
        if st.button("Load This Demo Profile"):
            demo = SAMPLE_PROFILES[demo_choice]
            p = st.session_state.applicant_profile
            p.full_name = demo["name"]
            p.first_name = demo["name"].split()[0]
            p.last_name = demo["name"].split()[-1] if len(demo["name"].split()) > 1 else ""
            p.headline = demo["headline"]
            p.about = demo["about"]
            p.experience = demo["experience"]
            p.skills = demo["skills"]
            st.success(f"Loaded demo profile: {demo['name']}")

    elif input_mode == "Upload LinkedIn PDF":
        st.caption("💡 *How to export:* Open your LinkedIn profile -> Click **More** -> Click **Save to PDF**.")
        uploaded_pdf = st.file_uploader("Upload LinkedIn PDF Export:", type=["pdf"])
        if uploaded_pdf is not None:
            should_parse_s3 = (st.session_state.get("last_processed_pdf_name") != uploaded_pdf.name)
            btn_clicked_s3 = st.button("Parse & Extract PDF", type="primary")
            if should_parse_s3 or btn_clicked_s3:
                with st.spinner("Extracting sections directly from PDF..."):
                    raw_text = extract_text_from_pdf(uploaded_pdf)
                    parsed = parse_linkedin_text(raw_text)
                    p = st.session_state.applicant_profile
                    p.full_name = parsed.get("name", "")
                    p.first_name = p.full_name.split()[0] if p.full_name else ""
                    p.last_name = p.full_name.split()[-1] if len(p.full_name.split()) > 1 else ""
                    p.headline = parsed.get("headline", "")
                    p.location = parsed.get("location", "")
                    p.country = parsed.get("country", "")
                    p.city = parsed.get("city", "")
                    p.current_location = p.location or f"{p.city}, {p.country}".strip(", ")
                    p.email = parsed.get("email", "")
                    p.phone = parsed.get("phone", "")
                    p.linkedin_url = parsed.get("linkedin_url", "")
                    p.about = parsed.get("about", "")
                    p.experience = parsed.get("experience", "")
                    p.skills = parsed.get("skills", [])
                    p.education = parsed.get("education", "")
                    st.session_state.profile_loaded = True
                    st.session_state.location_configured = True
                    st.session_state.last_processed_pdf_name = uploaded_pdf.name
                    if p.headline:
                        st.session_state.target_role_query = p.headline.split("|")[0].split("-")[0].strip()
                    st.session_state.discovered_jobs = []
                    loc_display = f"{p.city}, {p.country}".strip(", ") or p.location or "Location detected"
                    st.success(f"✅ LinkedIn PDF successfully parsed! Loaded {p.full_name or 'Candidate'} | Location: {loc_display}")
                    st.rerun()

    # Editable Profile Tabs
    p = st.session_state.applicant_profile
    tab_form, tab_audit = st.tabs(["📝 Applicant Form Details (For Auto-Fill)", "📊 LinkedIn Profile Audit & Heuristics"])

    with tab_form:
        st.markdown("#### Candidate Details for Auto-Filling Job Forms")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            p.full_name = st.text_input("Full Name:", value=p.full_name)
            p.email = st.text_input("Email:", value=p.email)
            p.phone = st.text_input("Phone:", value=p.phone)
            p.country = st.text_input("Country:", value=p.country)
            p.city = st.text_input("City / State:", value=p.city)
        with col_c2:
            p.linkedin_url = st.text_input("LinkedIn Profile URL:", value=p.linkedin_url)
            p.github_url = st.text_input("GitHub URL:", value=p.github_url)
            p.portfolio_url = st.text_input("Portfolio / Website URL:", value=p.portfolio_url)
            p.work_authorization = st.text_input("Work Authorization:", value=p.work_authorization)
            p.expected_salary = st.text_input("Expected Salary:", value=p.expected_salary)

        st.markdown("#### Resume / Profile Sections")
        p.headline = st.text_input("Headline (Max 220 chars):", value=p.headline)
        p.skills = [s.strip() for s in st.text_input("Skills (comma-separated):", value=", ".join(p.skills)).split(",") if s.strip()]
        p.about = st.text_area("About / Summary:", value=p.about, height=120)
        p.experience = st.text_area("Experience (Bullet points):", value=p.experience, height=140)

    with tab_audit:
        h_audit = score_headline(p.headline)
        a_audit = score_about(p.about)
        e_audit = score_experience(p.experience)
        eval_role = st.session_state.get("target_role_query", "") or (p.headline.split("|")[0].strip() if p.headline else "Software Engineer")
        r_fit = analyze_role_fit(f"{p.headline}\n{p.about}\n{p.experience}", p.skills, eval_role)
        overall = compute_overall_profile_score(h_audit, a_audit, e_audit, r_fit)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Overall Score", f"{overall['overall_score']}/100", overall['tier'])
        m2.metric("Headline Hook", f"{h_audit['score']}%")
        m3.metric("About Narrative", f"{a_audit['score']}%")
        m4.metric("Experience Metrics", f"{e_audit['score']}%")

        st.markdown("##### ⏱️ Recruiter 10-Second Scan Simulation")
        scan_items = recruiter_10_second_audit(p.to_dict(), overall["overall_score"])
        for item in scan_items:
            status_badge = "badge-success" if item["status"] == "PASS" else "badge-warning"
            with st.container(border=True):
                c_scan1, c_scan2 = st.columns([3.5, 1])
                c_scan1.markdown(f"**{item['phase']}**")
                c_scan2.markdown(f'<div style="text-align: right;"><span class="badge-pill {status_badge}">{item["status"]}</span></div>', unsafe_allow_html=True)
                st.caption(item["comment"])


# ==============================================================================
# SECTION 4: APPLICATION PIPELINE TRACKER
# ==============================================================================
elif app_mode == "📋 Application Pipeline Tracker":
    st.markdown('<div class="main-title">📋 Application Pipeline & Tracker</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Track your job applications, monitor interview stages, and manage your job hunt pipeline.</div>', unsafe_allow_html=True)

    stats = get_pipeline_stats()
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Shortlisted", stats.get("Shortlisted", 0))
    s2.metric("Consented", stats.get("Consented", 0))
    s3.metric("Applied", stats.get("Applied", 0))
    s4.metric("Interviewing", stats.get("Interviewing", 0))
    s5.metric("Offers", stats.get("Offer", 0))

    st.markdown("---")

    applications = get_all_applications()

    if not applications:
        st.info("No applications recorded yet. Start applying to jobs in **Job Search & Best-Fit Matches** and save them here!")
    else:
        st.markdown(f"### Tracked Applications ({len(applications)})")
        
        for app in reversed(applications):
            with st.container():
                col_info, col_stat, col_del = st.columns([3, 1.2, 0.5])
                with col_info:
                    st.markdown(f"**{app.job_title}** at **{app.company}**")
                    st.caption(f"📍 {app.location} &nbsp;•&nbsp; 🌐 {app.source} &nbsp;•&nbsp; 📅 Applied: {app.applied_date} &nbsp;•&nbsp; Match: {app.fit_score}%")
                    if app.notes:
                        st.caption(f"💬 *Note:* {app.notes}")
                    if app.job_url:
                        st.markdown(f"[View Job Posting]({app.job_url})")

                with col_stat:
                    new_status = st.selectbox(
                        "Status:",
                        ["Shortlisted", "Consented", "Applied", "Interviewing", "Offer", "Rejected"],
                        index=["Shortlisted", "Consented", "Applied", "Interviewing", "Offer", "Rejected"].index(app.status) if app.status in ["Shortlisted", "Consented", "Applied", "Interviewing", "Offer", "Rejected"] else 2,
                        key=f"status_{app.job_id}"
                    )
                    if new_status != app.status:
                        update_application_status(app.job_id, new_status)
                        st.rerun()

                with col_del:
                    st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_{app.job_id}", help="Delete application"):
                        delete_application(app.job_id)
                        st.rerun()

                st.markdown("---")

        # Export tracker
        export_json = json.dumps([a.to_dict() for a in applications], indent=2)
        st.download_button(
            "📥 Download Application History (JSON)",
            data=export_json,
            file_name=f"job_applications_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
