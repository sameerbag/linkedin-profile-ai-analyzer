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


def find_candidate_block(lines: List[str], linkedin_slug: str = "", email: str = "") -> Tuple[str, str, str]:
    """
    Finds (name, headline, location) from LinkedIn PDF text lines by scoring candidate lines
    and avoiding sidebars, contact blocks, certifications, and languages.
    """
    hints = []
    if linkedin_slug:
        cleaned_slug = re.sub(r"[-_0-9]+", " ", linkedin_slug).strip().lower()
        if len(cleaned_slug) >= 3:
            hints.append(cleaned_slug)
    if email:
        username = email.split("@")[0]
        cleaned_user = re.sub(r"[._0-9]+", " ", username).strip().lower()
        if len(cleaned_user) >= 3:
            hints.append(cleaned_user)

    cert_or_skip_words = [
        "certified", "certification", "solutions architect", "associate", "professional", 
        "foundation", "license", "credential", "university", "college", "school",
        "contact", "skills", "languages", "english", "hindi", "spanish", "french", "german",
        "page", "linkedin"
    ]

    best_idx = -1
    best_score = -100

    for i, line in enumerate(lines):
        line_clean = line.strip()
        low = line_clean.lower()

        if len(line_clean) < 2 or len(line_clean) > 50:
            continue
        if any(w in low for w in ["contact", "summary", "experience", "education", "top skills", "languages", "certifications"]):
            continue
        if any(w in low for w in cert_or_skip_words):
            continue
        if "@" in line_clean or "http" in low or "(mobile)" in low or "(email)" in low or "(linkedin)" in low:
            continue

        score = 0
        words = line_clean.split()
        if 2 <= len(words) <= 4:
            score += 15

        line_word_str = " ".join([w.lower() for w in words])
        for hint in hints:
            if hint in line_word_str or line_word_str in hint:
                score += 50

        if all(w[0].isupper() for w in words if w.isalpha()):
            score += 10

        # Check next line: Headline
        if i + 1 < len(lines):
            next_l = lines[i + 1].strip()
            next_low = next_l.lower()
            if any(title_w in next_low for title_w in [
                "engineer", "developer", "manager", "lead", "architect", "scientist", 
                "consultant", "analyst", "director", "officer", "intern", "student", 
                "designer", "specialist", "founder", "cto", "ceo", "|", "•", " at "
            ]):
                score += 35

        # Check line i+2: Location
        if i + 2 < len(lines):
            loc_l = lines[i + 2].strip()
            loc_low = loc_l.lower()
            if any(country_w in loc_low for country_w in ["india", "states", "usa", "area", "bengaluru", "pune", "mumbai", "london", "canada", "york", "francisco", "germany", "singapore", "australia"]) or "," in loc_l:
                score += 30

        # Check line i+3 or i+4: "Summary" or "Experience"
        for offset in [2, 3, 4]:
            if i + offset < len(lines) and lines[i + offset].strip().lower() in ["summary", "about", "experience"]:
                score += 40

        if score > best_score:
            best_score = score
            best_idx = i

    name = ""
    headline = ""
    location = ""

    if best_idx != -1 and best_score >= 30:
        name = lines[best_idx].strip()
        if best_idx + 1 < len(lines):
            headline = lines[best_idx + 1].strip()
        if best_idx + 2 < len(lines):
            cand_loc = lines[best_idx + 2].strip()
            if cand_loc.lower() not in ["summary", "about", "experience"]:
                location = cand_loc

    # Fallback if no high score candidate was found (e.g. pasted snippet or 1-column format)
    if not name and lines:
        for idx, line in enumerate(lines[:6]):
            low = line.strip().lower()
            if low not in ["contact", "top skills", "languages", "certifications"] and "@" not in line and "linkedin" not in low:
                name = line.strip()
                if idx + 1 < len(lines):
                    headline = lines[idx + 1].strip()
                if idx + 2 < len(lines):
                    location = lines[idx + 2].strip()
                break

    return name, headline, location


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
            "country": "",
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

    # Extract Contact Info via regex
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
    email = email_match.group(0).strip() if email_match else ""

    phone_match = re.search(r"(\+?\d{1,4}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?\d{3,4}[-.\s]?\d{3,4}", raw_text)
    phone = phone_match.group(0).strip() if phone_match else ""

    in_match = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_-]+)", raw_text)
    linkedin_url = ""
    linkedin_slug = ""
    if in_match:
        linkedin_slug = in_match.group(1)
        linkedin_url = f"https://www.linkedin.com/in/{linkedin_slug}"

    # Extract Top Skills from LinkedIn PDF sidebar
    skills = []
    in_skills_sec = False
    for line in lines:
        low = line.lower()
        if low in ["top skills", "skills", "core competencies"]:
            in_skills_sec = True
            continue
        elif in_skills_sec and (low in ["languages", "certifications", "summary", "experience", "education", "contact"] or len(line) > 60):
            in_skills_sec = False
        elif in_skills_sec:
            if not any(h in low for h in ["(professional", "(native", "(elementary", "(bilingual"]):
                skills.append(line.strip())

    # Find Candidate Name, Headline, Location reliably
    name, headline, location = find_candidate_block(lines, linkedin_slug=linkedin_slug, email=email)
    country, city = detect_country_and_city(location)

    # Parse Summary, Experience, Education
    about_lines = []
    experience_lines = []
    education_lines = []
    current_sec = None

    for line in lines:
        low = line.lower()
        if low in ["summary", "about", "about me", "profile summary"]:
            current_sec = "about"
            continue
        elif low in ["experience", "work experience", "employment history", "professional experience"]:
            current_sec = "experience"
            continue
        elif low in ["education", "academic history"]:
            current_sec = "education"
            continue
        elif low in ["certifications", "licenses & certifications", "languages", "publications", "honors-awards"]:
            current_sec = "other"
            continue

        if current_sec == "about":
            about_lines.append(line)
        elif current_sec == "experience":
            experience_lines.append(line)
        elif current_sec == "education":
            education_lines.append(line)

    # Clean up skills duplicates
    unique_skills = []
    for s in skills:
        cleaned_s = s.strip()
        if cleaned_s and cleaned_s.lower() not in [u.lower() for u in unique_skills] and len(cleaned_s) < 50:
            unique_skills.append(cleaned_s)

    return {
        "name": name,
        "headline": headline,
        "location": location,
        "country": country,
        "city": city,
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "about": "\n".join(about_lines).strip(),
        "experience": "\n".join(experience_lines).strip(),
        "skills": unique_skills,
        "education": "\n".join(education_lines).strip(),
        "raw_text": raw_text
    }
