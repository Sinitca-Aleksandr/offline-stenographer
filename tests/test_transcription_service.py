"""
Tests for transcription service functionality with mocked Docker dependencies.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from offline_stenographer.processing.transcription_service import (
    TranscriptionResult,
    TranscriptionStatus,
    WhisperXService,
)


class TestTranscriptionStatus:
    """Test cases for TranscriptionStatus enum."""

    def test_status_values(self):
        """Test that all status values are defined."""
        assert TranscriptionStatus.IDLE.value == "idle"
        assert TranscriptionStatus.RUNNING.value == "running"
        assert TranscriptionStatus.COMPLETED.value == "completed"
        assert TranscriptionStatus.FAILED.value == "failed"
        assert TranscriptionStatus.CANCELLED.value == "cancelled"


class TestTranscriptionResult:
    """Test cases for TranscriptionResult."""

    def test_successful_result(self):
        """Test successful transcription result."""
        output_files = [Path("output1.txt"), Path("output2.json")]

        result = TranscriptionResult(
            status=TranscriptionStatus.COMPLETED,
            output_files=output_files,
            processing_time=15.3,
            error_message=None,
            metadata={"model": "large-v3"},
        )

        assert result.status == TranscriptionStatus.COMPLETED
        assert result.output_files == output_files
        assert result.processing_time == 15.3
        assert result.error_message is None
        assert result.metadata["model"] == "large-v3"

    def test_failed_result(self):
        """Test failed transcription result."""
        result = TranscriptionResult(
            status=TranscriptionStatus.FAILED,
            output_files=[],
            processing_time=2.1,
            error_message="Docker container failed",
            metadata=None,
        )

        assert result.status == TranscriptionStatus.FAILED
        assert result.output_files == []
        assert result.processing_time == 2.1
        assert result.error_message == "Docker container failed"
        assert result.metadata is None


class TestWhisperXService:
    """Test cases for WhisperXService."""

    def test_initialization(self, mock_config_manager):
        """Test WhisperXService initialization."""
        service = WhisperXService(mock_config_manager)

        assert service.config_manager == mock_config_manager
        assert service.image_name == "ghcr.io/jim60105/whisperx:latest"
        assert service.cache_dir == Path.home() / "whisperx"
        assert service.current_container is None

    def test_initialization_without_config_manager(self):
        """Test WhisperXService initialization without config manager."""
        service = WhisperXService()

        assert service.config_manager is not None  # Should create default
        assert service.image_name == "ghcr.io/jim60105/whisperx:latest"

    def test_get_config_value_with_config_manager(self, mock_config_manager):
        """Test getting config values when config manager is available."""
        service = WhisperXService(mock_config_manager)

        # Mock the config manager response
        mock_config_manager.load_config.return_value.whisperx.model = "medium"

        value = service._get_config_value("WHISPER_MODEL", "large-v3")
        assert value == "medium"

    def test_check_requirements_hf_token_missing(self, mock_docker_client):
        """Test requirements check when HF token is missing for diarization."""
        service = WhisperXService()

        # Mock config with missing HF token but diarization enabled
        mock_config = MagicMock()
        mock_config.whisperx.hf_token = ""
        mock_config.whisperx.diarization = True

        with patch.object(service, "config_manager"):
            service.config_manager.load_config.return_value = mock_config

            with patch("docker.from_env", return_value=mock_docker_client):
                with patch.object(service, "docker_client", mock_docker_client):
                    is_ready, message = service.check_requirements()

                    assert is_ready is False
                    assert "HF_TOKEN required for diarization" in message

    def test_build_whisperx_command(self, mock_config_manager):
        """Test building WhisperX command."""
        service = WhisperXService(mock_config_manager)

        # Mock the config values to return actual strings instead of MagicMock objects
        mock_config = MagicMock()
        mock_config.whisperx.model = "large-v3"
        mock_config.whisperx.batch_size = "16"
        mock_config.whisperx.compute_type = "float16"
        mock_config.whisperx.hf_token = "test_token"
        mock_config.whisperx.diarization = True
        mock_config.whisperx.min_speakers = ""
        mock_config.whisperx.max_speakers = ""
        mock_config_manager.load_config.return_value = mock_config

        input_file = Path("test_audio.wav")
        command = service._build_whisperx_command(input_file, "cuda")

        assert "whisperx" in command
        assert "--output_dir" in command
        assert "--model" in command
        assert "--device" in command
        assert "cuda" in command
        # Check the full container path
        assert f"/audio/{input_file.name}" in command

    def test_build_whisperx_command_with_language(self, mock_config_manager):
        """Test building WhisperX command with language specification."""
        service = WhisperXService(mock_config_manager)

        # Mock language config
        mock_config_manager.load_config.return_value.whisperx.language = "en"

        input_file = Path("test_audio.wav")
        command = service._build_whisperx_command(input_file, "cuda")

        assert "--language" in command
        assert "en" in command

    def test_build_whisperx_command_cpu_device(self, mock_config_manager):
        """Test building WhisperX command for CPU device."""
        service = WhisperXService(mock_config_manager)

        input_file = Path("test_audio.wav")
        command = service._build_whisperx_command(input_file, "cpu")

        assert "--device" in command
        assert "cpu" in command
        assert "--compute_type" in command
        assert "float32" in command  # CPU uses float32

    def test_create_transcription_container(
        self, mock_config_manager, mock_docker_client
    ):
        """Test creating transcription container."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                input_file = Path("test_audio.wav")
                output_dir = Path("/tmp/output")

                container = service._create_transcription_container(
                    input_file, output_dir
                )

                # Verify container was created
                mock_docker_client.containers.create.assert_called_once()

                # Verify container configuration
                call_args = mock_docker_client.containers.create.call_args
                assert call_args[1]["image"] == service.image_name
                assert "volumes" in call_args[1]
                assert "environment" in call_args[1]
                assert "device_requests" in call_args[1]

    def test_transcribe_file_success(
        self, mock_config_manager, mock_docker_client, temp_dir
    ):
        """Test successful file transcription."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Mock successful container execution
                mock_container = MagicMock()
                mock_container.wait.return_value = {"StatusCode": 0}
                mock_container.attrs = {
                    "Mounts": [{"Destination": "/results", "Source": str(temp_dir)}]
                }
                mock_docker_client.containers.create.return_value = mock_container

                # Create output files
                output_files = [temp_dir / "test.txt", temp_dir / "test.json"]
                for file in output_files:
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.touch()

                with patch.object(
                    service, "_collect_output_files", return_value=output_files
                ):
                    input_file = temp_dir / "input.wav"
                    input_file.touch()

                    result = service.transcribe_file(input_file, temp_dir)

                    assert result.status == TranscriptionStatus.COMPLETED
                    assert len(result.output_files) == 2
                    assert result.processing_time > 0
                    assert result.error_message is None

    def test_transcribe_file_input_not_found(self, mock_config_manager):
        """Test transcription with nonexistent input file."""
        service = WhisperXService(mock_config_manager)

        nonexistent_file = Path("nonexistent.wav")
        output_dir = Path("output")
        result = service.transcribe_file(nonexistent_file, output_dir)

        assert result.status == TranscriptionStatus.FAILED
        assert len(result.output_files) == 0
        assert "Input file not found" in result.error_message

    def test_transcribe_file_container_failure(
        self, mock_config_manager, mock_docker_client
    ):
        """Test transcription when container fails."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Mock failed container execution
                mock_container = MagicMock()
                mock_container.wait.return_value = {"StatusCode": 1}
                mock_docker_client.containers.create.return_value = mock_container

                # Create input file so it exists
                input_file = Path("test.wav")
                input_file.touch()

                try:
                    output_dir = Path("output")
                    result = service.transcribe_file(input_file, output_dir)

                    assert result.status == TranscriptionStatus.FAILED
                    assert len(result.output_files) == 0
                    assert "Container exited with code 1" in result.error_message
                finally:
                    # Clean up test file
                    if input_file.exists():
                        input_file.unlink()

    def test_cancel_transcription(self, mock_config_manager, mock_docker_client):
        """Test cancelling transcription."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Set current container
                mock_container = MagicMock()
                service.current_container = mock_container

                service.cancel_transcription()

                # Verify container was stopped
                mock_container.stop.assert_called_once_with(timeout=10)
                assert service.current_container is None

    def test_cancel_transcription_no_container(self, mock_config_manager):
        """Test cancelling transcription when no container is running."""
        service = WhisperXService(mock_config_manager)

        # No current container
        service.current_container = None

        # Should not raise an exception
        service.cancel_transcription()

    def test_get_progress_no_container(self, mock_config_manager):
        """Test getting progress when no container is running."""
        service = WhisperXService(mock_config_manager)

        progress = service.get_progress()

        assert progress["status"] == "idle"
        assert progress["progress"] == 0
        assert "Not started" in progress["stage"]

    def test_get_progress_with_container(self, mock_config_manager, mock_docker_client):
        """Test getting progress when container is running."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Set current container
                mock_container = MagicMock()
                mock_container.logs.return_value = (
                    b"Performing transcription\nLoading model"
                )
                service.current_container = mock_container

                progress = service.get_progress()

                assert "status" in progress
                assert "progress" in progress
                assert "stage" in progress
                assert "logs" in progress

    def test_get_progress_container_error(
        self, mock_config_manager, mock_docker_client
    ):
        """Test getting progress when container has errors."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Set current container with error logs
                mock_container = MagicMock()
                mock_container.logs.return_value = (
                    b"Error: CUDA not available\nFailed to load model"
                )
                service.current_container = mock_container

                progress = service.get_progress()

                assert progress["status"] == "error"
                assert progress["progress"] == 0
                assert "Error" in progress["stage"]

    def test_collect_output_files(
        self, mock_config_manager, mock_docker_client, temp_dir
    ):
        """Test collecting output files from successful transcription."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Mock container with output directory
                mock_container = MagicMock()
                mock_container.attrs = {
                    "Mounts": [{"Destination": "/results", "Source": str(temp_dir)}]
                }

                # Create mock output files
                output_files = [
                    temp_dir / "transcript.txt",
                    temp_dir / "transcript.json",
                    temp_dir / "transcript.srt",
                ]
                for file in output_files:
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.touch()

                # Mock glob to return different files for each pattern
                def mock_glob_side_effect(pattern):
                    if pattern == "*.txt":
                        return [temp_dir / "transcript.txt"]
                    elif pattern == "*.json":
                        return [temp_dir / "transcript.json"]
                    elif pattern == "*.srt":
                        return [temp_dir / "transcript.srt"]
                    elif pattern == "*.vtt":
                        return []
                    elif pattern == "*.tsv":
                        return []
                    return []

                with patch("pathlib.Path.glob", side_effect=mock_glob_side_effect):
                    collected_files = service._collect_output_files(temp_dir)

                    assert len(collected_files) == 3
                    assert all(f in collected_files for f in output_files)

    def test_collect_output_files_no_mounts(
        self, mock_config_manager, mock_docker_client
    ):
        """Test collecting output files when no mounts are found."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Mock container without results mount
                mock_container = MagicMock()
                mock_container.attrs = {"Mounts": []}

                collected_files = service._collect_output_files(mock_container)

                assert collected_files == []

    def test_monitor_transcription_success(
        self, mock_config_manager, mock_docker_client, temp_dir
    ):
        """Test monitoring successful transcription."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Mock successful container
                mock_container = MagicMock()
                mock_container.wait.return_value = {"StatusCode": 0}

                # Mock output files
                output_files = [temp_dir / "output.txt"]
                for file in output_files:
                    file.parent.mkdir(parents=True, exist_ok=True)
                    file.touch()

                with patch.object(
                    service, "_collect_output_files", return_value=output_files
                ):
                    start_time = time.time()
                    output_dir = temp_dir
                    result = service._monitor_transcription(
                        mock_container, start_time, output_dir
                    )

                    assert result.status == TranscriptionStatus.COMPLETED
                    assert len(result.output_files) == 1
                    assert result.processing_time >= 0

    def test_monitor_transcription_failure(
        self, mock_config_manager, mock_docker_client
    ):
        """Test monitoring failed transcription."""
        service = WhisperXService(mock_config_manager)

        with patch("docker.from_env", return_value=mock_docker_client):
            with patch.object(service, "docker_client", mock_docker_client):
                # Mock failed container
                mock_container = MagicMock()
                mock_container.wait.return_value = {"StatusCode": 1}

                start_time = time.time()
                output_dir = Path("output")
                result = service._monitor_transcription(
                    mock_container, start_time, output_dir
                )

                assert result.status == TranscriptionStatus.FAILED
                assert len(result.output_files) == 0
                assert "Container exited with code 1" in result.error_message


def test_create_transcription_service():
    """Test the factory function for creating transcription service."""
    from offline_stenographer.processing.transcription_service import (
        create_transcription_service,
    )

    service = create_transcription_service()

    assert isinstance(service, WhisperXService)
    assert service.config_manager is not None
