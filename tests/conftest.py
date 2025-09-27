"""
Test configuration and fixtures for offline-stenographer tests.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client for testing."""
    mock_client = MagicMock()
    mock_container = MagicMock()

    # Configure container mock
    mock_container.id = "test_container_123"
    mock_container.wait.return_value = {"StatusCode": 0}
    mock_container.logs.return_value = b"Mock transcription completed"
    mock_container.attrs = {
        "Mounts": [{"Destination": "/results", "Source": "/tmp/test_output"}]
    }

    # Configure client mock
    mock_client.ping.return_value = True
    mock_client.containers.create.return_value = mock_container
    mock_client.containers.run.return_value = b"test_output"
    mock_client.images.get.return_value = MagicMock()
    mock_client.images.pull.return_value = [MagicMock()]

    return mock_client


@pytest.fixture
def mock_ffmpeg_process():
    """Create a mock FFmpeg subprocess for testing."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "Mock FFmpeg output"
    mock_process.stderr = ""
    mock_process.communicate.return_value = (b"output", b"")

    return mock_process


@pytest.fixture
def sample_video_file(temp_dir):
    """Create a sample video file path for testing."""
    video_file = temp_dir / "sample_video.mp4"
    video_file.touch()
    return video_file


@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a sample audio file path for testing."""
    audio_file = temp_dir / "sample_audio.wav"
    audio_file.touch()
    return audio_file


@pytest.fixture
def mock_config_manager():
    """Create a mock configuration manager for testing."""
    mock_manager = MagicMock()

    # Mock configuration data
    mock_config = MagicMock()
    mock_config.whisperx.hf_token = "test_token"
    mock_config.whisperx.model = "large-v3"
    mock_config.whisperx.language = "auto"
    mock_config.whisperx.device = "cuda"
    mock_config.whisperx.diarization = True
    mock_config.whisperx.batch_size = "16"

    mock_config.video_processing.audio_sample_rate = "16000"
    mock_config.video_processing.audio_channels = "1"
    mock_config.video_processing.audio_codec = "pcm_s16le"
    mock_config.video_processing.audio_format = "wav"
    mock_config.video_processing.ffmpeg_timeout = "300"

    mock_manager.load_config.return_value = mock_config
    mock_manager.save_config.return_value = True
    mock_manager.get_whisperx_config.return_value = mock_config.whisperx

    return mock_manager


@pytest.fixture
def sample_transcription_segments():
    """Create sample transcription segments for testing."""
    from offline_stenographer.processing.formatters import TranscriptionSegment

    return [
        TranscriptionSegment(
            start_time=0.0,
            end_time=5.2,
            text="Hello, welcome to this video.",
            speaker="Speaker 1",
        ),
        TranscriptionSegment(
            start_time=5.2,
            end_time=8.7,
            text="Thank you for having me.",
            speaker="Speaker 2",
        ),
        TranscriptionSegment(
            start_time=8.7,
            end_time=15.3,
            text="Today we're going to discuss the importance of video transcription.",
            speaker="Speaker 1",
        ),
    ]


@pytest.fixture
def sample_transcription_result(sample_transcription_segments):
    """Create a sample transcription result for testing."""
    from offline_stenographer.processing.formatters import TranscriptionResult

    return TranscriptionResult(
        segments=sample_transcription_segments,
        language="en",
        processing_time=15.3,
        metadata={
            "source_file": "sample_video.mp4",
            "whisper_model": "large-v3",
            "device": "cuda",
            "diarization": "enabled",
            "total_segments": len(sample_transcription_segments),
        },
    )


@pytest.fixture(autouse=True)
def mock_subprocess_run(mock_ffmpeg_process):
    """Automatically mock subprocess.run for all tests."""
    import subprocess

    original_run = subprocess.run
    subprocess.run = Mock(return_value=mock_ffmpeg_process)
    yield
    subprocess.run = original_run


@pytest.fixture(autouse=True)
def mock_shutil_which():
    """Automatically mock shutil.which for all tests."""
    import shutil

    original_which = shutil.which
    shutil.which = Mock(return_value="/usr/bin/ffmpeg")
    yield
    shutil.which = original_which


@pytest.fixture
def mock_file_operations():
    """Mock file system operations for testing."""
    import builtins

    original_open = builtins.open
    original_path_exists = Path.exists

    mock_files = {}

    def mock_open_func(path, mode="r", *args, **kwargs):
        path_str = str(path)
        if "w" in mode and path_str not in mock_files:
            mock_files[path_str] = ""
        return MagicMock()

    def mock_exists(self):
        return str(self) in mock_files

    builtins.open = mock_open_func
    Path.exists = mock_exists

    yield mock_files

    builtins.open = original_open
    Path.exists = original_path_exists
