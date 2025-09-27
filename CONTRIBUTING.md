# Contributing to Offline Stenographer

Thank you for your interest in contributing to Offline Stenographer! This document provides guidelines for contributing to the project.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- Poetry (for dependency management)
- Git
- Pre-commit hooks (for code quality)

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/offline-stenographer.git
   cd offline-stenographer
   ```

3. **Install dependencies** using Poetry:
   ```bash
   poetry install --with dev
   ```

4. **Set up pre-commit hooks**:
   ```bash
   pre-commit install
   ```

5. **Activate the virtual environment**:
   ```bash
   poetry shell
   ```

### IDE Setup Recommendations

- **VSCode**: Install Python, Pylint, and Pre-commit extensions
- **PyCharm**: Enable Black, isort, and pytest integration
- **General**: Configure your editor to format on save using Black

## Development Workflow

### Making Changes

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards

3. **Run tests** to ensure your changes don't break anything:
   ```bash
   python -m pytest
   ```

4. **Format your code** using the pre-commit hooks:
   ```bash
   pre-commit run --all-files
   ```

5. **Commit your changes** with a descriptive commit message:
   ```bash
   git add .
   git commit -m "Add: brief description of your changes"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Create a Pull Request** on GitHub

### Commit Message Guidelines

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests after the first line

## Code Style

### Python Code Style

This project uses:
- **Black** for code formatting
- **isort** for import sorting
- **trailing-whitespace** and **end-of-file-fixer** for whitespace management

All code is automatically formatted using pre-commit hooks. Please ensure your code follows these standards:

- 88 character line length
- Double quotes for strings
- Trailing comma on multi-line structures
- Sorted imports

### Documentation

- Update docstrings for new functions/classes
- Add comments for complex logic
- Update README.md if adding new features
- Update this CONTRIBUTION.md if changing contribution process
- Maintain the `memory-bank/` directory with project context and decisions

### Local Development Tips

- Use `poetry run offline-stenographer` to test your changes
- Check logs in the GUI for debugging information
- Test with different video formats (MP4, AVI, MOV)
- Verify Docker is running for WhisperX functionality
- Use the configuration dialog to test different settings

## Testing

- Write tests for new functionality
- Ensure all existing tests pass
- Test edge cases and error conditions
- Update test files in the appropriate directory

## Pull Request Process

1. **Ensure CI passes** - All GitHub Actions must pass
2. **Update documentation** - Update README and other docs as needed
3. **Add tests** - Include tests for new functionality
4. **Follow naming conventions** - Use descriptive branch names
5. **Request review** - Ask for review from maintainers

## Reporting Issues

- Use the GitHub issue tracker for bug reports and feature requests
- Include detailed information about your environment
- Provide steps to reproduce issues
- Use issue templates when available

## Getting Help

- Check the README.md for project documentation
- Search existing issues for similar problems
- Ask questions in GitHub Discussions

## License

By contributing, you agree that your contributions will be licensed under the same license as the original project.

## Architecture

### Technology Stack
- **Frontend**: Tkinter GUI (cross-platform)
- **Backend**: WhisperX in Docker container
- **Processing**: Docker SDK for Python
- **Audio/Video**: FFmpeg integration
- **Documents**: python-docx for Word export

### Project Structure
```
offline-stenographer/
├── offline_stenographer/          # Main package
│   ├── __init__.py               # Package metadata
│   ├── constants.py              # Application constants
│   ├── main.py                   # Entry point
│   ├── gui/                      # GUI components
│   │   ├── __init__.py
│   │   ├── app.py               # Main application window
│   │   └── widgets/             # Reusable UI components
│   │       ├── __init__.py
│   │       ├── about_dialog.py
│   │       ├── configuration_dialog.py
│   │       ├── control_frame.py
│   │       ├── export_dialog.py
│   │       ├── file_selection_frame.py
│   │       ├── log_frame.py
│   │       ├── menu_bar.py
│   │       ├── output_format_frame.py
│   │       └── progress_frame.py
│   ├── processing/               # Core processing logic
│   │   ├── __init__.py
│   │   ├── config_manager.py    # Configuration handling
│   │   ├── export_manager.py    # Export functionality
│   │   ├── formatters.py        # Output formatting
│   │   ├── transcription_service.py  # WhisperX integration
│   │   ├── type_hints.py        # Type definitions
│   │   └── video_processor.py   # Video processing
│   └── utils/                   # Utility modules
│       ├── __init__.py
│       └── url_utils.py        # URL handling utilities
├── memory-bank/                   # Documentation
├── pyproject.toml                 # Poetry configuration
├── config.env                     # Configuration template
├── .pre-commit-config.yaml       # Pre-commit hooks config
├── pytest.ini                    # Pytest configuration
├── tests/                        # Test suite
└── README.md                      # Project overview
```

### Key Components

#### Main Entry Point (`main.py`)
- Application entry point and initialization
- Coordinates GUI and processing components
- Handles application lifecycle

#### GUI Components (`gui/`)
- **app.py**: Main application window and overall layout
- **widgets/**: Modular UI components including:
  - `file_selection_frame.py`: File/directory selection interface
  - `output_format_frame.py`: Output format configuration
  - `control_frame.py`: Playback and processing controls
  - `progress_frame.py`: Progress tracking and status updates
  - `log_frame.py`: Logging and error display
  - `menu_bar.py`: Application menu and settings
  - `configuration_dialog.py`: Settings and preferences
  - `export_dialog.py`: Export options and configuration
  - `about_dialog.py`: Application information

#### Processing Components (`processing/`)
- **transcription_service.py**: Core WhisperX integration and Docker management
- **video_processor.py**: Video file processing and frame extraction
- **config_manager.py**: Application configuration and settings management
- **export_manager.py**: Export functionality for different formats
- **formatters.py**: Text formatting and output processing
- **type_hints.py**: Type definitions and interfaces

#### Utility Components (`utils/`)
- **url_utils.py**: URL validation and processing utilities

#### Configuration and Tests
- **constants.py**: Application-wide constants and configuration
- **tests/**: Comprehensive test suite with pytest
- **memory-bank/**: Project documentation and context management



---

Thank you for contributing to Offline Stenographer!
