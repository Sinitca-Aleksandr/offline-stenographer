"""
File selection frame widget for the Offline Stenographer application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class FileSelectionFrame:
    """File selection component."""

    def __init__(self, parent: ttk.Frame, callbacks: dict[str, Callable]):
        """
        Initialize the file selection frame.

        Args:
            parent: Parent frame
            callbacks: Dictionary of callback functions
        """
        self.parent = parent
        self.callbacks = callbacks
        self.file_label: Optional[ttk.Label] = None
        self._create_frame()

    def _create_frame(self) -> None:
        """Create the file selection frame."""
        # File selection section
        file_frame = ttk.LabelFrame(self.parent, text="Input File", padding="5")
        file_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        file_frame.columnconfigure(1, weight=1)

        ttk.Label(file_frame, text="Video File:").grid(row=0, column=0, sticky=tk.W)
        self.file_label = ttk.Label(file_frame, text="No file selected")
        self.file_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))

        ttk.Button(
            file_frame, text="Browse...", command=self.callbacks.get("select_file")
        ).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

    def update_file_label(self, filename: str) -> None:
        """Update the file label with selected filename."""
        if self.file_label:
            self.file_label.config(text=filename)
