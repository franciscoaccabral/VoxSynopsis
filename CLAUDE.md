# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VoxSynopsis is a Python desktop application for high-quality audio recording and automatic transcription using FastWhisper. The application features a PyQt5 GUI that allows users to record audio in continuous 60-second chunks, apply post-processing, and transcribe both audio (.wav) and video (.mp4) files.

## Key Commands

### Running the Application
```bash
python vox_synopsis_fast_whisper.py
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Testing
```bash
python -m pytest Tests/
```

### Code Quality
```bash
# Format code with ruff
ruff format .

# Lint code with ruff
ruff check .

# Type checking with pyright
pyright
```

## Architecture

### Modular Structure

The application has been restructured into a modular architecture with clear separation of concerns:

```
VoxSynopsis/
├── vox_synopsis_fast_whisper.py    # Backward compatibility wrapper (32 lines)
├── core/                           # Core application modules
│   ├── __init__.py                 # Module initialization
│   ├── main.py                     # Application entry point
│   ├── config.py                   # Configuration management
│   ├── cache.py                    # FFmpeg caching system
│   ├── main_window.py              # Main application window
│   ├── recording.py                # Audio recording thread
│   ├── transcription.py            # FastWhisper transcription thread
│   └── settings_dialog.py          # Settings configuration dialog
├── ui_vox_synopsis.py              # UI layout definition
├── style.qss                       # Qt stylesheet
└── config.json                     # Runtime configuration
```

### Core Components

- **Wrapper**: `vox_synopsis_fast_whisper.py` - Maintains backward compatibility (reduced from 1605 to 32 lines)
- **Core Package**: `core/` - Modular components with focused responsibilities
- **UI Definition**: `ui_vox_synopsis.py` - Separates UI layout from business logic using PyQt5
- **Styling**: `style.qss` - Qt stylesheet for application appearance
- **Configuration**: `config.json` - FastWhisper model settings and processing parameters

### Core Modules

- **core/main.py**: Application entry point and initialization
- **core/config.py**: Configuration management with ConfigManager class
- **core/cache.py**: FileCache and AudioFileInfo for FFmpeg optimization
- **core/main_window.py**: AudioRecorderApp main application class
- **core/recording.py**: RecordingThread for continuous audio capture
- **core/transcription.py**: TranscriptionThread for FastWhisper processing
- **core/settings_dialog.py**: FastWhisperSettingsDialog configuration interface

### Key Classes

- **AudioRecorderApp**: Main application window with device management and UI coordination
- **RecordingThread**: Handles continuous audio recording in 60-second chunks with real-time processing
- **TranscriptionThread**: Manages FastWhisper model loading and batch transcription of audio/video files
- **FastWhisperSettingsDialog**: Configuration interface for FastWhisper parameters (model size, device, VAD, etc.)
- **ConfigManager**: Persistent configuration management with JSON backend
- **FileCache**: FFmpeg operation caching for performance optimization

### Threading Architecture

The application uses QThread for:
- Audio recording (non-blocking continuous capture)
- Transcription processing (CPU/GPU intensive FastWhisper operations)
- Resource monitoring (real-time system metrics)

### Audio Processing Pipeline

1. **Recording**: Continuous 60-second chunks at 48kHz
2. **Post-processing**: Optional noise reduction and normalization
3. **Video handling**: MP4 files are converted to accelerated WAV (1.25x speed)
4. **Transcription**: FastWhisper with VAD (Voice Activity Detection) filtering
5. **Output**: Individual and compiled transcription files

## Configuration

### FastWhisper Settings (config.json)
- Model sizes: tiny, base, small, medium, large-v3
- Device: cpu, cuda (GPU acceleration)
- Compute types: int8, float16, float32 (affects speed/memory)
- VAD filtering for silence detection
- Language, temperature, beam search parameters

### Hardware Detection
The application includes automatic hardware analysis to suggest optimal FastWhisper configurations based on available CPU/GPU resources.

## Dependencies

Core libraries:
- PyQt5: Desktop GUI framework
- sounddevice: Audio I/O operations
- faster-whisper: Optimized Whisper transcription
- noisereduce: Audio post-processing
- torch: ML backend for FastWhisper
- psutil: System resource monitoring

## File Structure

```
VoxSynopsis/
├── core/                           # Modular application core
│   ├── __init__.py                 # Package initialization
│   ├── main.py                     # Entry point (18 lines)
│   ├── config.py                   # Configuration management (65 lines)
│   ├── cache.py                    # FFmpeg caching (61 lines)
│   ├── main_window.py              # Main window logic (292 lines)
│   ├── recording.py                # Recording thread (131 lines)
│   ├── transcription.py            # Transcription thread (564 lines)
│   └── settings_dialog.py          # Settings dialog (329 lines)
├── Tests/                          # Unit tests for core components
├── Tunning/                        # Performance optimization scripts and results
├── docs/                           # Generated documentation
├── gravacoes/                      # Default recording output directory
├── vox_synopsis_fast_whisper.py    # Backward compatibility wrapper
├── ui_vox_synopsis.py              # UI layout definition
├── style.qss                       # Qt stylesheet
├── config.json                     # Runtime configuration
├── requirements.txt                # Python dependencies
└── pyproject.toml                  # Project configuration
```

## Performance Optimizations

### Cache System
- **FileCache**: Armazena durações de arquivos para evitar chamadas FFmpeg repetidas
- **AudioFileInfo**: Metadados dos arquivos com verificação de modificação
- Cache é limpo automaticamente ao parar transcrição

### Parallel Processing
- **ThreadPoolExecutor**: Processamento paralelo de extração de áudio
- **Concurrent chunk acceleration**: Acelera múltiplos chunks simultaneamente
- **MAX_WORKERS**: Limite dinâmico baseado no número de CPUs disponíveis

### Memory Optimization
- **Smart file filtering**: Evita reprocessamento de arquivos já processados
- **Streaming approach**: Reduz uso de memória durante processamento
- **Automatic cleanup**: Remove arquivos intermediários após processamento

### Configuration
- `parallel_processes`: Número de processos paralelos (padrão: min(2, CPU//2))
- `cpu_threads`: Threads para FastWhisper (padrão: núcleos físicos)
- `max_workers`: Limite de workers para ThreadPoolExecutor

## Development Notes

### Modular Architecture Benefits
- **Separation of Concerns**: Each module has a single, well-defined responsibility
- **Maintainability**: Code is easier to understand, modify, and debug
- **Testability**: Individual components can be tested in isolation
- **Reusability**: Modules can be imported and used independently
- **Scalability**: New features can be added without affecting existing code

### Technical Requirements
- The application expects FFmpeg to be installed and available in PATH
- GPU acceleration requires CUDA-compatible PyTorch installation
- Audio processing is optimized for speech transcription (48kHz, noise reduction)
- The UI is designed to be responsive during long transcription operations
- Performance improvements include 2-4x faster processing and 40-60% less memory usage

### Configuration Management
- **ConfigManager** class handles all application settings
- **model_size** key used for FastWhisper model selection (tiny, base, small, medium, large-v2, large-v3)
- **device** setting supports "cpu" and "cuda" for hardware acceleration
- **compute_type** options include "int8", "float16", "float32", "int8_float16"
- Automatic config.json generation with sensible defaults

### Import Strategy
- **Backward Compatibility**: Original `vox_synopsis_fast_whisper.py` continues to work
- **Modular Imports**: Can import specific components from `core` package
- **Clean Dependencies**: Each module only imports what it needs
- **Relative Imports**: Core modules use relative imports for internal dependencies

### Error Handling
- **Configuration Keys**: All settings have fallback defaults to prevent KeyError
- **Model Loading**: Graceful handling of missing or invalid model configurations
- **FFmpeg Integration**: Robust error handling for external process calls
- **Thread Safety**: Proper cleanup and resource management in threading components