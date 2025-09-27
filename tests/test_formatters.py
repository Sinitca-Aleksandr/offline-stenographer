"""
Tests for output formatter functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from offline_stenographer.processing.formatters import (
    DocxFormatter,
    FormatterFactory,
    MarkdownFormatter,
    TextFormatter,
    TranscriptionResult,
    TranscriptionSegment,
)


class TestTranscriptionSegment:
    """Test cases for TranscriptionSegment."""

    def test_segment_creation(self):
        """Test creating a transcription segment."""
        segment = TranscriptionSegment(
            start_time=0.0,
            end_time=5.2,
            text="Hello, world!",
            speaker="Speaker 1",
            confidence=0.95,
        )

        assert segment.start_time == 0.0
        assert segment.end_time == 5.2
        assert segment.text == "Hello, world!"
        assert segment.speaker == "Speaker 1"
        assert segment.confidence == 0.95

    def test_segment_without_optional_fields(self):
        """Test creating a segment without optional fields."""
        segment = TranscriptionSegment(start_time=1.0, end_time=3.0, text="Test text")

        assert segment.start_time == 1.0
        assert segment.end_time == 3.0
        assert segment.text == "Test text"
        assert segment.speaker is None
        assert segment.confidence is None


class TestTranscriptionResult:
    """Test cases for TranscriptionResult."""

    def test_result_creation(self, sample_transcription_segments):
        """Test creating a transcription result."""
        result = TranscriptionResult(
            segments=sample_transcription_segments,
            language="en",
            processing_time=15.3,
            metadata={"source_file": "test.mp4"},
        )

        assert len(result.segments) == 3
        assert result.language == "en"
        assert result.processing_time == 15.3
        assert result.metadata["source_file"] == "test.mp4"


class TestTextFormatter:
    """Test cases for TextFormatter."""

    def test_format_transcription_success(self, sample_transcription_result, temp_dir):
        """Test successful text formatting."""
        output_file = temp_dir / "test_output.txt"
        formatter = TextFormatter(output_file)

        success = formatter.format_transcription(sample_transcription_result)

        assert success is True
        assert output_file.exists()

    def test_format_transcription_empty_segments(self, temp_dir):
        """Test formatting with empty segments."""
        output_file = temp_dir / "test_output.txt"
        formatter = TextFormatter(output_file)

        empty_result = TranscriptionResult(
            segments=[], language="en", processing_time=0.0
        )

        success = formatter.format_transcription(empty_result)

        assert success is True
        assert output_file.exists()

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        output_file = Path("dummy.txt")
        formatter = TextFormatter(output_file)

        # Test seconds only
        assert formatter._format_timestamp(30) == "00:30"

        # Test minutes and seconds
        assert formatter._format_timestamp(90) == "01:30"

        # Test hours, minutes and seconds
        assert formatter._format_timestamp(3661) == "01:01:01"


class TestMarkdownFormatter:
    """Test cases for MarkdownFormatter."""

    def test_format_transcription_success(self, sample_transcription_result, temp_dir):
        """Test successful markdown formatting."""
        output_file = temp_dir / "test_output.md"
        formatter = MarkdownFormatter(output_file)

        success = formatter.format_transcription(sample_transcription_result)

        assert success is True
        assert output_file.exists()

    def test_format_with_metadata(self, sample_transcription_segments, temp_dir):
        """Test markdown formatting with metadata."""
        output_file = temp_dir / "test_output.md"
        formatter = MarkdownFormatter(output_file)

        result = TranscriptionResult(
            segments=sample_transcription_segments,
            language="en",
            processing_time=15.3,
            metadata={
                "source_file": "test_video.mp4",
                "whisper_model": "large-v3",
                "speakers": ["Speaker 1", "Speaker 2"],
            },
        )

        success = formatter.format_transcription(result)

        assert success is True
        assert output_file.exists()


class TestDocxFormatter:
    """Test cases for DocxFormatter."""

    def test_format_transcription_success(self, sample_transcription_result, temp_dir):
        """Test successful DOCX formatting."""
        output_file = temp_dir / "test_output.docx"
        formatter = DocxFormatter(output_file)

        success = formatter.format_transcription(sample_transcription_result)

        assert success is True
        assert output_file.exists()

    def test_format_without_docx_library(self, sample_transcription_result, temp_dir):
        """Test DOCX formatter when python-docx is not available."""
        output_file = temp_dir / "test_output.docx"
        formatter = DocxFormatter(output_file)

        # Mock DOCX not being available
        with patch("offline_stenographer.processing.formatters.DOCX_AVAILABLE", False):
            success = formatter.format_transcription(sample_transcription_result)

            assert success is False

    def test_format_with_metadata(self, sample_transcription_segments, temp_dir):
        """Test DOCX formatting with metadata."""
        output_file = temp_dir / "test_output.docx"
        formatter = DocxFormatter(output_file)

        result = TranscriptionResult(
            segments=sample_transcription_segments,
            language="en",
            processing_time=15.3,
            metadata={
                "source_file": "test_video.mp4",
                "whisper_model": "large-v3",
                "device": "cuda",
            },
        )

        success = formatter.format_transcription(result)

        assert success is True
        assert output_file.exists()


class TestFormatterFactory:
    """Test cases for FormatterFactory."""

    def test_create_text_formatter(self, temp_dir):
        """Test creating text formatter."""
        output_file = temp_dir / "test.txt"
        formatter = FormatterFactory.create_formatter("txt", output_file)

        assert isinstance(formatter, TextFormatter)
        assert formatter.output_path == output_file

    def test_create_markdown_formatter(self, temp_dir):
        """Test creating markdown formatter."""
        output_file = temp_dir / "test.md"
        formatter = FormatterFactory.create_formatter("md", output_file)

        assert isinstance(formatter, MarkdownFormatter)
        assert formatter.output_path == output_file

    def test_create_docx_formatter(self, temp_dir):
        """Test creating DOCX formatter."""
        output_file = temp_dir / "test.docx"
        formatter = FormatterFactory.create_formatter("docx", output_file)

        assert isinstance(formatter, DocxFormatter)
        assert formatter.output_path == output_file

    def test_create_unsupported_formatter(self, temp_dir):
        """Test creating formatter for unsupported format."""
        output_file = temp_dir / "test.xyz"
        formatter = FormatterFactory.create_formatter("xyz", output_file)

        assert formatter is None

    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        formats = FormatterFactory.get_supported_formats()

        assert "txt" in formats
        assert "md" in formats
        assert "docx" in formats
        assert len(formats) == 3


def test_format_transcription_output_function(sample_transcription_result, temp_dir):
    """Test the format_transcription_output convenience function."""
    from offline_stenographer.processing.formatters import format_transcription_output

    output_file = temp_dir / "test_output.txt"

    success = format_transcription_output(
        sample_transcription_result, "txt", output_file
    )

    assert success is True
    assert output_file.exists()


def test_format_transcription_output_unsupported_format(
    sample_transcription_result, temp_dir
):
    """Test format_transcription_output with unsupported format."""
    from offline_stenographer.processing.formatters import format_transcription_output

    output_file = temp_dir / "test_output.xyz"

    success = format_transcription_output(
        sample_transcription_result, "xyz", output_file
    )

    assert success is False
    assert not output_file.exists()
