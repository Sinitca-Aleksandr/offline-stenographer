"""
Output format frame widget for the Offline Stenographer application.
"""

import tkinter as tk
from tkinter import ttk

from offline_stenographer.constants import AppConfig


class OutputFormatFrame:
    """Output format selection component."""

    def __init__(self, parent: ttk.Frame, output_var: tk.StringVar):
        """
        Initialize the output format frame.

        Args:
            parent: Parent frame
            output_var: StringVar for output format selection
        """
        self.parent = parent
        self.output_var = output_var
        self._create_frame()

    def _create_frame(self) -> None:
        """Create the output format selection frame."""
        format_frame = ttk.LabelFrame(self.parent, text="Output Format", padding="5")
        format_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        # Create radio buttons for each format
        for i, format_type in enumerate(AppConfig.OUTPUT_FORMATS):
            ttk.Radiobutton(
                format_frame,
                text=f"{format_type.upper()} (.{format_type})",
                variable=self.output_var,
                value=format_type,
            ).grid(row=0, column=i, sticky=tk.W, padx=(20 if i > 0 else 0, 0))
