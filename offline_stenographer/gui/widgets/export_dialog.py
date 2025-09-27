#!/usr/bin/env python3
"""
Export Dialog Widget - Handles transcription export options

This module contains the export dialog widget for managing transcription result exports.
"""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class ExportDialog:
    """Dialog widget for handling transcription export options."""

    def __init__(self, parent, docker_result, callbacks):
        """Initialize the export dialog.

        Args:
            parent: Parent window
            docker_result: Result from Docker transcription service
            callbacks: Dictionary of callback functions
        """
        self.parent = parent
        self.docker_result = docker_result
        self.callbacks = callbacks

        # Create the dialog window
        self.window = tk.Toplevel(parent)
        self.window.title("Export Transcription Results")
        self.window.geometry("500x450")
        self.window.transient(parent)
        self.window.grab_set()

        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - self.window.winfo_reqwidth()) // 2
        y = (self.window.winfo_screenheight() - self.window.winfo_reqheight()) // 2
        self.window.geometry(f"+{x}+{y}")

        # Create UI components
        self._create_ui()

        # Set focus
        self.window.focus_set()

    def _create_ui(self):
        """Create the user interface components."""
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Export transcription results:",
            font=("TkDefaultFont", 12, "bold"),
        )
        title_label.pack(pady=(0, 20))

        # Raw results section
        self._create_raw_results_section(main_frame)

        # Formatted results section
        self._create_formatted_results_section(main_frame)

        # Buttons
        self._create_buttons(main_frame)

    def _create_raw_results_section(self, parent):
        """Create the raw results export section."""
        raw_frame = ttk.LabelFrame(
            parent, text="Raw Results (All WhisperX files)", padding="10"
        )
        raw_frame.pack(fill=tk.X, pady=(0, 15))

        # Raw results checkbox
        self.raw_var = tk.BooleanVar(value=False)
        raw_check = ttk.Checkbutton(
            raw_frame,
            text="Export all raw files (.txt, .json, .srt, .vtt, .tsv)",
            variable=self.raw_var,
        )
        raw_check.pack(anchor=tk.W)

        # Raw folder selection
        self.raw_folder_var = tk.StringVar()
        raw_folder_frame = ttk.Frame(raw_frame)
        raw_folder_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(raw_folder_frame, text="Folder:").pack(side=tk.LEFT)
        raw_folder_entry = ttk.Entry(
            raw_folder_frame, textvariable=self.raw_folder_var, width=30
        )
        raw_folder_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        raw_folder_entry.insert(
            0, str(Path.home() / "Documents" / "offline_stenographer_raw")
        )

        ttk.Button(
            raw_folder_frame,
            text="Browse...",
            command=self._browse_raw_folder,
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _create_formatted_results_section(self, parent):
        """Create the formatted results export section."""
        formatted_frame = ttk.LabelFrame(parent, text="Formatted Results", padding="10")
        formatted_frame.pack(fill=tk.X, pady=(0, 15))

        # Format variables
        self.txt_var = tk.BooleanVar(value=True)
        self.md_var = tk.BooleanVar(value=False)
        self.docx_var = tk.BooleanVar(value=False)

        # Format checkboxes
        formats_frame = ttk.Frame(formatted_frame)
        formats_frame.pack(fill=tk.X)

        ttk.Checkbutton(
            formats_frame, text="Plain Text (.txt)", variable=self.txt_var
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            formats_frame, text="Markdown (.md)", variable=self.md_var
        ).pack(anchor=tk.W)

        ttk.Checkbutton(
            formats_frame, text="Microsoft Word (.docx)", variable=self.docx_var
        ).pack(anchor=tk.W)

        # Formatted folder selection
        self.formatted_folder_var = tk.StringVar()
        formatted_folder_frame = ttk.Frame(formatted_frame)
        formatted_folder_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(formatted_folder_frame, text="Folder:").pack(side=tk.LEFT)
        formatted_folder_entry = ttk.Entry(
            formatted_folder_frame, textvariable=self.formatted_folder_var, width=25
        )
        formatted_folder_entry.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)
        formatted_folder_entry.insert(
            0, str(Path.home() / "Documents" / "offline_stenographer_formatted")
        )

        ttk.Button(
            formatted_folder_frame,
            text="Browse...",
            command=self._browse_formatted_folder,
        ).pack(side=tk.LEFT, padx=(5, 0))

    def _create_buttons(self, parent):
        """Create the dialog buttons."""
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(fill=tk.X, pady=(20, 0))

        export_button = ttk.Button(
            buttons_frame, text="Export Selected", command=self._export_all
        )
        export_button.pack(side=tk.RIGHT, padx=(5, 0))

        close_button = ttk.Button(
            buttons_frame, text="Close", command=self._close_window
        )
        close_button.pack(side=tk.RIGHT)

    def _browse_raw_folder(self):
        """Browse for raw results folder."""
        folder_selected = filedialog.askdirectory(title="Select folder for raw results")
        if folder_selected:
            self.raw_folder_var.set(folder_selected)

    def _browse_formatted_folder(self):
        """Browse for formatted results folder."""
        folder_selected = filedialog.askdirectory(
            title="Select folder for formatted results"
        )
        if folder_selected:
            self.formatted_folder_var.set(folder_selected)

    def _export_all(self):
        """Export both raw and formatted results."""
        self.window.destroy()

        # Export raw results if selected
        if self.raw_var.get() and self.raw_folder_var.get().strip():
            self.callbacks["export_raw"](
                self.docker_result, self.raw_folder_var.get().strip()
            )

        # Export formatted results if any format selected
        selected_formats = []
        if self.txt_var.get():
            selected_formats.append("txt")
        if self.md_var.get():
            selected_formats.append("md")
        if self.docx_var.get():
            selected_formats.append("docx")

        if selected_formats and self.formatted_folder_var.get().strip():
            self.callbacks["export_formatted"](
                self.docker_result,
                selected_formats,
                self.formatted_folder_var.get().strip(),
            )

    def _close_window(self):
        """Close export window without exporting."""
        self.window.destroy()

    def show(self):
        """Show the export dialog."""
        self.window.mainloop()
