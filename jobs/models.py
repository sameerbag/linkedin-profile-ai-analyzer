from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import json


@dataclass
class JobPosting:
    id: str
    title: str
    company: str
    location: str
    country: str
    city: str = ""
    is_remote: bool = False
    job_type: str = "Full-time"  # Full-time, Contract, Part-time, Internship
    job_url: str = ""
    description: str = ""
    date_posted: str = ""
    source: str = "LinkedIn"  # LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google, RemoteOK
    salary: str = ""
    company_url: str = ""
    
    # Matching metadata computed by AI matcher
    fit_score: int = 0
    match_tier: str = "Pending"  # 🔥 Top Fit, ✨ Strong Match, ⚖️ Moderate, ⚠️ Low
    match_summary: str = ""
    matching_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    recommended_highlights: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "JobPosting":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ApplicantProfile:
    # Basic Contact & Identifiers
    full_name: str = ""
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: str = ""
    
    # Location
    country: str = ""
    city: str = ""
    state_province: str = ""
    postal_code: str = ""
    current_location: str = ""
    
    # Professional Links
    linkedin_url: str = ""
    github_url: str = ""
    portfolio_url: str = ""
    
    # Work Authorization & Preferences
    work_authorization: str = "Authorized to work (No sponsorship required)"
    requires_sponsorship: str = "No"
    willing_to_relocate: str = "Yes"
    target_work_mode: str = "Remote or Hybrid"  # Remote, Hybrid, On-site, Any
    notice_period: str = "Immediate / 2 Weeks"
    expected_salary: str = ""
    years_of_experience: str = ""
    
    # Profile sections (imported or parsed from LinkedIn)
    headline: str = ""
    about: str = ""
    experience: str = ""
    skills: List[str] = field(default_factory=list)
    education: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApplicantProfile":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class ApplicationRecord:
    job_id: str
    job_title: str
    company: str
    location: str
    job_url: str
    source: str
    fit_score: int
    applied_date: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M"))
    status: str = "Applied"  # Shortlisted, Consented, Applied, Interviewing, Offer, Rejected
    tailored_cover_letter: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ApplicationRecord":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
