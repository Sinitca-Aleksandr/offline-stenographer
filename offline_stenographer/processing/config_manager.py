#!/usr/bin/env python3
"""
Configuration Manager - Persistent settings management

This module handles saving and loading application configuration
following Context7 best practices for configuration management.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class VideoProcessingConfig:
    """Video processing configuration settings."""

    audio_sample_rate: str = "16000"
    audio_channels: str = "1"
    audio_codec: str = "pcm_s16le"
    audio_format: str = "wav"
    ffmpeg_timeout: str = "300"


@dataclass
class WhisperXConfig:
    """WhisperX configuration settings."""

    hf_token: str = ""
    model: str = "large-v3"
    language: str = "auto"
    device: str = "cuda"
    diarization: bool = True
    batch_size: str = "16"


@dataclass
class AppConfig:
    """Complete application configuration."""

    whisperx: WhisperXConfig
    video_processing: VideoProcessingConfig
    ui_preferences: Dict[str, Any]


class ConfigurationManager:
    """Manages persistent application configuration."""

    @staticmethod
    def get_default_config() -> AppConfig:
        """Get a fresh default configuration.

        Returns:
            New AppConfig instance with default values
        """
        return AppConfig(
            whisperx=WhisperXConfig(),
            video_processing=VideoProcessingConfig(),
            ui_preferences={
                "window_size": "800x600",
                "theme": "default",
            },
        )

    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize configuration manager.

        Args:
            config_dir: Directory for configuration files (optional)
        """
        self.logger = logging.getLogger("offline_stenographer.config")

        # Set up configuration directory
        if config_dir is None:
            self.config_dir = Path.home() / ".offline_stenographer"
        else:
            self.config_dir = config_dir

        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"

        self._config = None

    def _migrate_config_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate configuration data for backward compatibility.

        Args:
            data: Raw configuration data from file

        Returns:
            Migrated configuration data with all required sections
        """
        migrated = data.copy()

        # Ensure video_processing section exists (for backward compatibility)
        if "video_processing" not in migrated:
            migrated["video_processing"] = {}

        # Validate and set defaults for missing video processing fields
        video_processing = migrated["video_processing"]
        defaults = asdict(VideoProcessingConfig())

        for key, default_value in defaults.items():
            if key not in video_processing:
                video_processing[key] = default_value
                self.logger.info(
                    f"Added default video processing config: {key} = {default_value}"
                )

        return migrated

    def _validate_whisperx_config(self, config: WhisperXConfig) -> bool:
        """Validate WhisperX configuration parameters.

        Args:
            config: WhisperXConfig to validate

        Returns:
            True if valid
        """
        # Validate model
        valid_models = {
            "tiny",
            "base",
            "small",
            "medium",
            "large-v1",
            "large-v2",
            "large-v3",
        }
        if config.model not in valid_models:
            self.logger.warning(f"Invalid WhisperX model: {config.model}")
            return False

        # Validate language
        if config.language != "auto" and len(config.language) != 2:
            self.logger.warning(f"Invalid language code: {config.language}")
            return False

        # Validate device
        valid_devices = {"cuda", "cpu"}
        if config.device not in valid_devices:
            self.logger.warning(f"Invalid device: {config.device}")
            return False

        # Validate batch size
        try:
            batch_size = int(config.batch_size)
            if batch_size <= 0:
                self.logger.warning(f"Invalid batch size: {config.batch_size}")
                return False
        except ValueError:
            self.logger.warning(f"Invalid batch size format: {config.batch_size}")
            return False

        return True

    def _validate_video_processing_config(self, config: VideoProcessingConfig) -> bool:
        """Validate video processing configuration parameters.

        Args:
            config: VideoProcessingConfig to validate

        Returns:
            True if valid
        """
        # Validate sample rate
        try:
            sample_rate = int(config.audio_sample_rate)
            if sample_rate <= 0:
                self.logger.warning(f"Invalid sample rate: {config.audio_sample_rate}")
                return False
        except ValueError:
            self.logger.warning(
                f"Invalid sample rate format: {config.audio_sample_rate}"
            )
            return False

        # Validate channels
        try:
            channels = int(config.audio_channels)
            if channels not in {1, 2}:
                self.logger.warning(f"Invalid channels: {config.audio_channels}")
                return False
        except ValueError:
            self.logger.warning(f"Invalid channels format: {config.audio_channels}")
            return False

        # Validate timeout
        try:
            timeout = int(config.ffmpeg_timeout)
            if timeout <= 0:
                self.logger.warning(f"Invalid timeout: {config.ffmpeg_timeout}")
                return False
        except ValueError:
            self.logger.warning(f"Invalid timeout format: {config.ffmpeg_timeout}")
            return False

        return True

    def load_config(self) -> AppConfig:
        """Load configuration from file.

        Returns:
            AppConfig with loaded settings
        """
        if self._config is not None:
            return self._config

        try:
            if self.config_file.exists():
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Load and migrate configuration with backward compatibility
                config_data = self._migrate_config_data(data)

                # Load WhisperX settings
                whisperx_data = config_data.get("whisperx", {})
                whisperx_config = WhisperXConfig(**whisperx_data)

                # Load video processing settings
                video_processing_data = config_data.get("video_processing", {})
                video_processing_config = VideoProcessingConfig(**video_processing_data)

                # Load UI preferences
                ui_preferences = config_data.get("ui_preferences", {})

                self._config = AppConfig(
                    whisperx=whisperx_config,
                    video_processing=video_processing_config,
                    ui_preferences=ui_preferences,
                )

                self.logger.info(f"Configuration loaded from {self.config_file}")
            else:
                self._config = self.get_default_config()
                self.logger.info("Using default configuration")

        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            self._config = self.get_default_config()

        return self._config

    def save_config(self, config: AppConfig) -> bool:
        """Save configuration to file.

        Args:
            config: Configuration to save

        Returns:
            True if successful
        """
        try:
            # Validate configuration before saving
            if not self._validate_whisperx_config(config.whisperx):
                self.logger.error("Invalid WhisperX configuration, not saving")
                return False

            if not self._validate_video_processing_config(config.video_processing):
                self.logger.error("Invalid video processing configuration, not saving")
                return False

            # Ensure config directory exists
            self.config_dir.mkdir(exist_ok=True)

            # Convert to dictionary
            data = {
                "whisperx": asdict(config.whisperx),
                "video_processing": asdict(config.video_processing),
                "ui_preferences": config.ui_preferences,
            }

            # Save with proper formatting and atomic write
            temp_file = self.config_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic move
            temp_file.replace(self.config_file)

            self._config = config
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False

    def get_whisperx_config(self) -> WhisperXConfig:
        """Get WhisperX configuration.

        Returns:
            WhisperXConfig with current settings
        """
        config = self.load_config()
        return config.whisperx

    def update_whisperx_config(self, **kwargs) -> bool:
        """Update WhisperX configuration.

        Args:
            **kwargs: Configuration parameters to update

        Returns:
            True if successful
        """
        config = self.load_config()
        for key, value in kwargs.items():
            if hasattr(config.whisperx, key):
                setattr(config.whisperx, key, value)
            else:
                self.logger.warning(f"Unknown WhisperX config parameter: {key}")

        return self.save_config(config)

    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults.

        Returns:
            True if successful
        """
        default_config = self.get_default_config()
        return self.save_config(default_config)

    def get_config_file_path(self) -> Path:
        """Get path to configuration file.

        Returns:
            Path to config file
        """
        return self.config_file


def create_config_manager(config_dir: Optional[Path] = None) -> ConfigurationManager:
    """Factory function to create configuration manager.

    Args:
        config_dir: Directory for configuration files (optional)

    Returns:
        Configured ConfigurationManager instance
    """
    return ConfigurationManager(config_dir)


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> ConfigurationManager:
    """Get global configuration manager instance.

    Returns:
        Global ConfigurationManager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    return _config_manager


def load_whisperx_config() -> Dict[str, Any]:
    """Load WhisperX configuration settings.

    Returns:
        Dictionary with WhisperX configuration
    """
    manager = get_config_manager()
    config = manager.get_whisperx_config()
    return asdict(config)


def save_whisperx_config(**kwargs) -> bool:
    """Save WhisperX configuration settings.

    Args:
        **kwargs: Configuration parameters to update

    Returns:
        True if successful
    """
    manager = get_config_manager()
    return manager.update_whisperx_config(**kwargs)


# Test function for development
def test_config_management():
    """Test configuration management functionality."""
    manager = ConfigurationManager()

    # Test loading
    config = manager.load_config()
    print(f"Loaded config: {config}")

    # Test updating
    success = manager.update_whisperx_config(
        model="medium", language="en", hf_token="test_token_123"
    )

    if success:
        print("✅ Configuration updated successfully")
    else:
        print("❌ Failed to update configuration")

    # Test loading updated config
    updated_config = manager.load_config()
    print(f"Updated config: {updated_config}")


if __name__ == "__main__":
    test_config_management()
