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
    Example: 'Pune Division, Maharashtra, India' -> ('India', 'Pune')
             'Bengaluru, Karnataka, India' -> ('India', 'Bengaluru')
             'San Francisco, CA' -> ('USA', 'San Francisco')
    """
    if not location_str:
        return "India", ""

    loc_lower = location_str.lower()

    # Detect country
    country = "India"  # default
    if any(k in loc_lower for k in [
        "india", "karnataka", "maharashtra", "delhi", "tamil nadu", "telangana", "gujarat", "punjab", "haryana",
        "bengaluru", "bangalore", "mumbai", "pune", "hyderabad", "chennai", "noida", "gurgaon", "gurugram", "nasik", "nagpur"
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

    # Detect City: Take first token before comma, Division, District, or State
    parts = [p.strip() for p in location_str.split(",") if p.strip()]
    city = parts[0] if parts else location_str
    city = re.sub(r"\b(Greater|Area|Bay|City of|Division|District)\b", "", city, flags=re.IGNORECASE).strip()

    return country, city


def parse_linkedin_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse LinkedIn profile PDF export text into structured candidate fields:
    Name, Headline, Location, Country, City, Contact (Email, Phone, LinkedIn URL),
    Summary/About, Experience, Skills, Certifications, and Education.
    """
    # Clean special artifacts, non-breaking spaces, HTML entities, and control characters
    cleaned = raw_text.replace("\xa0", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)
    
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
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

    # 1. Extract Email Address
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", cleaned)
    email = email_match.group(0).strip() if email_match else ""

    # 2. Extract Phone Number (handles LinkedIn formats like '09226410033 (Mobile)' or '+91 92264 10033')
    phone = ""
    for line in lines:
        m = re.search(r"(\+?\d[\d\s-]{8,14}\d)", line)
        if m and any(kw in line.lower() for kw in ["(mobile)", "(phone)", "mobile", "phone"]):
            phone = m.group(1).strip()
            break
    if not phone:
        for line in lines:
            m = re.search(r"(\+?\d{1,4}[-.\s]?)?(\d{10,12})", line)
            if m:
                digits = re.sub(r"\D", "", m.group(0))
                # Validate length and ensure it's not a postal code
                if 10 <= len(digits) <= 13 and not digits.startswith("411") and not digits.startswith("560"):
                    phone = m.group(0).strip()
                    break

    # 3. Extract LinkedIn URL (handles narrow column line breaks: www.linkedin.com/in/\nsameerbagade)
    linkedin_url = ""
    linkedin_slug = ""
    for i, line in enumerate(lines):
        if "linkedin.com/in" in line.lower():
            combined = line
            if i + 1 < len(lines) and not any(kw in lines[i+1].lower() for kw in ["contact", "top skills", "certifications", "http"]):
                combined += lines[i+1]
            m = re.search(r"(?:https?:\/\/)?(?:www\.)?linkedin\.com\/in\/([a-zA-Z0-9_-]+)", combined)
            if m:
                linkedin_slug = m.group(1)
                linkedin_url = f"https://www.linkedin.com/in/{linkedin_slug}"
                break

    # 4. Extract Top Skills & Certifications from sidebar
    skills = []
    certifications = []
    in_top_skills = False
    in_certifications = False

    for line in lines:
        low = line.lower()
        if low in ["top skills", "skills", "core skills"]:
            in_top_skills = True
            in_certifications = False
            continue
        elif low in ["certifications", "licenses & certifications"]:
            in_certifications = True
            in_top_skills = False
            continue
        elif in_top_skills and (low in ["certifications", "languages", "summary", "experience", "education", "contact"]):
            in_top_skills = False
        elif in_certifications and (low in ["languages", "summary", "experience", "education", "contact"]):
            in_certifications = False

        if in_top_skills:
            if not any(h in low for h in ["(professional", "(native", "(elementary", "(bilingual"]) and len(line) < 50:
                skills.append(line.strip())
        elif in_certifications:
            if len(line) < 70 and not any(h in low for h in ["page ", "contact", "summary", "experience"]):
                certifications.append(line.strip())

    # 5. Extract Candidate Block (Name, Headline, Location)
    # In official LinkedIn PDFs, the profile header sits immediately above "Summary" (or "Experience")
    summary_idx = -1
    for i, line in enumerate(lines):
        if line.lower() in ["summary", "about", "about me", "profile summary"]:
            summary_idx = i
            break
    if summary_idx == -1:
        for i, line in enumerate(lines):
            if line.lower() in ["experience", "work experience"]:
                summary_idx = i
                break

    name = ""
    headline = ""
    location = ""

    if summary_idx != -1:
        # Header lines occur prior to summary
        header_lines = lines[:summary_idx]
        
        # Last line of header block is the Location
        if header_lines:
            cand_loc = header_lines[-1].strip()
            if any(w in cand_loc.lower() for w in [
                "india", "division", "district", "states", "usa", "area", "bengaluru",
                "pune", "mumbai", "london", "canada", "york", "francisco", "germany", "australia"
            ]) or "," in cand_loc:
                location = cand_loc
                header_lines = header_lines[:-1]

        # Scan for Candidate Name in header_lines (above headline lines)
        cert_skip_words = [
            "certified", "practitioner", "aws", "exam", "prep", "essentials",
            "google", "associate", "professional", "foundation", "architect", "developer"
        ]
        
        name_idx = -1
        # Scan backward from end of remaining header_lines
        for k in range(len(header_lines) - 1, max(-1, len(header_lines) - 8), -1):
            cand = header_lines[k].strip()
            low_cand = cand.lower()
            words = cand.split()
            
            # Check if text matches LinkedIn URL slug
            if linkedin_slug and re.sub(r"[-\s_]+", "", low_cand) == linkedin_slug.lower():
                name_idx = k
                break
                
            # Or if it's 2-4 capitalized name words, not a certification or header
            if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
                if not any(sw in low_cand for sw in cert_skip_words):
                    if not any(sw in low_cand for sw in ["top skills", "certifications", "contact", "languages"]):
                        name_idx = k
                        break

        if name_idx != -1:
            name = header_lines[name_idx].strip()
            # Everything between name_idx+1 and the end of header_lines forms the headline
            headline_parts = [l.strip() for l in header_lines[name_idx + 1:] if l.strip()]
            headline = " ".join(headline_parts)
            headline = re.sub(r"\s+", " ", headline).strip()

    # Fallback for simple pasted profiles where Name is Line 0
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

    country, city = detect_country_and_city(location)

    # 6. Extract Summary, Experience, Education sections
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
        elif re.match(r"^Page \d+ of \d+$", line, re.IGNORECASE):
            continue

        if current_sec == "about":
            about_lines.append(line)
        elif current_sec == "experience":
            experience_lines.append(line)
        elif current_sec == "education":
            education_lines.append(line)

    # Add core skills mentioned in headline if missing
    if headline:
        for term in ["AI", "Machine Learning", "Python", "Solution Architecture", "Cloud", "PyTorch", "LLM", "Docker", "Kubernetes", "FastAPI", "React"]:
            if term.lower() in headline.lower() and term.lower() not in [s.lower() for s in skills]:
                skills.append(term)

    # Clean up duplicate skills
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
        "certifications": certifications,
        "raw_text": raw_text
    }
