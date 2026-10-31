import re
from typing import Dict, Any, List, Tuple
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


def detect_country_and_city(location_str: str) -> Tuple[str, str]:
    """
    Detects standardized Country and City from a location string.
    Example: 'Bengaluru, Karnataka, India' -> ('India', 'Bengaluru')
             'San Francisco, CA' -> ('USA', 'San Francisco')
    """
    if not location_str:
        return "India", ""

    loc_lower = location_str.lower()

    # Detect country
    country = "India"  # default
    if any(k in loc_lower for k in [
        "india", "karnataka", "maharashtra", "delhi", "tamil nadu", "telangana",
        "bengaluru", "bangalore", "mumbai", "pune", "hyderabad", "chennai", "noida", "gurgaon", "gurugram"
    ]):
        country = "India"
    elif any(k in loc_lower for k in [
        "united states", "usa", "u.s.a", "san francisco", "new york", "seattle", "austin",
        "california", "texas", "washington", "boston", "chicago", "los angeles", "colorado"
    ]):
        country = "USA"
    elif any(k in loc_lower for k in [
        "united kingdom", "uk", "u.k.", "london", "england", "scotland", "manchester", "birmingham"
    ]):
        country = "United Kingdom"
    elif any(k in loc_lower for k in [
        "canada", "toronto", "vancouver", "ontario", "montreal", "quebec", "ottawa", "british columbia"
    ]):
        country = "Canada"
    elif any(k in loc_lower for k in [
        "germany", "deutschland", "berlin", "munich", "münchen", "frankfurt", "hamburg"
    ]):
        country = "Germany"
    elif any(k in loc_lower for k in [
        "australia", "sydney", "melbourne", "brisbane", "perth"
    ]):
        country = "Australia"
    elif "singapore" in loc_lower:
        country = "Singapore"
    elif "france" in loc_lower or "paris" in loc_lower:
        country = "France"
    elif "netherlands" in loc_lower or "amsterdam" in loc_lower:
        country = "Netherlands"

    # Detect City: Take first token before comma
    parts = [p.strip() for p in location_str.split(",") if p.strip()]
    city = parts[0] if parts else location_str
    city = re.sub(r"\b(Greater|Area|Bay|City of)\b", "", city, flags=re.IGNORECASE).strip()

    return country, city


def parse_linkedin_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse LinkedIn profile text (exported PDF or pasted profile)
    into structured sections: Name, Headline, Location, Country, City, Contact,
    Summary/About, Experience, Skills, Education.
    """
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    if not lines:
        return {
            "name": "",
            "headline": "",
            "location": "",
            "country": "India",
            "city": "",
            "email": "",
            "phone": "",
            "linkedin_url": "",
            "about": "",
            "experience": "",
            "skills": [],
            "education": "",
            "raw_text": raw_text
        }

    # Line 0: Candidate Name
    name = lines[0] if len(lines) > 0 else ""

    # Line 1: Headline
    headline = lines[1] if len(lines) > 1 and len(lines[1]) < 220 else ""

    # Line 2-4: Often location in LinkedIn PDF export
    location = ""
    for candidate_line in lines[2:6]:
        # Check if line looks like a location (e.g., contains comma or known country/city)
        low = candidate_line.lower()
        if any(w in low for w in ["india", "states", "usa", "area", "bengaluru", "pune", "mumbai", "london", "canada", "york", "francisco", "germany"]) or ("," in candidate_line and len(candidate_line) < 80):
            if not any(header in low for header in ["contact", "summary", "experience", "education", "skills"]):
                location = candidate_line
                break

    country, city = detect_country_and_city(location)

    # Extract Contact Info via regex
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
    email = email_match.group(0) if email_match else ""

    phone_match = re.search(r"(\+?\d{1,4}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}", raw_text)
    phone = phone_match.group(0).strip() if phone_match else ""

    in_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/[a-zA-Z0-9_-]+", raw_text)
    linkedin_url = in_match.group(0) if in_match else ""
    if linkedin_url and not linkedin_url.startswith("http"):
        linkedin_url = "https://" + linkedin_url

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
            sub_skills = [s.strip() for s in re.split(r"[,•|\n]", line) if s.strip()]
            skills.extend(sub_skills)

    # Fallback if sections were not cleanly labeled
    if not about and not experience_lines:
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
        "location": location,
        "country": country,
        "city": city,
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "about": about.strip(),
        "experience": "\n".join(experience_lines).strip(),
        "skills": unique_skills,
        "education": "\n".join(education_lines).strip(),
        "raw_text": raw_text
    }
