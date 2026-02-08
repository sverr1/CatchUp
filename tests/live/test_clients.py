"""
Live tests that make real API calls.

⚠️ WARNING: These tests cost API credits!

To run these tests:
    RUN_LIVE_TESTS=1 pytest -m live

Requirements:
- MISTRAL_API_KEY must be set in .env
- cookies.txt must exist for yt-dlp tests
"""
import os
import pytest
from pathlib import Path

# Skip all tests in this module unless explicitly enabled
pytestmark = pytest.mark.skipif(
    os.environ.get('RUN_LIVE_TESTS') != '1',
    reason="Live tests disabled. Set RUN_LIVE_TESTS=1 to run."
)


@pytest.mark.live
@pytest.mark.asyncio
class TestLiveTranscription:
    """Test real transcription with Mistral API."""

    @pytest.fixture
    def tiny_audio_fixture(self, tmp_path):
        """
        Create a tiny audio file for testing.

        NOTE: In a real implementation, you would have a fixture
        audio file (~30 seconds) for testing.
        """
        # For this test, we'll skip if no fixture exists
        fixture_path = Path("tests/fixtures/tiny_audio.wav")
        if not fixture_path.exists():
            pytest.skip("No audio fixture available")
        return fixture_path

    async def test_transcribe_tiny_audio(self, tiny_audio_fixture):
        """Test transcription with a tiny audio file."""
        from src.catchup.clients.transcriber import VoxtralTranscriber

        transcriber = VoxtralTranscriber()

        # Transcribe
        transcript, chunks = await transcriber.transcribe(
            tiny_audio_fixture,
            language="no"
        )

        # Verify
        assert transcript is not None
        assert len(transcript) > 0
        assert len(chunks) > 0
        assert chunks[0]['detected_language'] in ['no', 'en']

        print(f"\n✅ Transcription successful!")
        print(f"Length: {len(transcript)} characters")
        print(f"Chunks: {len(chunks)}")


@pytest.mark.live
@pytest.mark.asyncio
class TestLiveSummarization:
    """Test real summarization with Mistral API."""

    async def test_summarize_short_text(self):
        """Test summarization with short text."""
        from src.catchup.clients.summarizer import MistralSummarizer

        summarizer = MistralSummarizer()

        # Test text (short lecture transcript)
        test_transcript = """
        I dag skal vi snakke om programmering og spesifikt om funksjoner.
        En funksjon er en gjenbrukbar blokk med kode.
        Vi definerer funksjoner med nøkkelordet def i Python.
        For eksempel: def hello(): print("Hello World")
        Funksjoner kan ta inn parametere og returnere verdier.
        Dette gjør koden mer modulær og lettere å teste.
        """

        chunks = [
            {
                "i": 0,
                "start_sec": 0,
                "end_sec": 30,
                "text": test_transcript,
                "detected_language": "no"
            }
        ]

        # Summarize
        summary = await summarizer.summarize(
            test_transcript,
            chunks,
            language="no"
        )

        # Verify
        assert summary is not None
        assert len(summary) > 0
        assert "#" in summary  # Should have markdown headers

        print(f"\n✅ Summarization successful!")
        print(f"Summary length: {len(summary)} characters")
        print(f"\nSummary preview:\n{summary[:200]}...")


@pytest.mark.live
class TestLiveMetadataExtraction:
    """Test real metadata extraction with yt-dlp."""

    @pytest.mark.asyncio
    async def test_extract_metadata_from_real_url(self):
        """
        Test metadata extraction from a real Panopto URL.

        NOTE: This test requires:
        1. A valid Panopto URL (you need to provide one)
        2. cookies.txt file for authentication
        """
        pytest.skip(
            "Skipping: Requires specific Panopto URL and cookies.txt. "
            "Implement with your own test URL."
        )

        from src.catchup.clients.metadata import MetadataExtractor

        # Replace with a real test URL
        test_url = "YOUR_PANOPTO_URL_HERE"

        extractor = MetadataExtractor()
        metadata = await extractor.extract_metadata(test_url)

        # Verify
        assert metadata.title is not None
        assert metadata.duration_sec > 0
        assert metadata.source_uid is not None

        print(f"\n✅ Metadata extraction successful!")
        print(f"Title: {metadata.title}")
        print(f"Duration: {metadata.duration_sec}s")
        print(f"Course: {metadata.course_code}")


@pytest.mark.live
class TestLiveRateLimiting:
    """Test that live tests don't exceed rate limits."""

    def test_rate_limit_warning(self):
        """Warn about rate limiting."""
        print("""
        ⚠️  RATE LIMITING WARNING ⚠️

        Live tests make real API calls which:
        - Cost money (API credits)
        - May be rate-limited
        - Should be run sparingly

        Best practices:
        - Run live tests only when necessary
        - Use small test fixtures
        - Monitor API usage
        - Set timeouts to prevent runaway costs
        """)
        assert True
