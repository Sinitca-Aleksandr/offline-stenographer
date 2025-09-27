"""
Progress frame widget for the Offline Stenographer application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional


class ProgressFrame:
    """Progress display component."""

    def __init__(self, parent: ttk.Frame):
        """
        Initialize the progress frame.

        Args:
            parent: Parent frame
        """
        self.parent = parent
        self.progress_var: Optional[tk.DoubleVar] = None
        self.progress_bar: Optional[ttk.Progressbar] = None
        self.status_label: Optional[ttk.Label] = None
        self._create_frame()

    def _create_frame(self) -> None:
        """Create the progress display frame."""
        progress_frame = ttk.LabelFrame(self.parent, text="Progress", padding="5")
        progress_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        progress_frame.columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame, variable=self.progress_var, maximum=100
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 5))

        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=1, column=0, sticky=tk.W)

    def update_progress(self, value: float, status: Optional[str] = None) -> None:
        """Update progress bar and status."""
        if self.progress_var and self.status_label:
            self.progress_var.set(value)
            if status is not None:
                self.status_label.config(text=status)

    def set_status(self, status: str) -> None:
        """Update status label."""
        if self.status_label:
            self.status_label.config(text=status)
