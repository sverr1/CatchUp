"""Factory for creating pipeline with real or fake clients."""
from .runner import PipelineRunner
from .interfaces import (
    Downloader,
    MediaConverter,
    VadProcessor,
    TranscriberClient,
    SummarizerClient
)


def create_pipeline(use_fake_clients: bool = None) -> PipelineRunner:
    """
    Create pipeline with real or fake clients.

    Args:
        use_fake_clients: If True, use fake clients. If False, use real clients.
                         If None, auto-detect from settings.

    Returns:
        PipelineRunner instance
    """
    if use_fake_clients is None:
        # Auto-detect from settings (which loads from .env)
        from ..core.config import settings
        use_fake_clients = settings.use_fake_clients

    if use_fake_clients:
        return _create_fake_pipeline()
    else:
        return _create_real_pipeline()


def _create_fake_pipeline() -> PipelineRunner:
    """Create pipeline with fake clients (for testing/development)."""
    from .fake_clients import (
        FakeDownloader,
        FakeMediaConverter,
        FakeVadProcessor,
        FakeTranscriberClient,
        FakeSummarizerClient
    )

    return PipelineRunner(
        downloader=FakeDownloader(),
        converter=FakeMediaConverter(),
        vad_processor=FakeVadProcessor(),
        transcriber=FakeTranscriberClient(),
        summarizer=FakeSummarizerClient()
    )


def _create_real_pipeline() -> PipelineRunner:
    """Create pipeline with real clients (production)."""
    from ..clients.downloader import YtdlpDownloader
    from ..clients.converter import FFmpegConverter
    from ..clients.vad import SileroVadProcessor
    from ..clients.transcriber import VoxtralTranscriber
    from ..clients.summarizer import MistralSummarizer

    return PipelineRunner(
        downloader=YtdlpDownloader(),
        converter=FFmpegConverter(),
        vad_processor=SileroVadProcessor(),
        transcriber=VoxtralTranscriber(),
        summarizer=MistralSummarizer()
    )
