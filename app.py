import os
import streamlit as st
import plotly.graph_objects as go
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()

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

# Page configuration
st.set_page_config(
    page_title="LinkedIn Profile AI Analyzer & Optimizer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 800;
        color: #0A66C2;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.5rem;
    }
    .score-card {
        background: #f8fafd;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .score-val {
        font-size: 2.2rem;
        font-weight: 800;
        margin: 5px 0;
    }
    .score-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-pill {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 2px;
    }
    .badge-success { background: #dcfce7; color: #166534; }
    .badge-warning { background: #fef3c7; color: #92400e; }
    .badge-info { background: #e0f2fe; color: #075985; }
    .recruiter-scan-box {
        background: #ffffff;
        border-left: 5px solid #0A66C2;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 10px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state for profile inputs
if "profile_data" not in st.session_state:
    st.session_state.profile_data = {
        "name": "",
        "headline": "",
        "about": "",
        "experience": "",
        "skills": [],
        "target_role": "AI & Machine Learning Engineer"
    }

# SIDEBAR CONFIGURATION
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3536/3536505.png", width=55)
st.sidebar.title("Profile Controls")

input_mode = st.sidebar.radio(
    "Choose Input Method:",
    ["Upload LinkedIn PDF", "Manual Text Input", "Demo Profiles"],
    index=0
)

target_roles_list = list(ROLE_BENCHMARKS.keys())
selected_target_role = st.sidebar.selectbox(
    "Target Job Role / Benchmarks:",
    target_roles_list,
    index=0
)

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

# HANDLE INPUT MODES
if input_mode == "Demo Profiles":
    st.sidebar.markdown("---")
    demo_choice = st.sidebar.selectbox("Select a Demo Profile:", list(SAMPLE_PROFILES.keys()))
    if st.sidebar.button("Load This Demo Profile", use_container_width=True):
        demo = SAMPLE_PROFILES[demo_choice]
        st.session_state.profile_data = {
            "name": demo["name"],
            "headline": demo["headline"],
            "about": demo["about"],
            "experience": demo["experience"],
            "skills": demo["skills"],
            "target_role": demo["target_role"]
        }
        st.sidebar.success(f"Loaded demo: {demo['name']}")

elif input_mode == "Upload LinkedIn PDF":
    st.sidebar.markdown("---")
    st.sidebar.caption("💡 *How to export:* Open your LinkedIn profile -> Click **More** -> Click **Save to PDF**.")
    uploaded_pdf = st.sidebar.file_uploader("Upload LinkedIn PDF Export:", type=["pdf"])
    if uploaded_pdf is not None:
        if st.sidebar.button("Parse & Extract PDF", use_container_width=True):
            with st.spinner("Extracting sections from PDF..."):
                raw_text = extract_text_from_pdf(uploaded_pdf)
                parsed = parse_linkedin_text(raw_text)
                st.session_state.profile_data = {
                    "name": parsed["name"] or "LinkedIn Member",
                    "headline": parsed["headline"],
                    "about": parsed["about"],
                    "experience": parsed["experience"],
                    "skills": parsed["skills"],
                    "target_role": selected_target_role
                }
                st.sidebar.success("PDF successfully parsed!")

# MAIN HEADER
st.markdown('<div class="main-title">💼 LinkedIn Profile AI Analyzer & Optimizer</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Audit your LinkedIn profile like a top-tier executive recruiter. Uncover keyword gaps, boost recruiter search ranking, and generate high-impact rewrites.</div>', unsafe_allow_html=True)

# EDITABLE PROFILE SECTION
with st.expander("📝 View / Edit Profile Inputs", expanded=(input_mode == "Manual Text Input" or not st.session_state.profile_data["headline"])):
    col1, col2 = st.columns([1, 1])
    with col1:
        prof_name = st.text_input("Full Name:", value=st.session_state.profile_data.get("name", "Candidate"))
        prof_headline = st.text_input("Headline (Max 220 chars):", value=st.session_state.profile_data.get("headline", ""), max_chars=220)
        prof_skills_raw = st.text_input("Skills (comma-separated):", value=", ".join(st.session_state.profile_data.get("skills", [])))
    with col2:
        prof_about = st.text_area("About / Summary Section:", value=st.session_state.profile_data.get("about", ""), height=135)
    
    prof_experience = st.text_area("Experience (Bullet points / Work History):", value=st.session_state.profile_data.get("experience", ""), height=150)
    
    # Save edits into session state
    if st.button("Apply & Update Profile"):
        parsed_skills = [s.strip() for s in prof_skills_raw.split(",") if s.strip()]
        st.session_state.profile_data.update({
            "name": prof_name,
            "headline": prof_headline,
            "about": prof_about,
            "experience": prof_experience,
            "skills": parsed_skills,
            "target_role": selected_target_role
        })
        st.success("Profile updated!")

# CURRENT DATA REFERENCE
cur_data = st.session_state.profile_data
cur_headline = cur_data.get("headline", "")
cur_about = cur_data.get("about", "")
cur_experience = cur_data.get("experience", "")
cur_skills = cur_data.get("skills", [])
cur_role = selected_target_role

# CHECK IF ENOUGH DATA TO ANALYZE
if not cur_headline and not cur_about and not cur_experience:
    st.info("👋 Welcome! To begin analysis, select a **Demo Profile** from the left sidebar, or upload your LinkedIn profile PDF export.")
    st.stop()

# RUN ANALYSIS ENGINES
headline_audit = score_headline(cur_headline)
about_audit = score_about(cur_about)
exp_audit = score_experience(cur_experience)
combined_text = f"{cur_headline}\n{cur_about}\n{cur_experience}"
role_fit = analyze_role_fit(combined_text, cur_skills, cur_role)
overall_res = compute_overall_profile_score(headline_audit, about_audit, exp_audit, role_fit)
recruiter_scan = recruiter_10_second_audit(cur_data, overall_res["overall_score"])

# TOP METRICS DASHBOARD
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    color_map = {"green": "#16a34a", "blue": "#2563eb", "orange": "#ea580c", "red": "#dc2626"}
    c = color_map.get(overall_res["badge_color"], "#2563eb")
    st.markdown(f"""
    <div class="score-card">
        <div class="score-label">Overall Score</div>
        <div class="score-val" style="color: {c};">{overall_res["overall_score"]}/100</div>
        <span class="badge-pill badge-info">{overall_res["tier"].split()[0]} {overall_res["tier"].split()[1]}</span>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="score-card">
        <div class="score-label">Headline Hook</div>
        <div class="score-val" style="color: #0A66C2;">{headline_audit["score"]}%</div>
        <span class="badge-pill badge-info">{headline_audit["char_count"]} / 220 chars</span>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="score-card">
        <div class="score-label">About Section</div>
        <div class="score-val" style="color: #0A66C2;">{about_audit["score"]}%</div>
        <span class="badge-pill badge-info">{about_audit["word_count"]} words</span>
    </div>
    """, unsafe_allow_html=True)

with m4:
    st.markdown(f"""
    <div class="score-card">
        <div class="score-label">Experience Impact</div>
        <div class="score-val" style="color: #0A66C2;">{exp_audit["score"]}%</div>
        <span class="badge-pill badge-success">{exp_audit["metrics_count"]} metrics found</span>
    </div>
    """, unsafe_allow_html=True)

with m5:
    st.markdown(f"""
    <div class="score-card">
        <div class="score-label">Target Role Match</div>
        <div class="score-val" style="color: #0A66C2;">{role_fit["match_percentage"]}%</div>
        <span class="badge-pill badge-info">{len(role_fit["found_skills"])} core skills</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# VISUAL RADAR CHART & 10-SEC SCAN ROW
col_chart, col_scan = st.columns([1, 1])

with col_chart:
    st.subheader("📈 Profile Strength Radar")
    categories = ['Headline Hook', 'About Narrative', 'Metrics & STAR', 'Role Match', 'Action Verbs']
    
    # Normalize action verb score out of 100
    verb_score = min(int((exp_audit["action_verbs_count"] / 8) * 100), 100)
    
    values = [
        headline_audit["score"],
        about_audit["score"],
        exp_audit["score"],
        role_fit["match_percentage"],
        verb_score
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(10, 102, 194, 0.25)',
        line=dict(color='#0A66C2', width=2.5),
        name='Your Profile'
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickfont=dict(size=9))
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=320
    )
    st.plotly_chart(fig, use_container_width=True)

with col_scan:
    st.subheader("⏱️ Recruiter 10-Second Scan Simulation")
    st.caption("How recruiters triage your profile in the initial 10-second glance:")
    for item in recruiter_scan:
        status_badge = "badge-success" if item["status"] == "PASS" else "badge-warning"
        st.markdown(f"""
        <div class="recruiter-scan-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <strong>{item["phase"]}</strong>
                <span class="badge-pill {status_badge}">{item["status"]}</span>
            </div>
            <div style="font-size: 0.9rem; color: #475569;">{item["comment"]}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# DEEP DIVE TABS
tabs = st.tabs([
    "📊 Section Audit & Gaps",
    "🎯 Target Role Fit",
    "✨ AI Headline Generator",
    "📝 AI About Section",
    "🚀 Google XYZ Bullet Optimizer",
    "💡 LinkedIn Creator Posts",
    "📥 Download Full Report"
])

# TAB 1: SECTION AUDIT & GAPS
with tabs[0]:
    st.subheader("Deep-Dive Breakdown & Recommendations")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📌 Headline Analysis")
        st.metric("Headline Score", f"{headline_audit['score']}/100")
        if headline_audit["strengths"]:
            st.success("✅ **Strengths:**\n- " + "\n- ".join(headline_audit["strengths"]))
        if headline_audit["feedback"]:
            st.warning("⚠️ **Improvement Areas:**\n- " + "\n- ".join(headline_audit["feedback"]))

        st.markdown("#### 📖 About / Summary Analysis")
        st.metric("About Score", f"{about_audit['score']}/100")
        if about_audit["strengths"]:
            st.success("✅ **Strengths:**\n- " + "\n- ".join(about_audit["strengths"]))
        if about_audit["feedback"]:
            st.warning("⚠️ **Improvement Areas:**\n- " + "\n- ".join(about_audit["feedback"]))

    with c2:
        st.markdown("#### 💼 Experience & Achievements")
        st.metric("Experience Score", f"{exp_audit['score']}/100")
        if exp_audit["strengths"]:
            st.success("✅ **Strengths:**\n- " + "\n- ".join(exp_audit["strengths"]))
        if exp_audit["feedback"]:
            st.warning("⚠️ **Improvement Areas:**\n- " + "\n- ".join(exp_audit["feedback"]))
            
        if exp_audit.get("sample_verbs"):
            st.info(f"**Identified Action Verbs:** {', '.join(exp_audit['sample_verbs'])}")

# TAB 2: TARGET ROLE FIT
with tabs[1]:
    st.subheader(f"Role Benchmark: {cur_role}")
    st.write(f"Compare your profile keyword density against real-world recruiter search benchmarks for **{cur_role}**.")
    
    st.progress(role_fit["match_percentage"] / 100)
    st.caption(f"ATS Keyword Match Rate: **{role_fit['match_percentage']}%**")
    
    col_found, col_miss = st.columns(2)
    with col_found:
        st.markdown("##### ✅ Keywords & Skills Present in Profile")
        if role_fit["found_skills"]:
            found_html = " ".join([f'<span class="badge-pill badge-success">{s}</span>' for s in role_fit["found_skills"]])
            st.markdown(found_html, unsafe_allow_html=True)
        else:
            st.write("No matching primary skills detected yet.")

    with col_miss:
        st.markdown("##### ⚠️ High-Value Keywords Missing")
        if role_fit["missing_skills"]:
            miss_html = " ".join([f'<span class="badge-pill badge-warning">{s}</span>' for s in role_fit["missing_skills"]])
            st.markdown(miss_html, unsafe_allow_html=True)
            st.caption("Consider adding relevant experience or projects demonstrating these skills to improve recruiter discovery.")
        else:
            st.success("Outstanding! All benchmark skills for this role are represented.")

    st.markdown("##### 🚀 Recommended High-Impact Verbs for this Role:")
    st.write(", ".join([f"**{v}**" for v in role_fit["recommended_action_verbs"]]))

# TAB 3: AI HEADLINE GENERATOR
with tabs[2]:
    st.subheader("Tailored LinkedIn Headlines (5 Variations)")
    st.caption("A top-tier headline converts profile views into recruiter interview inquiries.")
    
    if st.button("Generate Headline Variants", key="btn_headlines"):
        with st.spinner("Crafting high-converting headlines..."):
            headlines = generate_headlines(cur_headline, cur_role, cur_skills, api_key_input)
            st.session_state["generated_headlines"] = headlines

    if "generated_headlines" in st.session_state:
        for item in st.session_state["generated_headlines"]:
            with st.container():
                st.markdown(f"**{item['style']}**")
                st.code(item["headline"], language="text")

# TAB 4: AI ABOUT SECTION
with tabs[3]:
    st.subheader("Rewritten About Section (3 Styles)")
    st.caption("Pick the voice that best fits your career stage and personality.")
    
    if st.button("Generate Rewritten About Sections", key="btn_about"):
        with st.spinner("Drafting full profile summaries..."):
            about_variants = generate_about_rewrites(cur_about, cur_role, cur_skills, api_key_input)
            st.session_state["generated_about"] = about_variants

    if "generated_about" in st.session_state:
        about_tabs = st.tabs([item["style"] for item in st.session_state["generated_about"]])
        for i, tab in enumerate(about_tabs):
            with tab:
                st.text_area(f"Copy {st.session_state['generated_about'][i]['style']}:", value=st.session_state["generated_about"][i]["content"], height=320)

# TAB 5: GOOGLE XYZ BULLET OPTIMIZER
with tabs[4]:
    st.subheader("Google XYZ Formula Experience Bullet Transformer")
    st.markdown("""
    > **Google's Formula for High-Impact Resumes & Profiles:**  
    > *"Accomplished [X] as measured by [Y], by doing [Z]"*
    """)
    
    sample_bullets_input = st.text_area(
        "Enter 1 to 5 experience bullet points to transform:",
        value=cur_experience[:600] if cur_experience else "Responsible for developing features for the main product.\nWorked on database speed.\nHelped junior developers with code reviews.",
        height=120
    )
    
    if st.button("Transform Bullets with XYZ Formula", key="btn_bullets"):
        with st.spinner("Applying Google XYZ formula..."):
            transformed = transform_bullet_points(sample_bullets_input, api_key_input)
            st.session_state["transformed_bullets"] = transformed

    if "transformed_bullets" in st.session_state:
        for idx, t in enumerate(st.session_state["transformed_bullets"]):
            st.markdown(f"##### Bullet #{idx+1}")
            col_b1, col_b2 = st.columns([1, 1.3])
            with col_b1:
                st.markdown("**Original:**")
                st.info(t["original"])
            with col_b2:
                st.markdown("**Optimized (XYZ Formula):**")
                st.success(t["optimized"])
                st.caption(f"💡 *Breakdown:* {t['breakdown']}")
            st.markdown("---")

# TAB 6: LINKEDIN CREATOR POSTS
with tabs[5]:
    st.subheader("Thought Leadership & Personal Brand Post Ideas")
    st.caption("Posting once a week on LinkedIn increases profile visits by up to 500% according to LinkedIn Creator analytics.")
    
    if st.button("Generate 5 LinkedIn Post Hooks", key="btn_posts"):
        with st.spinner("Generating viral post concepts..."):
            post_ideas = generate_linkedin_post_ideas(cur_role, cur_skills, cur_experience, api_key_input)
            st.session_state["generated_posts"] = post_ideas

    if "generated_posts" in st.session_state:
        for post in st.session_state["generated_posts"]:
            with st.expander(post.get("title", "Post Concept"), expanded=True):
                if "hook" in post:
                    st.markdown(f"**Hook (First 2 Lines):**\n> *\"{post['hook']}\"*")
                    st.markdown(f"**Core Takeaway:** {post['concept']}")
                    st.caption(post.get("hashtags", ""))
                else:
                    st.write(post.get("content", ""))

# TAB 7: DOWNLOAD REPORT
with tabs[6]:
    st.subheader("Export Comprehensive LinkedIn Profile Audit")
    st.write("Generate a complete, actionable audit report formatted in clean Markdown to save or share with mentors.")
    
    report_md = f"""# LinkedIn Profile AI Audit Report
**Candidate:** {cur_data.get('name', 'Professional')}  
**Target Role:** {cur_role}  
**Overall Score:** {overall_res['overall_score']}/100 ({overall_res['tier']})  

---

## 1. Scorecard Overview
- **Headline Score:** {headline_audit['score']}/100 ({headline_audit['char_count']} chars)
- **About / Summary Score:** {about_audit['score']}/100 ({about_audit['word_count']} words)
- **Experience Impact Score:** {exp_audit['score']}/100 ({exp_audit['metrics_count']} metrics identified)
- **Target Role Keyword Fit:** {role_fit['match_percentage']}%

---

## 2. Recruiter 10-Second Scan Simulation
"""
    for item in recruiter_scan:
        report_md += f"- **[{item['status']}] {item['phase']}:** {item['comment']}\n"

    report_md += f"""
---

## 3. Targeted Skill Gap Analysis
- **Matching Core Skills ({len(role_fit['found_skills'])}):** {', '.join(role_fit['found_skills']) if role_fit['found_skills'] else 'None'}
- **Missing Priority Keywords ({len(role_fit['missing_skills'])}):** {', '.join(role_fit['missing_skills']) if role_fit['missing_skills'] else 'None'}

---

## 4. Key Strengths
### Headline:
{chr(10).join(['- ' + s for s in headline_audit['strengths']]) if headline_audit['strengths'] else '- Needs optimization.'}

### About Section:
{chr(10).join(['- ' + s for s in about_audit['strengths']]) if about_audit['strengths'] else '- Needs optimization.'}

### Experience:
{chr(10).join(['- ' + s for s in exp_audit['strengths']]) if exp_audit['strengths'] else '- Needs optimization.'}

---

## 5. Priority Action Checklist
{chr(10).join(['- ' + f for f in headline_audit['feedback']]) if headline_audit['feedback'] else ''}
{chr(10).join(['- ' + f for f in about_audit['feedback']]) if about_audit['feedback'] else ''}
{chr(10).join(['- ' + f for f in exp_audit['feedback']]) if exp_audit['feedback'] else ''}

*Report generated by LinkedIn Profile AI Analyzer & Optimizer*
"""

    import re as re_mod
    safe_name = re_mod.sub(r'[^a-zA-Z0-9_-]', '_', cur_data.get('name', 'profile')).lower()
    st.download_button(
        label="📥 Download Audit Report (.md)",
        data=report_md,
        file_name=f"linkedin_audit_{safe_name}.md",
        mime="text/markdown",
        use_container_width=True
    )
    
    with st.expander("Preview Audit Report"):
        st.markdown(report_md)
