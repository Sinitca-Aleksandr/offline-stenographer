"""
Control frame widget for the Offline Stenographer application.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ControlFrame:
    """Control buttons component."""

    def __init__(self, parent: ttk.Frame, callbacks: dict[str, Callable]):
        """
        Initialize the control frame.

        Args:
            parent: Parent frame
            callbacks: Dictionary of callback functions
        """
        self.parent = parent
        self.callbacks = callbacks
        self.transcribe_button: Optional[ttk.Button] = None
        self._create_frame()

    def _create_frame(self) -> None:
        """Create the control buttons frame."""
        button_frame = ttk.Frame(self.parent)
        button_frame.grid(row=3, column=0, columnspan=2, pady=(10, 0))

        self.transcribe_button = ttk.Button(
            button_frame,
            text="Start Transcription",
            command=self.callbacks.get("start_transcription"),
        )
        self.transcribe_button.grid(row=0, column=0, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="Cancel",
            command=self.callbacks.get("cancel_transcription"),
        ).grid(row=0, column=1, padx=(5, 0))

    def update_transcribe_button_state(self, enabled: bool) -> None:
        """Enable or disable the transcribe button."""
        if self.transcribe_button:
            state = tk.NORMAL if enabled else tk.DISABLED
            self.transcribe_button.config(state=state)
