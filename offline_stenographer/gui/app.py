#!/usr/bin/env python3
"""
GUI Application Module - VideoTranscriptionApp

This module contains the main GUI application class for the Offline Stenographer.
"""

import logging
import os
import sys
import tempfile
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from offline_stenographer import __author__, __version__
from offline_stenographer.constants import AppConfig, LoggingConfig, UIConfig
from offline_stenographer.gui.widgets import (
    AboutDialog,
    ConfigurationDialog,
    ControlFrame,
    ExportDialog,
    FileSelectionFrame,
    LogFrame,
    MenuBar,
    ProgressFrame,
)
from offline_stenographer.processing.config_manager import get_config_manager
from offline_stenographer.processing.export_manager import ExportManager
from offline_stenographer.processing.transcription_service import (
    TranscriptionStatus,
    WhisperXService,
)
from offline_stenographer.processing.video_processor import VideoProcessor


class VideoTranscriptionApp:
    """Main application class for the Video Transcription GUI."""

    def __init__(self):
        """Initialize the main application."""
        self.root = tk.Tk()
        self.root.title(f"Offline Stenographer v{__version__}")
        self.root.geometry(AppConfig.WINDOW_SIZE)
        self.root.minsize(*AppConfig.MIN_WINDOW_SIZE.split("x"))

        # Application state
        self.input_file = None
        self.is_processing = False

        # Configuration manager - single source of truth
        self.config_manager = (
            get_config_manager() if get_config_manager is not None else None
        )

        # Transcription service
        self.transcription_service = None
        self.requirements_checked = False

        # Progress monitoring
        self.progress_update_thread = None
        self.progress_update_active = False

        # Track recent log messages to avoid duplicates
        self.recent_log_messages = []
        self.max_recent_messages = UIConfig.MAX_RECENT_LOG_MESSAGES

        # Temporary directory management
        self.temp_dir_manager = None

        # Configure logging first
        self._setup_logging()

        # Export manager for handling export operations
        self.export_manager = ExportManager(self.logger)

        # Create GUI components
        self._create_menu_bar()
        self._create_main_interface()
        self._setup_bindings()

        # Load persistent configuration
        self._load_configuration()

        self.session_temp_dir = tempfile.TemporaryDirectory(prefix="whisperx_session_")

        self.logger.info(f"Offline Stenographer v{__version__} started")

    def _load_configuration(self):
        """Load persistent configuration from ConfigurationManager."""
        try:
            if self.config_manager is None:
                self.logger.warning("Configuration manager not available")
                return

            # Load saved configuration - this is now our single source of truth
            self.current_config = self.config_manager.load_config()
            self.logger.info("Configuration loaded from persistent storage")

        except Exception as e:
            self.logger.warning(f"Failed to load configuration: {e}")
            # Use default configuration
            self.current_config = (
                self.config_manager.load_config() if self.config_manager else None
            )

    def _setup_logging(self):
        """Configure application logging."""
        self.logger = logging.getLogger(LoggingConfig.LOGGER_NAME)
        self.logger.setLevel(LoggingConfig.DEFAULT_LEVEL)

        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(LoggingConfig.DEFAULT_LEVEL)
        formatter = logging.Formatter(LoggingConfig.LOG_FORMAT)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _create_menu_bar(self):
        """Create the application menu bar."""
        callbacks = {
            "select_file": self._select_file,
            "quit": self._quit,
            "show_config": self._show_whisperx_config,
            "show_about": self._show_about,
        }
        self.menu_bar = MenuBar(self.root, callbacks)

    def _create_main_interface(self):
        """Create the main application interface using components."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Create GUI components
        self.file_selection = FileSelectionFrame(
            main_frame, {"select_file": self._select_file}
        )
        self.progress_frame = ProgressFrame(main_frame)
        self.control_frame = ControlFrame(
            main_frame,
            {
                "start_transcription": self._start_transcription,
                "cancel_transcription": self._cancel_transcription,
            },
        )
        self.log_frame = LogFrame(main_frame)

        # Configure main frame resizing
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)

    def _setup_bindings(self):
        """Set up keyboard and other event bindings."""
        self.root.protocol("WM_DELETE_WINDOW", self._quit)
        self.root.bind("<Control-o>", lambda e: self._select_file())
        self.root.bind("<Control-q>", lambda e: self._quit())

    def _select_file(self):
        """Open file selection dialog."""
        filename = filedialog.askopenfilename(
            title="Select Video File", filetypes=AppConfig.VIDEO_FILETYPES
        )

        if filename:
            self.input_file = filename
            self.file_selection.update_file_label(os.path.basename(filename))
            self._log_message(f"Selected file: {filename}")
            self._update_transcribe_button_state()

    def _update_transcribe_button_state(self):
        """Update the transcribe button state based on current conditions."""
        if self.input_file and not self.is_processing:
            self.control_frame.update_transcribe_button_state(True)
        else:
            self.control_frame.update_transcribe_button_state(False)

    def _start_transcription(self):
        """Start the transcription process."""
        if not self.input_file:
            messagebox.showerror("Error", "Please select a video file first.")
            return

        # Check requirements before starting
        if not self._check_requirements():
            return

        self.is_processing = True
        self._update_transcribe_button_state()
        self._log_message(f"Starting transcription of {self.input_file}")

        # Start real transcription process
        self._start_real_transcription()

    def _check_requirements(self) -> bool:
        """Check if all requirements for transcription are met.

        Returns:
            True if requirements are met, False otherwise
        """
        try:
            # Try to import and initialize WhisperX service
            if WhisperXService is None:
                messagebox.showerror(
                    "Error",
                    "Transcription service not available. Please check installation.",
                )
                return False

            # Create temporary service to check requirements
            temp_service = WhisperXService(self.config_manager)
            is_ready, error_msg = temp_service.check_requirements()

            if not is_ready:
                self._log_message(f"Requirements check failed: {error_msg}")
                messagebox.showerror("Requirements Check Failed", error_msg)
                return False

            self._log_message("Requirements check passed")
            return True

        except Exception as e:
            error_msg = f"Error checking requirements: {e}"
            self._log_message(error_msg)
            messagebox.showerror("Error", error_msg)
            return False

    def _start_real_transcription(self):
        """Start real transcription process using WhisperX Docker service."""

        def transcribe():
            # Create temporary directory for this transcription session
            try:
                # Create video processor with ConfigurationManager
                if VideoProcessor is None:
                    raise ImportError("Video processor not available")

                video_processor = VideoProcessor(self.config_manager)
                input_path = Path(self.input_file)

                # Step 1: Validate and preprocess video
                self._log_message("Analyzing video file...")
                is_valid, validation_msg = video_processor.validate_video_format(
                    input_path
                )

                if not is_valid:
                    self.progress_frame.set_status("Invalid video format")
                    self._log_message(f"Video validation failed: {validation_msg}")
                    messagebox.showerror("Invalid Format", validation_msg)
                    return

                self._log_message(f"Video format validated: {validation_msg}")

                # Preprocess video (extract audio) using session temp directory
                self._log_message("Extracting audio from video...")
                preprocess_result = video_processor.preprocess_video(
                    input_path, Path(self.session_temp_dir.name)
                )

                if not preprocess_result.success:
                    self.progress_frame.set_status("Audio extraction failed")
                    error_msg = (
                        preprocess_result.error_message or "Failed to extract audio"
                    )
                    self._log_message(f"Preprocessing failed: {error_msg}")
                    messagebox.showerror("Preprocessing Failed", error_msg)
                    return

                audio_file = preprocess_result.audio_file
                self._log_message(f"Audio extracted: {audio_file}")

                # Step 2: Create transcription service with ConfigurationManager config
                if WhisperXService is None:
                    raise ImportError("Transcription service not available")

                # Create service with ConfigurationManager
                self.transcription_service = WhisperXService(self.config_manager)

                # Start transcription with preprocessed audio
                self._log_message("Initializing WhisperX transcription...")
                self._start_progress_monitoring()  # Start progress monitoring
                result = self.transcription_service.transcribe_file(
                    audio_file, Path(self.session_temp_dir.name) / "audio"
                )

                if result.status == TranscriptionStatus.COMPLETED:
                    self.progress_frame.set_status("Transcription completed!")
                    self._log_message(
                        f"Success! Generated {len(result.output_files)} files"
                    )
                    self._log_message(f"Processing time: {result.processing_time:.1f}s")

                    # Store result for export and show export options
                    self.transcription_result = result
                    self._show_export_options(result)

                    # Show output files
                    if result.output_files:
                        files_str = "\n".join(
                            f"  • {f.name}" for f in result.output_files
                        )
                        self._log_message(f"Output files:\n{files_str}")

                elif result.status == TranscriptionStatus.FAILED:
                    self.progress_frame.set_status("Transcription failed")
                    error_msg = result.error_message or "Unknown error"
                    self._log_message(f"Transcription failed: {error_msg}")
                    messagebox.showerror("Transcription Failed", error_msg)

                # Temporary directory cleanup is automatic - happens when context exits

            except Exception as e:
                self.progress_frame.set_status("Error occurred")
                error_msg = f"Transcription error: {e}"
                self._log_message(error_msg)
                messagebox.showerror("Error", error_msg)
                self.logger.error(f"Transcription exception: {e}", exc_info=True)

            finally:
                self.is_processing = False
                self._update_transcribe_button_state()

        # Start transcription in background thread
        thread = threading.Thread(target=transcribe, daemon=True)
        thread.start()

    def _start_progress_monitoring(self):
        """Start the progress monitoring thread."""
        if (
            self.progress_update_thread is not None
            and self.progress_update_thread.is_alive()
        ):
            return  # Already running

        self.progress_update_active = True
        self.progress_update_thread = threading.Thread(
            target=self._progress_monitor_loop, daemon=True
        )
        self.progress_update_thread.start()
        self.logger.info("Progress monitoring started")

    def _stop_progress_monitoring(self):
        """Stop the progress monitoring thread."""
        self.progress_update_active = False
        if self.progress_update_thread and self.progress_update_thread.is_alive():
            self.progress_update_thread.join(timeout=1.0)
        self.logger.info("Progress monitoring stopped")

    def _progress_monitor_loop(self):
        """Main loop for progress monitoring thread."""
        while self.progress_update_active and self.is_processing:
            try:
                if self.transcription_service:
                    progress_info = self.transcription_service.get_progress()

                    # Update GUI progress (must be called from main thread)
                    self.root.after(0, lambda: self._update_gui_progress(progress_info))

                # Check every defined interval
                time.sleep(UIConfig.PROGRESS_UPDATE_INTERVAL)

            except Exception as e:
                self.logger.error(f"Error in progress monitoring: {e}")
                break

    def _update_gui_progress(self, progress_info):
        """Update GUI progress display (called from main thread).

        Args:
            progress_info: Progress information from transcription service
        """
        try:
            # Update progress bar
            progress = progress_info.get("progress", 0)
            self.progress_frame.update_progress(progress)

            # Update status label with current stage
            stage = progress_info.get("stage", "Processing")
            status = progress_info.get("status", "running")

            if status == "completed":
                self.progress_frame.set_status(f"✅ {stage}")
            elif status == "error":
                self.progress_frame.set_status(f"❌ {stage}")
            elif status == "running":
                self.progress_frame.set_status(f"⏳ {stage} ({progress}%)")
            else:
                self.progress_frame.set_status(stage)

            # Update log with recent messages if available
            recent_logs = progress_info.get("logs", [])
            if recent_logs:
                for log_msg in recent_logs[-3:]:  # Show last 3 log messages
                    if log_msg.strip() and log_msg not in self.recent_log_messages:
                        self._log_message(f"[WhisperX] {log_msg}")
                        # Add to recent messages list to avoid duplicates
                        self.recent_log_messages.append(log_msg)
                        # Keep only the most recent messages
                        if len(self.recent_log_messages) > self.max_recent_messages:
                            self.recent_log_messages = self.recent_log_messages[
                                -self.max_recent_messages :
                            ]

        except Exception as e:
            self.logger.error(f"Error updating GUI progress: {e}")

    def _cancel_transcription(self):
        """Cancel the current transcription process."""
        if self.is_processing:
            self.is_processing = False
            self._stop_progress_monitoring()

            # Cancel transcription service if available
            if self.transcription_service:
                self.transcription_service.cancel_transcription()

            self.progress_frame.set_status("Cancelled")
            self.progress_frame.update_progress(0.0)
            self._log_message("Transcription cancelled by user")
            self._update_transcribe_button_state()

    def _show_whisperx_config(self):
        """Show WhisperX configuration dialog."""
        callbacks = {"log_message": self._log_message, "open_url": self._open_url}
        self.config_dialog = ConfigurationDialog(
            self.root, self.config_manager, callbacks
        )

    def _open_url(self, url):
        """Open URL in default browser.

        Args:
            url: URL to open
        """
        try:
            import webbrowser

            webbrowser.open(url)
            self._log_message(f"Opened URL: {url}")
        except Exception as e:
            self._log_message(f"Failed to open URL {url}: {e}")
            messagebox.showerror("Error", f"Failed to open URL: {url}")

    def _show_export_options(self, docker_result):
        """Show export options dialog after transcription completion.

        Args:
            docker_result: Result from Docker transcription service
        """
        # Define callbacks for the export dialog
        callbacks = {
            "export_raw": self._export_raw_results,
            "export_formatted": self._export_formatted_results,
        }

        # Create and show the export dialog
        export_dialog = ExportDialog(self.root, docker_result, callbacks)

    def _export_raw_results(self, docker_result, output_folder):
        """Export raw WhisperX output files to folder.

        Args:
            docker_result: Result from Docker transcription service
            output_folder: Folder to save raw results
        """
        success = self.export_manager.export_raw_results(
            docker_result,
            output_folder,
            log_callback=self._log_message,
            status_callback=lambda text: self.progress_frame.set_status(text),
        )

        if success:
            messagebox.showinfo(
                "Export Complete",
                f"Raw results exported successfully!\n\nSaved to: {output_folder}",
            )
        else:
            messagebox.showwarning("No Files", "No raw files found to export.")

    def _export_formatted_results(self, docker_result, formats, output_folder):
        """Export transcription results to selected formats.

        Args:
            docker_result: Result from Docker transcription service
            formats: List of formats to export (txt, md, docx)
            output_folder: Folder to save formatted results
        """
        success = self.export_manager.export_formatted_results(
            docker_result,
            formats,
            output_folder,
            input_file=self.input_file,
            current_config=self.current_config,
            log_callback=self._log_message,
            status_callback=lambda text: self.progress_frame.set_status(text),
        )

        if success:
            messagebox.showinfo(
                "Export Complete",
                f"Successfully exported {len(formats)} format(s)!\n\nSaved to: {output_folder}",
            )
        else:
            messagebox.showerror(
                "Export Failed",
                "Failed to export any formats. Check the log for details.",
            )

    def _show_about(self):
        """Show the About dialog."""
        about_dialog = AboutDialog(self.root)
        about_dialog.show()

    def _quit(self):
        """Quit the application."""
        if self.is_processing:
            if messagebox.askyesno(
                "Quit", "Transcription is in progress. Do you want to quit?"
            ):
                self.is_processing = False
                self._stop_progress_monitoring()
            else:
                return

        # Stop progress monitoring if still active
        self._stop_progress_monitoring()

        # Log cleanup message
        self._log_message("🧹 Cleaning up temporary files...")
        self.logger.info("Application closing - cleaning up temporary files")

        # Application cleanup is automatic thanks to tempfile.TemporaryDirectory
        # The temporary directories will be cleaned up when the application exits
        self.root.quit()

    def _log_message(self, message):
        """Add a message to the log area."""
        self.log_frame.add_message(message)
        self.logger.info(message)

    def run(self):
        """Start the application main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._quit()
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            messagebox.showerror("Error", f"Application error: {e}")
            raise


def create_app() -> VideoTranscriptionApp:
    """Factory function to create the GUI application.

    Returns:
        Configured VideoTranscriptionApp instance
    """
    return VideoTranscriptionApp()
