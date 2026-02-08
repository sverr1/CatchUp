#!/usr/bin/env python3
"""Test core logic without external dependencies."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.catchup.core.parsing import (
    extract_course_code,
    parse_date_from_title,
    extract_panopto_id,
    generate_source_uid,
    generate_source_uid_short,
    generate_lecture_id,
    get_default_language_for_course,
    resolve_language
)

def test_course_code_extraction():
    """Test course code extraction."""
    print("Testing course code extraction...")
    assert extract_course_code("ELE130 - Lecture 1") == "ELE130"
    assert extract_course_code("MAT200 Introduction") == "MAT200"
    assert extract_course_code("Random text") == "UNKNOWN"
    print("  ✅ Course code extraction")

def test_date_parsing():
    """Test date parsing."""
    print("Testing date parsing...")
    assert parse_date_from_title("ELE130 2026-02-08 Lecture") == "2026-02-08"
    assert parse_date_from_title("Lecture 08.02.2026") == "2026-02-08"
    assert parse_date_from_title("Test 08/02/2026") == "2026-02-08"
    assert parse_date_from_title("No date here") == "unknown"
    print("  ✅ Date parsing")

def test_panopto_id():
    """Test Panopto ID extraction."""
    print("Testing Panopto ID extraction...")
    url1 = "https://panopto.com/Panopto/Pages/Viewer.aspx?id=abc123-def456"
    assert extract_panopto_id(url1) == "abc123-def456"

    url2 = "https://panopto.com/video/550e8400-e29b-41d4-a716-446655440000/player"
    assert extract_panopto_id(url2) == "550e8400-e29b-41d4-a716-446655440000"

    assert extract_panopto_id("https://example.com/video") is None
    print("  ✅ Panopto ID extraction")

def test_source_uid():
    """Test source UID generation."""
    print("Testing source UID generation...")
    # With metadata ID
    assert generate_source_uid("url", "meta-123") == "meta-123"

    # From URL (use same URL as test_panopto_id)
    url = "https://panopto.com/Panopto/Pages/Viewer.aspx?id=abc123-def456"
    assert generate_source_uid(url) == "abc123-def456"

    # Hash fallback
    url2 = "https://example.com/video"
    uid = generate_source_uid(url2)
    assert len(uid) == 40  # SHA1 hex length
    assert uid == generate_source_uid(url2)  # Deterministic
    print("  ✅ Source UID generation")

def test_source_uid_short():
    """Test short UID generation."""
    print("Testing short UID...")
    assert generate_source_uid_short("abcdef1234567890") == "abcdef12"
    assert generate_source_uid_short("abcdef1234567890", 10) == "abcdef1234"
    print("  ✅ Short UID generation")

def test_lecture_id():
    """Test lecture ID generation."""
    print("Testing lecture ID...")
    lecture_id = generate_lecture_id("ELE130", "2026-02-08", "abc123de")
    assert lecture_id == "ELE130_2026-02-08_abc123de"
    print("  ✅ Lecture ID generation")

def test_language_resolution():
    """Test language resolution."""
    print("Testing language resolution...")
    assert get_default_language_for_course("ELE130") == "no"
    assert get_default_language_for_course("MAT200") == "no"
    assert get_default_language_for_course("UNKNOWN") == "auto"

    assert resolve_language("no", "ELE130") == "no"
    assert resolve_language("en", "MAT200") == "en"
    assert resolve_language("auto", "ELE130") == "no"
    assert resolve_language("auto", "UNKNOWN") == "auto"
    print("  ✅ Language resolution")

def main():
    """Run all tests."""
    print("🧪 Running core logic tests...\n")

    tests = [
        test_course_code_extraction,
        test_date_parsing,
        test_panopto_id,
        test_source_uid,
        test_source_uid_short,
        test_lecture_id,
        test_language_resolution
    ]

    failed = []
    for test_func in tests:
        try:
            test_func()
        except AssertionError as e:
            print(f"  ❌ {test_func.__name__}: {e}")
            failed.append(test_func.__name__)
        except Exception as e:
            print(f"  ❌ {test_func.__name__}: Unexpected error: {e}")
            failed.append(test_func.__name__)

    print("\n" + "="*60)
    if failed:
        print(f"❌ {len(failed)} test(s) failed:")
        for name in failed:
            print(f"   - {name}")
        return 1
    else:
        print(f"✅ All {len(tests)} core logic tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())
