"""
About dialog widget for the Offline Stenographer application.
"""

import tkinter as tk
from tkinter import ttk

from offline_stenographer import __author__, __version__


class AboutDialog:
    """About dialog widget component."""

    def __init__(self, parent):
        """
        Initialize the About dialog.

        Args:
            parent: The parent Tk window
        """
        self.parent = parent
        self.dialog = None

    def show(self):
        """Show the About dialog."""
        # Create dialog if it doesn't exist
        if self.dialog is None or not self.dialog.winfo_exists():
            self._create_dialog()

        # Center the dialog
        self._center_dialog()

        # Set focus and make modal
        self.dialog.focus_set()
        self.dialog.grab_set()

    def _create_dialog(self):
        """Create the About dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("About - Offline Stenographer")
        self.dialog.resizable(False, False)

        # Configure dialog close behavior
        self.dialog.protocol("WM_DELETE_WINDOW", self._close_dialog)
        self.dialog.bind("<Escape>", lambda e: self._close_dialog())

        # Create main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Application icon/title area
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 20))

        # Title
        title_label = ttk.Label(
            title_frame,
            text=f"Offline Stenographer v{__version__}",
            font=("TkDefaultFont", 14, "bold"),
        )
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = ttk.Label(
            title_frame,
            text="A GUI application for creating transcripts from video files using WhisperX.",
            wraplength=350,
            justify=tk.CENTER,
        )
        desc_label.pack()

        # Content area
        content_frame = ttk.LabelFrame(
            main_frame, text="Application Details", padding="15"
        )
        content_frame.pack(fill=tk.X, pady=(0, 20))

        # Application details
        details = [
            ("Version:", __version__),
            ("Author:", __author__),
            ("License:", "Apache License 2.0"),
            ("Technology:", "WhisperX with Docker"),
        ]

        for label_text, value_text in details:
            detail_frame = ttk.Frame(content_frame)
            detail_frame.pack(fill=tk.X, pady=(5, 0))

            label = ttk.Label(
                detail_frame,
                text=label_text,
                width=12,
                font=("TkDefaultFont", 9, "bold"),
            )
            label.pack(side=tk.LEFT)

            value = ttk.Label(detail_frame, text=value_text)
            value.pack(side=tk.LEFT, fill=tk.X)

        # Features section
        features_frame = ttk.LabelFrame(main_frame, text="Features", padding="15")
        features_frame.pack(fill=tk.X, pady=(0, 20))

        features_text = """• Offline video transcription
• Speaker diarization
• Multiple export formats
• Real-time progress monitoring
• Configurable WhisperX settings
• Batch processing support"""

        features_label = ttk.Label(
            features_frame,
            text=features_text,
            justify=tk.LEFT,
            font=("TkDefaultFont", 9),
        )
        features_label.pack()

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        close_button = ttk.Button(
            button_frame, text="Close", command=self._close_dialog, width=10
        )
        close_button.pack()

        # Make close button the default (activated by Enter key)
        close_button.focus_set()

    def _center_dialog(self):
        """Center the dialog on the screen."""
        if self.dialog:
            self.dialog.update_idletasks()

            # Get parent window position and size
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            # Calculate dialog position to center it on parent
            dialog_width = self.dialog.winfo_reqwidth()
            dialog_height = self.dialog.winfo_reqheight()

            x = parent_x + (parent_width - dialog_width) // 2
            y = parent_y + (parent_height - dialog_height) // 2

            # Ensure dialog stays within screen bounds
            if x < 0:
                x = 0
            if y < 0:
                y = 0

            self.dialog.geometry(f"+{x}+{y}")

    def _close_dialog(self):
        """Close the About dialog."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None
