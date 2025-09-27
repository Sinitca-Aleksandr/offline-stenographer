#!/usr/bin/env python3
"""
Export Manager Module

This module handles exporting transcription results in various formats.
Separated from GUI logic for better modularity and testability.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import List, Optional

from offline_stenographer.processing.formatters import (
    TranscriptionResult,
    TranscriptionSegment,
    format_transcription_output,
)


class ExportManager:
    """Manages export operations for transcription results."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize the export manager.

        Args:
            logger: Optional logger instance for logging messages
        """
        self.logger = logger or logging.getLogger(__name__)

    def export_raw_results(
        self,
        docker_result,
        output_folder: str,
        log_callback: Optional[callable] = None,
        status_callback: Optional[callable] = None,
    ) -> bool:
        """Export raw WhisperX output files to folder.

        Args:
            docker_result: Result from Docker transcription service
            output_folder: Folder to save raw results
            log_callback: Optional callback for logging messages
            status_callback: Optional callback for status updates

        Returns:
            True if export was successful, False otherwise
        """
        try:
            if log_callback:
                log_callback("Exporting raw results...")

            # Create output directory if it doesn't exist
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)

            # Copy all output files
            copied_files = []
            for source_file in docker_result.output_files:
                if source_file.exists():
                    dest_file = output_path / source_file.name
                    shutil.copy2(source_file, dest_file)
                    copied_files.append(dest_file.name)

            if copied_files:
                files_str = "\n".join(f"  • {f}" for f in copied_files)
                success_msg = f"✅ Exported raw files to {output_folder}:\n{files_str}"
                if log_callback:
                    log_callback(success_msg)
                if status_callback:
                    status_callback(f"Raw results exported to {output_path.name}")

                return True
            else:
                error_msg = "❌ No files to export"
                if log_callback:
                    log_callback(error_msg)
                return False

        except Exception as e:
            error_msg = f"Error exporting raw results: {e}"
            if log_callback:
                log_callback(error_msg)
            if self.logger:
                self.logger.error(f"Raw export exception: {e}", exc_info=True)
            return False

    def export_formatted_results(
        self,
        docker_result,
        formats: List[str],
        output_folder: str,
        input_file: Optional[str] = None,
        current_config=None,
        log_callback: Optional[callable] = None,
        status_callback: Optional[callable] = None,
    ) -> bool:
        """Export transcription results to selected formats.

        Args:
            docker_result: Result from Docker transcription service
            formats: List of formats to export (txt, md, docx)
            output_folder: Folder to save formatted results
            input_file: Optional input file path for metadata
            current_config: Optional configuration object
            log_callback: Optional callback for logging messages
            status_callback: Optional callback for status updates

        Returns:
            True if at least one format was exported successfully, False otherwise
        """
        try:
            if format_transcription_output is None:
                error_msg = "Formatter not available, skipping export"
                if log_callback:
                    log_callback(error_msg)
                return False

            # Parse actual WhisperX output files to create proper segments
            segments = self._parse_whisperx_output(docker_result, log_callback)

            if not segments:
                error_msg = "No transcription segments found, skipping export"
                if log_callback:
                    log_callback(error_msg)
                return False

            # Create output directory if it doesn't exist
            output_path = Path(output_folder)
            output_path.mkdir(parents=True, exist_ok=True)

            # Create transcription result with real data
            input_path = Path(input_file) if input_file else Path("unknown")
            transcription_result = TranscriptionResult(
                segments=segments,
                language=(
                    current_config.whisperx.language if current_config else "auto"
                ),
                processing_time=docker_result.processing_time,
                metadata={
                    "source_file": input_path.name,
                    "whisper_model": (
                        current_config.whisperx.model if current_config else "large-v3"
                    ),
                    "device": (
                        current_config.whisperx.device if current_config else "cuda"
                    ),
                    "diarization": (
                        "enabled"
                        if (current_config and current_config.whisperx.diarization)
                        else "disabled"
                    ),
                    "total_segments": len(segments),
                },
            )

            # Export to each selected format
            success_count = 0
            base_name = input_path.stem

            for export_format in formats:
                try:
                    output_file = (
                        output_path / f"{base_name}_transcript.{export_format}"
                    )

                    # Export to selected format
                    success = format_transcription_output(
                        transcription_result, export_format, output_file
                    )

                    if success:
                        success_msg = (
                            f"✅ Exported {export_format.upper()}: {output_file.name}"
                        )
                        if log_callback:
                            log_callback(success_msg)
                        success_count += 1
                    else:
                        error_msg = f"❌ Failed to export {export_format.upper()}"
                        if log_callback:
                            log_callback(error_msg)

                except Exception as e:
                    error_msg = f"❌ Error exporting {export_format.upper()}: {e}"
                    if log_callback:
                        log_callback(error_msg)

            if success_count > 0:
                success_msg = (
                    f"Exported {success_count} format(s) to {output_path.name}"
                )
                if status_callback:
                    status_callback(success_msg)
                return True
            else:
                return False

        except Exception as e:
            error_msg = f"Export error: {e}"
            if log_callback:
                log_callback(error_msg)
            if self.logger:
                self.logger.error(f"Formatted export exception: {e}", exc_info=True)
            return False

    def _parse_whisperx_output(
        self, docker_result, log_callback: Optional[callable] = None
    ):
        """Parse WhisperX output files to create transcription segments.
        Prioritizes JSON format for accurate timing and speaker information.

        Args:
            docker_result: Result from Docker transcription service
            log_callback: Optional callback for logging messages

        Returns:
            List of TranscriptionSegment objects
        """
        try:
            if not docker_result.output_files:
                if log_callback:
                    log_callback("No output files found from WhisperX")
                return []

            segments = []

            # Prioritize JSON format for accurate timing and speaker data
            json_files = [f for f in docker_result.output_files if f.suffix == ".json"]
            txt_files = [f for f in docker_result.output_files if f.suffix == ".txt"]

            # Try JSON first (more accurate)
            for json_file in json_files:
                if json_file.exists():
                    segments = self._parse_json_output(json_file, log_callback)
                    if segments:
                        if log_callback:
                            log_callback(
                                f"✅ Successfully parsed JSON output: {json_file.name}"
                            )
                        break

            # Fallback to text format if JSON parsing failed
            if not segments:
                for txt_file in txt_files:
                    if txt_file.exists():
                        segments = self._parse_txt_output(txt_file, log_callback)
                        if segments:
                            if log_callback:
                                log_callback(
                                    f"✅ Successfully parsed text output: {txt_file.name}"
                                )
                            break

            if not segments:
                if log_callback:
                    log_callback("❌ No valid transcription data found in output files")
                    available_files = [f.name for f in docker_result.output_files]
                    if log_callback:
                        log_callback(f"Available files: {available_files}")
                return []

            if log_callback:
                log_callback(
                    f"✅ Parsed {len(segments)} transcription segments from {len(docker_result.output_files)} output files"
                )
            return segments

        except Exception as e:
            if log_callback:
                log_callback(f"❌ Error parsing WhisperX output: {e}")
            if self.logger:
                self.logger.error(f"Parse error details: {e}", exc_info=True)
            return []

    def _parse_txt_output(
        self, txt_file: Path, log_callback: Optional[callable] = None
    ):
        """Parse WhisperX text output file.

        Args:
            txt_file: Path to text output file
            log_callback: Optional callback for logging messages

        Returns:
            List of TranscriptionSegment objects
        """
        segments = []

        try:
            with open(txt_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Parse the Russian transcript format
            # Format: [SPEAKER_XX]: text content
            lines = content.split("\n")
            current_speaker = None
            current_text = []
            current_start_time = 0.0

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Check if line starts with speaker label
                if line.startswith("[SPEAKER_") and "]:" in line:
                    # Save previous segment if exists
                    if current_speaker and current_text:
                        combined_text = " ".join(current_text)
                        segments.append(
                            TranscriptionSegment(
                                start_time=current_start_time,
                                end_time=current_start_time + 5.0,  # Estimate
                                text=combined_text,
                                speaker=current_speaker,
                            )
                        )

                    # Parse new speaker segment
                    speaker_end = line.find("]:")
                    if speaker_end > 0:
                        # Include the closing bracket
                        current_speaker = line[: speaker_end + 1]
                        # Text after ]:
                        current_text = [line[speaker_end + 2 :].strip()]
                        # Simple time estimation
                        current_start_time = len(segments) * 5.0
                else:
                    # Continuation of current speaker
                    if current_speaker:
                        current_text.append(line)

            # Don't forget the last segment
            if current_speaker and current_text:
                combined_text = " ".join(current_text)
                segments.append(
                    TranscriptionSegment(
                        start_time=current_start_time,
                        end_time=current_start_time + 5.0,
                        text=combined_text,
                        speaker=current_speaker,
                    )
                )

        except Exception as e:
            if log_callback:
                log_callback(f"Error parsing text file {txt_file}: {e}")

        return segments

    def _parse_json_output(
        self, json_file: Path, log_callback: Optional[callable] = None
    ):
        """Parse WhisperX JSON output file with proper structure.

        Args:
            json_file: Path to JSON output file
            log_callback: Optional callback for logging messages

        Returns:
            List of TranscriptionSegment objects
        """
        segments = []

        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Parse segments from JSON structure - WhisperX format
            for segment_data in data.get("segments", []):
                start_time = float(segment_data.get("start", 0))
                end_time = float(segment_data.get("end", 0))
                text = segment_data.get("text", "").strip()
                speaker = segment_data.get("speaker", "SPEAKER_UNKNOWN")

                if text:
                    segments.append(
                        TranscriptionSegment(
                            start_time=start_time,
                            end_time=end_time,
                            text=text,
                            speaker=speaker,
                        )
                    )

            if log_callback:
                log_callback(
                    f"Parsed {len(segments)} segments from JSON {json_file.name}"
                )

        except Exception as e:
            if log_callback:
                log_callback(f"Error parsing JSON file {json_file}: {e}")
            if self.logger:
                self.logger.error(f"JSON parse error details: {e}", exc_info=True)

        return segments
