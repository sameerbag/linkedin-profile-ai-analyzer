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

    # Extract City: first part before comma, removing noise words
    parts = [p.strip() for p in location_str.split(",") if p.strip()]
    city = parts[0] if parts else location_str
    city = re.sub(r"\b(Greater|Area|Bay|City of|Division|District)\b", "", city, flags=re.IGNORECASE).strip()

    return country, city


def parse_linkedin_text(raw_text: str) -> Dict[str, Any]:
    """
    Parse LinkedIn profile PDF export text into structured candidate fields.

    LinkedIn PDF layout (pypdf linear extraction):
    -----------------------------------------------
    Page 1 starts with the LEFT sidebar content first:
      Contact
      [address block]
      [phone] (Mobile)
      [email]
      www.linkedin.com/in/[slug] (LinkedIn)
      [blog] (Blog)
      Top Skills
      [skill1]
      [skill2]
      [skill3]
      Certifications
      [cert1]
      [cert2]
    Then the MAIN COLUMN header block:
      [Candidate Full Name]
      [Headline - may wrap across multiple lines]
      [City, State/Division, Country]
    Then section markers:
      Summary
      [summary text...]
      Experience
      [experience entries...]
      Education
      [education entries...]
    """
    # Step 1: Clean text
    cleaned = raw_text.replace("\xa0", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", cleaned)

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    if not lines:
        return _empty_result(raw_text)

    # ─── STEP 2: Contact Info (regex over full text) ───────────────────────────

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}", cleaned)
    email = email_match.group(0).strip() if email_match else ""

    phone = ""
    for line in lines:
        # "(Mobile)" or "(Phone)" tagged lines are guaranteed phone lines
        m = re.search(r"(\+?[\d\s\-\.]{7,})", line)
        if m and any(tag in line.lower() for tag in ["(mobile)", "(phone)", "(work)", "(home)"]):
            candidate = re.sub(r"[^\d+]", "", m.group(0))
            if 8 <= len(candidate) <= 15:
                phone = m.group(0).strip()
                break
    if not phone:
        # Fallback: find a standalone 10-digit number not in a postal-code context
        for line in lines:
            m = re.search(r"(?<!\d)(\+?91[-\s]?)?(0?[6-9]\d{9})(?!\d)", line)
            if m:
                phone = m.group(0).strip()
                break

    # LinkedIn URL - may be split across two lines: "www.linkedin.com/in/" + slug
    # The slug line may have " (LinkedIn)" appended (e.g. "sameerbagade (LinkedIn)")
    linkedin_url = ""
    linkedin_slug = ""
    for i, line in enumerate(lines):
        if "linkedin.com/in" in line.lower():
            combined = line
            # Check next line for slug continuation — but only if it doesn't look like a section
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                if not any(kw in next_line.lower() for kw in ["contact", "top skills", "certifications", "summary", "experience", "education", "http", "@"]):
                    combined = line + " " + next_line
            # Strip common LinkedIn PDF suffixes like "(LinkedIn)", "(Blog)", etc.
            combined_clean = re.sub(r"\s*\([^)]*\)\s*$", "", combined).strip()
            # Collapse space between "linkedin.com/in/" and the slug (PDF may insert a space)
            combined_clean = re.sub(r"(linkedin\.com/in/)\s+", r"\1", combined_clean)
            m = re.search(r"linkedin\.com/in/([a-zA-Z0-9_-]+)", combined_clean)
            if m:
                linkedin_slug = m.group(1)
                linkedin_url = f"https://www.linkedin.com/in/{linkedin_slug}"
                break

    # ─── STEP 3: Identify all section boundary indices ─────────────────────────
    SECTION_HEADERS = {
        "contact": re.compile(r"^contact$", re.IGNORECASE),
        "top_skills": re.compile(r"^top skills$", re.IGNORECASE),
        "languages": re.compile(r"^languages$", re.IGNORECASE),
        "certifications": re.compile(r"^certifications$", re.IGNORECASE),
        "summary": re.compile(r"^(summary|about|about me|profile summary)$", re.IGNORECASE),
        "experience": re.compile(r"^(experience|work experience|professional experience|employment)$", re.IGNORECASE),
        "education": re.compile(r"^(education|academic background)$", re.IGNORECASE),
        "publications": re.compile(r"^(publications|projects|honors|awards|volunteer)$", re.IGNORECASE),
    }

    section_boundaries = []  # list of (line_index, section_name)
    for i, line in enumerate(lines):
        for sec_name, pat in SECTION_HEADERS.items():
            if pat.match(line):
                section_boundaries.append((i, sec_name))
                break

    def get_section_lines(target_sec: str) -> List[str]:
        """Return lines belonging to a section (between its header and the next section header)."""
        start_idx = None
        end_idx = len(lines)
        for j, (idx, sec) in enumerate(section_boundaries):
            if sec == target_sec:
                start_idx = idx + 1
                if j + 1 < len(section_boundaries):
                    end_idx = section_boundaries[j + 1][0]
                break
        if start_idx is None:
            return []
        return [l for l in lines[start_idx:end_idx] if l.strip()]

    # ─── STEP 4: Skills from "Top Skills" section ──────────────────────────────
    raw_skills = get_section_lines("top_skills")
    skills = []
    for s in raw_skills:
        low = s.lower()
        # Skip language proficiency lines
        if any(h in low for h in ["(professional", "(native", "(elementary", "(bilingual", "(limited"]):
            continue
        if len(s) < 60:
            skills.append(s.strip())

    # ─── STEP 5: Certifications ────────────────────────────────────────────────
    cert_lines_raw = get_section_lines("certifications")
    certifications = []
    for s in cert_lines_raw:
        low = s.lower()
        if re.match(r"^page \d+ of \d+$", s, re.IGNORECASE):
            continue
        # Stop when we hit a 2-4 Title Case word line that looks like a person's name
        # (this is where the sidebar ends and the main column candidate block begins)
        words = s.split()
        if (2 <= len(words) <= 4
                and all(w[0].isupper() for w in words if w.isalpha() and len(w) > 1)
                and not any(cw in low for cw in ["certified", "practitioner", "aws", "exam",
                                                  "prep", "essentials", "google", "associate",
                                                  "professional", "foundation", "architect",
                                                  "developer", "analyst", "specialist", "generative"])
                and not re.search(r"[\d@/|]", s)):
            break
        if len(s) < 80:
            certifications.append(s.strip())

    # ─── STEP 6: Candidate Header Block — scan backward from Summary boundary ──
    # Strategy: Look at lines BEFORE the Summary/Experience section header.
    # The candidate name, headline, and location are the last few lines before Summary.
    # We identify the name line by matching it to the LinkedIn slug or Title Case heuristics,
    # making sure not to confuse it with certifications or skills.
    summary_boundary = next(((idx, sec) for idx, sec in section_boundaries if sec == "summary"), None)
    experience_boundary = next(((idx, sec) for idx, sec in section_boundaries if sec == "experience"), None)
    anchor = summary_boundary or experience_boundary

    name = ""
    headline = ""
    location = ""

    CERT_WORDS = {"certified", "practitioner", "aws", "exam", "prep", "essentials",
                  "google", "associate", "professional", "foundation", "architect",
                  "developer", "analyst", "specialist", "generative"}
    SIDEBAR_HEADERS = {"contact", "top skills", "certifications", "languages", "honors", "awards"}

    if anchor is not None:
        anchor_idx = anchor[0]
        # Scan backward from anchor to find Name, Headline, Location
        # Location: The line immediately before Summary is the candidate location
        # Name: A 2-4 Title Case word line, matched by slug or heuristics
        # Headline: Lines between Name and Location

        # Collect candidate block — all lines from after top_skills/certs up to anchor
        # But we don't know exactly where sidebar ends, so we scan all lines before anchor
        pre_anchor = [l for l in lines[:anchor_idx] if not re.match(r"^page \d+ of \d+$", l, re.IGNORECASE)]

        # Find Location: last line before anchor that looks like a geographic location
        location_idx_in_pre = -1
        for k in range(len(pre_anchor) - 1, -1, -1):
            cand_loc = pre_anchor[k].strip()
            if (
                any(w in cand_loc.lower() for w in [
                    "india", "division", "district", "states", "usa", "area",
                    "bengaluru", "bangalore", "pune", "mumbai", "london", "canada",
                    "york", "francisco", "germany", "australia", "singapore",
                    "kolkata", "hyderabad", "chennai", "delhi", "noida", "maharashtra",
                    "karnataka", "gujarat", "telangana", "punjab", "haryana"
                ]) or ("," in cand_loc and len(cand_loc) < 80 and not any(sw in cand_loc.lower() for sw in CERT_WORDS))
            ):
                # Make sure it's not a street address (has digit) — allow postal area matches if no digit
                if not re.search(r"\d{4,}", cand_loc):
                    location = cand_loc
                    location_idx_in_pre = k
                    break

        # Search backward from location for Name (2-4 Title Case words matching slug or heuristic)
        search_end = location_idx_in_pre if location_idx_in_pre != -1 else len(pre_anchor)
        name_idx_in_pre = -1
        for k in range(search_end - 1, max(-1, search_end - 15), -1):
            cand_line = pre_anchor[k].strip()
            low_cand = cand_line.lower()
            words = cand_line.split()

            # Skip sidebar section headers and known noise
            if low_cand in SIDEBAR_HEADERS:
                continue
            # Skip lines with cert keywords
            if any(cw in low_cand for cw in CERT_WORDS):
                continue
            # Skip skill lines
            if any(low_cand == s.lower() for s in skills):
                continue
            # Skip lines that are too long to be a name
            if len(cand_line) > 60:
                continue

            # Slug-based match (most reliable)
            if linkedin_slug:
                slug_clean = re.sub(r"[-\s_0-9]+", "", linkedin_slug.lower())
                line_clean = re.sub(r"[^a-z]", "", low_cand)
                if line_clean == slug_clean and 2 <= len(words) <= 4:
                    name_idx_in_pre = k
                    break

            # Title Case heuristic: 2-4 capitalized words, no cert/tech terms
            if 2 <= len(words) <= 4:
                if all(w[0].isupper() for w in words if w.isalpha() and len(w) > 1):
                    if not any(cw in low_cand for cw in CERT_WORDS):
                        if not re.search(r"[\d@/]", cand_line):
                            name_idx_in_pre = k
                            break

        if name_idx_in_pre != -1:
            name = pre_anchor[name_idx_in_pre].strip()
            # Headline = lines between name and location
            hl_start = name_idx_in_pre + 1
            hl_end = location_idx_in_pre if location_idx_in_pre != -1 else search_end
            headline_parts = [l.strip() for l in pre_anchor[hl_start:hl_end] if l.strip()]
            headline = " ".join(headline_parts)
            headline = re.sub(r"\s+", " ", headline).strip()

    # ─── STEP 7: Fallback Name lookup via slug/email ───────────────────────────
    if not name and (linkedin_slug or email):
        token = linkedin_slug if linkedin_slug else email.split("@")[0]
        token_clean = re.sub(r"[0-9.\-_]+", "", token).lower()
        for l in lines:
            l_clean = re.sub(r"[^a-z]", "", l.lower())
            if l_clean == token_clean and 2 <= len(l.split()) <= 4:
                name = l.strip()
                break

    # ─── STEP 8: Summary, Experience, Education ────────────────────────────────
    about_lines = get_section_lines("summary")
    experience_lines = get_section_lines("experience")
    education_lines = get_section_lines("education")

    # Remove page markers from experience (appears mid-text in LinkedIn PDFs)
    experience_lines = [l for l in experience_lines if not re.match(r"^page \d+ of \d+$", l, re.IGNORECASE)]

    country, city = detect_country_and_city(location)

    # ─── STEP 9: Add skills from headline (if not already present) ─────────────
    if headline:
        for term in ["AI", "Machine Learning", "Python", "Cloud", "PyTorch", "LLM", "Docker",
                     "Kubernetes", "FastAPI", "React", "Solution Architecture"]:
            if term.lower() in headline.lower() and term.lower() not in [s.lower() for s in skills]:
                skills.append(term)

    # ─── STEP 10: Guardrails ───────────────────────────────────────────────────
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


def _empty_result(raw_text: str) -> Dict[str, Any]:
    return {
        "name": "", "headline": "", "location": "", "country": "", "city": "",
        "email": "", "phone": "", "linkedin_url": "", "about": "", "experience": "",
        "skills": [], "education": "", "certifications": [], "raw_text": raw_text
    }
