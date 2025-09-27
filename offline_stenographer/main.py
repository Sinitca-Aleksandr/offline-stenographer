#!/usr/bin/env python3
"""
Offline Stenographer - Main Application Entry Point

A GUI application for creating transcripts from video files using
WhisperX (Docker) backend for transcription and diarization.
"""

from offline_stenographer.gui.app import create_app


def main():
    """Main entry point for the application."""
    try:
        app = create_app()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        raise


if __name__ == "__main__":
    main()
