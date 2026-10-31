import re
from typing import Dict, Any, List, Tuple
from pypdf import PdfReader


def extract_text_from_pdf(pdf_file, max_pages: int = 25) -> str:
    """
    Safely extract raw text from uploaded PDF file.
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
             'San Francisco Bay Area' -> ('USA', 'San Francisco')
    """
    if not location_str:
        return "", ""

    loc_lower = location_str.lower()
    country = ""

    if any(k in loc_lower for k in [
        "india", "karnataka", "maharashtra", "delhi", "tamil nadu", "telangana", "gujarat", "punjab",
        "haryana", "bengaluru", "bangalore", "mumbai", "pune", "hyderabad", "chennai", "noida",
        "gurgaon", "gurugram", "nasik", "nagpur", "kolkata", "ahmedabad", "jaipur", "chandigarh"
    ]):
        country = "India"
    elif any(k in loc_lower for k in [
        "united states", "usa", "u.s.a", "san francisco", "new york", "seattle", "austin",
        "california", "texas", "washington", "boston", "chicago", "los angeles", "colorado", "new jersey"
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
    elif "united arab emirates" in loc_lower or "uae" in loc_lower or "dubai" in loc_lower:
        country = "United Arab Emirates"

    # Extract City: first part before comma, removing noise words
    parts = [p.strip() for p in location_str.split(",") if p.strip()]
    city = parts[0] if parts else location_str
    city = re.sub(r"\b(Greater|Area|Bay|City of|Division|District)\b", "", city, flags=re.IGNORECASE).strip()

    return country, city


def estimate_years_of_experience(experience_text: str) -> str:
    """
    Computes total years of experience from extracted experience lines.
    E.g. '4 years 6 months' + '3 years 5 months' -> '8+ years'
    """
    if not experience_text:
        return ""
    
    total_months = 0
    # Match patterns like "4 years 6 months", "3 years", "6 months"
    matches = re.findall(r"(?:(\d+)\s*(?:years?|yrs?))?\s*(?:(\d+)\s*(?:months?|mos?))?", experience_text, re.IGNORECASE)
    for y_str, m_str in matches:
        if y_str or m_str:
            y = int(y_str) if y_str else 0
            m = int(m_str) if m_str else 0
            if y > 0 or m > 0:
                total_months += y * 12 + m

    if total_months >= 12:
        years = round(total_months / 12)
        return f"{years}+ years"
    elif total_months > 0:
        return f"{total_months} months"

    # Fallback: check earliest year mentioned in experience
    years_found = [int(y) for y in re.findall(r"\b(19\d\d|20\d\d)\b", experience_text)]
    if years_found:
        earliest = min(years_found)
        if 1980 <= earliest <= 2026:
            calc_years = 2026 - earliest
            if calc_years > 0:
                return f"{calc_years}+ years"

    return ""


def parse_linkedin_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse LinkedIn profile PDF export text into structured candidate fields.

    LinkedIn PDF layout (pypdf linear text stream):
    -------------------------------------------------
    Page 1 starts with the LEFT sidebar items first:
      Contact
        [Address lines]
        [Phone] (Mobile)
        [Email]
        www.linkedin.com/in/[slug] (LinkedIn)
        [Blog/Portfolio] (Blog)
      Top Skills
        [skill1]
        [skill2]
        [skill3]
      Languages (optional)
        [lang1]
      Certifications (optional)
        [cert1]
        [cert2]
      Honors-Awards (optional)
    THEN the RIGHT column (Main Column) begins with:
      [Candidate Full Name]
      [Headline - 1 to 4 lines]
      [Location]
    THEN the main body sections follow:
      Summary (or About)
      Experience
      Education
    """
    cleaned = raw_text.replace("\xa0", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return _empty_result(raw_text)

    # ─── STEP 1: Contact Details ──────────────────────────────────────────────
    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", cleaned)
    email = email_match.group(0).strip() if email_match else ""

    phone = ""
    for line in lines:
        m = re.search(r"(\+?[\d\s\-\.]{7,})", line)
        if m and any(tag in line.lower() for tag in ["(mobile)", "(phone)", "(work)", "(home)"]):
            candidate = re.sub(r"[^\d+]", "", m.group(0))
            if 8 <= len(candidate) <= 15:
                phone = m.group(0).strip()
                break
    if not phone:
        for line in lines:
            m = re.search(r"(?<!\d)(\+?91[-\s]?)?(0?[6-9]\d{9})(?!\d)", line)
            if m:
                phone = m.group(0).strip()
                break

    # LinkedIn URL extraction
    linkedin_url = ""
    linkedin_slug = ""
    for i, line in enumerate(lines):
        if "linkedin.com/in" in line.lower():
            combined = line
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if not any(kw in next_line.lower() for kw in ["contact", "top skills", "certifications", "summary", "experience", "education", "http", "@"]):
                    combined = line + " " + next_line
            combined_clean = re.sub(r"\s*\([^)]*\)\s*$", "", combined).strip()
            combined_clean = re.sub(r"(linkedin\.com/in/)\s+", r"\1", combined_clean)
            m = re.search(r"linkedin\.com/in/([a-zA-Z0-9_-]+)", combined_clean)
            if m:
                linkedin_slug = m.group(1)
                linkedin_url = f"https://www.linkedin.com/in/{linkedin_slug}"
                break

    # Portfolio / Blog links
    portfolio_url = ""
    for line in lines:
        if any(tag in line.lower() for tag in ["(blog)", "(portfolio)", "(company website)", "github.com"]):
            link_clean = re.sub(r"\s*\([^)]*\)\s*$", "", line).strip()
            if not link_clean.startswith("http"):
                link_clean = "https://" + link_clean
            portfolio_url = link_clean
            break

    # Postal code in contact address block
    postal_code = ""
    for line in lines[:10]:
        m = re.search(r"\b(\d{5,6})\b", line)
        if m and line != phone:
            postal_code = m.group(1)
            break

    # ─── STEP 2: Section Header Detection ──────────────────────────────────────
    SIDEBAR_PATTERNS = {
        "contact": re.compile(r"^contact$", re.IGNORECASE),
        "top_skills": re.compile(r"^top skills$", re.IGNORECASE),
        "languages": re.compile(r"^languages$", re.IGNORECASE),
        "certifications": re.compile(r"^certifications$", re.IGNORECASE),
        "honors": re.compile(r"^(honors|honors-awards|honors & awards|awards)$", re.IGNORECASE),
        "publications": re.compile(r"^(publications|patents)$", re.IGNORECASE),
    }

    MAIN_PATTERNS = {
        "summary": re.compile(r"^(summary|about|about me|profile summary)$", re.IGNORECASE),
        "experience": re.compile(r"^(experience|work experience|professional experience|employment)$", re.IGNORECASE),
        "education": re.compile(r"^(education|academic background)$", re.IGNORECASE),
        "volunteer": re.compile(r"^(volunteer|volunteering|volunteer experience)$", re.IGNORECASE),
    }

    # Find all header line positions
    sidebar_headers: List[Tuple[int, str]] = []  # (index, section_name)
    main_headers: List[Tuple[int, str]] = []     # (index, section_name)

    for i, line in enumerate(lines):
        matched = False
        for sec_name, pat in SIDEBAR_PATTERNS.items():
            if pat.match(line):
                sidebar_headers.append((i, sec_name))
                matched = True
                break
        if not matched:
            for sec_name, pat in MAIN_PATTERNS.items():
                if pat.match(line):
                    main_headers.append((i, sec_name))
                    matched = True
                    break

    # Main column anchor = first main body section header (Summary or Experience)
    anchor_idx = main_headers[0][0] if main_headers else len(lines)

    # ─── STEP 3: Identify Candidate Header Block (Name, Headline, Location) ────
    # In LinkedIn PDFs, the main column starts with:
    # [Candidate Name] -> [Headline 1..N lines] -> [Location]
    # immediately preceding the first main body section (Summary / Experience).
    pre_anchor = [l for l in lines[:anchor_idx] if not re.match(r"^page \d+ of \d+$", l, re.IGNORECASE)]

    CERT_WORDS = {
        "certified", "practitioner", "aws", "exam", "prep", "essentials",
        "google", "associate", "professional", "foundation", "architect",
        "developer", "analyst", "specialist", "generative", "cloud"
    }

    # 3a. Find Location: last line before anchor that looks geographic
    location = ""
    loc_idx = -1
    for k in range(len(pre_anchor) - 1, -1, -1):
        cand_loc = pre_anchor[k].strip()
        low = cand_loc.lower()
        # Skip section headers
        if any(pat.match(cand_loc) for pat in {**SIDEBAR_PATTERNS, **MAIN_PATTERNS}.values()):
            continue
        # Check geographic patterns
        is_geo = any(w in low for w in [
            "india", "division", "district", "states", "usa", "area", "bay",
            "bengaluru", "bangalore", "pune", "mumbai", "london", "canada",
            "york", "francisco", "germany", "australia", "singapore",
            "kolkata", "hyderabad", "chennai", "delhi", "noida", "maharashtra",
            "karnataka", "gujarat", "telangana", "punjab", "haryana", "emirates", "dubai"
        ]) or ("," in cand_loc and len(cand_loc) < 80 and not any(sw in low for sw in CERT_WORDS))

        if is_geo and not re.search(r"\d{4,}", cand_loc) and not re.search(r"[@|/]", cand_loc):
            location = cand_loc
            loc_idx = k
            break

    # 3b. Find Name: look backward from location for a 2-4 Title Case word line
    search_end = loc_idx if loc_idx != -1 else len(pre_anchor)
    name = ""
    name_idx = -1

    # First attempt: Match via LinkedIn slug or email prefix
    slug_clean = re.sub(r"[-\s_0-9]+", "", linkedin_slug.lower()) if linkedin_slug else ""
    email_clean = re.sub(r"[0-9.\-_]+", "", email.split("@")[0].lower()) if email else ""

    for k in range(search_end - 1, max(-1, search_end - 12), -1):
        cand_line = pre_anchor[k].strip()
        low_cand = cand_line.lower()
        words = cand_line.split()

        # Cannot contain symbols
        if re.search(r"[@|/\\+]", cand_line) or len(cand_line) > 50:
            continue
        # Cannot be a section header
        if any(pat.match(cand_line) for pat in SIDEBAR_PATTERNS.values()):
            continue

        cand_clean = re.sub(r"[^a-z]", "", low_cand)
        if slug_clean and cand_clean == slug_clean and 2 <= len(words) <= 4:
            name = cand_line
            name_idx = k
            break
        elif email_clean and cand_clean == email_clean and 2 <= len(words) <= 4:
            name = cand_line
            name_idx = k
            break

    # Second attempt: Heuristic Title Case scan
    if not name:
        for k in range(search_end - 1, max(-1, search_end - 12), -1):
            cand_line = pre_anchor[k].strip()
            low_cand = cand_line.lower()
            words = cand_line.split()

            if re.search(r"[@|/\\+]", cand_line) or len(cand_line) > 50:
                continue
            if any(cw in low_cand for cw in CERT_WORDS):
                continue
            if any(pat.match(cand_line) for pat in SIDEBAR_PATTERNS.values()):
                continue

            if 2 <= len(words) <= 4:
                if all(w[0].isupper() for w in words if w.isalpha() and len(w) > 1):
                    # Ensure it does not look like a job role headline (e.g. "Senior Software Engineer")
                    # unless it is the highest line before location
                    name = cand_line
                    name_idx = k
                    break

    # 3c. Extract Headline: all lines strictly between Name and Location
    headline = ""
    if name_idx != -1 and loc_idx != -1 and name_idx < loc_idx:
        hl_lines = [pre_anchor[idx].strip() for idx in range(name_idx + 1, loc_idx) if pre_anchor[idx].strip()]
        headline = " ".join(hl_lines)
        headline = re.sub(r"\s+", " ", headline).strip()
    elif name_idx != -1 and loc_idx == -1:
        hl_lines = [pre_anchor[idx].strip() for idx in range(name_idx + 1, len(pre_anchor)) if pre_anchor[idx].strip()]
        headline = " ".join(hl_lines)
        headline = re.sub(r"\s+", " ", headline).strip()

    # ─── STEP 4: STRICT SIDEBAR BOUNDARY ──────────────────────────────────────
    # Crucial Guarantee: The Left Sidebar ENDS before Candidate Name starts!
    # No sidebar section (skills, certs, languages) can ever extend past name_idx!
    sidebar_end_idx = name_idx if name_idx != -1 else (loc_idx if loc_idx != -1 else anchor_idx)

    def get_sidebar_section_lines(target_sec: str) -> List[str]:
        """Extract lines of a sidebar section strictly bounded by the next sidebar header or name_idx."""
        start = None
        for j, (idx, sname) in enumerate(sidebar_headers):
            if sname == target_sec:
                start = idx + 1
                # Find the next sidebar section header after this one
                end = sidebar_end_idx
                for next_idx, _ in sidebar_headers[j + 1:]:
                    if next_idx < sidebar_end_idx:
                        end = next_idx
                        break
                return [l.strip() for l in lines[start:end] if l.strip() and not re.match(r"^page \d+ of \d+$", l, re.IGNORECASE)]
        return []

    # Skills from "Top Skills"
    raw_skills = get_sidebar_section_lines("top_skills")
    skills = []
    for s in raw_skills:
        low = s.lower()
        # Filter language proficiencies or noise
        if any(h in low for h in ["(professional", "(native", "(elementary", "(bilingual", "(limited"]):
            continue
        if len(s) < 60:
            skills.append(s.strip())

    # Certifications
    raw_certs = get_sidebar_section_lines("certifications")
    certifications = [c.strip() for c in raw_certs if len(c) < 80 and not re.match(r"^page \d+ of \d+$", c, re.IGNORECASE)]

    # ─── STEP 5: Main Body Sections ───────────────────────────────────────────
    def get_main_section_lines(target_sec: str) -> List[str]:
        """Extract lines of a main body section between its header and the next main header."""
        for j, (idx, mname) in enumerate(main_headers):
            if mname == target_sec:
                start = idx + 1
                end = main_headers[j + 1][0] if j + 1 < len(main_headers) else len(lines)
                return [l.strip() for l in lines[start:end] if l.strip() and not re.match(r"^page \d+ of \d+$", l, re.IGNORECASE)]
        return []

    about_lines = get_main_section_lines("summary")
    experience_lines = get_main_section_lines("experience")
    education_lines = get_main_section_lines("education")

    country, city = detect_country_and_city(location)
    exp_text = "\n".join(experience_lines).strip()
    years_exp = estimate_years_of_experience(exp_text)

    # ─── STEP 6: Add relevant skills from headline ─────────────────────────────
    if headline:
        for term in ["AI", "Machine Learning", "Python", "Cloud", "PyTorch", "LLM", "Docker",
                     "Kubernetes", "FastAPI", "React", "Solution Architecture"]:
            if term.lower() in headline.lower() and term.lower() not in [s.lower() for s in skills]:
                skills.append(term)

    # ─── STEP 7: Guardrails ───────────────────────────────────────────────────
    TECH_TERMS = {
        "cascading style sheets (css)", "css", "html", "solution architecture",
        "ai", "machine learning", "python", "java", "docker", "kubernetes",
        "top skills", "skills", "cloud", "aws", "react", "c++", "c#",
        "angular", "javascript", "typescript", "devops", "sql", "nosql", "git", "linux"
    }
    if name and name.lower().strip() in TECH_TERMS:
        name = ""
    if city and city.lower().strip() in TECH_TERMS:
        city = ""
    if not city:
        for known_city in ["Pune", "Bengaluru", "Bangalore", "Mumbai", "Hyderabad", "Chennai",
                           "Delhi", "Noida", "Gurgaon", "Gurugram", "San Francisco", "New York",
                           "London", "Toronto", "Nasik", "Nagpur", "Kolkata", "Ahmedabad"]:
            if re.search(r"\b" + re.escape(known_city) + r"\b", cleaned, re.IGNORECASE):
                city = known_city
                break

    # Deduplicate skills
    unique_skills = []
    for s in skills:
        cs = s.strip()
        if cs and cs.lower() not in [u.lower() for u in unique_skills] and len(cs) < 60:
            unique_skills.append(cs)

    first_name = name.split()[0] if name else ""
    last_name = " ".join(name.split()[1:]) if len(name.split()) > 1 else ""

    return {
        "full_name": name,
        "name": name,
        "first_name": first_name,
        "last_name": last_name,
        "headline": headline,
        "location": location,
        "current_location": location or f"{city}, {country}".strip(", "),
        "country": country,
        "city": city,
        "postal_code": postal_code,
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "portfolio_url": portfolio_url,
        "years_of_experience": years_exp,
        "about": "\n".join(about_lines).strip(),
        "experience": exp_text,
        "skills": unique_skills,
        "education": "\n".join(education_lines).strip(),
        "certifications": certifications,
        "raw_text": raw_text
    }


def _empty_result(raw_text: str) -> Dict[str, Any]:
    return {
        "full_name": "", "name": "", "first_name": "", "last_name": "", "headline": "",
        "location": "", "country": "", "city": "", "postal_code": "",
        "email": "", "phone": "", "linkedin_url": "", "portfolio_url": "",
        "years_of_experience": "", "about": "", "experience": "",
        "skills": [], "education": "", "certifications": [], "raw_text": raw_text
    }
