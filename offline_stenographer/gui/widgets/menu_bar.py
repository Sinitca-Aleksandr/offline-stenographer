"""
Menu bar widget for the Offline Stenographer application.
"""

import tkinter as tk
from typing import Callable


class MenuBar:
    """Application menu bar component."""

    def __init__(self, root: tk.Tk, callbacks: dict[str, Callable]):
        """
        Initialize the menu bar.

        Args:
            root: The root Tk window
            callbacks: Dictionary of callback functions for menu commands
        """
        self.root = root
        self.callbacks = callbacks
        self._create_menu_bar()

    def _create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(
            label="Select Video File", command=self.callbacks.get("select_file")
        )
        file_menu.add_command(label="Exit", command=self.callbacks.get("quit"))

        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(
            label="WhisperX Configuration", command=self.callbacks.get("show_config")
        )

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.callbacks.get("show_about"))
