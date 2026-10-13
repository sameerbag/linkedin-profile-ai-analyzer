import re
from typing import Dict, Any, List
from pypdf import PdfReader


def extract_text_from_pdf(pdf_file, max_pages: int = 25) -> str:
    """
    Safely extract raw text from uploaded PDF file.
    Includes page-limit guard to prevent resource exhaustion from malformed files.
    """
    try:
        reader = PdfReader(pdf_file)
        text_pages = []
        for i, page in enumerate(reader.pages):
            if i >= max_pages:
                break
            page_text = page.extract_text()
            if page_text:
                text_pages.append(page_text)
        return "\n".join(text_pages)
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"


def parse_linkedin_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse LinkedIn profile text (exported PDF or pasted profile)
    into structured sections: Name, Headline, Summary/About, Experience, Skills, Education.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return {
            "name": "",
            "headline": "",
            "about": "",
            "experience": "",
            "skills": [],
            "education": "",
            "raw_text": raw_text
        }

    # Common LinkedIn PDF export patterns
    name = lines[0] if len(lines) > 0 else ""
    headline = lines[1] if len(lines) > 1 and len(lines[1]) < 220 else ""

    about = ""
    experience_lines = []
    education_lines = []
    skills = []

    current_section = None
    section_patterns = {
        "summary": re.compile(r"^(summary|about|profile|overview)$", re.IGNORECASE),
        "experience": re.compile(r"^(experience|work experience|employment history)$", re.IGNORECASE),
        "education": re.compile(r"^(education|academic history)$", re.IGNORECASE),
        "skills": re.compile(r"^(skills|top skills|core competencies|technologies)$", re.IGNORECASE)
    }

    for line in lines:
        matched = False
        for sec, pat in section_patterns.items():
            if pat.match(line):
                current_section = sec
                matched = True
                break
        if matched:
            continue

        if current_section == "summary":
            about += (" " + line if about else line)
        elif current_section == "experience":
            experience_lines.append(line)
        elif current_section == "education":
            education_lines.append(line)
        elif current_section == "skills":
            # LinkedIn PDF skills are often comma-separated or one per line
            sub_skills = [s.strip() for s in re.split(r"[,•|\n]", line) if s.strip()]
            skills.extend(sub_skills)

    # Fallback if sections were not cleanly labeled
    if not about and not experience_lines:
        # Simple heuristic split
        about = "\n".join(lines[2:6]) if len(lines) > 5 else ""
        experience_lines = lines[6:] if len(lines) > 6 else []

    # Clean up skills duplicates
    unique_skills = []
    for s in skills:
        if s.lower() not in [u.lower() for u in unique_skills] and len(s) < 50:
            unique_skills.append(s)

    return {
        "name": name,
        "headline": headline,
        "about": about.strip(),
        "experience": "\n".join(experience_lines).strip(),
        "skills": unique_skills,
        "education": "\n".join(education_lines).strip(),
        "raw_text": raw_text
    }
