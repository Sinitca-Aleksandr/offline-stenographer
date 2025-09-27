"""
Type hints for the Offline Stenographer application.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Protocol, Union


# Protocol definitions
class TranscriptionServiceProtocol(Protocol):
    """Protocol for transcription service objects."""

    def check_requirements(self) -> tuple[bool, str]:
        """Check if service requirements are met."""
        ...

    def transcribe_file(self, input_file: Path, output_dir: Path) -> Any:
        """Transcribe audio file to output directory."""
        ...

    def get_progress(self) -> Dict[str, Any]:
        """Get current progress information."""
        ...

    def cancel_transcription(self) -> None:
        """Cancel current transcription."""
        ...


class VideoProcessorProtocol(Protocol):
    """Protocol for video processor objects."""

    def validate_video_format(self, video_path: Path) -> tuple[bool, str]:
        """Validate video file format."""
        ...

    def preprocess_video(self, video_path: Path, output_dir: Path) -> Any:
        """Preprocess video file."""
        ...


class ConfigurationManagerProtocol(Protocol):
    """Protocol for configuration manager objects."""

    def load_config(self) -> Any:
        """Load configuration from storage."""
        ...

    def save_config(self, config: Any) -> bool:
        """Save configuration to storage."""
        ...


# Type aliases
ProgressInfo = Dict[str, Any]
TranscriptionResult = Any
TranscriptionSegment = Any
PreprocessingResult = Any
WhisperXConfig = Any

# Callback function types
CallbackDict = Dict[str, Callable]
LogCallback = Callable[[str], None]
ProgressCallback = Callable[[ProgressInfo], None]
StatusCallback = Callable[[str], None]

# UI component types
TkWidget = Union[tk.Widget, ttk.Widget]
FrameType = Union[tk.Frame, ttk.Frame, ttk.LabelFrame]
