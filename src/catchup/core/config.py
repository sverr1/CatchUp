"""Configuration management for CatchUp."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Keys
    mistral_api_key: str = "your_mistral_api_key_here"  # Set in .env

    # Paths
    data_dir: Path = Path("./data")
    sqlite_path: Path = Path("./catchup.sqlite")
    cookies_path: Path = Path("./cookies.txt")

    # VAD settings
    long_silence_sec: float = 1.6
    keep_silence_sec: float = 0.35
    padding_sec: float = 0.2

    # Transcription chunking
    chunk_minutes: int = 15
    chunk_overlap_sec: int = 6

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    # Client mode
    use_fake_clients: bool = True  # Use fake clients by default for safety

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
