"""
Log frame widget for the Offline Stenographer application.
"""

import tkinter as tk
from tkinter import ttk

from offline_stenographer.constants import UIConfig


class LogFrame:
    """Log display component."""

    def __init__(self, parent: ttk.Frame):
        """
        Initialize the log frame.

        Args:
            parent: Parent frame
        """
        self.parent = parent
        self.log_text: Optional[tk.Text] = None
        self._create_frame()

    def _create_frame(self) -> None:
        """Create the log display frame."""
        log_frame = ttk.LabelFrame(self.parent, text="Log", padding="5")
        log_frame.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0)
        )
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_frame, height=UIConfig.LOG_TEXT_HEIGHT, wrap=tk.WORD, state=tk.DISABLED
        )
        log_scrollbar = ttk.Scrollbar(
            log_frame, orient=tk.VERTICAL, command=self.log_text.yview
        )
        self.log_text.configure(yscrollcommand=log_scrollbar.set)

        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

    def add_message(self, message: str) -> None:
        """Add a message to the log."""
        if self.log_text:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
            self.log_text.config(state=tk.DISABLED)
