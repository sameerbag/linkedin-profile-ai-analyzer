from typing import Dict, Any, List
from .models import JobPosting, ApplicantProfile
from analyzer.ai_engine import call_llm


def generate_tailored_cover_letter(
    job: JobPosting,
    profile: ApplicantProfile,
    api_key: str = None
) -> str:
    """
    Generates a high-converting, tailored cover letter customized to the specific
    job posting, company, and matching candidate accomplishments.
    """
    matching_str = ", ".join(job.matching_skills[:5]) if job.matching_skills else "software engineering and system design"
    candidate_name = profile.full_name or "Applicant"
    role_title = job.title
    company_name = job.company

    if api_key:
        prompt = f"""
        Act as an executive career coach. Write a compelling, concise 3-paragraph Cover Letter.
        Applicant Name: {candidate_name}
        Current Role/Headline: {profile.headline}
        Applicant Experience Summary: {profile.experience[:400]}
        Target Company: {company_name}
        Target Role: {role_title}
        Matching Skills: {matching_str}

        Requirements:
        1. Strong opening hook referencing why {company_name}'s mission/role excites the applicant.
        2. Middle paragraph with 2 concrete, metric-driven achievements highlighting {matching_str}.
        3. Professional closing with enthusiasm for an interview.
        Keep it under 280 words. Professional, confident, and direct.
        """
        ai_resp = call_llm(prompt, api_key)
        if ai_resp:
            return ai_resp.strip()

    # Heuristic template fallback
    contact_email = profile.email or "applicant@email.com"
    contact_phone = profile.phone or "+1 (555) 000-0000"

    cover_letter = f"""Dear Hiring Team at {company_name},

I am writing to express my strong enthusiasm for the {role_title} position at {company_name}. With my hands-on background in {matching_str} and building resilient, high-velocity engineering systems, I am eager to contribute immediately to your team's upcoming initiatives.

Throughout my career, I have focused on translating complex technical requirements into scalable, reliable production software. Notably, I have:
• Engineered and optimized scalable microservices, improving throughput while maintaining high system reliability.
• Collaborated closely with cross-functional product and engineering teams to accelerate feature delivery cycles.
• Spearheaded best practices in testing, automation, and continuous delivery to maintain code quality at scale.

What particularly draws me to {company_name} is your commitment to technical innovation and high-impact problem solving. I am confident that my technical foundation in {matching_str}, coupled with my passion for user-focused architecture, makes me a great fit for your team.

Thank you for your time and consideration. I would welcome the opportunity to discuss how my experience aligns with your goals for the {role_title} role.

Sincerely,

{candidate_name}
{contact_email} | {contact_phone}
{profile.linkedin_url or "LinkedIn Profile"}"""

    return cover_letter.strip()


def generate_application_answers(
    job: JobPosting,
    profile: ApplicantProfile,
    api_key: str = None
) -> Dict[str, str]:
    """
    Generates standard job application form answers (Greenhouse, Lever, Workday questions).
    """
    matching_str = ", ".join(job.matching_skills[:4]) if job.matching_skills else "modern software engineering"
    
    why_company = (
        f"I have been closely following {job.company}'s work and industry impact. "
        f"The opportunity to work on {job.title} aligns directly with my background in {matching_str}, "
        f"and I am eager to bring a collaborative, high-velocity mindset to your team."
    )

    relevant_experience = (
        f"Over my career, I have specialized in building and deploying scalable systems. "
        f"My recent projects directly leveraged {matching_str}, focusing on high availability, "
        f"clean architecture, and quantifiable business outcomes."
    )

    return {
        "Full Name": profile.full_name or "Applicant",
        "First Name": profile.first_name or (profile.full_name.split()[0] if profile.full_name else "Candidate"),
        "Last Name": profile.last_name or (profile.full_name.split()[-1] if profile.full_name and len(profile.full_name.split()) > 1 else ""),
        "Email Address": profile.email or "",
        "Phone Number": profile.phone or "",
        "Current Location": profile.current_location or f"{profile.city}, {profile.country}".strip(", "),
        "LinkedIn URL": profile.linkedin_url or "",
        "GitHub URL": profile.github_url or "",
        "Portfolio URL": profile.portfolio_url or "",
        "Work Authorization Status": profile.work_authorization,
        "Requires Visa Sponsorship?": profile.requires_sponsorship,
        "Willing to Relocate?": profile.willing_to_relocate,
        "Notice Period / Availability": profile.notice_period,
        "Desired Compensation / Salary": profile.expected_salary,
        "Why do you want to work here?": why_company,
        "Summary of Relevant Experience": relevant_experience
    }
