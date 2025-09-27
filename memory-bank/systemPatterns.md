# Video Transcription GUI - System Patterns

## Architecture Overview
The application follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────┐
│           GUI Layer (Tkinter)       │
│  ┌─────────────┐ ┌─────────────────┐ │
│  │ File Dialog │ │ Progress Display│ │
│  │ Selection   │ │                 │ │
│  └─────────────┘ └─────────────────┘ │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Processing Layer              │
│  ┌─────────────┐ ┌─────────────────┐ │
│  │Docker       │ │ File            │ │
│  │Manager      │ │ Formatters      │ │
│  └─────────────┘ └─────────────────┘ │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         WhisperX (Docker)            │
│  ┌─────────────┐ ┌─────────────────┐ │
│  │Transcription│ │ Speaker         │ │
│  │             │ │ Diarization     │ │
│  └─────────────┘ └─────────────────┘ │
└─────────────────────────────────────┘
```

## Key Design Patterns

### 1. Facade Pattern - Docker Integration
- **WhisperXDocker** class provides a simplified interface to complex Docker operations
- Hides Docker container lifecycle, volume mounting, and command execution details
- Provides clean API for transcription operations

### 2. Strategy Pattern - Output Formats
- **OutputFormatter** interface with concrete implementations:
  - **TextFormatter**: Plain text with timestamps
  - **MarkdownFormatter**: Rich formatting with speaker labels
  - **DocxFormatter**: Microsoft Word document with styling
- Easy to add new formats without changing core logic

### 3. Observer Pattern - Progress Updates
- **ProgressSubject** notifies multiple **ProgressObserver** instances
- GUI components subscribe to progress updates
- Decouples progress reporting from processing logic

### 4. Command Pattern - Processing Pipeline
- **TranscriptionCommand** encapsulates video processing workflow
- **AudioExtractionCommand** handles video-to-audio conversion
- **FormatConversionCommand** manages output formatting
- Enables queuing, undo operations, and pipeline management

## Component Architecture

### GUI Components
```
MainWindow
├── MenuBar
├── FileSelectionWidget
├── ProgressWidget
├── FormatSelectionWidget
├── StatusBar
└── OutputPreviewWidget (optional)
```

### Processing Components
```
TranscriptionService
├── DockerManager
├── VideoProcessor
├── AudioExtractor
├── WhisperXClient
└── OutputManager
```

### Data Flow
1. **Input**: User selects video file through GUI
2. **Preprocessing**: Video file → Audio extraction → Format validation
3. **Processing**: Audio → WhisperX Docker → Transcription + Diarization
4. **Post-processing**: Raw output → Format-specific processing → Final output
5. **Output**: Formatted file saved to user-selected location

## Error Handling Strategy
- **Validation Layer**: Input file validation before processing
- **Recovery Mechanisms**: Automatic retry for transient Docker failures
- **Graceful Degradation**: Continue without GPU if CUDA unavailable
- **User Feedback**: Clear error messages with actionable solutions
- **Logging**: Comprehensive logging for debugging and monitoring

## State Management
- **Application State**: Managed through central ApplicationModel
- **Processing State**: Tracked per file with status transitions
- **UI State**: Synchronized with processing state changes
- **Configuration State**: Persistent user preferences

## Performance Considerations
- **Asynchronous Processing**: Non-blocking GUI during long operations
- **Memory Management**: Streaming for large files, cleanup after processing
- **Caching**: Model caching in Docker volumes for faster subsequent runs
- **Resource Limits**: Docker container resource constraints
- **Progress Estimation**: Based on file size and historical performance

## Security Patterns
- **Container Isolation**: All processing in isolated Docker containers
- **Input Sanitization**: Validate file paths and formats
- **Resource Limits**: Prevent resource exhaustion attacks
- **No Network Access**: Offline processing by default
- **Temporary File Cleanup**: Secure deletion of intermediate files

## Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: Docker container communication
- **GUI Tests**: Tkinter interface testing with mocking
- **E2E Tests**: Full workflow testing with sample files
- **Performance Tests**: Load testing with various file sizes
