"""
Tests for video processor functionality with mocked dependencies.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from offline_stenographer.processing.video_processor import (
    PreprocessingResult,
    VideoInfo,
    VideoProcessor,
)


class TestVideoInfo:
    """Test cases for VideoInfo."""

    def test_video_info_creation(self):
        """Test creating VideoInfo object."""
        info = VideoInfo(
            duration=120.5,
            has_audio=True,
            audio_codec="aac",
            video_codec="h264",
            width=1920,
            height=1080,
            format="mp4",
        )

        assert info.duration == 120.5
        assert info.has_audio is True
        assert info.audio_codec == "aac"
        assert info.video_codec == "h264"
        assert info.width == 1920
        assert info.height == 1080
        assert info.format == "mp4"

    def test_video_info_without_optional_fields(self):
        """Test VideoInfo with missing optional fields."""
        info = VideoInfo(
            duration=60.0,
            has_audio=False,
            audio_codec=None,
            video_codec=None,
            width=None,
            height=None,
            format="avi",
        )

        assert info.duration == 60.0
        assert info.has_audio is False
        assert info.audio_codec is None
        assert info.video_codec is None
        assert info.width is None
        assert info.height is None
        assert info.format == "avi"


class TestVideoProcessor:
    """Test cases for VideoProcessor."""

    def test_initialization(self, mock_config_manager):
        """Test VideoProcessor initialization."""
        processor = VideoProcessor(mock_config_manager)

        assert processor.config_manager == mock_config_manager
        assert processor.ffmpeg_available is True  # Mocked by conftest
        assert isinstance(processor.supported_video_formats, set)
        assert isinstance(processor.supported_audio_formats, set)

    def test_initialization_without_config_manager(self):
        """Test VideoProcessor initialization without config manager."""
        processor = VideoProcessor()

        assert processor.config_manager is None
        assert processor.ffmpeg_available is True  # Mocked by conftest

    def test_get_video_config_value_with_config_manager(self, mock_config_manager):
        """Test getting config values when config manager is available."""
        processor = VideoProcessor(mock_config_manager)

        # Mock the config manager response
        mock_config_manager.load_config.return_value.video_processing.audio_sample_rate = (
            "22050"
        )

        value = processor._get_video_config_value("AUDIO_SAMPLE_RATE", "16000")
        assert value == "22050"

    def test_get_video_config_value_without_config_manager(self):
        """Test getting config values when config manager is not available."""
        processor = VideoProcessor()

        value = processor._get_video_config_value("AUDIO_SAMPLE_RATE", "16000")
        assert value == "16000"  # Returns default

    def test_validate_video_format_supported(self, sample_video_file):
        """Test validation of supported video format."""
        processor = VideoProcessor()

        is_valid, reason = processor.validate_video_format(sample_video_file)

        assert is_valid is True
        assert "supported" in reason.lower()

    def test_validate_video_format_unsupported(self, temp_dir):
        """Test validation of unsupported video format."""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.touch()

        processor = VideoProcessor()

        is_valid, reason = processor.validate_video_format(unsupported_file)

        assert is_valid is False
        assert "unsupported" in reason.lower()

    def test_validate_video_format_nonexistent(self):
        """Test validation of nonexistent file."""
        processor = VideoProcessor()
        nonexistent_file = Path("nonexistent_file.mp4")

        is_valid, reason = processor.validate_video_format(nonexistent_file)

        assert is_valid is False
        assert "does not exist" in reason.lower()

    def test_analyze_video_with_mock_ffmpeg(
        self, sample_video_file, mock_ffmpeg_process
    ):
        """Test video analysis with mocked FFmpeg."""
        processor = VideoProcessor()

        with patch("subprocess.run", return_value=mock_ffmpeg_process):
            # Mock the JSON response from ffprobe
            mock_ffmpeg_process.stdout = """{
                "format": {
                    "duration": "120.5",
                    "format_name": "mp4"
                },
                "streams": [
                    {
                        "codec_type": "video",
                        "codec_name": "h264",
                        "width": 1920,
                        "height": 1080
                    },
                    {
                        "codec_type": "audio",
                        "codec_name": "aac"
                    }
                ]
            }"""

            video_info = processor.analyze_video(sample_video_file)

            assert video_info is not None
            assert video_info.duration == 120.5
            assert video_info.has_audio is True
            assert video_info.audio_codec == "aac"
            assert video_info.video_codec == "h264"
            assert video_info.width == 1920
            assert video_info.height == 1080
            assert video_info.format == "mp4"

    def test_analyze_video_ffmpeg_not_available(self, sample_video_file):
        """Test video analysis when FFmpeg is not available."""
        processor = VideoProcessor()

        # Mock FFmpeg not being available
        with patch.object(processor, "ffmpeg_available", False):
            video_info = processor.analyze_video(sample_video_file)

            assert video_info is None

    def test_analyze_video_nonexistent_file(self):
        """Test video analysis with nonexistent file."""
        processor = VideoProcessor()
        nonexistent_file = Path("nonexistent.mp4")

        video_info = processor.analyze_video(nonexistent_file)

        assert video_info is None

    def test_preprocess_video_success(
        self, sample_video_file, temp_dir, mock_ffmpeg_process
    ):
        """Test successful video preprocessing."""
        processor = VideoProcessor()

        # Mock both analyze_video and _extract_audio methods
        with (
            patch.object(processor, "analyze_video") as mock_analyze,
            patch.object(
                processor, "_extract_audio", return_value=True
            ) as mock_extract,
        ):

            # Mock successful video analysis
            mock_analyze.return_value = VideoInfo(
                duration=120.5,
                has_audio=True,
                audio_codec="aac",
                video_codec="h264",
                width=1920,
                height=1080,
                format="mp4",
            )

            # Create the expected output file
            expected_audio_file = temp_dir / "sample_video_audio.wav"
            expected_audio_file.touch()

            result = processor.preprocess_video(sample_video_file, temp_dir)

            assert result.success is True
            assert result.audio_file is not None
            assert result.original_info is not None
            assert result.error_message is None

    def test_preprocess_video_no_audio(self, temp_dir):
        """Test preprocessing video without audio track."""
        processor = VideoProcessor()
        video_file = temp_dir / "no_audio.mp4"
        video_file.touch()

        with patch.object(processor, "analyze_video") as mock_analyze:
            # Mock video analysis showing no audio
            mock_analyze.return_value = VideoInfo(
                duration=60.0,
                has_audio=False,
                audio_codec=None,
                video_codec="h264",
                width=1920,
                height=1080,
                format="mp4",
            )

            result = processor.preprocess_video(video_file, temp_dir)

            assert result.success is False
            assert result.audio_file is None
            assert "no audio track" in result.error_message.lower()

    def test_preprocess_video_analysis_fails(self, sample_video_file, temp_dir):
        """Test preprocessing when video analysis fails."""
        processor = VideoProcessor()

        with patch.object(processor, "analyze_video", return_value=None):
            result = processor.preprocess_video(sample_video_file, temp_dir)

            assert result.success is False
            assert result.audio_file is None
            assert "failed to analyze" in result.error_message.lower()

    def test_extract_audio_ffmpeg_not_available(self, sample_video_file, temp_dir):
        """Test audio extraction when FFmpeg is not available."""
        processor = VideoProcessor()

        # Mock FFmpeg not being available
        with patch.object(processor, "ffmpeg_available", False):
            video_info = VideoInfo(
                duration=60.0,
                has_audio=True,
                audio_codec="aac",
                video_codec="h264",
                width=1920,
                height=1080,
                format="mp4",
            )

            success = processor._extract_audio(
                sample_video_file, temp_dir / "output.wav", video_info
            )

            assert success is False

    def test_extract_audio_success(
        self, sample_video_file, temp_dir, mock_ffmpeg_process
    ):
        """Test successful audio extraction."""
        processor = VideoProcessor()

        # Mock the entire _extract_audio method to return True
        with patch.object(processor, "_extract_audio", return_value=True):
            video_info = VideoInfo(
                duration=60.0,
                has_audio=True,
                audio_codec="aac",
                video_codec="h264",
                width=1920,
                height=1080,
                format="mp4",
            )

            audio_file = temp_dir / "output.wav"
            success = processor._extract_audio(
                sample_video_file, audio_file, video_info
            )

            assert success is True

    def test_extract_audio_ffmpeg_failure(self, sample_video_file, temp_dir):
        """Test audio extraction when FFmpeg fails."""
        processor = VideoProcessor()

        # Mock failed FFmpeg execution
        with patch("subprocess.run") as mock_run:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.stderr = "FFmpeg error: invalid codec"
            mock_run.return_value = mock_process

            video_info = VideoInfo(
                duration=60.0,
                has_audio=True,
                audio_codec="aac",
                video_codec="h264",
                width=1920,
                height=1080,
                format="mp4",
            )

            audio_file = temp_dir / "output.wav"
            success = processor._extract_audio(
                sample_video_file, audio_file, video_info
            )

            assert success is False


class TestPreprocessingResult:
    """Test cases for PreprocessingResult."""

    def test_successful_result(self):
        """Test successful preprocessing result."""
        audio_file = Path("output.wav")
        original_info = VideoInfo(
            duration=60.0,
            has_audio=True,
            audio_codec="aac",
            video_codec="h264",
            width=1920,
            height=1080,
            format="mp4",
        )

        result = PreprocessingResult(
            success=True,
            audio_file=audio_file,
            original_info=original_info,
            processed_info=original_info,
            error_message=None,
            metadata={"processing_time": 5.2},
        )

        assert result.success is True
        assert result.audio_file == audio_file
        assert result.original_info == original_info
        assert result.processed_info == original_info
        assert result.error_message is None
        assert result.metadata["processing_time"] == 5.2

    def test_failed_result(self):
        """Test failed preprocessing result."""
        original_info = VideoInfo(
            duration=0.0,
            has_audio=False,
            audio_codec=None,
            video_codec=None,
            width=None,
            height=None,
            format="unknown",
        )

        result = PreprocessingResult(
            success=False,
            audio_file=None,
            original_info=original_info,
            error_message="Audio extraction failed",
        )

        assert result.success is False
        assert result.audio_file is None
        assert result.original_info == original_info
        assert result.processed_info is None
        assert result.error_message == "Audio extraction failed"
        assert result.metadata is None
