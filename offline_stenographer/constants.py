"""
Constants for the Offline Stenographer application.
"""

from typing import Final


# Application constants
class AppConfig:
    """Application configuration constants."""

    WINDOW_TITLE: Final[str] = "Offline Stenographer"
    WINDOW_SIZE: Final[str] = "800x600"
    MIN_WINDOW_SIZE: Final[str] = "600x400"

    # Supported output formats
    OUTPUT_FORMATS: Final[tuple] = ("txt", "md", "docx")

    # Supported video formats
    VIDEO_FILETYPES: Final[tuple] = (
        ("Video files", "*.mp4;*.avi;*.mkv;*.mov;*.wmv;*.flv;*.webm"),
        ("All files", "*.*"),
    )

    # WhisperX model options
    WHISPER_MODELS: Final[tuple] = (
        "tiny",
        "base",
        "small",
        "medium",
        "large-v1",
        "large-v2",
        "large-v3",
    )

    # Language options
    SUPPORTED_LANGUAGES: Final[tuple] = (
        "auto",
        "en",
        "ru",
        "es",
        "fr",
        "de",
        "it",
        "pt",
        "zh",
        "ja",
    )

    # Device options
    DEVICE_OPTIONS: Final[tuple] = ("cuda", "cpu")

    # Batch size options
    BATCH_SIZE_OPTIONS: Final[tuple] = ("4", "8", "16", "32", "64")


# UI Constants
class UIConfig:
    """UI configuration constants."""

    PROGRESS_UPDATE_INTERVAL: Final[float] = 1.0  # seconds
    MAX_RECENT_LOG_MESSAGES: Final[int] = 10
    LOG_TEXT_HEIGHT: Final[int] = 10

    # Default configuration values
    DEFAULT_MODEL: Final[str] = "large-v3"
    DEFAULT_LANGUAGE: Final[str] = "auto"
    DEFAULT_DEVICE: Final[str] = "cuda"
    DEFAULT_BATCH_SIZE: Final[str] = "16"
    DEFAULT_DIARIZATION: Final[bool] = True


# File paths and directories
class FileConfig:
    """File and directory configuration."""

    TRANSCRIPTS_DIR: Final[str] = "transcripts"
    TEMP_DIR_PREFIX: Final[str] = "whisperx_session_"


# URLs
class URLs:
    """External URLs used in the application."""

    HUGGINGFACE_TOKENS: Final[str] = "https://huggingface.co/settings/tokens"
    PYANNOTE_SEGMENTATION: Final[str] = (
        "https://huggingface.co/pyannote/segmentation-3.0"
    )
    PYANNOTE_DIARIZATION: Final[str] = (
        "https://huggingface.co/pyannote/speaker-diarization-3.1"
    )


# Logging configuration
class LoggingConfig:
    """Logging configuration constants."""

    LOGGER_NAME: Final[str] = "offline_stenographer"
    LOG_FORMAT: Final[str] = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    DEFAULT_LEVEL: Final[int] = 20  # INFO level
