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
pipx install -r requirements.txt
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

## Development Guidelines

### Adding New Features
1. **Modular Design**: Place new components in appropriate core/ subdirectories
2. **Fallback Support**: Always implement graceful degradation
3. **Type Safety**: Add comprehensive type hints
4. **Testing**: Include unit tests with mocks
5. **Documentation**: Update both docstrings and CLAUDE.md
6. **Mandatory Review**: Use Gemini CLI for plan and code review

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
3. **Implementation**: Use Claude Code for actual coding
4. **Code Review**: Use Gemini Pro for comprehensive code review
5. **Testing**: Run tests and verify quality checks
6. **Integration**: Only after all reviews pass

### Best Practices Summary

1. **Structured Prompts**: Always use the context-task-output framework for Gemini CLI
2. **Start with Flash**: Use gemini-2.5-flash for initial exploration and simple queries
3. **Escalate to Pro**: Switch to gemini-2.5-pro for deep analysis or reasoning
4. **Specify Context**: Always use `@` syntax to include relevant files/directories
5. **Be Specific**: Clear, focused questions with expected output format
6. **Combine Tools**: Use Gemini for analysis, then Claude Code for implementation
7. **Mandatory Reviews**: Always perform code and plan reviews before implementation
8. **Quality First**: Prioritize code quality and maintainability over speed

This comprehensive workflow ensures high-quality development with systematic critical review at every stage.