# Video Transcription GUI - Technical Context

## Core Technologies

### Primary Stack
- **Python 3.12+**: Main programming language
- **Tkinter**: Cross-platform GUI framework (built into Python)
- **Docker**: Containerization for WhisperX backend
- **WhisperX**: State-of-the-art speech recognition with diarization

### Audio/Video Processing
- **FFmpeg**: Video format conversion and audio extraction
- **docker**: Official Docker SDK for Python (preferred over subprocess)
- **python-docx**: Microsoft Word document generation
- **Pillow**: Image processing for GUI icons (if needed)

### Development Tools
- **VS Code**: Primary development environment
- **Git**: Version control
- **pytest**: Unit testing framework
- **black**: Code formatting
- **flake8**: Code linting
- **pyinstaller**: Application packaging (for distribution)

## Development Environment Setup

### Prerequisites
1. **Python 3.12+**: Download from python.org or use pyenv
2. **Docker Desktop**: For running WhisperX containers
3. **FFmpeg**: For audio/video format conversion
4. **Git**: For version control

### Installation Steps
```bash
# 1. Clone repository
git clone https://github.com/Sinitca-Aleksandr/offline-stenographer.git
cd offline-stenographer

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Pull WhisperX Docker image
sudo docker pull ghcr.io/jim60105/whisperx:latest

# 5. Set up Hugging Face token for diarization
# Get token from: https://huggingface.co/settings/tokens
# Accept licenses for pyannote models
```

### Configuration
Create `config.env` file with:
```env
# HuggingFace token for diarization
HF_TOKEN=your_token_here

# Whisper model (tiny, base, small, medium, large-v3)
WHISPER_MODEL=large-v3

# Language (ru, en, auto)
LANGUAGE=auto

# Processing settings
BATCH_SIZE=16
DEVICE=cuda
COMPUTE_TYPE=float16
```

## Docker Integration

### Container Management
- **Base Image**: `ghcr.io/jim60105/whisperx:latest`
- **Volume Mounting**: Mount input/output directories
- **GPU Support**: Automatic CUDA detection and mounting
- **Model Caching**: Persistent model storage in `~/.whisperx/`

### Docker SDK Integration
The application uses the official Docker SDK for Python (`docker` package) instead of subprocess for better integration:

```python
import docker

# Create Docker client
client = docker.from_env()

# Run WhisperX container with proper resource management
container = client.containers.run(
    image='ghcr.io/jim60105/whisperx:latest',
    command=whisperx_command,
    volumes={
        '/host/input': {'bind': '/audio', 'mode': 'ro'},
        '/host/output': {'bind': '/results', 'mode': 'rw'},
        '/host/cache': {'bind': '/models', 'mode': 'rw'}
    },
    environment={'HF_TOKEN': token},
    device_requests=[docker.types.DeviceRequest(device_ids=['0'], capabilities=[['gpu']])] if use_gpu else None,
    auto_remove=True,  # Auto-cleanup
    detach=True   # Run in background for progress monitoring
)
```

### Container Lifecycle
1. **Pull Image**: Ensure latest WhisperX image is available
2. **Create Container**: Configure volumes, environment, and GPU access
3. **Execute Processing**: Run with proper resource management
4. **Progress Monitoring**: Stream logs for real-time updates
5. **Cleanup**: Automatic container removal after completion

### GPU Acceleration
```python
# GPU-enabled container with proper device handling
gpu_config = docker.types.DeviceRequest(
    device_ids=['0'],  # Use first GPU
    capabilities=[['gpu']]
)

container = client.containers.run(
    'ghcr.io/jim60105/whisperx:latest',
    command=['whisperx', '--model', 'large-v3', '--device', 'cuda'],
    device_requests=[gpu_config],
    # ... other configuration
)
```

## File Format Support

### Input Formats
- **Video**: MP4, AVI, MKV, MOV, WMV, FLV, WebM
- **Audio**: MP3, WAV, M4A, FLAC, OGG, AAC, WMA
- **Requirements**: Must contain audio track

### Output Formats
- **Plain Text (.txt)**: Simple timestamped transcript
- **Markdown (.md)**: Rich formatting with speaker labels
- **Microsoft Word (.docx)**: Styled document with formatting

### Format Conversion Strategy
1. **Detection**: Identify input file format and codec
2. **Extraction**: Extract audio track using FFmpeg
3. **Validation**: Verify audio quality and format compatibility
4. **Processing**: Send to WhisperX for transcription
5. **Formatting**: Apply format-specific styling and structure

## Performance Optimization

### Memory Management
- **Streaming**: Process large files in chunks
- **Cleanup**: Remove temporary files after processing
- **Container Limits**: Set memory and CPU limits for Docker
- **Model Caching**: Reuse downloaded models across sessions

### Processing Speed
- **GPU Acceleration**: 10-50x faster than CPU for large models
- **Batch Size**: Optimize based on available GPU memory
- **Chunk Size**: Balance between accuracy and speed
- **Concurrent Processing**: Queue multiple files (future enhancement)

### Storage Considerations
- **Temporary Files**: Store in system temp directory
- **Model Cache**: `~/.whisperx/` (persistent across runs)
- **Output Directory**: User-configurable location
- **Cleanup Policies**: Automatic removal of old temporary files

## Development Workflow

### Code Organization
```
offline_stenographer/
├── gui/               # Tkinter interface components
│   ├── app.py         # Main GUI application window
│   └── components.py  # Reusable GUI components
├── processing/        # Business logic and processing
│   ├── config_manager.py    # Configuration management
│   ├── formatters.py        # Output format handlers
│   ├── transcription_service.py  # WhisperX integration
│   ├── type_hints.py        # Type definitions
│   └── video_processor.py   # Video/audio processing
├── constants.py       # Application constants
├── main.py           # Application entry point
├── tests/            # Unit and integration tests
├── memory-bank/      # Project documentation
├── requirements.txt  # Python dependencies
├── config.env        # Application configuration
└── README.md         # Setup instructions
```

### Development Commands
```bash
# Run application
python -m offline_stenographer.main

# Run tests
pytest tests/

# Format code
black offline_stenographer/

# Lint code
flake8 offline_stenographer/

# Build executable (future)
pyinstaller offline_stenographer.main --onefile --noconsole
```

## Deployment Considerations

### Distribution Methods
1. **Source Code**: Git repository with setup instructions
2. **PyInstaller**: Single executable for end users
3. **Docker Container**: Self-contained application image
4. **Conda Package**: Cross-platform package management

### Platform Support
- **Windows 10+**: Primary target platform
- **macOS 10.15+**: Secondary support
- **Linux**: Community support (Ubuntu/Debian)

### System Requirements
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB for application + models
- **GPU**: Optional, NVIDIA with CUDA support
- **Docker**: Latest stable version
