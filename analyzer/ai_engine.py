import os
import re
from typing import Dict, List, Any


def call_gemini(prompt: str, api_key: str = None) -> str:
    """Invokes Gemini using google.genai or legacy google.generativeai if available."""
    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        return ""
    
    # Try modern google.genai
    try:
        from google import genai
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        if response and response.text:
            return response.text
    except Exception:
        pass

    # Fallback to legacy SDK if present
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=key)
        model = legacy_genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text
    except Exception:
        pass

    return ""


def generate_headlines(current_headline: str, target_role: str, top_skills: List[str], api_key: str = None) -> List[Dict[str, str]]:
    """
    Generates 5 distinct high-converting LinkedIn headline variations.
    Uses Gemini LLM if key is present, otherwise uses intelligent parametric templates.
    """
    skills_str = ", ".join(top_skills[:5]) if top_skills else "Full Lifecycle Development, Architecture"
    
    prompt = f"""
    Act as an elite LinkedIn Executive Career Coach and Recruiter.
    The candidate's current headline is: "{current_headline}"
    Their target role is: "{target_role}"
    Their top skills: "{skills_str}"

    Generate exactly 5 distinct, high-impact LinkedIn headlines (each under 220 characters).
    Return in this exact format:
    1. [The Recruiter Magnet] - Headline text
    2. [The Metrics & Impact Driven] - Headline text
    3. [The Value Proposition] - Headline text
    4. [The Storyteller & Thought Leader] - Headline text
    5. [The Minimalist Authority] - Headline text
    """
    ai_resp = call_gemini(prompt, api_key)
    if ai_resp:
        try:
            lines = [line.strip() for line in ai_resp.splitlines() if line.strip()]
            results = []
            for line in lines:
                match = re.match(r"^\d+\.\s*\[(.*?)\]\s*[:-]\s*(.*)$", line)
                if match:
                    results.append({"style": match.group(1), "headline": match.group(2).strip()})
                elif " - " in line:
                    parts = line.split(" - ", 1)
                    results.append({"style": parts[0].strip(), "headline": parts[1].strip()})
            if len(results) >= 4:
                return results
        except Exception:
            pass

    # Offline Intelligent Template Engine
    role_clean = target_role if target_role and target_role != "General Tech / Custom" else (current_headline.split("|")[0].strip() or "Senior Software Engineer")
    skill_a = top_skills[0] if len(top_skills) > 0 else "Cloud Architecture"
    skill_b = top_skills[1] if len(top_skills) > 1 else "Scalable Distributed Systems"
    skill_c = top_skills[2] if len(top_skills) > 2 else "Performance Tuning"

    return [
        {
            "style": "The Recruiter Magnet (Search-Optimized)",
            "headline": f"{role_clean} | {skill_a} • {skill_b} • {skill_c} | Driving High-Scale Engineering Impact"
        },
        {
            "style": "The Metrics & Impact Driven",
            "headline": f"{role_clean} | Scaling systems from 0 to 1M+ users | Reduced latency by 40% & cut cloud infrastructure costs"
        },
        {
            "style": "The Value Proposition (Who You Help & How)",
            "headline": f"Helping tech organizations build resilient {skill_a} & {skill_b} solutions | {role_clean} passionate about team velocity"
        },
        {
            "style": "The Storyteller & Thought Leader",
            "headline": f"Building the future of {skill_a} | {role_clean} @ intersection of clean architecture and user-centric products"
        },
        {
            "style": "The Minimalist Authority",
            "headline": f"{role_clean} • {skill_a} Specialist • Technical Leadership & Systems Innovation"
        }
    ]


def generate_about_rewrites(current_about: str, target_role: str, top_skills: List[str], api_key: str = None) -> List[Dict[str, str]]:
    """
    Generates 3 full rewritten versions of the LinkedIn About section:
    1. Conversational & First-Person
    2. Executive & Metrics-Led
    3. Story-Driven Narrative
    """
    skills_str = ", ".join(top_skills[:6]) if top_skills else "Python, Cloud Architecture, System Design"
    
    prompt = f"""
    Act as an elite LinkedIn copywriter.
    Current About Section: "{current_about}"
    Target Role: "{target_role}"
    Top Skills: "{skills_str}"

    Generate 3 completely rewritten versions of this LinkedIn About section:
    1. Conversational & First-Person (Relatable, high hook, engaging)
    2. Executive & Metric-Led (Polished, strategic, KPI focused, bulleted)
    3. Story-Driven (Hero journey: challenges conquered, philosophy, vision)

    Use clean formatting with whitespace and a Call-to-Action at the end.
    Format output clearly with markdown headers:
    ### 1. Conversational Style
    [content]
    ### 2. Executive Style
    [content]
    ### 3. Story-Driven Style
    [content]
    """
    ai_resp = call_gemini(prompt, api_key)
    if ai_resp:
        try:
            sections = re.split(r"###\s*\d+\.\s*", ai_resp)
            if len(sections) >= 4:
                return [
                    {"style": "Conversational & First-Person", "content": sections[1].strip()},
                    {"style": "Executive & Metric-Led", "content": sections[2].strip()},
                    {"style": "Story-Driven Narrative", "content": sections[3].strip()}
                ]
        except Exception:
            pass

    # Heuristic offline generator
    role = target_role if target_role and target_role != "General Tech / Custom" else "Technology Leader"
    skill1 = top_skills[0] if len(top_skills) > 0 else "systems engineering"
    skill2 = top_skills[1] if len(top_skills) > 1 else "cloud infrastructure"

    conversational = f"""I build software that solves real, messy business problems without the unnecessary complexity.

Over the past few years, I've specialized as a {role}, designing and delivering scalable solutions across {skill1} and {skill2}. What excites me most is bridging the gap between high-level architectural strategy and hands-on, high-velocity engineering.

A few highlights I'm proud of:
• Re-architected legacy services, improving response times by over 40% while maintaining 99.9% uptime.
• Mentored cross-functional engineering teams, fostering a culture of test-driven development and continuous delivery.
• Championed customer-first features that directly drove engagement and reduced operational friction.

Outside the terminal, I’m an avid reader, tech writer, and open-source enthusiast.

📬 Looking to collaborate, discuss architecture, or explore new opportunities? Feel free to connect or drop a message here!"""

    executive = f"""Strategic {role} with a track record of driving technical velocity, building resilient infrastructure, and leading high-performing teams.

CORE COMPETENCIES:
• Architecture & Systems: {skill1}, {skill2}, Distributed Systems, Microservices
• Engineering Leadership: Technical Mentorship, Agile/Scrum, Cross-Functional Alignment
• Business Impact: Cloud Cost Reduction, Scalability, High Availability (99.9% SLA)

SELECTED KEY ACHIEVEMENTS:
• Spearheaded migration of mission-critical services, slashing infrastructure costs by 30% and modernizing the developer experience.
• Automated release pipelines to reduce deployment cycles from weeks to single-day automated workflows.
• Partnered with Product & Design leaders to translate product roadmaps into reliable, maintainable code.

Let’s connect to discuss engineering leadership, tech strategy, or ambitious projects."""

    story = f"""When I wrote my very first script, I realized something that has guided my entire career: great code isn't just about syntax—it's about leverage and human empowerment.

Over my career as a {role}, I’ve had the privilege of seeing how clean design and thoughtful automation can transform teams and unlock massive business growth. Whether debugging an elusive race condition at 2 AM or architecting multi-region systems handling peak traffic, I thrive on tackling tough engineering challenges head-on.

My technical toolkit centers around {skill1}, {skill2}, and robust cloud deployments. But what really drives me is creating software that users genuinely love and teammates feel proud to maintain.

If you’re passionate about technology, building high-impact products, or just want to geek out over software design, my inbox is always open!"""

    return [
        {"style": "Conversational & First-Person", "content": conversational},
        {"style": "Executive & Metric-Led", "content": executive},
        {"style": "Story-Driven Narrative", "content": story}
    ]


def transform_bullet_points(bullets: str, api_key: str = None) -> List[Dict[str, str]]:
    """
    Transforms weak or generic experience bullet points into high-impact
    Google XYZ formula achievements ("Accomplished [X] as measured by [Y], by doing [Z]").
    """
    raw_lines = [b.strip().lstrip("•-* ") for b in bullets.splitlines() if len(b.strip()) > 5]
    if not raw_lines:
        raw_lines = [
            "Responsible for building features for the web application",
            "Worked on database queries and improved speed",
            "Helped team with weekly bug fixes and releases"
        ]

    prompt = f"""
    Transform each of the following resume/LinkedIn bullet points into the famous Google XYZ formula:
    "Accomplished [X], as measured by [Y], by doing [Z]"
    Use strong active verbs, specific metrics, and business impact.

    Original Bullets:
    {chr(10).join(['- ' + b for b in raw_lines[:5]])}

    Format output as a list of pairs:
    Original: [text]
    Optimized: [text]
    Formula Breakdown: [Action + Metric + Impact explanation]
    """
    ai_resp = call_gemini(prompt, api_key)
    if ai_resp:
        try:
            blocks = ai_resp.split("Original:")
            transformed = []
            for block in blocks[1:]:
                parts = block.split("Optimized:")
                if len(parts) >= 2:
                    orig = parts[0].strip()
                    subparts = parts[1].split("Formula Breakdown:")
                    opt = subparts[0].strip()
                    breakdown = subparts[1].strip() if len(subparts) > 1 else "Google XYZ Formula Applied"
                    transformed.append({"original": orig, "optimized": opt, "breakdown": breakdown})
            if transformed:
                return transformed
        except Exception:
            pass

    # Heuristic bullet enhancer
    enhancements = []
    sample_metrics = ["by 35%", "serving 100K+ monthly active users", "reducing bug escape rate by 45%", "cutting processing time from 4s to 450ms", "saving $25K in annual infrastructure costs"]
    verbs = ["Architected and deployed", "Spearheaded development of", "Engineered and streamlined", "Refactored core services for"]

    for i, line in enumerate(raw_lines[:5]):
        metric = sample_metrics[i % len(sample_metrics)]
        verb = verbs[i % len(verbs)]
        clean = line.replace("Responsible for", "").replace("Worked on", "").replace("Helped with", "").strip()
        enhanced = f"{verb} {clean}, delivering a {metric} while enhancing overall system reliability and developer velocity."
        enhancements.append({
            "original": line,
            "optimized": enhanced,
            "breakdown": f"Replaced passive phrasing with proactive verb ('{verb.split()[0]}') and added quantifiable KPI."
        })
    return enhancements


def generate_linkedin_post_ideas(role: str, skills: List[str], experience_text: str, api_key: str = None) -> List[Dict[str, str]]:
    """
    Generates 5 personalized LinkedIn post hooks and topics
    to build personal brand and creator engagement.
    """
    skills_str = ", ".join(skills[:4]) if skills else "Software Engineering"
    
    prompt = f"""
    Act as a LinkedIn viral growth strategist.
    Role: {role}
    Top Skills: {skills_str}
    
    Generate 5 high-converting LinkedIn post concepts tailored to this professional's background.
    Format:
    1. [Hook / Headline]
       Concept: [Core takeaway]
       Opening Lines: [First 2 lines that stop the scroll]
    """
    ai_resp = call_gemini(prompt, api_key)
    if ai_resp:
        try:
            return [{"title": f"Post Idea #{i+1}", "content": chunk.strip()} for i, chunk in enumerate(ai_resp.split("\n\n")[:5]) if chunk.strip()]
        except Exception:
            pass

    # Heuristic post generator
    return [
        {
            "title": "1. The Counter-Intuitive Technical Lesson",
            "hook": "Most people think scaling is about adding more servers. Here is why they are wrong:",
            "concept": "Share a time when simpler code or better database indexing outperformed complex distributed architecture.",
            "hashtags": "#SoftwareEngineering #SystemDesign #TechLeadership"
        },
        {
            "title": "2. Behind-The-Scenes 'Build in Public' Post",
            "hook": "We spent 3 weeks chasing a production bug that took 1 line of code to fix.",
            "concept": "Tell a relatable debugging or architectural story showing resilience, methodical problem-solving, and teamwork.",
            "hashtags": "#DeveloperLife #Coding #TechJourney"
        },
        {
            "title": "3. The Industry Shift / Opinion Post",
            "hook": f"Here is how {skills[0] if skills else 'modern tech'} is actually changing how engineering teams ship in 2026:",
            "concept": "Give your perspective on modern tools vs foundational fundamentals. Position yourself as a thoughtful practitioner.",
            "hashtags": "#TechTrends #Engineering #Innovation"
        },
        {
            "title": "4. Career Retrospective / Mentorship Post",
            "hook": f"What I wish I knew before becoming a {role if role else 'Senior Engineer'}:",
            "concept": "3 actionable pieces of advice for early-career developers. Generates high saves, shares, and recruiter comments.",
            "hashtags": "#CareerAdvice #Mentorship #PersonalGrowth"
        },
        {
            "title": "5. The Milestone / Project Post-Mortem",
            "hook": "Proud to share: we just hit a milestone of 99.99% uptime after migrating our core infrastructure.",
            "concept": "Celebrate a team win, tag collaborators, and highlight 3 key technical decisions that made it possible.",
            "hashtags": "#DevOps #CloudComputing #ProudMoment"
        }
    ]
