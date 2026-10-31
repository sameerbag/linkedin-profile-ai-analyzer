import re
import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from .models import JobPosting
from .sample_jobs import SAMPLE_JOBS

logger = logging.getLogger(__name__)

# Map common country names to Indeed country codes for JobSpy
COUNTRY_INDEED_MAP = {
    "USA": "USA",
    "United States": "USA",
    "India": "india",
    "United Kingdom": "UK",
    "UK": "UK",
    "Canada": "canada",
    "Germany": "germany",
    "Australia": "australia",
    "France": "france",
    "Netherlands": "netherlands",
    "Singapore": "singapore",
    "Global / Remote": "USA"
}


def search_jobs_multi_portal(
    search_term: str = "Software Engineer",
    country: str = "USA",
    location: str = "",
    is_remote: bool = False,
    selected_portals: Optional[List[str]] = None,
    results_wanted: int = 15,
    hours_old: int = 72,
    use_live_scraper: bool = True
) -> List[JobPosting]:
    """
    Scrapes or aggregates live jobs across multiple portals:
    LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google, RemoteOK.
    
    Gracefully handles rate-limiting, network constraints, and fallbacks.
    """
    if selected_portals is None or not selected_portals:
        selected_portals = ["linkedin", "indeed", "glassdoor", "zip_recruiter"]

    postings: List[JobPosting] = []

    # 1. Attempt Live Multi-Portal Scraping via JobSpy if requested
    if use_live_scraper:
        try:
            from jobspy import scrape_jobs
            
            # Filter portals supported by JobSpy
            valid_sites = [s.lower() for s in selected_portals if s.lower() in [
                "linkedin", "indeed", "glassdoor", "zip_recruiter", "google", "naukri"
            ]]
            if not valid_sites:
                valid_sites = ["indeed", "linkedin"]

            country_code = COUNTRY_INDEED_MAP.get(country, "USA")
            search_loc = location.strip()
            if not search_loc:
                search_loc = "Remote" if is_remote else country

            logger.info(f"Running JobSpy: query='{search_term}', loc='{search_loc}', sites={valid_sites}")

            # Call scrape_jobs
            df = scrape_jobs(
                site_name=valid_sites,
                search_term=search_term,
                location=search_loc,
                results_wanted=min(results_wanted, 25),
                hours_old=hours_old,
                country_indeed=country_code,
                is_remote=is_remote
            )

            if df is not None and not df.empty:
                for _, row in df.iterrows():
                    title = str(row.get("title", "") or "").strip()
                    company = str(row.get("company", "") or "").strip()
                    if not title or title.lower() == "nan":
                        continue

                    # Extract salary string if available
                    min_sal = row.get("min_amount")
                    max_sal = row.get("max_amount")
                    curr = row.get("currency", "$") or "$"
                    sal_str = ""
                    if min_sal and str(min_sal) != "nan":
                        if max_sal and str(max_sal) != "nan":
                            sal_str = f"{curr}{min_sal:,.0f} - {curr}{max_sal:,.0f}"
                        else:
                            sal_str = f"{curr}{min_sal:,.0f}+"

                    job_site = str(row.get("site", "Web") or "Web").capitalize()
                    job_url = str(row.get("job_url", "") or "")
                    desc = str(row.get("description", "") or "")
                    job_loc = str(row.get("location", "") or search_loc)

                    postings.append(
                        JobPosting(
                            id=f"live-{uuid.uuid4().hex[:8]}",
                            title=title,
                            company=company,
                            location=job_loc,
                            country=country,
                            city=location if location else job_loc,
                            is_remote=bool(row.get("is_remote", is_remote)),
                            job_type=str(row.get("job_type", "Full-time") or "Full-time"),
                            job_url=job_url,
                            description=desc if desc != "nan" else f"Job opportunity for {title} at {company}.",
                            date_posted=str(row.get("date_posted", "Recently") or "Recently"),
                            source=job_site,
                            salary=sal_str
                        )
                    )
        except Exception as e:
            logger.warning(f"JobSpy live scrape notice (falling back gracefully): {e}")

    # 2. If postings are few or scraper was restricted, blend in relevant sample benchmarks
    if len(postings) < 3:
        filtered_samples = []
        term_tokens = set(re.findall(r"\w+", search_term.lower()))
        for sample in SAMPLE_JOBS:
            # Check title match or role relevance
            sample_tokens = set(re.findall(r"\w+", sample.title.lower()))
            matches_term = bool(term_tokens & sample_tokens) or not search_term
            matches_country = (
                country.lower() in sample.country.lower()
                or sample.country.lower() in country.lower()
                or country in ["All Countries", "Global / Remote"]
                or sample.is_remote
            )
            if matches_term or matches_country or len(postings) == 0:
                filtered_samples.append(sample)

        # Merge unique by title & company
        seen = {(p.title.lower(), p.company.lower()) for p in postings}
        for s in filtered_samples:
            if (s.title.lower(), s.company.lower()) not in seen:
                postings.append(s)
                seen.add((s.title.lower(), s.company.lower()))

    return postings[:results_wanted]
