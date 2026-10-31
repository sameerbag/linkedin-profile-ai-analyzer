import re
from typing import List, Dict, Any, Tuple
from .models import JobPosting, ApplicantProfile
from analyzer.ai_engine import call_gemini


TECH_SKILL_LEXICON = [
    # Programming & Frameworks
    "python", "javascript", "typescript", "react", "next.js", "node.js", "fastapi",
    "flask", "django", "pytorch", "tensorflow", "keras", "scikit-learn", "sql",
    "postgresql", "mongodb", "redis", "graphql", "rest api", "c++", "java", "golang",
    # AI & ML
    "llm", "llms", "rag", "langchain", "llamaindex", "transformers", "hugging face",
    "vector database", "pinecone", "qdrant", "milvus", "chroma", "embeddings",
    "prompt engineering", "fine-tuning", "lora", "deep learning", "nlp", "computer vision",
    # Cloud, DevOps & Tools
    "aws", "gcp", "azure", "docker", "kubernetes", "ci/cd", "terraform", "git",
    "linux", "bash", "prometheus", "grafana", "microservices", "system design",
    # Product & Data
    "agile", "scrum", "product management", "a/b testing", "pandas", "numpy", "spark"
]


def extract_skills_from_text(text: str) -> List[str]:
    """Extract known technical and soft skills from free-form text."""
    found = set()
    text_lower = f" {text.lower()} "
    for skill in TECH_SKILL_LEXICON:
        # Match as whole word/phrase
        pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
        if re.search(pattern, text_lower):
            found.add(skill.title() if len(skill) > 3 else skill.upper())
    return sorted(list(found))


def compute_job_fit(job: JobPosting, profile: ApplicantProfile, api_key: str = None) -> JobPosting:
    """
    Computes fit score, matching skills, missing skills, and a recruiter verdict
    between the Job Posting and Applicant Profile.
    """
    job_text = f"{job.title}\n{job.description}"
    job_skills = extract_skills_from_text(job_text)
    
    profile_text = f"{profile.headline}\n{profile.about}\n{profile.experience}\n{' '.join(profile.skills)}"
    profile_skills = extract_skills_from_text(profile_text)
    
    # Also add explicit profile skills
    for s in profile.skills:
        s_clean = s.strip()
        if s_clean and s_clean.lower() not in [p.lower() for p in profile_skills]:
            profile_skills.append(s_clean)

    # Calculate overlaps
    profile_skills_lower = {s.lower() for s in profile_skills}
    matching = []
    missing = []
    
    for js in job_skills:
        if js.lower() in profile_skills_lower or js.lower() in profile_text.lower():
            matching.append(js)
        else:
            missing.append(js)

    # Check title / role alignment
    title_words = set(re.findall(r"\w+", job.title.lower()))
    profile_title_words = set(re.findall(r"\w+", (profile.headline or "").lower()))
    title_overlap = len(title_words & profile_title_words)
    title_bonus = min(title_overlap * 8, 20)

    # Base skill match percentage
    if job_skills:
        skill_ratio = len(matching) / len(job_skills)
        raw_score = int(skill_ratio * 75) + title_bonus
    else:
        raw_score = 65 + title_bonus

    # Location / Remote preference match
    if job.is_remote and "remote" in profile.target_work_mode.lower():
        raw_score += 5
    elif job.country.lower() in profile.country.lower() or profile.country.lower() in job.country.lower():
        raw_score += 5

    fit_score = max(25, min(98, raw_score))

    # Tier assignment
    if fit_score >= 82:
        tier = "🔥 Top Fit"
    elif fit_score >= 68:
        tier = "✨ Strong Match"
    elif fit_score >= 50:
        tier = "⚖️ Moderate Fit"
    else:
        tier = "⚠️ Low Fit"

    # AI-generated verdict if Gemini is available, else heuristic
    summary = ""
    if api_key:
        prompt = f"""
        You are an elite technical recruiter. In 2 concise sentences, summarize why this candidate fits this job:
        Candidate Headline: {profile.headline}
        Job Title: {job.title} at {job.company}
        Matching Skills: {', '.join(matching[:6])}
        Missing Skills: {', '.join(missing[:4])}
        Fit Score: {fit_score}%
        """
        ai_resp = call_gemini(prompt, api_key)
        if ai_resp:
            summary = ai_resp.strip()

    if not summary:
        matched_str = ", ".join(matching[:4]) if matching else "core engineering skills"
        missing_str = f"Missing: {', '.join(missing[:3])}" if missing else "No critical skill gaps detected."
        summary = f"Strong alignment on {matched_str} for the {job.title} position. {missing_str}"

    highlights = [
        f"Demonstrated proficiency in {', '.join(matching[:3])}" if matching else "Relevant software development background",
        f"Aligns with target role title '{job.title}'",
        f"Matches {job.location} ({'Remote' if job.is_remote else 'On-site/Hybrid'}) preferences"
    ]

    job.fit_score = fit_score
    job.match_tier = tier
    job.match_summary = summary
    job.matching_skills = matching
    job.missing_skills = missing
    job.recommended_highlights = highlights
    return job


def rank_jobs_for_applicant(
    jobs: List[JobPosting],
    profile: ApplicantProfile,
    min_score: int = 0,
    api_key: str = None
) -> List[JobPosting]:
    """
    Ranks all job postings in descending order of Fit Score.
    """
    scored = [compute_job_fit(j, profile, api_key) for j in jobs]
    filtered = [j for j in scored if j.fit_score >= min_score]
    filtered.sort(key=lambda x: x.fit_score, reverse=True)
    return filtered
