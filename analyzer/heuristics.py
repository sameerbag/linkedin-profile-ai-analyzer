import re
from typing import Dict, List, Any


ACTION_VERBS = [
    "accelerated", "achieved", "architected", "automated", "built", "championed",
    "collaborated", "created", "delivered", "deployed", "designed", "developed",
    "devised", "discovered", "doubled", "drove", "engineered", "established",
    "executed", "expanded", "expedited", "formulated", "founded", "generated",
    "guided", "headed", "implemented", "improved", "increased", "initiated",
    "innovated", "instituted", "integrated", "introduced", "launched", "led",
    "maximized", "mentored", "migrated", "modernized", "negotiated", "optimized",
    "orchestrated", "overhauled", "pioneered", "produced", "reduced", "refactored",
    "restructured", "revamped", "saved", "scaled", "simplified", "spearheaded",
    "standardized", "streamlined", "strengthened", "succeeded", "surpassed",
    "transformed", "tripled", "upgraded", "yielded"
]

WEAK_PHRASES = [
    "responsible for", "helped with", "worked on", "assisted in", "participated in",
    "duties included", "handled", "involved in", "tasked with", "hard worker",
    "team player", "detail-oriented", "results-driven", "synergy", "go-getter"
]


def score_headline(headline: str) -> Dict[str, Any]:
    """
    Evaluates LinkedIn headline (Max 220 chars).
    Recruiters look for: Role title + key skills/tech + value proposition or impact.
    """
    headline = headline.strip()
    score = 0
    feedback = []
    strengths = []

    if not headline:
        return {
            "score": 0,
            "char_count": 0,
            "strengths": [],
            "feedback": ["Headline is empty. A strong headline is crucial for recruiter search discoverability."]
        }

    char_len = len(headline)

    # 1. Length check (ideal: 70 - 180 chars)
    if char_len < 35:
        score += 15
        feedback.append(f"Headline is too short ({char_len} chars). Expand to showcase skills and value proposition.")
    elif 35 <= char_len < 70:
        score += 25
        feedback.append("Headline is somewhat brief. Consider adding target technologies or industry impact.")
    elif 70 <= char_len <= 190:
        score += 35
        strengths.append(f"Great headline length ({char_len} chars) - provides ample context without being cut off.")
    else:
        score += 25
        feedback.append("Headline is near or exceeds 200 chars. Ensure the first 60 chars contain your primary keywords for mobile.")

    # 2. Separators check (| or • or / or -)
    separators = ["|", "•", "·", "-", "/", "—"]
    has_separator = any(sep in headline for sep in separators)
    if has_separator:
        score += 20
        strengths.append("Uses clean dividers to organize role, skills, and value proposition.")
    else:
        score += 10
        feedback.append("Consider using dividers (e.g., '|' or '•') to clearly separate your title, specialty, and achievement.")

    # 3. Value proposition / helping / impact words
    value_patterns = [r"helping\b", r"building\b", r"scaling\b", r"empowering\b", r"driving\b", r"specializing in\b", r"passionate about\b", r"\bex-", r"\bformer\b", r"\bfounder\b"]
    has_value_prop = any(re.search(pat, headline, re.IGNORECASE) for pat in value_patterns)
    if has_value_prop:
        score += 25
        strengths.append("Contains a clear value proposition or distinct positioning.")
    else:
        score += 10
        feedback.append("Add a value hook: Who do you help, or what measurable outcome do you deliver?")

    # 4. Keyword count check
    words = headline.split()
    if len(words) >= 6:
        score += 20
        strengths.append("Rich in descriptive keywords for LinkedIn search algorithm (SEO).")
    else:
        score += 10
        feedback.append("Add more specific industry keywords to increase recruiter search appearances.")

    final_score = min(score, 100)
    return {
        "score": final_score,
        "char_count": char_len,
        "strengths": strengths,
        "feedback": feedback
    }


def score_about(about: str) -> Dict[str, Any]:
    """
    Evaluates LinkedIn About / Summary section (Max 2600 chars).
    Crucial: First 3 lines hook before user clicks 'see more', storytelling, metrics, CTA.
    """
    about = about.strip()
    if not about:
        return {
            "score": 0,
            "word_count": 0,
            "strengths": [],
            "feedback": ["About section is blank. This is your personal pitch to recruiters and clients."]
        }

    words = about.split()
    word_count = len(words)
    score = 0
    strengths = []
    feedback = []

    # 1. Word count / Length
    if word_count < 40:
        score += 15
        feedback.append(f"About section is too short ({word_count} words). Aim for 120-300 words to tell your story.")
    elif 40 <= word_count < 100:
        score += 25
        feedback.append("Decent start, but adding career milestones, tech stack, and a personal philosophy will elevate it.")
    elif 100 <= word_count <= 450:
        score += 35
        strengths.append(f"Ideal word count ({word_count} words) - thorough yet easy to digest.")
    else:
        score += 25
        feedback.append("About section is very long. Consider using bullet points and whitespace to keep it scannable.")

    # 2. Hook in first 2-3 lines (check if first sentence is compelling and not generic)
    first_paragraph = about.split("\n")[0]
    first_sentence = re.split(r"[.!?]", first_paragraph)[0]
    generic_openers = ["i am a", "my name is", "i'm a", "experienced professional", "hardworking individual"]
    if any(first_sentence.lower().startswith(g) for g in generic_openers):
        score += 5
        feedback.append("Your opening sentence is generic. Hook the reader immediately with your passion, niche, or biggest win.")
    else:
        score += 20
        strengths.append("Opening hook avoids cliché introductory phrases.")

    # 3. Quantifiable impact / Numbers check
    numbers = re.findall(r"\b(?:\d+[\.,]?\d*|\$\d+|\d+%)", about)
    if len(numbers) >= 2:
        score += 20
        strengths.append(f"Includes quantifiable achievements ({', '.join(numbers[:3])}) to back up claims.")
    elif len(numbers) == 1:
        score += 12
        feedback.append("Good start with quantifiable metrics. Add 1-2 more numbers (e.g. % growth, team size, scale).")
    else:
        score += 5
        feedback.append("No numerical data found. Recruiters trust metrics (% improvement, revenue, users served, latency reduction).")

    # 4. Call to action (CTA) & Contact info
    cta_patterns = [r"feel free to", r"reach out", r"connect", r"email", r"contact", r"let's chat", r"message me"]
    has_cta = any(re.search(pat, about, re.IGNORECASE) for pat in cta_patterns)
    if has_cta:
        score += 15
        strengths.append("Includes a clear Call-to-Action (CTA) inviting readers to connect or collaborate.")
    else:
        score += 5
        feedback.append("Missing a Call-to-Action at the end (e.g., 'Let's connect: name@domain.com').")

    # 5. Weak buzzwords check
    found_weak = [w for w in WEAK_PHRASES if w in about.lower()]
    if not found_weak:
        score += 10
        strengths.append("Avoids overused buzzwords ('hard worker', 'team player', 'results-driven').")
    else:
        feedback.append(f"Replace passive buzzwords ({', '.join(found_weak[:3])}) with concrete examples.")

    final_score = min(score, 100)
    return {
        "score": final_score,
        "word_count": word_count,
        "numbers_found": numbers,
        "strengths": strengths,
        "feedback": feedback
    }


def score_experience(experience: str) -> Dict[str, Any]:
    """
    Evaluates LinkedIn Experience Section.
    Looks for:
    - Action verb density at bullet start
    - Quantifiable metrics (Google XYZ formula: Accomplished X, measured by Y, by doing Z)
    - Absence of weak phrases like 'Responsible for'
    """
    experience = experience.strip()
    if not experience:
        return {
            "score": 0,
            "metrics_count": 0,
            "action_verbs_count": 0,
            "strengths": [],
            "feedback": ["Experience section is blank. This is the core evidence recruiters evaluate."]
        }

    lines = [line.strip() for line in experience.splitlines() if len(line.strip()) > 10]
    total_lines = len(lines)
    score = 0
    strengths = []
    feedback = []

    # 1. Quantifiable metrics count
    metrics = re.findall(r"\b(?:\$\d+[\.,]?\d*[kKmMbB]?|\d+[\.,]?\d*\%|\d{1,3}(?:,\d{3})+|\b\d+\b(?:\s*(?:users|clients|engineers|projects|ms|queries|x|million|billion|k))\b)", experience, re.IGNORECASE)
    metrics_count = len(metrics)

    if metrics_count >= 5:
        score += 35
        strengths.append(f"Exceptional metric density ({metrics_count}+ data points found). Demonstrates quantifiable impact!")
    elif metrics_count >= 2:
        score += 25
        strengths.append(f"Includes {metrics_count} quantifiable data points.")
        feedback.append("Aim for at least one metric (% improvement, cost saved, scale reached) per key bullet point.")
    else:
        score += 10
        feedback.append("Low metric density. Use the Google XYZ formula: 'Accomplished [X], as measured by [Y], by doing [Z]'.")

    # 2. Action Verbs analysis
    exp_lower = experience.lower()
    found_verbs = [verb for verb in ACTION_VERBS if re.search(r"\b" + verb + r"\b", exp_lower)]
    action_verbs_count = len(found_verbs)

    if action_verbs_count >= 8:
        score += 35
        strengths.append(f"High action-verb diversity ({action_verbs_count} unique powerful verbs used, e.g. {', '.join(found_verbs[:4])}).")
    elif action_verbs_count >= 4:
        score += 25
        strengths.append(f"Found {action_verbs_count} strong action verbs.")
    else:
        score += 15
        feedback.append("Lacks strong action verbs. Start bullets with words like 'Spearheaded', 'Architected', 'Reduced', 'Engineered'.")

    # 3. Weak phrases penalty check
    found_weak = [phrase for phrase in WEAK_PHRASES if phrase in exp_lower]
    if not found_weak:
        score += 15
        strengths.append("No passive phrases ('Responsible for', 'Worked on') detected.")
    else:
        score += 5
        feedback.append(f"Found passive language: '{', '.join(found_weak)}'. Change to direct proactive achievements.")

    # 4. Bullet structure and length
    avg_len = sum(len(line.split()) for line in lines) / max(total_lines, 1)
    if 8 <= avg_len <= 30:
        score += 15
        strengths.append("Bullet points have good length and scannability.")
    else:
        score += 8
        feedback.append("Some bullet points are either too terse or overly dense paragraphs.")

    final_score = min(score, 100)
    return {
        "score": final_score,
        "metrics_count": metrics_count,
        "action_verbs_count": action_verbs_count,
        "sample_metrics": metrics[:5],
        "sample_verbs": found_verbs[:6],
        "strengths": strengths,
        "feedback": feedback
    }


def compute_overall_profile_score(headline_res: Dict, about_res: Dict, exp_res: Dict, role_fit_res: Dict) -> Dict[str, Any]:
    """
    Weighted calculation of overall profile score (0-100):
    - Headline: 20%
    - About: 25%
    - Experience: 35%
    - Role / Skills Fit: 20%
    """
    h_score = headline_res.get("score", 0)
    a_score = about_res.get("score", 0)
    e_score = exp_res.get("score", 0)
    r_score = role_fit_res.get("match_percentage", 50)

    overall = int((h_score * 0.20) + (a_score * 0.25) + (e_score * 0.35) + (r_score * 0.20))
    overall = max(0, min(100, overall))

    if overall >= 85:
        tier = "🏆 All-Star (Top 5% Profile)"
        badge_color = "green"
        summary = "Your profile is primed for recruiter outreach and ATS search visibility."
    elif overall >= 70:
        tier = "✨ Strong Candidate (Top 25%)"
        badge_color = "blue"
        summary = "Solid foundation! A few strategic metric additions and headline tweaks will put you in the top tier."
    elif overall >= 50:
        tier = "⚠️ Developing Profile"
        badge_color = "orange"
        summary = "Profile has good material, but needs stronger action verbs, metrics, and targeted keywords."
    else:
        tier = "🚨 Needs Immediate Optimization"
        badge_color = "red"
        summary = "Major opportunities for improvement in headline, metrics, and keyword alignment."

    return {
        "overall_score": overall,
        "tier": tier,
        "badge_color": badge_color,
        "summary": summary,
        "breakdown": {
            "Headline Impact": h_score,
            "About Storytelling": a_score,
            "Experience & Metrics": e_score,
            "Target Role Fit": r_score
        }
    }


def recruiter_10_second_audit(profile_data: Dict[str, Any], overall_score: int) -> List[Dict[str, str]]:
    """
    Simulates the brutal reality of the 10-second recruiter scan.
    Returns key impressions recruiters form immediately.
    """
    items = []
    headline = profile_data.get("headline", "")
    about = profile_data.get("about", "")
    experience = profile_data.get("experience", "")

    # 1. Headline scan (First 3 seconds)
    if len(headline) > 50 and any(sep in headline for sep in ["|", "•", "-", "/"]):
        items.append({
            "phase": "0-3 Seconds: Headline & Role Title",
            "status": "PASS",
            "comment": "Recruiter instantly identifies your core domain, specialty, and seniority level."
        })
    else:
        items.append({
            "phase": "0-3 Seconds: Headline & Role Title",
            "status": "ATTENTION NEEDED",
            "comment": "Headline is vague or lacking separators. Recruiters may scroll past if title doesn't match search."
        })

    # 2. Summary hook scan (Seconds 3-6)
    if len(about) > 100:
        items.append({
            "phase": "3-6 Seconds: About / Hook Scan",
            "status": "PASS",
            "comment": "Profile summary provides a clear narrative and professional positioning."
        })
    else:
        items.append({
            "phase": "3-6 Seconds: About / Hook Scan",
            "status": "ATTENTION NEEDED",
            "comment": "Summary is too short or missing. Recruiters miss out on your personal value proposition."
        })

    # 3. Experience metrics scan (Seconds 6-10)
    has_metrics = bool(re.search(r"\b(?:\d+\%|\$\d+|\d+x|\d{2,}\b)", experience))
    if has_metrics:
        items.append({
            "phase": "6-10 Seconds: Bullet Point Metrics Scan",
            "status": "PASS",
            "comment": "Numbers and percentages pop out immediately, validating that you drive measurable business results."
        })
    else:
        items.append({
            "phase": "6-10 Seconds: Bullet Point Metrics Scan",
            "status": "ATTENTION NEEDED",
            "comment": "No prominent numbers or KPIs caught the recruiter's eye. Bullets risk looking like a job description rather than accomplishments."
        })

    return items
