"""Unit tests for parsing utilities."""
import pytest
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


@pytest.mark.unit
class TestCourseCodeExtraction:
    """Test course code extraction."""

    def test_valid_course_code(self):
        """Test extracting valid course code."""
        assert extract_course_code("ELE130 - Lecture 1") == "ELE130"
        assert extract_course_code("MAT200 Introduction to Math") == "MAT200"
        assert extract_course_code("FYS101-2024") == "FYS101"

    def test_course_code_must_be_at_start(self):
        """Test that course code must be at the beginning."""
        assert extract_course_code("Introduction to ELE130") == "UNKNOWN"

    def test_missing_course_code(self):
        """Test missing course code returns UNKNOWN."""
        assert extract_course_code("Random Lecture") == "UNKNOWN"
        assert extract_course_code("") == "UNKNOWN"
        assert extract_course_code("123456") == "UNKNOWN"


@pytest.mark.unit
class TestDateParsing:
    """Test date parsing from titles."""

    def test_yyyy_mm_dd_format(self):
        """Test YYYY-MM-DD format."""
        assert parse_date_from_title("ELE130 2026-02-08 Lecture") == "2026-02-08"
        assert parse_date_from_title("Lecture on 2025-12-31") == "2025-12-31"

    def test_dd_mm_yyyy_dot_format(self):
        """Test DD.MM.YYYY format."""
        assert parse_date_from_title("ELE130 08.02.2026") == "2026-02-08"
        assert parse_date_from_title("Lecture 31.12.2025") == "2025-12-31"

    def test_dd_mm_yyyy_slash_format(self):
        """Test DD/MM/YYYY format."""
        assert parse_date_from_title("ELE130 08/02/2026") == "2026-02-08"
        assert parse_date_from_title("Lecture 31/12/2025") == "2025-12-31"

    def test_missing_date(self):
        """Test missing date returns unknown."""
        assert parse_date_from_title("ELE130 Lecture") == "unknown"
        assert parse_date_from_title("Random text") == "unknown"


@pytest.mark.unit
class TestPanoptoId:
    """Test Panopto ID extraction."""

    def test_extract_id_from_query_param(self):
        """Test extracting ID from query parameter."""
        url = "https://panopto.com/Panopto/Pages/Viewer.aspx?id=abc123-def456"
        assert extract_panopto_id(url) == "abc123-def456"

    def test_extract_id_from_path(self):
        """Test extracting UUID from path."""
        url = "https://panopto.com/video/550e8400-e29b-41d4-a716-446655440000/player"
        panopto_id = extract_panopto_id(url)
        assert panopto_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_no_id_found(self):
        """Test when no ID is found."""
        assert extract_panopto_id("https://example.com/video") is None


@pytest.mark.unit
class TestSourceUid:
    """Test source UID generation."""

    def test_use_metadata_id_first(self):
        """Test that metadata ID is used first."""
        url = "https://example.com/video"
        metadata_id = "metadata-123"
        assert generate_source_uid(url, metadata_id) == metadata_id

    def test_extract_from_url(self):
        """Test extracting ID from URL."""
        url = "https://panopto.com/Panopto/Pages/Viewer.aspx?id=abc123-def456"
        assert generate_source_uid(url) == "abc123-def456"

    def test_hash_fallback(self):
        """Test fallback to URL hash."""
        url = "https://example.com/video/random"
        uid = generate_source_uid(url)
        # Should be a hex string (sha1 produces 40 chars)
        assert len(uid) == 40
        assert all(c in '0123456789abcdef' for c in uid)

        # Should be deterministic
        assert generate_source_uid(url) == uid


@pytest.mark.unit
class TestSourceUidShort:
    """Test short UID generation."""

    def test_default_length(self):
        """Test default length of 8 characters."""
        uid = "abcdef1234567890"
        assert generate_source_uid_short(uid) == "abcdef12"

    def test_custom_length(self):
        """Test custom length."""
        uid = "abcdef1234567890"
        assert generate_source_uid_short(uid, 10) == "abcdef1234"


@pytest.mark.unit
class TestLectureId:
    """Test lecture ID generation."""

    def test_lecture_id_format(self):
        """Test lecture ID format."""
        lecture_id = generate_lecture_id("ELE130", "2026-02-08", "abc123de")
        assert lecture_id == "ELE130_2026-02-08_abc123de"


@pytest.mark.unit
class TestLanguageResolution:
    """Test language resolution."""

    def test_default_language_for_known_courses(self):
        """Test default language for known courses."""
        assert get_default_language_for_course("ELE130") == "no"
        assert get_default_language_for_course("MAT200") == "no"

    def test_default_language_for_unknown_course(self):
        """Test default language for unknown course."""
        assert get_default_language_for_course("UNKNOWN") == "auto"
        assert get_default_language_for_course("XYZ999") == "auto"

    def test_respect_explicit_language(self):
        """Test that explicit language choice is respected."""
        assert resolve_language("no", "ELE130") == "no"
        assert resolve_language("en", "MAT200") == "en"

    def test_auto_uses_course_default(self):
        """Test that auto uses course default."""
        assert resolve_language("auto", "ELE130") == "no"
        assert resolve_language("auto", "MAT200") == "no"
        assert resolve_language("auto", "UNKNOWN") == "auto"
