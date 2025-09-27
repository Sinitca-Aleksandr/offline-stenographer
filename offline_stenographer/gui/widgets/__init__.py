"""
GUI widgets subpackage for the Offline Stenographer application.
"""

from .about_dialog import AboutDialog
from .configuration_dialog import ConfigurationDialog
from .control_frame import ControlFrame
from .export_dialog import ExportDialog
from .file_selection_frame import FileSelectionFrame
from .log_frame import LogFrame
from .menu_bar import MenuBar
from .output_format_frame import OutputFormatFrame
from .progress_frame import ProgressFrame

__all__ = [
    "AboutDialog",
    "MenuBar",
    "FileSelectionFrame",
    "OutputFormatFrame",
    "ProgressFrame",
    "ControlFrame",
    "LogFrame",
    "ConfigurationDialog",
    "ExportDialog",
]
