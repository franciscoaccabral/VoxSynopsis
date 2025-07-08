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

### Core Components

- **Main Application**: `vox_synopsis_fast_whisper.py` - Contains the main application logic, threading, and FastWhisper integration
- **UI Definition**: `ui_vox_synopsis.py` - Separates UI layout from business logic using PyQt5
- **Styling**: `style.qss` - Qt stylesheet for application appearance
- **Configuration**: `config.json` - FastWhisper model settings and processing parameters

### Key Classes

- **RecordingThread**: Handles continuous audio recording in 60-second chunks with real-time processing
- **TranscriptionThread**: Manages FastWhisper model loading and batch transcription of audio/video files
- **SettingsDialog**: Configuration interface for FastWhisper parameters (model size, device, VAD, etc.)
- **ResourceMonitor**: Tracks CPU and memory usage during operation

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

- `Tests/`: Unit tests for core components
- `Tunning/`: Performance optimization scripts and results
- `docs/`: Generated documentation
- `gravacoes/`: Default recording output directory

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

- The application expects FFmpeg to be installed and available in PATH
- GPU acceleration requires CUDA-compatible PyTorch installation
- Audio processing is optimized for speech transcription (48kHz, noise reduction)
- The UI is designed to be responsive during long transcription operations
- Performance improvements include 2-4x faster processing and 40-60% less memory usage