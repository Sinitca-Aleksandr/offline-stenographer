# Offline Stenographer

A modern, privacy-focused GUI application for creating accurate transcripts from video files using WhisperX with a Docker backend.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://python.org)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![Docker](https://img.shields.io/badge/Backend-Docker-orange.svg)](https://docker.com)
[![WhisperX](https://img.shields.io/badge/AI-WhisperX-red.svg)](https://github.com/m-bain/whisperX)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-yellow.svg)](https://opensource.org/licenses/Apache-2.0)

> **Privacy-First Transcription**: All processing happens locally in Docker containers - no data leaves your machine

## Features

- **Professional GUI**: Clean, intuitive Tkinter interface
- **Multiple Video Formats**: Support for MP4, AVI, MKV, MOV, and more
- **Speaker Diarization**: Automatic speaker identification and labeling
- **Multiple Output Formats**: Export as TXT, Markdown, or DOCX
- **GPU Acceleration**: Automatic CUDA detection for faster processing
- **Real-time Progress**: Live progress updates during transcription
- **Offline Processing**: All processing happens locally via Docker
- **Configurable Settings**: GUI-based configuration for all WhisperX options

## Requirements

### System Requirements
- **Python 3.12+**
- **Docker Desktop** (for WhisperX container)
- **FFmpeg** (for audio/video processing)
- **8GB RAM** minimum, 16GB recommended
- **NVIDIA GPU** (optional, for faster processing)

### Supported File Formats

#### Video Formats
- **MP4** (H.264, H.265, AV1)
- **AVI** (various codecs)
- **MKV** (Matroska)
- **MOV** (QuickTime)
- **WMV** (Windows Media Video)
- **FLV** (Flash Video)
- **WebM** (VP8, VP9)

#### Audio Formats
- **MP3** (MPEG Audio Layer 3)
- **WAV** (Waveform Audio)
- **M4A** (MPEG-4 Audio)
- **FLAC** (Free Lossless Audio Codec)
- **OGG** (Ogg Vorbis)
- **AAC** (Advanced Audio Coding)
- **WMA** (Windows Media Audio)

#### Requirements
- Files must contain an **audio track**
- Minimum audio quality: **8kHz sampling rate**
- Recommended: **16kHz+ for better accuracy**

### Performance Expectations

| Video Length | CPU Processing | GPU Processing (RTX 30xx+) |
|-------------|----------------|---------------------------|
| 5 minutes   | ~2-3 minutes  | ~30 seconds - 1 minute   |
| 30 minutes  | ~10-15 minutes| ~2-4 minutes             |
| 1 hour      | ~25-40 minutes| ~5-8 minutes             |
| 2 hours     | ~50-80 minutes| ~10-15 minutes           |

> **Note**: Processing times vary based on model size, audio quality, and system specifications. GPU acceleration provides 5-10x speedup with WhisperX large models.

## Installation

### Prerequisites

#### Installing FFmpeg

Before using `ffmpeg-python`, FFmpeg must be installed and accessible via the `$PATH` environment variable.

There are a variety of ways to install FFmpeg, such as the [official download links](https://ffmpeg.org/download.html), or using your package manager of choice (e.g. `sudo apt install ffmpeg` on Debian/Ubuntu, `brew install ffmpeg` on OS X, etc.).

Regardless of how FFmpeg is installed, you can check if your environment path is set correctly by running the `ffmpeg` command from the terminal, in which case the version information should appear, as in the following example (truncated for brevity):

```
$ ffmpeg
ffmpeg version 4.2.4-1ubuntu0.1 Copyright (c) 2000-2020 the FFmpeg developers
  built with gcc 9 (Ubuntu 9.3.0-10ubuntu2)
```

> **Note**: The actual version information displayed here may vary from one system to another; but if a message such as `ffmpeg: command not found` appears instead of the version information, FFmpeg is not properly installed.

### Installation Methods

#### Method 1: From PyPI (Recommended)

```bash
pip install offline-stenographer
```

#### Method 2: From Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Sinitca-Aleksandr/offline-stenographer.git
   cd offline-stenographer
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

#### Method 3: Development Setup

For contributors and advanced users:

```bash
git clone https://github.com/Sinitca-Aleksandr/offline-stenographer.git
cd offline-stenographer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

## Quick Start

### Step 1: Initial Setup

1. **Launch the application:**
   ```bash
   offline-stenographer
   ```

2. **Set up HuggingFace token (required for speaker diarization):**
   - Navigate to: Settings → WhisperX Configuration
   - Click the "Get HuggingFace Token" link to create your token
   - Click "Accept Model Licenses" to access pyannote models
   - Enter your token in the configuration dialog

   > **Note**: Speaker diarization requires a [HuggingFace token](https://huggingface.co/settings/tokens) and acceptance of pyannote model licenses.

### Step 2: Process Your First Video

3. **Select a video file:**
   - Click "Browse..." or use `Ctrl+O`
   - Supported formats: MP4, AVI, MKV, MOV, WMV, FLV, WebM
   - Files must contain an audio track

4. **Configure settings (optional):**
   - Model: Choose from `tiny`, `base`, `small`, `medium`, `large-v3`
   - Language: Auto-detection or select specific language
   - Device: CUDA (GPU) or CPU processing
   - Speaker Diarization: Enable for automatic speaker identification

5. **Start transcription:**
   - Click "Start Transcription"
   - Monitor real-time progress in the progress bar
   - View detailed logs in the log area
   - Processing happens in background Docker container

6. **Export results:**
   - Select output format: Plain Text (.txt), Markdown (.md), or Word (.docx)
   - Files are automatically saved to your chosen location
   - Transcript includes timestamps and speaker identification (if enabled)

### Example Output Formats

**Plain Text:**
```
[00:00:00] Speaker 1: Hello, welcome to our meeting today.
[00:00:03] Speaker 2: Thank you for joining us.
```

**Markdown:**
```markdown
### Transcription

**Speaker 1** (00:00:00): Hello, welcome to our meeting today.

**Speaker 2** (00:00:03): Thank you for joining us.
```

## Configuration

### GUI Configuration
All settings can be configured through the user-friendly GUI:

- **Model Selection**: tiny, base, small, medium, large-v1/v2/v3
- **Language**: Auto-detection or specific language selection
- **Device**: CUDA (GPU) or CPU processing
- **Speaker Diarization**: Enable/disable automatic speaker detection
- **Performance**: Batch size optimization

### Advanced Settings
- **HuggingFace Token**: One-click setup with direct links to token page and license acceptance
- **Speaker Diarization**: Visual status indicator for token configuration
- **Batch Size**: Optimize for your hardware
- **Processing Parameters**: Fine-tune for specific use cases

## Troubleshooting

### Common Issues and Solutions

#### 1. Docker Issues

**Problem**: `Docker command not found` or Docker Desktop not starting
```
# Check if Docker is installed and running
docker --version
docker info

# On Windows, ensure Docker Desktop is running
# On Linux, start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

**Problem**: Permission denied when accessing Docker
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Then logout and login again
```

#### 2. GPU Acceleration Issues

**Problem**: GPU not detected or CUDA out of memory
```bash
# Check GPU availability
nvidia-smi

# Test Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base-ubuntu20.04 nvidia-smi
```

**Solutions**:
- Ensure **NVIDIA drivers 470+** are installed
- Update Docker Desktop to latest version
- Enable GPU support in Docker settings
- Reduce batch size in application settings
- Use smaller WhisperX model (tiny/base instead of large)

#### 3. Speaker Diarization Problems

**Problem**: Speaker identification fails or models won't download

**Step 1**: Get HuggingFace token
- Visit [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
- Create new token with **read permissions**
- Copy token to application settings

**Step 2**: Accept model licenses
- Visit [https://huggingface.co/pyannote/speaker-diarization](https://huggingface.co/pyannote/speaker-diarization)
- [https://huggingface.co/pyannote/segmentation](https://huggingface.co/pyannote/segmentation)
- Accept the terms and conditions

**Problem**: Network timeout during model download
```bash
# Test internet connection
ping huggingface.co
```

#### 4. Memory and Performance Issues

**Problem**: Out of memory errors during processing

**Solutions**:
- **Use smaller model**: `tiny` or `base` instead of `large-v3`
- **Close other applications** to free up RAM
- **Enable GPU acceleration** for better memory efficiency
- **Process shorter videos** (split long videos if needed)

**Problem**: Slow processing times
```bash
# Monitor system resources
htop  # or Task Manager on Windows

# Check GPU utilization
nvidia-smi -l 1
```

#### 5. Audio/Video Processing Issues

**Problem**: "No audio track found" or "Unsupported format"

**Check audio track**:
```bash
# Analyze media file
ffprobe input_video.mp4

# Extract audio track for testing
ffmpeg -i input_video.mp4 -vn -acodec copy audio.m4a
```

**Supported audio codecs**:
- AAC, MP3, Opus (recommended)
- PCM, FLAC (uncompressed)
- Vorbis, WMA (may have issues)

#### 6. Application Startup Issues

**Problem**: `Module not found` or import errors
```bash
# Verify Python version
python --version  # Should be 3.12+

# Check if package is installed
pip list | grep offline-stenographer

# Reinstall if necessary
pip uninstall offline-stenographer
pip install offline-stenographer
```

### Getting Additional Help

1. **Check application logs**: Look in the GUI log panel for detailed error messages
2. **Docker logs**: `docker logs <container_id>` for container-specific issues
3. **System requirements**: Verify all prerequisites are met
4. **Create GitHub issue**: Include system info, error logs, and steps to reproduce

### Performance Optimization Tips

- **GPU acceleration**: 5-10x faster processing with NVIDIA GPUs
- **Model selection**: Choose appropriate model size for your accuracy needs
- **Batch processing**: Process multiple files in sequence for efficiency
- **Audio quality**: Higher quality audio = better transcription accuracy
- **Language specification**: Set target language for better accuracy

## Contributing

We welcome contributions! Please see our detailed [CONTRIBUTION.md](CONTRIBUTION.md) file for comprehensive guidelines on:

- Development setup and environment configuration
- Architecture and technical details
- Development workflow and best practices
- Code style and formatting standards
- Testing requirements
- Pull request process
- Commit message guidelines

## License

Apache License Version 2.0 - see [LICENSE](LICENSE) file for details.

## Architecture Overview

### System Architecture
```
┌─────────────────────────────────────────────────┐
│                GUI Layer (Tkinter)              │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │  File       │ │  Progress   │ │  Export     │ │
│ │  Selection  │ │  Display    │ │  Options    │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────┬───────────────────────────────┘
                  │ HTTP/RPC
                  ▼
┌─────────────────────────────────────────────────┐
│            Processing Layer                     │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │  Docker     │ │  Video      │ │  Export     │ │
│ │  Manager    │ │  Processor  │ │  Manager    │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────┬───────────────────────────────┘
                  │ Docker API
                  ▼
┌─────────────────────────────────────────────────┐
│           WhisperX Container                    │
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│ │Transcription│ │Speaker      │ │Audio        │ │
│ │             │ │Diarization  │ │Extraction   │ │
│ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────┘
```

### Data Flow
1. **Input**: User selects video file through GUI
2. **Preprocessing**: Extract audio track using FFmpeg
3. **Processing**: Send audio to WhisperX Docker container
4. **Analysis**: Perform transcription and speaker diarization
5. **Formatting**: Convert to user-selected output format
6. **Output**: Save transcript file to specified location

### Security & Privacy
- **Local Processing**: All data remains on your machine
- **Container Isolation**: WhisperX runs in isolated Docker container
- **No Data Upload**: Internet only used for model downloads
- **Temporary Files**: Automatic cleanup after processing

## Support

For support and questions:
- Create an issue on GitHub
- Check existing documentation
- Review troubleshooting guide
- Join our community discussions
