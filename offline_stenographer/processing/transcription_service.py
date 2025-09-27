#!/usr/bin/env python3
"""
Transcription Service - Docker SDK Integration for WhisperX

This module provides a clean interface to WhisperX using the Docker SDK
instead of subprocess for better error handling and resource management.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

import docker

if TYPE_CHECKING:
    from .config_manager import ConfigurationManager


class TranscriptionStatus(Enum):
    """Status of transcription process."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TranscriptionResult:
    """Result of transcription process."""

    status: TranscriptionStatus
    output_files: list[Path]
    processing_time: float
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class WhisperXService:
    """Service class for WhisperX Docker integration using Docker SDK."""

    def __init__(self, config_manager: "ConfigurationManager" = None):
        """Initialize the WhisperX service.

        Args:
            config_manager: ConfigurationManager instance (optional)
        """
        self.logger = logging.getLogger("offline_stenographer.transcription")

        # Initialize ConfigurationManager if not provided
        if config_manager is None:
            from .config_manager import get_config_manager

            config_manager = get_config_manager()

        self.config_manager = config_manager
        self.docker_client = docker.from_env()
        self.current_container = None

        # Configuration
        self.image_name = "ghcr.io/jim60105/whisperx:latest"
        self.cache_dir = Path.home() / "whisperx"
        self.cache_dir.mkdir(exist_ok=True)

        self.logger.info("WhisperX service initialized")

    def _get_config_value(self, key: str, default: str = "") -> str:
        """Get configuration value from ConfigurationManager.

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
            if key == "HF_TOKEN":
                return config.whisperx.hf_token
            elif key == "WHISPER_MODEL":
                return config.whisperx.model
            elif key == "LANGUAGE":
                return config.whisperx.language
            elif key == "BATCH_SIZE":
                return config.whisperx.batch_size
            elif key == "DEVICE":
                return config.whisperx.device
            elif key == "ENABLE_DIARIZATION":
                return "true" if config.whisperx.diarization else "false"
            elif key == "MIN_SPEAKERS":
                return getattr(config.whisperx, "min_speakers", "")
            elif key == "MAX_SPEAKERS":
                return getattr(config.whisperx, "max_speakers", "")
            elif key == "COMPUTE_TYPE":
                return getattr(config.whisperx, "compute_type", "float16")
            elif key == "VAD_METHOD":
                return getattr(config.whisperx, "vad_method", "pyannote")
            elif key == "CHUNK_SIZE":
                return getattr(config.whisperx, "chunk_size", "30")
        except Exception as e:
            self.logger.warning(f"Error getting config value {key}: {e}")

        return default

    def _load_config(self, config_path: str) -> Dict[str, str]:
        """Load configuration from file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dictionary with configuration values
        """
        config = {
            "HF_TOKEN": "",
            "WHISPER_MODEL": "large-v3",
            "LANGUAGE": "auto",
            "BATCH_SIZE": "16",
            "DEVICE": "cuda",
            "ENABLE_DIARIZATION": "true",
            "MIN_SPEAKERS": "",
            "MAX_SPEAKERS": "",
            "COMPUTE_TYPE": "float16",
            "VAD_METHOD": "pyannote",
            "CHUNK_SIZE": "30",
        }

        config_file = Path(config_path)
        if config_file.exists():
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            config[key.strip()] = value.strip().strip("\"'")
            except Exception as e:
                self.logger.warning(f"Error loading config: {e}")

        return config

    def check_requirements(self) -> Tuple[bool, str]:
        """Check if all requirements for transcription are met.

        Returns:
            Tuple of (is_ready, error_message)
        """
        try:
            # Check Docker availability
            self.docker_client.ping()
        except Exception as e:
            return (
                False,
                f"Docker not available: {e}. Please ensure Docker is installed and running.",
            )

        # Check if WhisperX image is available, pull if necessary
        try:
            self.docker_client.images.get(self.image_name)
            self.logger.info(f"WhisperX image found: {self.image_name}")
        except docker.errors.ImageNotFound:
            self.logger.info(f"WhisperX image not found, pulling: {self.image_name}")
            try:
                self.logger.info(
                    "Pulling WhisperX image (this may take several minutes)..."
                )
                self.docker_client.images.pull(self.image_name)
                self.logger.info("WhisperX image pulled successfully")
            except Exception as e:
                return (
                    False,
                    f"Failed to pull WhisperX image: {e}. Please check your internet connection and try again.",
                )
        except Exception as e:
            return False, f"Error checking WhisperX image: {e}"

        # Check GPU availability if CUDA is requested
        device = self._get_config_value("DEVICE", "cuda")
        if device == "cuda":
            gpu_available = self._check_gpu_availability()
            if not gpu_available:
                self.logger.warning("GPU not available, will fall back to CPU mode")
            else:
                self.logger.info("GPU acceleration available")

        # Check HuggingFace token for diarization
        hf_token = self._get_config_value("HF_TOKEN", "").strip()
        enable_diarization = (
            self._get_config_value("ENABLE_DIARIZATION", "true").lower() == "true"
        )
        if enable_diarization:
            if not hf_token:
                return (
                    False,
                    "HF_TOKEN required for diarization. Please configure HF_TOKEN in settings.",
                )
            elif hf_token == "your_token_here":
                return (
                    False,
                    "HF_TOKEN placeholder found. Please replace 'your_token_here' with your actual HuggingFace token in settings.",
                )
            else:
                self.logger.info("HuggingFace token configured for diarization")

        # Check cache directory permissions
        try:
            test_file = self.cache_dir / "test_write.tmp"
            test_file.touch()
            test_file.unlink()
        except Exception as e:
            return False, f"Cannot write to cache directory {self.cache_dir}: {e}"

        return True, "Ready"

    def _check_gpu_availability(self) -> bool:
        """Check if GPU is available through Docker.

        Returns:
            True if GPU is available
        """
        try:
            container = self.docker_client.containers.run(
                "nvidia/cuda:12.4.1-base-ubuntu22.04",
                "nvidia-smi --query-gpu=name --format=csv,noheader",
                auto_remove=True,
                device_requests=[
                    docker.types.DeviceRequest(device_ids=["0"], capabilities=[["gpu"]])
                ],
            )
            return bool(container.decode().strip())
        except Exception:
            return False

    def transcribe_file(
        self, input_file: Path, output_dir: Path
    ) -> TranscriptionResult:
        """Transcribe a video/audio file using WhisperX.

        Args:
            input_file: Path to input video/audio file
            output_dir: Directory for output files (optional)

        Returns:
            TranscriptionResult with status and output information
        """
        start_time = time.time()

        try:
            # Validate input file
            if not input_file.exists():
                return TranscriptionResult(
                    status=TranscriptionStatus.FAILED,
                    output_files=[],
                    processing_time=time.time() - start_time,
                    error_message=f"Input file not found: {input_file}",
                )

            output_dir.mkdir(parents=True, exist_ok=True)

            self.logger.info(f"Starting transcription: {input_file} -> {output_dir}")

            # Prepare Docker container
            container = self._create_transcription_container(input_file, output_dir)

            # Start container and monitor progress
            container.start()
            self.current_container = container

            # Monitor progress
            result = self._monitor_transcription(container, start_time, output_dir)

            return result

        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            return TranscriptionResult(
                status=TranscriptionStatus.FAILED,
                output_files=[],
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    def _create_transcription_container(self, input_file: Path, output_dir: Path):
        """Create Docker container for transcription using Docker SDK best practices.

        Args:
            input_file: Input file path
            output_dir: Output directory path

        Returns:
            Configured Docker container
        """
        try:
            # Prepare volumes using proper Docker SDK format
            # Mount the directory containing the audio file to /audio
            volumes = {
                str(input_file.parent): {"bind": "/audio", "mode": "ro"},
                str(output_dir): {"bind": "/results", "mode": "rw"},
                str(self.cache_dir): {"bind": "/models", "mode": "rw"},
            }

            # Prepare environment variables
            environment = {
                "HOME": "/models",
                "HF_HOME": "/models/.cache/huggingface",
                "XDG_CACHE_HOME": "/models/.cache",
                "TORCH_HOME": "/models/.cache/torch",
                # Disable buffering for real-time log output
                "PYTHONUNBUFFERED": "1",
                "PYTHONIOENCODING": "utf-8",
            }

            # Add HuggingFace token if available
            hf_token = self._get_config_value("HF_TOKEN", "").strip()
            if hf_token and hf_token != "your_token_here":
                environment["HF_TOKEN"] = hf_token

            # Prepare device requests for GPU using Docker SDK best practices
            device_requests = []
            device = self._get_config_value("DEVICE", "cuda")
            if device == "cuda":
                try:
                    device_requests.append(
                        docker.types.DeviceRequest(
                            device_ids=["0"], capabilities=[["gpu"]]
                        )
                    )
                    self.logger.info("GPU acceleration enabled")
                except Exception as e:
                    self.logger.warning(f"GPU request failed, falling back to CPU: {e}")
                    device = "cpu"  # Fall back to CPU

            # Build WhisperX command with the actual device that will be used
            command = self._build_whisperx_command(input_file, device)

            # Create container with proper resource management
            container = self.docker_client.containers.create(
                image=self.image_name,
                command=command,
                volumes=volumes,
                environment=environment,
                device_requests=device_requests if device_requests else None,
                working_dir="/app",
                detach=True,
                auto_remove=True,  # Auto-cleanup after completion
                # Unique name
                name=f"whisperx-transcription-{int(time.time())}",
                labels={
                    "app": "offline-stenographer",
                    "type": "transcription",
                    "created_by": "whisperx-service",
                },
            )

            self.logger.info(f"Created container: {container.id[:12]}")
            return container

        except Exception as e:
            self.logger.error(f"Failed to create container: {e}")
            raise

    def _build_whisperx_command(self, input_file: Path, device: str = None) -> list:
        """Build WhisperX command arguments.

        Args:
            input_file: Input file path
            device: Device to use (cuda/cpu), if None will get from config

        Returns:
            List of command arguments
        """
        cmd = ["whisperx"]

        # Get device setting
        if device is None:
            device = self._get_config_value("DEVICE", "cuda")

        # Basic arguments
        cmd.extend(
            [
                "--output_dir",
                "/results",
                "--model",
                self._get_config_value("WHISPER_MODEL", "large-v3"),
                "--batch_size",
                self._get_config_value("BATCH_SIZE", "16"),
                "--device",
                device,
                "--output_format",
                "all",
                "--verbose",
                "False",
            ]
        )

        # Add language only if it's not 'auto' (WhisperX doesn't support 'auto')
        language = self._get_config_value("LANGUAGE", "auto")
        if language and language != "auto":
            cmd.extend(["--language", language])

        # Set compute type based on device
        if device == "cpu":
            # CPU doesn't support efficient float16, use float32
            cmd.extend(["--compute_type", "float32"])
        else:
            # GPU can use float16 for better performance
            cmd.extend(
                ["--compute_type", self._get_config_value("COMPUTE_TYPE", "float16")]
            )

        # Diarization arguments
        hf_token = self._get_config_value("HF_TOKEN", "").strip()
        enable_diarization = (
            self._get_config_value("ENABLE_DIARIZATION", "true").lower() == "true"
        )
        if enable_diarization and hf_token and hf_token != "your_token_here":
            cmd.extend(["--diarize", f"--hf_token={hf_token}"])

            # Add speaker constraints if specified
            for key, flag in [
                ("MIN_SPEAKERS", "--min_speakers"),
                ("MAX_SPEAKERS", "--max_speakers"),
            ]:
                value = self._get_config_value(key, "")
                if value and value.isdigit() and int(value) > 0:
                    cmd.extend([flag, value])

        # Input file
        cmd.append(f"/audio/{input_file.name}")

        return cmd

    def _monitor_transcription(
        self, container, start_time: float, output_dir: Path
    ) -> TranscriptionResult:
        """Monitor transcription progress and collect results.

        Args:
            container: Docker container running transcription
            start_time: Process start time
            output_dir: Directory where output files should be located

        Returns:
            TranscriptionResult with final status
        """
        try:
            # Wait for container to complete
            result = container.wait()

            if result["StatusCode"] == 0:
                # Success - collect output files from the specified output directory
                output_files = self._collect_output_files(output_dir)
                processing_time = time.time() - start_time

                self.logger.info(f"Transcription completed in {processing_time:.1f}s")
                self.logger.info(f"Generated {len(output_files)} output files")

                return TranscriptionResult(
                    status=TranscriptionStatus.COMPLETED,
                    output_files=output_files,
                    processing_time=processing_time,
                )
            else:
                # Failed
                error_msg = f"Container exited with code {result['StatusCode']}"
                self.logger.error(error_msg)

                return TranscriptionResult(
                    status=TranscriptionStatus.FAILED,
                    output_files=[],
                    processing_time=time.time() - start_time,
                    error_message=error_msg,
                )

        except Exception as e:
            self.logger.error(f"Error monitoring transcription: {e}")
            return TranscriptionResult(
                status=TranscriptionStatus.FAILED,
                output_files=[],
                processing_time=time.time() - start_time,
                error_message=str(e),
            )

    def _collect_output_files(self, output_dir: Path) -> list[Path]:
        """Collect output files from successful transcription.

        Args:
            output_dir: Directory where output files should be located

        Returns:
            List of output file paths
        """
        try:
            if not output_dir.exists():
                self.logger.error(f"Output directory does not exist: {output_dir}")
                return []

            # Look for WhisperX output files
            output_files = []

            # Common WhisperX output files
            patterns = [
                "*.txt",  # Main transcript
                "*.json",  # Detailed JSON output
                "*.srt",  # Subtitles
                "*.vtt",  # WebVTT
                "*.tsv",  # TSV format
            ]

            for pattern in patterns:
                for output_file in output_dir.glob(pattern):
                    output_files.append(output_file)

            self.logger.info(f"Found {len(output_files)} output files in {output_dir}")
            for file_path in output_files:
                self.logger.info(f"  - {file_path.name}")

            return output_files

        except Exception as e:
            self.logger.error(f"Error collecting output files: {e}")
            return []

    def cancel_transcription(self):
        """Cancel current transcription if running."""
        if self.current_container:
            try:
                self.current_container.stop(timeout=10)
                self.logger.info("Transcription cancelled")
            except Exception as e:
                self.logger.error(f"Error cancelling transcription: {e}")
            finally:
                self.current_container = None

    def get_progress(self) -> Dict[str, Any]:
        """Get current transcription progress with enhanced monitoring.

        Returns:
            Dictionary with progress information
        """
        if not self.current_container:
            return {"status": "idle", "progress": 0, "stage": "Not started"}

        try:
            # Get container logs for progress estimation
            logs = self.current_container.logs(tail=100).decode(
                "utf-8", errors="ignore"
            )

            # Enhanced progress estimation based on WhisperX log patterns
            progress = 0
            status = "running"
            stage = "Processing"

            # Check for completion first
            if (
                "Transcription complete" in logs
                or "Output files saved" in logs
                or "All done!" in logs
            ):
                progress = 100
                status = "completed"
                stage = "Complete"
            # Check for errors
            elif "Error" in logs or "Failed" in logs or "Exception" in logs:
                progress = 0
                status = "error"
                stage = "Error occurred"
            # Check for specific WhisperX error patterns
            elif "could not be found" in logs.lower() or (
                "alignment" in logs.lower() and "error" in logs.lower()
            ):
                progress = 0
                status = "error"
                stage = (
                    "Alignment model not found - check HF_TOKEN and model availability"
                )
            # Check for authentication issues
            elif (
                "authentication" in logs.lower()
                or "permission" in logs.lower()
                or "unauthorized" in logs.lower()
                or "403" in logs
            ):
                progress = 0
                status = "error"
                stage = "Authentication failed - check HF_TOKEN"
            # Check for GPU/CUDA issues
            elif "cuda" in logs.lower() and (
                "error" in logs.lower() or "failed" in logs.lower()
            ):
                progress = 0
                status = "error"
                stage = "GPU/CUDA error - check GPU availability"
            # Progress stages with WhisperX-specific patterns
            elif "Performing diarization" in logs or "speaker" in logs.lower():
                progress = 90
                status = "running"
                stage = "Speaker diarization"
            elif "Performing alignment" in logs or "alignment" in logs.lower():
                progress = 75
                status = "running"
                stage = "Aligning timestamps"
            elif "Performing transcription" in logs or "transcrib" in logs.lower():
                progress = 50
                status = "running"
                stage = "Transcribing audio"
            elif "Loading model" in logs or "Downloading" in logs:
                progress = 15
                status = "running"
                stage = "Loading WhisperX model"
            elif "Preprocessing" in logs or "preprocess" in logs.lower():
                progress = 10
                status = "running"
                stage = "Preprocessing audio"
            elif (
                "Performing VAD" in logs
                or "voice activity detection" in logs.lower()
                or "silero" in logs.lower()
            ):
                progress = 25
                status = "running"
                stage = "Detecting speech"
            elif "Detecting language" in logs or "Language detected" in logs:
                progress = 5
                status = "running"
                stage = "Detecting language"
            elif "Initializing" in logs or "Starting" in logs:
                progress = 2
                status = "running"
                stage = "Initializing"
            else:
                # Try to estimate progress based on log volume/length
                log_lines = len([line for line in logs.split("\n") if line.strip()])
                if log_lines > 100:
                    progress = min(15, log_lines // 8)
                    stage = "Processing"
                elif log_lines > 20:
                    progress = 5
                    stage = "Starting up"
                else:
                    progress = 1
                    stage = "Initializing"

            # Get recent log lines for debugging
            recent_logs = [line for line in logs.split("\n") if line.strip()][-15:]

            return {
                "status": status,
                "progress": progress,
                "stage": stage,
                "logs": recent_logs,
                "log_count": len(recent_logs),
            }

        except Exception as e:
            self.logger.error(f"Error getting progress: {e}")
            return {
                "status": "error",
                "progress": 0,
                "stage": f"Error: {str(e)}",
                "error": str(e),
            }


def create_transcription_service(config_path: str = "config.env") -> WhisperXService:
    """Factory function to create WhisperX service.

    Args:
        config_path: Path to configuration file

    Returns:
        Configured WhisperXService instance
    """
    return WhisperXService(config_path)
