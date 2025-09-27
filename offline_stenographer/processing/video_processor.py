#!/usr/bin/env python3
"""
Video Preprocessing Module

This module handles video file preprocessing including:
- Audio extraction from video files
- Video format validation and conversion
- Audio format optimization for WhisperX
- File integrity checks
"""

import json
import logging
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .config_manager import ConfigurationManager


@dataclass
class VideoInfo:
    """Information about a video file."""

    duration: float
    has_audio: bool
    audio_codec: Optional[str]
    video_codec: Optional[str]
    width: Optional[int]
    height: Optional[int]
    format: str


@dataclass
class PreprocessingResult:
    """Result of video preprocessing."""

    success: bool
    audio_file: Optional[Path]
    original_info: VideoInfo
    processed_info: Optional[VideoInfo] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class VideoProcessor:
    """Handles video file preprocessing for WhisperX."""

    def __init__(self, config_manager: Optional["ConfigurationManager"] = None):
        """Initialize the video processor.

        Args:
            config_manager: ConfigurationManager instance (optional)
        """
        self.logger = logging.getLogger("offline_stenographer.video_processor")
        self.config_manager = config_manager

        # Check if FFmpeg is available
        self.ffmpeg_available = self._check_ffmpeg()
        if not self.ffmpeg_available:
            self.logger.warning(
                "FFmpeg not found. Video preprocessing will be limited."
            )

        # Supported video formats
        self.supported_video_formats = {
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",
            ".wmv",
            ".flv",
            ".webm",
            ".m4v",
            ".3gp",
            ".3g2",
            ".asf",
            ".divx",
            ".f4v",
            ".m2ts",
            ".mts",
            ".ogv",
            ".rm",
            ".rmvb",
            ".vob",
            ".xvid",
        }

        # Audio formats that WhisperX can process directly
        self.supported_audio_formats = {
            ".mp3",
            ".wav",
            ".m4a",
            ".flac",
            ".ogg",
            ".aac",
            ".wma",
        }

        # Temporary directory for audio extraction - automatically cleaned up
        self.temp_dir = None

    def _get_video_config_value(self, key: str, default: str = "") -> str:
        """Get video processing configuration value from ConfigurationManager.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value
        """
        # If no ConfigurationManager provided, return default
        if self.config_manager is None:
            return default

        try:
            config = self.config_manager.load_config()

            # Video processing configuration values
            if key == "AUDIO_SAMPLE_RATE":
                return getattr(config.video_processing, "audio_sample_rate", "16000")
            elif key == "AUDIO_CHANNELS":
                return getattr(config.video_processing, "audio_channels", "1")
            elif key == "AUDIO_CODEC":
                return getattr(config.video_processing, "audio_codec", "pcm_s16le")
            elif key == "AUDIO_FORMAT":
                return getattr(config.video_processing, "audio_format", "wav")
            elif key == "FFMPEG_TIMEOUT":
                return getattr(config.video_processing, "ffmpeg_timeout", "300")

        except Exception as e:
            self.logger.warning(f"Error getting video config value {key}: {e}")

        return default

    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available on the system.

        Returns:
            True if FFmpeg is available
        """
        return (
            shutil.which("ffprobe") is not None and shutil.which("ffmpeg") is not None
        )

    def analyze_video(self, video_path: Path) -> Optional[VideoInfo]:
        """Analyze a video file to extract metadata.

        Args:
            video_path: Path to the video file

        Returns:
            VideoInfo object with metadata or None if analysis fails
        """
        if not video_path.exists():
            self.logger.error(f"Video file not found: {video_path}")
            return None

        if not self.ffmpeg_available:
            self.logger.warning("FFmpeg not available for video analysis")
            return None

        try:
            # Get video information using ffprobe
            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_format",
                "-show_streams",
                str(video_path),
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                self.logger.error(f"FFprobe failed: {result.stderr}")
                return None

            data = json.loads(result.stdout)

            # Extract video stream info
            video_stream = None
            audio_stream = None

            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    video_stream = stream
                elif stream.get("codec_type") == "audio":
                    audio_stream = stream

            # Extract format information
            format_info = data.get("format", {})

            return VideoInfo(
                duration=float(format_info.get("duration", 0)),
                has_audio=audio_stream is not None,
                audio_codec=audio_stream.get("codec_name") if audio_stream else None,
                video_codec=video_stream.get("codec_name") if video_stream else None,
                width=video_stream.get("width") if video_stream else None,
                height=video_stream.get("height") if video_stream else None,
                format=format_info.get("format_name", "unknown"),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing video {video_path}: {e}")
            return None

    def preprocess_video(
        self, input_file: Path, output_dir: Path
    ) -> PreprocessingResult:
        """Preprocess a video file for WhisperX processing.

        Args:
            input_file: Path to input video file
            output_dir: Temporary directory for audio extraction

        Returns:
            PreprocessingResult with processing status and output information
        """
        start_time = time.time()

        try:
            # Analyze input file
            original_info = self.analyze_video(input_file)
            if original_info is None:
                return PreprocessingResult(
                    success=False,
                    audio_file=None,
                    original_info=VideoInfo(
                        0, False, None, None, None, None, "unknown"
                    ),
                    processed_info=None,
                    error_message=f"Failed to analyze video file: {input_file}",
                )

            # Check if file has audio
            if not original_info.has_audio:
                return PreprocessingResult(
                    success=False,
                    audio_file=None,
                    original_info=original_info,
                    processed_info=None,
                    error_message=f"Video file has no audio track: {input_file}",
                )

            # Generate output filename
            base_name = input_file.stem
            audio_filename = f"{base_name}_audio.wav"
            audio_path = output_dir / audio_filename

            # Extract audio to output_dir directory
            success = self._extract_audio(input_file, audio_path, original_info)

            if success:
                # Analyze processed audio
                processed_info = (
                    self.analyze_video(audio_path) if audio_path.exists() else None
                )

                processing_time = time.time() - start_time

                return PreprocessingResult(
                    success=True,
                    audio_file=audio_path,
                    original_info=original_info,
                    processed_info=processed_info,
                    metadata={
                        "processing_time": processing_time,
                        "original_duration": original_info.duration,
                        "extraction_method": "ffmpeg",
                        "output_dir_path": str(output_dir),
                    },
                )
            else:
                return PreprocessingResult(
                    success=False,
                    audio_file=None,
                    original_info=original_info,
                    processed_info=None,
                    error_message="Failed to extract audio from video",
                )

        except Exception as e:
            self.logger.error(f"Error preprocessing video {input_file}: {e}")
            return PreprocessingResult(
                success=False,
                audio_file=None,
                original_info=VideoInfo(0, False, None, None, None, None, "unknown"),
                processed_info=None,
                error_message=str(e),
            )

    def _extract_audio(
        self, video_path: Path, audio_path: Path, video_info: VideoInfo
    ) -> bool:
        """Extract audio from video file.

        Args:
            video_path: Path to input video file
            audio_path: Path where to save extracted audio
            video_info: Video information for optimization

        Returns:
            True if extraction successful
        """
        if not self.ffmpeg_available:
            self.logger.error("FFmpeg not available for audio extraction")
            return False

        try:
            # Get configurable audio extraction parameters
            sample_rate = self._get_video_config_value("AUDIO_SAMPLE_RATE", "16000")
            channels = self._get_video_config_value("AUDIO_CHANNELS", "1")
            codec = self._get_video_config_value("AUDIO_CODEC", "pcm_s16le")
            format_type = self._get_video_config_value("AUDIO_FORMAT", "wav")
            timeout = int(self._get_video_config_value("FFMPEG_TIMEOUT", "300"))

            # Validate parameters
            try:
                sample_rate_int = int(sample_rate)
                channels_int = int(channels)
                timeout_int = int(timeout)

                if sample_rate_int <= 0 or channels_int <= 0 or timeout_int <= 0:
                    raise ValueError("Invalid parameter values")
            except ValueError as e:
                self.logger.error(f"Invalid audio extraction parameters: {e}")
                return False

            # Build FFmpeg command for audio extraction with configurable parameters
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output files
                "-i",
                str(video_path),  # Input file
                "-vn",  # No video
                "-acodec",
                codec,  # Configurable audio codec
                "-ar",
                sample_rate,  # Configurable sample rate
                "-ac",
                channels,  # Configurable channels
                "-f",
                format_type,  # Configurable format
                str(audio_path),
            ]

            self.logger.info(f"Running FFmpeg: {' '.join(cmd)}")

            # Run FFmpeg with configurable timeout
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_int
            )

            if result.returncode == 0:
                # Verify output file was created and has content
                if audio_path.exists() and audio_path.stat().st_size > 0:
                    self.logger.info(
                        f"Audio extracted successfully: {audio_path} ({audio_path.stat().st_size} bytes)"
                    )
                    return True
                else:
                    self.logger.error(f"FFmpeg completed but no output file created")
                    return False
            else:
                self.logger.error(f"FFmpeg failed with code {result.returncode}")
                if result.stderr:
                    self.logger.error(f"FFmpeg stderr: {result.stderr.strip()}")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"Audio extraction timed out after {timeout} seconds")
            return False
        except FileNotFoundError:
            self.logger.error("FFmpeg executable not found")
            return False
        except Exception as e:
            self.logger.error(f"Error during audio extraction: {e}")
            return False

    def validate_video_format(self, video_path: Path) -> Tuple[bool, str]:
        """Validate if video file format is supported.

        Args:
            video_path: Path to video file

        Returns:
            Tuple of (is_supported, reason)
        """
        if not video_path.exists():
            return False, "File does not exist"

        # Check file extension
        file_ext = video_path.suffix.lower()

        if file_ext in self.supported_video_formats:
            return True, "Format supported"
        elif file_ext in self.supported_audio_formats:
            return True, "Audio format supported"
        else:
            return False, f"Unsupported format: {file_ext}"


def create_video_processor() -> VideoProcessor:
    """Factory function to create video processor.

    Returns:
        Configured VideoProcessor instance
    """
    return VideoProcessor()
