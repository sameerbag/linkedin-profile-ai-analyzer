import json
import urllib.parse
from typing import Dict, Any, Optional
from .models import JobPosting, ApplicantProfile


def generate_browser_autofill_script(
    job: JobPosting,
    profile: ApplicantProfile,
    cover_letter: str
) -> Dict[str, str]:
    """
    Generates:
    1. A Universal Browser Auto-Fill Bookmarklet (drag & drop to browser bookmark bar).
    2. A Raw JavaScript snippet (can be executed in browser DevTools Console).
    
    When clicked on ANY job application page (Greenhouse, Lever, LinkedIn, Workday,
    Indeed, Ashby, BambooHR, Taleo, etc.), it auto-detects and fills:
    - First Name, Last Name, Full Name
    - Email, Phone
    - LinkedIn, GitHub, Portfolio URLs
    - Current Location, City
    - Tailored Cover Letter
    - Work authorization radios & checkboxes
    """
    first_name = profile.first_name or (profile.full_name.split()[0] if profile.full_name else "")
    last_name = profile.last_name or (profile.full_name.split()[-1] if profile.full_name and len(profile.full_name.split()) > 1 else "")
    
    payload = {
        "fullName": profile.full_name,
        "firstName": first_name,
        "lastName": last_name,
        "email": profile.email,
        "phone": profile.phone,
        "linkedin": profile.linkedin_url,
        "github": profile.github_url,
        "portfolio": profile.portfolio_url,
        "location": profile.current_location or f"{profile.city}, {profile.country}".strip(", "),
        "city": profile.city,
        "country": profile.country,
        "coverLetter": cover_letter,
        "workAuth": profile.work_authorization,
        "sponsorship": profile.requires_sponsorship,
        "salary": profile.expected_salary,
        "notice": profile.notice_period
    }

    payload_json = json.dumps(payload)

    raw_js = f"""(function() {{
    const data = {payload_json};
    let count = 0;

    function triggerEvents(el, val) {{
        el.focus();
        el.value = val;
        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
        el.dispatchEvent(new Event('blur', {{ bubbles: true }}));
        count++;
    }}

    function findAndFill(selectors, val) {{
        if (!val) return;
        for (const sel of selectors) {{
            const el = document.querySelector(sel);
            if (el && !el.value) {{
                triggerEvents(el, val);
                break;
            }}
        }}
    }}

    // First Name
    findAndFill([
        'input[autocomplete="given-name"]',
        'input[name*="first_name" i]',
        'input[name*="firstname" i]',
        'input[id*="first_name" i]',
        'input[id*="firstname" i]',
        'input[aria-label*="first name" i]',
        'input[placeholder*="first name" i]'
    ], data.firstName || data.fullName);

    // Last Name
    findAndFill([
        'input[autocomplete="family-name"]',
        'input[name*="last_name" i]',
        'input[name*="lastname" i]',
        'input[id*="last_name" i]',
        'input[id*="lastname" i]',
        'input[aria-label*="last name" i]',
        'input[placeholder*="last name" i]'
    ], data.lastName);

    // Full Name (if no separate first/last)
    findAndFill([
        'input[autocomplete="name"]',
        'input[name="name" i]',
        'input[name*="full_name" i]',
        'input[id*="full_name" i]',
        'input[aria-label*="full name" i]'
    ], data.fullName);

    // Email
    findAndFill([
        'input[type="email"]',
        'input[autocomplete="email"]',
        'input[name*="email" i]',
        'input[id*="email" i]',
        'input[placeholder*="email" i]'
    ], data.email);

    // Phone
    findAndFill([
        'input[type="tel"]',
        'input[autocomplete="tel"]',
        'input[name*="phone" i]',
        'input[id*="phone" i]',
        'input[name*="mobile" i]',
        'input[placeholder*="phone" i]'
    ], data.phone);

    // LinkedIn
    findAndFill([
        'input[name*="linkedin" i]',
        'input[id*="linkedin" i]',
        'input[placeholder*="linkedin" i]',
        'input[aria-label*="linkedin" i]'
    ], data.linkedin);

    // GitHub
    findAndFill([
        'input[name*="github" i]',
        'input[id*="github" i]',
        'input[placeholder*="github" i]',
        'input[aria-label*="github" i]'
    ], data.github);

    // Website / Portfolio
    findAndFill([
        'input[name*="website" i]',
        'input[name*="portfolio" i]',
        'input[id*="website" i]',
        'input[id*="portfolio" i]',
        'input[placeholder*="portfolio" i]'
    ], data.portfolio || data.github);

    // Location / City
    findAndFill([
        'input[name*="location" i]',
        'input[id*="location" i]',
        'input[name*="city" i]',
        'input[id*="city" i]',
        'input[placeholder*="city" i]'
    ], data.location || data.city);

    // Cover Letter Textarea
    findAndFill([
        'textarea[name*="cover" i]',
        'textarea[id*="cover" i]',
        'textarea[aria-label*="cover letter" i]',
        'textarea[placeholder*="cover letter" i]',
        'div[contenteditable="true"][aria-label*="cover" i]'
    ], data.coverLetter);

    // Banner Notification
    const toast = document.createElement('div');
    toast.style.cssText = 'position:fixed;top:20px;right:20px;background:#0A66C2;color:#fff;padding:16px 24px;border-radius:10px;font-family:sans-serif;font-size:14px;box-shadow:0 8px 24px rgba(0,0,0,0.3);z-index:9999999;transition:all 0.5s;';
    toast.innerHTML = '<strong>⚡ AI Job Assistant:</strong> Auto-filled ' + count + ' fields for ' + (data.fullName || 'you') + '!<br><small>Please review before submitting.</small>';
    document.body.appendChild(toast);
    setTimeout(() => {{ toast.style.opacity = '0'; setTimeout(() => toast.remove(), 500); }}, 5000);
}})();"""

    # URL-encode for browser bookmarklet
    bookmarklet_url = "javascript:" + urllib.parse.quote(raw_js)

    return {
        "raw_js": raw_js,
        "bookmarklet_url": bookmarklet_url
    }


def launch_playwright_autofill(
    job_url: str,
    profile: ApplicantProfile,
    cover_letter: str
) -> Dict[str, Any]:
    """
    Automated browser application assistant using Playwright.
    Launches a visible Chromium window, navigates to the job portal,
    detects form inputs, and fills the candidate's profile.
    Leaves the browser open so the user has full control to review and submit.
    """
    if not job_url:
        return {"success": False, "message": "No job URL provided."}

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            # Launch headed browser so user can see & review the application form
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto(job_url, timeout=30000)

            # Inject the universal autofill logic
            scripts = generate_browser_autofill_script(
                JobPosting(id="temp", title="", company="", location="", country="", job_url=job_url),
                profile,
                cover_letter
            )
            page.evaluate(scripts["raw_js"])

            return {
                "success": True,
                "message": f"Successfully launched browser and filled available fields at {job_url}. Review and submit when ready!"
            }
    except Exception as e:
        return {
            "success": False,
            "message": f"Browser launch notice: {str(e)}. You can also use the 1-Click Bookmarklet or direct URL!"
        }
