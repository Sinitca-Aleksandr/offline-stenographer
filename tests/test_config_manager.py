"""
Tests for configuration manager functionality.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from offline_stenographer.processing.config_manager import (
    AppConfig,
    ConfigurationManager,
    VideoProcessingConfig,
    WhisperXConfig,
)


class TestConfigurationManager:
    """Test cases for ConfigurationManager."""

    def test_initialization_creates_config_dir(self, temp_dir):
        """Test that ConfigurationManager creates config directory."""
        config_manager = ConfigurationManager(config_dir=temp_dir)
        assert config_manager.config_dir == temp_dir
        assert config_manager.config_file == temp_dir / "config.json"

    def test_default_configuration(self):
        """Test default configuration values."""
        config = ConfigurationManager.get_default_config()

        # Test default WhisperX config
        assert config.whisperx.model == "large-v3"
        assert config.whisperx.language == "auto"
        assert config.whisperx.device == "cuda"
        assert config.whisperx.diarization is True
        assert config.whisperx.batch_size == "16"
        assert config.whisperx.hf_token == ""

        # Test default video processing config
        assert config.video_processing.audio_sample_rate == "16000"
        assert config.video_processing.audio_channels == "1"
        assert config.video_processing.audio_codec == "pcm_s16le"
        assert config.video_processing.audio_format == "wav"
        assert config.video_processing.ffmpeg_timeout == "300"

        # Test default UI preferences
        assert config.ui_preferences["window_size"] == "800x600"
        assert config.ui_preferences["theme"] == "default"

    def test_load_nonexistent_config(self):
        """Test loading configuration when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigurationManager(config_dir=Path(tmpdir))

            config = config_manager.load_config()
            assert isinstance(config, AppConfig)
            assert config.whisperx.model == "large-v3"

    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigurationManager(config_dir=Path(tmpdir))

            # Create custom config
            custom_config = AppConfig(
                whisperx=WhisperXConfig(
                    model="medium", language="en", hf_token="test_token_123"
                ),
                video_processing=VideoProcessingConfig(
                    audio_sample_rate="22050", audio_channels="2"
                ),
                ui_preferences={"theme": "dark"},
            )

            # Save config
            success = config_manager.save_config(custom_config)
            assert success is True

            # Load config
            loaded_config = config_manager.load_config()
            assert loaded_config.whisperx.model == "medium"
            assert loaded_config.whisperx.language == "en"
            assert loaded_config.whisperx.hf_token == "test_token_123"
            assert loaded_config.video_processing.audio_sample_rate == "22050"
            assert loaded_config.video_processing.audio_channels == "2"
            assert loaded_config.ui_preferences["theme"] == "dark"

    def test_update_whisperx_config(self):
        """Test updating WhisperX configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigurationManager(config_dir=Path(tmpdir))

            # Update config
            success = config_manager.update_whisperx_config(
                model="small", language="ru", device="cpu"
            )

            assert success is True

            # Verify changes
            config = config_manager.load_config()
            assert config.whisperx.model == "small"
            assert config.whisperx.language == "ru"
            assert config.whisperx.device == "cpu"

    def test_invalid_model_validation(self):
        """Test validation of invalid model names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigurationManager(config_dir=Path(tmpdir))

            # Try to set invalid model
            success = config_manager.update_whisperx_config(model="invalid_model")
            assert success is False

    def test_invalid_batch_size_validation(self):
        """Test validation of invalid batch size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigurationManager(config_dir=Path(tmpdir))

            # Try to set invalid batch size
            success = config_manager.update_whisperx_config(batch_size="-1")
            assert success is False

    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigurationManager(config_dir=Path(tmpdir))

            # First modify config
            config_manager.update_whisperx_config(model="small", language="en")
            config = config_manager.load_config()
            assert config.whisperx.model == "small"
            assert config.whisperx.language == "en"

        # Reset to defaults
        success = config_manager.reset_to_defaults()
        assert success is True

        # Verify reset
        config = config_manager.load_config()
        assert config.whisperx.model == "large-v3"
        assert config.whisperx.language == "auto"

    def test_config_file_path(self):
        """Test getting config file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_manager = ConfigurationManager(config_dir=Path(tmpdir))

            expected_path = Path(tmpdir) / "config.json"
            assert config_manager.get_config_file_path() == expected_path


class TestWhisperXConfig:
    """Test cases for WhisperXConfig."""

    def test_default_values(self):
        """Test default WhisperX configuration values."""
        config = WhisperXConfig()

        assert config.hf_token == ""
        assert config.model == "large-v3"
        assert config.language == "auto"
        assert config.device == "cuda"
        assert config.diarization is True
        assert config.batch_size == "16"

    def test_custom_values(self):
        """Test custom WhisperX configuration values."""
        config = WhisperXConfig(
            hf_token="test_token_123",
            model="medium",
            language="en",
            device="cpu",
            diarization=False,
            batch_size="8",
        )

        assert config.hf_token == "test_token_123"
        assert config.model == "medium"
        assert config.language == "en"
        assert config.device == "cpu"
        assert config.diarization is False
        assert config.batch_size == "8"


class TestVideoProcessingConfig:
    """Test cases for VideoProcessingConfig."""

    def test_default_values(self):
        """Test default video processing configuration values."""
        config = VideoProcessingConfig()

        assert config.audio_sample_rate == "16000"
        assert config.audio_channels == "1"
        assert config.audio_codec == "pcm_s16le"
        assert config.audio_format == "wav"
        assert config.ffmpeg_timeout == "300"

    def test_custom_values(self):
        """Test custom video processing configuration values."""
        config = VideoProcessingConfig(
            audio_sample_rate="22050",
            audio_channels="2",
            audio_codec="flac",
            audio_format="flac",
            ffmpeg_timeout="600",
        )

        assert config.audio_sample_rate == "22050"
        assert config.audio_channels == "2"
        assert config.audio_codec == "flac"
        assert config.audio_format == "flac"
        assert config.ffmpeg_timeout == "600"


class TestAppConfig:
    """Test cases for AppConfig."""

    def test_default_configuration(self):
        """Test default application configuration."""
        config = AppConfig(
            whisperx=WhisperXConfig(),
            video_processing=VideoProcessingConfig(),
            ui_preferences={"theme": "default"},
        )

        assert isinstance(config.whisperx, WhisperXConfig)
        assert isinstance(config.video_processing, VideoProcessingConfig)
        assert config.ui_preferences == {"theme": "default"}

    def test_custom_configuration(self):
        """Test custom application configuration."""
        custom_whisperx = WhisperXConfig(model="small", language="en")
        custom_video = VideoProcessingConfig(audio_sample_rate="22050")
        custom_ui = {"theme": "dark", "window_size": "1024x768"}

        config = AppConfig(
            whisperx=custom_whisperx,
            video_processing=custom_video,
            ui_preferences=custom_ui,
        )

        assert config.whisperx.model == "small"
        assert config.whisperx.language == "en"
        assert config.video_processing.audio_sample_rate == "22050"
        assert config.ui_preferences["theme"] == "dark"
        assert config.ui_preferences["window_size"] == "1024x768"
