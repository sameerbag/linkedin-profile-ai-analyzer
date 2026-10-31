import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from .models import ApplicationRecord

TRACKER_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "applications.json")


def _ensure_dir():
    os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
    if not os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def get_all_applications() -> List[ApplicationRecord]:
    _ensure_dir()
    try:
        with open(TRACKER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return [ApplicationRecord.from_dict(d) for d in data]
    except Exception:
        return []


def save_application(record: ApplicationRecord) -> bool:
    _ensure_dir()
    apps = get_all_applications()
    # Update existing or append new
    updated = False
    for i, app in enumerate(apps):
        if app.job_id == record.job_id:
            apps[i] = record
            updated = True
            break
    if not updated:
        apps.append(record)

    try:
        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in apps], f, indent=2)
        return True
    except Exception:
        return False


def update_application_status(job_id: str, new_status: str) -> bool:
    apps = get_all_applications()
    found = False
    for app in apps:
        if app.job_id == job_id:
            app.status = new_status
            found = True
            break
    if found:
        with open(TRACKER_FILE, "w", encoding="utf-8") as f:
            json.dump([a.to_dict() for a in apps], f, indent=2)
    return found


def delete_application(job_id: str) -> bool:
    apps = get_all_applications()
    filtered = [a for a in apps if a.job_id != job_id]
    with open(TRACKER_FILE, "w", encoding="utf-8") as f:
        json.dump([a.to_dict() for a in filtered], f, indent=2)
    return True


def get_pipeline_stats() -> Dict[str, int]:
    apps = get_all_applications()
    stats = {
        "Shortlisted": 0,
        "Consented": 0,
        "Applied": 0,
        "Interviewing": 0,
        "Offer": 0,
        "Rejected": 0
    }
    for a in apps:
        s = a.status.capitalize()
        if s in stats:
            stats[s] += 1
        elif "interview" in s.lower():
            stats["Interviewing"] += 1
        elif "applied" in s.lower():
            stats["Applied"] += 1
        else:
            stats["Applied"] += 1
    return stats
