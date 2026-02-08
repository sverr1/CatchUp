"""Parsing utilities for CatchUp."""
import re
import hashlib
from typing import Optional
from datetime import datetime


def extract_course_code(title: str) -> str:
    """
    Extract course code from title.
    Course code is ALWAYS the first 6 characters matching ^[A-Z]{3}\\d{3}.
    Returns "UNKNOWN" if not found.
    """
    match = re.search(r'^[A-Z]{3}\d{3}', title)
    if match:
        return match.group(0)
    return "UNKNOWN"


def parse_date_from_title(title: str) -> str:
    """
    Parse date from title. Supports formats:
    - YYYY-MM-DD
    - DD.MM.YYYY
    - DD/MM/YYYY
    - DD.MM (uses current year)

    Returns "unknown" if not found.
    """
    # Try YYYY-MM-DD
    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', title)
    if match:
        return match.group(0)

    # Try DD.MM.YYYY
    match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', title)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"

    # Try DD/MM/YYYY
    match = re.search(r'(\d{2})/(\d{2})/(\d{4})', title)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month}-{day}"

    # Try DD.MM (without year - use current year)
    match = re.search(r'\b(\d{2})\.(\d{2})\b', title)
    if match:
        day, month = match.groups()
        current_year = datetime.now().year
        return f"{current_year}-{month}-{day}"

    return "unknown"


def extract_panopto_id(url: str) -> Optional[str]:
    """
    Extract Panopto ID from URL.
    Panopto URLs typically contain an ID parameter or path segment.
    Example: https://panopto.com/Panopto/Pages/Viewer.aspx?id=abc123-def456
    """
    # Try to extract ID from query parameter
    match = re.search(r'[?&]id=([a-f0-9\-]+)', url, re.IGNORECASE)
    if match:
        return match.group(1)

    # Try to extract ID from path
    match = re.search(r'/([a-f0-9\-]{36})/', url, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def generate_source_uid(url: str, metadata_id: Optional[str] = None) -> str:
    """
    Generate source UID.
    Primary: Use Panopto ID from metadata or URL
    Fallback: Use stable hash of URL (sha1)
    """
    # Try metadata ID first
    if metadata_id:
        return metadata_id

    # Try to extract from URL
    panopto_id = extract_panopto_id(url)
    if panopto_id:
        return panopto_id

    # Fallback: hash the URL
    return hashlib.sha1(url.encode('utf-8')).hexdigest()


def generate_source_uid_short(source_uid: str, length: int = 8) -> str:
    """Generate short version of source UID for directory names."""
    return source_uid[:length]


def generate_lecture_id(course_code: str, lecture_date: str, source_uid_short: str) -> str:
    """Generate canonical lecture ID."""
    return f"{course_code}_{lecture_date}_{source_uid_short}"


def get_default_language_for_course(course_code: str) -> str:
    """
    Get default language for a course.
    ELE130 -> no
    MAT200 -> no
    UNKNOWN -> auto
    """
    course_defaults = {
        "ELE130": "no",
        "MAT200": "no",
    }
    return course_defaults.get(course_code, "auto")


def resolve_language(user_choice: str, course_code: str) -> str:
    """
    Resolve language based on user choice and course default.

    Rules:
    - If user chooses no/en: respect it
    - If user chooses auto: use course default if known, otherwise auto
    """
    if user_choice in ["no", "en"]:
        return user_choice

    if user_choice == "auto":
        return get_default_language_for_course(course_code)

    return "auto"
