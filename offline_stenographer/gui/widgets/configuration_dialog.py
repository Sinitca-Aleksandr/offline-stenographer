"""
Configuration dialog widget for the Offline Stenographer application.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Optional

from offline_stenographer.constants import AppConfig, UIConfig, URLs
from offline_stenographer.utils import open_url


class ConfigurationDialog:
    """WhisperX configuration dialog component."""

    def __init__(
        self, parent: tk.Tk, config_manager: Any, callbacks: dict[str, Callable]
    ):
        """
        Initialize the configuration dialog.

        Args:
            parent: Parent window
            config_manager: Configuration manager instance
            callbacks: Dictionary of callback functions
        """
        self.parent = parent
        self.config_manager = config_manager
        self.callbacks = callbacks
        self.token_status_label: Optional[ttk.Label] = None
        self._create_dialog()

    def _create_dialog(self) -> None:
        """Create the configuration dialog."""
        self.config_window = tk.Toplevel(self.parent)
        self.config_window.title("WhisperX Configuration")
        self.config_window.geometry("650x550")
        self.config_window.resizable(False, False)

        # Center the window
        self.config_window.transient(self.parent)
        self.config_window.grab_set()

        # Load current configuration
        if self.config_manager is None:
            messagebox.showerror("Error", "Configuration manager not available")
            return

        current_config = self.config_manager.load_config()

        # Configuration variables
        hf_token_var = tk.StringVar(value=current_config.whisperx.hf_token)
        model_var = tk.StringVar(value=current_config.whisperx.model)
        language_var = tk.StringVar(value=current_config.whisperx.language)
        device_var = tk.StringVar(value=current_config.whisperx.device)
        diarization_var = tk.BooleanVar(value=current_config.whisperx.diarization)
        batch_size_var = tk.StringVar(value=current_config.whisperx.batch_size)

        # Create notebook for organized settings
        notebook = ttk.Notebook(self.config_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self._create_basic_settings_tab(notebook, model_var, language_var, device_var)
        self._create_advanced_settings_tab(
            notebook, hf_token_var, diarization_var, batch_size_var
        )
        self._create_buttons(
            self.config_window,
            hf_token_var,
            model_var,
            language_var,
            device_var,
            diarization_var,
            batch_size_var,
        )

        # Auto-size window to fit content
        self.config_window.update_idletasks()
        req_width = self.config_window.winfo_reqwidth()
        req_height = self.config_window.winfo_reqheight()
        self.config_window.geometry(f"{req_width}x{req_height}")

        # Set focus on the window
        self.config_window.focus_set()

    def _create_url_handler(self, url: str) -> Callable[[], None]:
        """Create a URL handler that opens URL and shows error if failed."""

        def handler():
            log_message = self.callbacks.get("log_message")
            if not open_url(url, log_message):
                messagebox.showerror("Error", f"Failed to open URL: {url}")

        return handler

    def _create_basic_settings_tab(
        self,
        notebook: ttk.Notebook,
        model_var: tk.StringVar,
        language_var: tk.StringVar,
        device_var: tk.StringVar,
    ) -> None:
        """Create the basic settings tab."""
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text="Basic Settings")

        # Model selection
        model_frame = ttk.LabelFrame(basic_frame, text="Model", padding="5")
        model_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        model_frame.columnconfigure(1, weight=1)

        ttk.Label(model_frame, text="Whisper Model:").grid(row=0, column=0, sticky=tk.W)
        model_combo = ttk.Combobox(
            model_frame, textvariable=model_var, state="readonly"
        )
        model_combo["values"] = AppConfig.WHISPER_MODELS
        model_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))

        # Language selection
        lang_frame = ttk.LabelFrame(basic_frame, text="Language", padding="5")
        lang_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        lang_frame.columnconfigure(1, weight=1)

        ttk.Label(lang_frame, text="Language:").grid(row=0, column=0, sticky=tk.W)
        lang_combo = ttk.Combobox(
            lang_frame, textvariable=language_var, state="readonly"
        )
        lang_combo["values"] = AppConfig.SUPPORTED_LANGUAGES
        lang_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))

        # Device selection
        device_frame = ttk.LabelFrame(basic_frame, text="Device", padding="5")
        device_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        device_frame.columnconfigure(1, weight=1)

        ttk.Label(device_frame, text="Device:").grid(row=0, column=0, sticky=tk.W)
        device_combo = ttk.Combobox(
            device_frame, textvariable=device_var, state="readonly"
        )
        device_combo["values"] = AppConfig.DEVICE_OPTIONS
        device_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))

    def _create_advanced_settings_tab(
        self,
        notebook: ttk.Notebook,
        hf_token_var: tk.StringVar,
        diarization_var: tk.BooleanVar,
        batch_size_var: tk.StringVar,
    ) -> None:
        """Create the advanced settings tab."""
        advanced_frame = ttk.Frame(notebook)
        notebook.add(advanced_frame, text="Advanced Settings")

        # HuggingFace token
        token_frame = ttk.LabelFrame(
            advanced_frame,
            text="HuggingFace Token (Required for Speaker Diarization)",
            padding="5",
        )
        token_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        token_frame.columnconfigure(1, weight=1)

        # Instructions
        instruction_frame = ttk.Frame(token_frame)
        instruction_frame.grid(
            row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5)
        )
        instruction_frame.columnconfigure(1, weight=1)

        ttk.Label(
            instruction_frame, text="1. Get token:", font=("TkDefaultFont", 9, "bold")
        ).grid(row=0, column=0, sticky=tk.W)
        ttk.Button(
            instruction_frame,
            text="huggingface.co/settings/tokens",
            command=self._create_url_handler(URLs.HUGGINGFACE_TOKENS),
        ).grid(row=0, column=1, sticky=tk.W, padx=(5, 0))

        ttk.Label(
            instruction_frame,
            text="2. Accept model terms:",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=1, column=0, sticky=tk.W)

        # Create frame for model buttons
        models_frame = ttk.Frame(instruction_frame)
        models_frame.grid(row=1, column=1, sticky=tk.W, padx=(5, 0))
        models_frame.columnconfigure(1, weight=1)

        ttk.Button(
            models_frame,
            text="pyannote/segmentation-3.0",
            command=self._create_url_handler(URLs.PYANNOTE_SEGMENTATION),
        ).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(models_frame, text="and").grid(
            row=0, column=1, sticky=tk.W, padx=(5, 0)
        )
        ttk.Button(
            models_frame,
            text="pyannote/speaker-diarization-3.1",
            command=self._create_url_handler(URLs.PYANNOTE_DIARIZATION),
        ).grid(row=0, column=2, sticky=tk.W)

        ttk.Label(
            instruction_frame,
            text="3. Enter token below:",
            font=("TkDefaultFont", 9, "bold"),
        ).grid(row=2, column=0, sticky=tk.W)
        token_entry = ttk.Entry(
            token_frame, textvariable=hf_token_var, show="*", width=40
        )
        token_entry.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=(5, 0), pady=(5, 0)
        )

        # Status indicator
        self.token_status_label = ttk.Label(
            token_frame,
            text="⚠️ Token required for speaker diarization",
            foreground="orange",
        )
        self.token_status_label.grid(row=4, column=0, columnspan=2, sticky=tk.W)

        # Update status when token changes
        def update_token_status(*args):
            token = hf_token_var.get().strip()
            if token:
                self.token_status_label.config(
                    text="✅ Token configured", foreground="green"
                )
            else:
                self.token_status_label.config(
                    text="⚠️ Token required for speaker diarization", foreground="orange"
                )

        update_token_status()
        hf_token_var.trace("w", update_token_status)

        # Diarization settings
        diarization_frame = ttk.LabelFrame(
            advanced_frame, text="Speaker Diarization", padding="5"
        )
        diarization_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )

        diarization_check = ttk.Checkbutton(
            diarization_frame,
            text="Enable speaker diarization",
            variable=diarization_var,
        )
        diarization_check.grid(row=0, column=0, sticky=tk.W)

        # Performance settings
        perf_frame = ttk.LabelFrame(advanced_frame, text="Performance", padding="5")
        perf_frame.grid(
            row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        perf_frame.columnconfigure(1, weight=1)

        ttk.Label(perf_frame, text="Batch Size:").grid(row=0, column=0, sticky=tk.W)
        batch_combo = ttk.Combobox(
            perf_frame, textvariable=batch_size_var, state="readonly", width=10
        )
        batch_combo["values"] = AppConfig.BATCH_SIZE_OPTIONS
        batch_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))

    def _create_buttons(
        self,
        parent: tk.Widget,
        hf_token_var: tk.StringVar,
        model_var: tk.StringVar,
        language_var: tk.StringVar,
        device_var: tk.StringVar,
        diarization_var: tk.BooleanVar,
        batch_size_var: tk.StringVar,
    ) -> None:
        """Create dialog buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        def save_config():
            """Save configuration settings."""
            try:
                if self.config_manager is None:
                    self.callbacks.get("log_message", lambda x: None)(
                        "Configuration manager not available"
                    )
                    messagebox.showerror("Error", "Configuration manager not available")
                    return

                # Create new WhisperX configuration with form values

                from offline_stenographer.processing.config_manager import (
                    WhisperXConfig,
                )

                new_whisperx_config = WhisperXConfig(
                    hf_token=hf_token_var.get(),
                    model=model_var.get(),
                    language=language_var.get(),
                    device=device_var.get(),
                    diarization=diarization_var.get(),
                    batch_size=batch_size_var.get(),
                )

                # Load current full configuration and update WhisperX settings
                current_config = self.config_manager.load_config()
                current_config.whisperx = new_whisperx_config

                # Save through ConfigurationManager
                success = self.config_manager.save_config(current_config)
                if success:
                    log_message = self.callbacks.get("log_message", lambda x: None)
                    log_message(
                        f"✅ Configuration saved: Model={new_whisperx_config.model}, Device={new_whisperx_config.device}"
                    )
                else:
                    messagebox.showerror(
                        "Save Failed", "Failed to save configuration to file"
                    )
                    return

                self.config_window.destroy()

            except Exception as e:
                error_msg = f"Error saving configuration: {e}"
                log_message = self.callbacks.get("log_message", lambda x: None)
                log_message(error_msg)
                messagebox.showerror("Error", error_msg)

        def reset_config():
            """Reset to default configuration."""
            model_var.set(UIConfig.DEFAULT_MODEL)
            language_var.set(UIConfig.DEFAULT_LANGUAGE)
            device_var.set(UIConfig.DEFAULT_DEVICE)
            diarization_var.set(UIConfig.DEFAULT_DIARIZATION)
            batch_size_var.set(UIConfig.DEFAULT_BATCH_SIZE)
            hf_token_var.set("")

        ttk.Button(button_frame, text="Save", command=save_config).grid(
            row=0, column=0, padx=(0, 5)
        )
        ttk.Button(button_frame, text="Reset", command=reset_config).grid(
            row=0, column=1, padx=(5, 0)
        )
        ttk.Button(
            button_frame, text="Cancel", command=self.config_window.destroy
        ).grid(row=0, column=2, padx=(5, 0))
