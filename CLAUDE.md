# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VoxSynopsis is a Python desktop application for high-quality audio recording and automatic transcription using FastWhisper. The application features a PyQt5 GUI that allows users to record audio in continuous 60-second chunks, apply post-processing, and transcribe both audio (.wav) and video (.mp4) files.

## Key Commands

### Running the Application
```bash
python3 vox_synopsis_fast_whisper.py
```

### Installing Dependencies
```bash
# Use uv (requires pyproject.toml with [project] section)
uv venv .venv --python 3.11
uv add -r requirements.txt

# If uv fails, contact user for guidance - do not use pip without permission
```

### Running with Virtual Environment
```bash
# Easy script runner (recommended)
./run_voxsynopsis.sh

# Manual activation
source .venv/bin/activate && python3 vox_synopsis_fast_whisper.py
```

### Testing
```bash
python3 -m pytest Tests/
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
- torch + torchaudio: ML backend for FastWhisper with CUDA support
- psutil: System resource monitoring
- pynvml: NVIDIA GPU monitoring
- ctranslate2: High-performance inference engine
- scipy: Scientific computing for audio processing

## CUDA Acceleration

### 🚀 Intelligent CUDA Implementation (Janeiro 2025)

VoxSynopsis implementa aceleração CUDA inteligente, aplicando GPU acceleration apenas onde é tecnicamente possível e benéfico.

#### **CUDA Components**
- **FastWhisper GPU Processing**: Transcrição acelerada por GPU (2-5x speedup)
- **FFmpeg Video Decoding**: Decodificação de vídeo acelerada (H.264/HEVC)
- **Automatic Detection**: Detecção automática de capacidades CUDA
- **Graceful Fallback**: Fallback automático para CPU quando necessário

#### **Supported Hardware**
- **GTX 10xx Series**: Suporte `int8` para FastWhisper + decodificação de vídeo
- **RTX 20xx/30xx/40xx**: Suporte completo com `float16` e `int8_float16`
- **Professional Cards**: Suporte total para todas as funcionalidades

#### **Realistic CUDA Usage**
```python
# ✅ Operations using CUDA
- FastWhisper transcription (GPU processing)
- Video decoding (H.264/HEVC → audio extraction from MP4)

# ❌ Operations NOT using CUDA (CPU optimized)
- Audio chunking (audio-only, no video stream)
- Audio tempo changes (audio filters)
- Silence detection (audio filters)
- Pure audio processing operations
```

#### **Performance Gains**
- **FastWhisper**: 2-5x speedup com CUDA vs CPU
- **Video Decoding**: 2-3x mais rápido para extração de áudio de MP4
- **Audio Operations**: CPU multi-thread otimizado (sem CUDA, mas eficiente)
- **Overall**: Aceleração focada nas operações que realmente se beneficiam

#### **Auto-Configuration**
```python
# Configuração automática baseada no hardware
{
    "device": "cuda",                    # Detectado automaticamente
    "compute_type": "int8",              # Otimizado para hardware específico
    "model_size": "base",                # Baseado na VRAM disponível
    "enable_model_caching": true         # Cache GPU otimizado
}
```

#### **Interface Monitoring**
```
# Interface Status (realística)
🚀 CUDA (GTX 1050 Ti) | int8
⚡ Whisper: GPU | FFmpeg: Video only
🧵 Threads: 6

# GPU Monitoring (quando disponível)
GPU: [████████░░] 80% (GTX 1050 Ti, 65°C)
VRAM: [███░░░░░░░] 30% (1.2GB / 4.0GB)
```

#### **Implementation Files**
- `core/ffmpeg_cuda.py`: Engine de otimização FFmpeg CUDA
- `core/performance.py`: Detecção de hardware e status CUDA
- `test_cuda.py`: Validação e benchmarking CUDA
- `docs/CUDA_Implementation_Guide.md`: Guia técnico completo

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

### 🚀 Advanced CPU Optimizations (Janeiro 2025)

O VoxSynopsis implementou otimizações avançadas de performance alcançando **ganhos de 25-180x velocidade** através de configuração inteligente automática.

#### **CRÍTICO: Performance Protection**
⚠️ **ANTES DE FAZER QUALQUER ALTERAÇÃO que possa impactar a performance de transcrição:**

1. **SEMPRE pergunte ao usuário antes de modificar:**
   - Configurações de `beam_size`, `best_of`, `condition_on_previous_text`
   - Parâmetros de `batch_processing`, `batch_threshold`, `batch_size`
   - Configurações de `vad_filter`, `vad_threshold`, `target_sample_rate`
   - Threading (`cpu_threads`, `parallel_processes`)
   - Configurações de modelo (`model_size`, `compute_type`)
   - Environment variables CTranslate2
   - Configurações de cache e memória

2. **EXPLIQUE o impacto na performance:**
   - Quantificar degradação estimada (ex: "pode reduzir velocidade em 2-5x")
   - Explicar alternativas que mantêm performance
   - Sugerir configurações otimizadas como padrão

3. **REFERÊNCIA obrigatória:**
   - Consulte `docs/Performance_Optimization_VoxSynopsis.md` para configurações otimizadas
   - Mantenha compatibilidade com implementações de alto desempenho

**Exemplo de pergunta obrigatória:**
"⚠️ Esta alteração pode reduzir a velocidade de transcrição em 5x (mudança de beam_size=1 para beam_size=5). Você deseja prosseguir? Posso sugerir alternativas que mantêm a performance otimizada."

#### **Auto-Configuration System**
- **Hardware Detection**: Detecção automática de cores físicos e memória
- **Dynamic Configuration**: Configurações otimizadas baseadas no hardware detectado
- **Intelligent Fallback**: Sistema robusto de fallback para configurações seguras

#### **FastWhisper Optimizations**
- **Model Upgrade**: Upgrade automático `tiny` → `base` em hardware adequado (8GB+ RAM)
- **Aggressive Mode**: `conservative_mode=false` para performance máxima
- **Optimized Parameters**: `beam_size=1`, `best_of=1`, `condition_on_previous_text=false`
- **Enhanced VAD**: `vad_threshold=0.6`, `vad_min_silence_duration_ms=500`

#### **Threading Configuration**
- **Physical Cores**: Uso completo dos cores físicos disponíveis
- **CTranslate2 Variables**: Environment variables otimizadas automaticamente
- **Intel Optimizations**: MKL e PACKED_GEMM habilitados para CPUs Intel
- **AVX2 Instructions**: Conjunto de instruções forçado para performance máxima

#### **Batch Processing Enhanced**
- **Aggressive Batching**: `batch_threshold=2` (mais agressivo que padrão)
- **Hardware-Based Sizing**: `batch_size` calculado baseado em cores e memória
- **Auto-Activation**: Ativação automática baseada no número de arquivos

#### **Audio Preprocessing**
- **Target Sample Rate**: Reamostragem automática para 16kHz
- **Noise Reduction**: Redução de ruído inteligente habilitada
- **Silero VAD**: Integração com modelo VAD de 1.8MB para filtragem de silêncio

### Cache System
- **FileCache**: Armazena durações de arquivos para evitar chamadas FFmpeg repetidas
- **AudioFileInfo**: Metadados dos arquivos com verificação de modificação
- **IntelligentModelCache**: Cache LRU com weak references e cleanup automático
- Cache é limpo automaticamente ao parar transcrição

### Parallel Processing
- **ThreadPoolExecutor**: Processamento paralelo de extração de áudio
- **Concurrent chunk acceleration**: Acelera múltiplos chunks simultaneamente
- **BatchedInferencePipeline**: Processamento em lote otimizado do FastWhisper
- **MAX_WORKERS**: Limite dinâmico baseado no número de CPUs disponíveis

### Memory Optimization
- **Smart file filtering**: Evita reprocessamento de arquivos já processados
- **Streaming approach**: Reduz uso de memória durante processamento
- **Automatic cleanup**: Remove arquivos intermediários após processamento
- **INT8 Quantization**: Redução de 35% no uso de memória

### Performance Configuration
```python
# Configuração automática implementada
{
    "model_size": "base",              # Auto-upgrade baseado na memória
    "conservative_mode": False,        # Modo de performance máxima
    "cpu_threads": 6,                  # Cores físicos completos
    "batch_threshold": 2,              # Batching agressivo
    "enable_audio_preprocessing": True, # VAD e reamostragem
    "target_sample_rate": 16000,       # Otimização de sample rate
    "vad_threshold": 0.6               # Detecção melhorada
}
```

### Benchmarks Estimados
| Cenário | Tempo Original | Tempo Otimizado | Melhoria |
|---------|----------------|-----------------|----------|
| Arquivo 5min | ~5min | ~20-40s | **7.5-15x** |
| Arquivo 30min | ~30min | ~1.5-3min | **10-20x** |
| Batch 10 arquivos | ~50min | ~2-5min | **10-25x** |
| Arquivo 3h | ~3h | ~6-15min | **12-30x** |

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

## Gemini CLI Usage Patterns

### Basic Information Gathering (use flash):
```bash
# Quick project overview
gemini -m gemini-2.5-flash -p "@./ What files and directories exist in this project?"

# Find specific implementations
gemini -m gemini-2.5-flash -p "@core/ Does this codebase have dark mode implemented?"

# Check dependencies
gemini -m gemini-2.5-flash -p "@requirements.txt @package.json List all project dependencies"
```

### Deep Analysis Tasks (use pro):
```bash
# Architectural analysis
gemini -m gemini-2.5-pro -p "@core/ @tests/ Analyze the software architecture and identify potential improvements"

# Security review
gemini -m gemini-2.5-pro -p "@./ Perform a security audit and identify potential vulnerabilities"

# Performance analysis
gemini -m gemini-2.5-pro -p "@core/ Identify performance bottlenecks and suggest optimizations"
```

### File and Directory Inclusion Syntax:
```bash
# Single file analysis
gemini -p "@core/gui.py Explain this file's purpose and structure"

# Multiple files
gemini -p "@core/core.py @core/cli.py Compare these two files and explain their relationship"

# Entire directory
gemini -p "@core/ Summarize the architecture of this module"

# Multiple directories
gemini -p "@core/ @tests/ Analyze test coverage for the source code"

# Current directory (complete project)
gemini -p "@./ Give me an overview of this entire project"

# Alternative syntax for entire project
gemini --all_files -p "Analyze the project structure and dependencies"
```

## Decision Matrix: When to Use Which Tool

| Task Type | Claude Code | Gemini Flash | Gemini Pro |
|-----------|-------------|--------------|------------|
| Writing new code | ✅ | ❌ | ❌ |
| Debugging existing code | ✅ | ❌ | ❌ |
| Running tests/builds | ✅ | ❌ | ❌ |
| Quick file search | ❌ | ✅ | ❌ |
| Architecture analysis | ❌ | ❌ | ✅ |
| Security audit | ❌ | ❌ | ✅ |
| Basic documentation | ❌ | ✅ | ❌ |
| Complex problem solving | ✅ | ❌ | ✅ |
| Performance optimization | ✅ | ❌ | ✅ |
| Code refactoring | ✅ | ❌ | ❌ |

## Implementation Verification Examples

### Quick Checks (Flash):
```bash
# Check if feature exists
gemini -m gemini-2.5-flash -p "@core/ Is dark mode implemented? Show me the relevant files"

# Find specific functions
gemini -m gemini-2.5-flash -p "@core/ List all functions that handle video processing"

# Dependency check
gemini -m gemini-2.5-flash -p "@./ What UI framework is this project using?"
```

### Deep Analysis (Pro):
```bash
# Comprehensive feature analysis
gemini -m gemini-2.5-pro -p "@core/ @tests/ How robust is the error handling throughout the application?"

# Security assessment
gemini -m gemini-2.5-pro -p "@./ Are there any security vulnerabilities in file handling or user input processing?"

# Performance review
gemini -m gemini-2.5-pro -p "@core/ What are the performance characteristics of the summarization system?"
```

## Best Practices

1. **Start with Flash**: Use gemini-2.5-flash for initial exploration and simple queries
2. **Escalate to Pro**: Switch to gemini-2.5-pro when you need deep analysis or reasoning
3. **Specify Context**: Always use `@` syntax to include relevant files/directories
4. **Be Specific**: Clear, focused questions get better results
5. **Combine Tools**: Use Gemini for analysis, then Claude Code for implementation
6. **Iterative Approach**: Gather information with Gemini, then execute with Claude Code

This division ensures optimal use of each AI's strengths while maintaining efficient development workflows.

## Advanced Prompt Engineering for Gemini CLI

### MANDATORY: Always Use Structured Prompts
When using Gemini CLI, always follow this prompt engineering framework:

```bash
gemini -m [model] -p "@[context_files] 

## Context
[Provide comprehensive background about the project, current state, and relevant constraints]

## Task
[Detailed description of what you want Gemini to analyze or do]

## Expected Output
[Specify exact format, level of detail, structure, and scope of the analysis]

## Specific Focus Areas
[List specific aspects to emphasize in the analysis]

[Your specific request here]"
```

### Structured Analysis Examples

**Basic Information Gathering (Flash):**
```bash
# Quick project overview with context
gemini -m gemini-2.5-flash -p "@./ 

## Context
VoxSynopsis is a Python desktop audio recording and transcription application with modular architecture using FastWhisper.

## Task
Analyze the project structure and provide an overview of main components.

## Expected Output
- Bullet-point list of main directories and their purposes
- Key dependencies identified
- Architecture overview in 3-4 sentences

What files and directories exist in this project and what is their purpose?"
```

**Deep Analysis (Pro):**
```bash
# Comprehensive architectural analysis with structured prompt
gemini -m gemini-2.5-pro -p "@core/ @Tests/ 

## Context
VoxSynopsis features a modular architecture with enhanced reporting system, performance monitoring, and FastWhisper integration. The codebase follows Python best practices with comprehensive type hints.

## Task
Perform a comprehensive architecture analysis focusing on code quality, design patterns, and potential improvements.

## Expected Output
1. Architecture strengths and weaknesses
2. Design pattern usage assessment
3. Code quality metrics and observations
4. Specific improvement recommendations with rationale
5. Potential refactoring opportunities

## Specific Focus Areas
- Modularity and separation of concerns
- Error handling and resilience
- Performance optimization opportunities
- Testing coverage and quality

Analyze the software architecture and identify potential improvements."
```

## Mandatory Code Review Process

### ALWAYS Use Gemini CLI for:

#### 1. Peer Code Review (Before Integration)
**MANDATORY**: Always execute before code integration:
```bash
gemini -m gemini-2.5-pro -p "@path/to/changed/files 

## Context
VoxSynopsis codebase follows strict quality standards with comprehensive type hints, modular architecture, and graceful error handling. Code must adhere to established patterns.

## Task
Perform comprehensive peer code review focusing on quality, security, and maintainability.

## Expected Output
1. Code quality assessment (1-10 scale with justification)
2. Specific bug risks or edge cases identified
3. Security considerations and potential vulnerabilities
4. Performance implications analysis
5. Maintainability and readability evaluation
6. Adherence to project conventions assessment
7. Actionable improvement recommendations

## Specific Focus Areas
- Type safety and error handling
- Performance optimization opportunities
- Security best practices
- Code consistency with existing patterns

Review this code implementation for best practices, potential bugs, and improvement suggestions."
```

#### 2. Plan Review (Before Implementation)
**MANDATORY**: Always execute before implementing development plans:
```bash
gemini -m gemini-2.5-pro -p "@./ 

## Context
VoxSynopsis is a production-ready application with established architecture patterns, comprehensive testing strategy, and strict quality standards.

## Task
Critically analyze the proposed development plan to identify gaps, risks, and optimization opportunities.

## Expected Output
1. Completeness assessment: missing steps or considerations
2. Technical feasibility analysis with risk factors
3. Dependencies and prerequisites identification
4. Alternative approach suggestions with trade-offs
5. Implementation timeline and resource estimates
6. Testing and validation strategy review
7. Potential blockers and mitigation strategies

## Specific Focus Areas
- Technical feasibility and complexity
- Integration with existing architecture
- Testing and quality assurance approach
- Risk assessment and mitigation

Plan: [DETAILED_PLAN_DESCRIPTION]

Review this development plan and identify missing steps, potential challenges, and suggest improvements."
```

### Code Review Checklist
Before considering any implementation complete, verify with Gemini CLI:
- ✅ **Code Quality**: Coding standards, naming conventions, structure
- ✅ **Security**: Vulnerabilities, input validation, sanitization
- ✅ **Performance**: Optimizations, bottlenecks, resource usage
- ✅ **Testing**: Test coverage, edge cases
- ✅ **Documentation**: Docstrings, comments, type hints
- ✅ **Architecture**: Adherence to project patterns

### Plan Review Checklist
Before executing any development plan:
- ✅ **Completeness**: All necessary steps included
- ✅ **Feasibility**: Technical viability of proposed solutions
- ✅ **Dependencies**: Dependencies and prerequisites identified
- ✅ **Risk Assessment**: Risk identification and mitigation strategies
- ✅ **Alternative Approaches**: Consideration of alternative approaches
- ✅ **Testing Strategy**: Testing and validation plan

## Code Quality Standards

### Type Hints and Documentation
- **Type Annotations**: Comprehensive typing throughout codebase
- **Docstrings**: Detailed function and class documentation
- **Logging**: Structured logging with appropriate levels
- **Error Handling**: Graceful degradation with informative messages

### Testing Strategy
- **Framework**: pytest for unit and integration tests
- **Mocking**: External services and hardware dependencies
- **Coverage Target**: ≥85% code coverage
- **Tests**: Integration and unit tests with edge cases

### Code Consistency Rules
- **Import Order**: Standard library, third-party, local imports
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error Messages**: Use f-strings with descriptive context
- **Logging**: Use module-level loggers, not print statements

## Troubleshooting

### CTranslate2/FastWhisper Import Errors
Se você encontrar erros como "No module named 'ctranslate2'" ou "No module named 'faster_whisper'" durante a transcrição:

**Problema**: Dependências não instaladas no ambiente virtual correto.

**Solução**:
```bash
# 1. Criar ambiente virtual com Python 3.11
uv venv .venv --python 3.11

# 2. Instalar dependências (uv gerencia o ambiente automaticamente)
uv add -r requirements.txt

# 3. Executar aplicação
./run_voxsynopsis.sh
```

**Verificação**:
```bash
source .venv/bin/activate
python3 -c "import faster_whisper; import ctranslate2; print('✅ Dependencies OK')"
```

### Virtual Environment Issues
- **Problema**: `uv add` requer `pyproject.toml` com seção `[project]`
- **Solução**: Use `uv venv .venv --python 3.11` para criar ambiente e `uv add -r requirements.txt` para instalar
- **Script**: Use `./run_voxsynopsis.sh` que ativa automaticamente o ambiente
- **Nota**: O uv gerencia automaticamente o ambiente virtual - não precisa de `source .venv/bin/activate`
- **Fallback**: Se uv falhar, questione o usuário antes de usar pip

### Performance Issues
- Consulte `docs/Performance_Optimization_VoxSynopsis.md` para otimizações
- ⚠️ **Performance Protection**: Sempre pergunte antes de modificar parâmetros de performance

## Development Guidelines

### Adding New Features
1. **Modular Design**: Place new components in appropriate core/ subdirectories
2. **Fallback Support**: Always implement graceful degradation
3. **Type Safety**: Add comprehensive type hints
4. **Testing**: Include unit tests with mocks
5. **Documentation**: Update both docstrings and CLAUDE.md
6. **Mandatory Review**: Use Gemini CLI for plan and code review
7. **⚠️ Performance Protection**: ALWAYS ask before changes that impact transcription performance
8. **Package Management**: ALWAYS use uv - if uv fails, ask user before using pip

### Performance Protection Protocol
**MANDATORY before any changes to performance-critical code:**

1. **Identify Performance-Critical Areas:**
   - `core/config.py` - Configuration management
   - `core/transcription.py` - FastWhisper integration
   - `core/batch_transcription.py` - Batch processing
   - `core/audio_preprocessing.py` - Audio preprocessing
   - `core/performance.py` - Environment variables and threading
   - `config.json` - Runtime configuration parameters

2. **Ask User Permission Template:**
   ```
   ⚠️ PERFORMANCE IMPACT WARNING
   
   The proposed change will affect transcription performance:
   - Parameter: [specific parameter]
   - Current optimized value: [current value]
   - Proposed change: [new value]
   - Estimated performance impact: [X]% slower / [Y]x degradation
   
   This change may reduce transcription speed from the current 25-180x optimized performance.
   
   Would you like to proceed with this change?
   Alternative: I can suggest performance-preserving alternatives.
   ```

3. **Performance Impact Assessment:**
   - **Critical Impact**: Changes to beam_size, best_of, batch_threshold, model_size
   - **Moderate Impact**: Threading, VAD parameters, sample rate
   - **Minor Impact**: UI settings, logging, non-critical features

4. **Always Offer Alternatives:**
   - Suggest configuration options that maintain performance
   - Provide conditional implementation (user can choose)
   - Reference `docs/Performance_Optimization_VoxSynopsis.md` for optimal settings

### Enhanced Decision Matrix

| Task Type | Claude Code | Gemini Flash | Gemini Pro |
|-----------|-------------|--------------|------------|
| Writing new code | ✅ | ❌ | ❌ |
| Debugging existing code | ✅ | ❌ | ❌ |
| Running tests/builds | ✅ | ❌ | ❌ |
| Quick file search | ❌ | ✅ | ❌ |
| Architecture analysis | ❌ | ❌ | ✅ |
| Security audit | ❌ | ❌ | ✅ |
| Basic documentation | ❌ | ✅ | ❌ |
| Complex problem solving | ✅ | ❌ | ✅ |
| Performance optimization | ✅ | ❌ | ✅ |
| Code refactoring | ✅ | ❌ | ❌ |
| **Peer code review** | ❌ | ❌ | ✅ |
| **Plan review & validation** | ❌ | ❌ | ✅ |
| **Risk assessment** | ❌ | ❌ | ✅ |
| **Design pattern analysis** | ❌ | ❌ | ✅ |

## Quality Assurance Workflow

### Before Implementation
1. **Plan Creation**: Use Claude Code to create detailed implementation plan
2. **Plan Review**: Use Gemini Pro to validate plan completeness and feasibility
3. **⚠️ Performance Impact Assessment**: Check if changes affect transcription performance
4. **User Approval**: Ask user permission for any performance-impacting changes
5. **Implementation**: Use Claude Code for actual coding
6. **Code Review**: Use Gemini Pro for comprehensive code review
7. **Performance Validation**: Verify no unintended performance degradation
8. **Testing**: Run tests and verify quality checks
9. **Integration**: Only after all reviews pass

### Best Practices Summary

1. **Structured Prompts**: Always use the context-task-output framework for Gemini CLI
2. **Start with Flash**: Use gemini-2.5-flash for initial exploration and simple queries
3. **Escalate to Pro**: Switch to gemini-2.5-pro for deep analysis or reasoning
4. **Specify Context**: Always use `@` syntax to include relevant files/directories
5. **Be Specific**: Clear, focused questions with expected output format
6. **Combine Tools**: Use Gemini for analysis, then Claude Code for implementation
7. **Mandatory Reviews**: Always perform code and plan reviews before implementation
8. **Quality First**: Prioritize code quality and maintainability over speed
9. **⚠️ Performance Protection**: ALWAYS ask before changes that impact transcription performance
10. **User Consent**: Get explicit approval for any performance-degrading modifications
11. **Package Manager**: ALWAYS use uv - question user if uv fails before using pip

### Performance Protection Commitment

This VoxSynopsis codebase has achieved **25-180x transcription performance gains** through careful optimization. As the development assistant, I commit to:

- **Always ask permission** before modifying performance-critical parameters
- **Quantify performance impact** of proposed changes
- **Suggest performance-preserving alternatives** when possible
- **Reference optimization documentation** for best practices
- **Prioritize performance preservation** alongside code quality

This comprehensive workflow ensures high-quality development with systematic critical review at every stage, while protecting the significant performance investments made in the transcription system.