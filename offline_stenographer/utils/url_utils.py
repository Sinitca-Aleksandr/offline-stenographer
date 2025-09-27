"""
URL utility functions for the Offline Stenographer application.
"""

import webbrowser
from typing import Callable, Optional


def open_url(url: str, log_message: Optional[Callable[[str], None]] = None) -> bool:
    """
    Open URL in default browser.

    Args:
        url: URL to open
        log_message: Optional callback function for logging messages

    Returns:
        bool: True if URL was opened successfully, False otherwise
    """
    try:
        webbrowser.open(url)
        if log_message:
            log_message(f"Opened URL: {url}")
        return True
    except Exception as e:
        error_msg = f"Failed to open URL {url}: {e}"
        if log_message:
            log_message(error_msg)
        return False
