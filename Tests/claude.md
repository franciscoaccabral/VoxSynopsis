# Testing Guidelines for VoxSynopsis

This file provides specific guidance for testing in the VoxSynopsis project.

## Testing Framework

### Primary Tools
- **pytest**: Main testing framework
- **unittest.mock**: Mocking external dependencies
- **PyQt5.QtTest**: GUI testing utilities

### Test Commands
```bash
# Run all tests
python3 -m pytest Tests/

# Run specific test file
python3 -m pytest Tests/test_recording_thread.py

# Run with coverage
python3 -m pytest Tests/ --cov=core --cov-report=html

# Run with verbose output
python3 -m pytest Tests/ -v

# Run tests matching pattern
python3 -m pytest Tests/ -k "test_recording"
```

## Test Structure

### Current Test Files
- `test_recording_thread.py`: Tests for audio recording functionality
- `test_settings_dialog.py`: Tests for FastWhisper settings interface
- `test_stylesheet.py`: Tests for UI styling and themes

### Test Organization
```
Tests/
├── claude.md                    # This file - testing guidelines
├── __init__.py                  # Package initialization
├── test_recording_thread.py     # Recording functionality tests
├── test_settings_dialog.py      # Settings dialog tests
├── test_stylesheet.py           # UI styling tests
├── fixtures/                    # Test fixtures and mock data
└── conftest.py                  # pytest configuration (if needed)
```

## Testing Standards

### Code Coverage Target
- **Minimum**: 85% code coverage
- **Critical modules**: 90%+ coverage (core/transcription.py, core/config.py)
- **GUI components**: 70%+ coverage (focus on logic, not UI interactions)

### Test Naming Convention
```python
def test_[component]_[scenario]_[expected_outcome]():
    # Example: test_recording_thread_starts_successfully()
    pass
```

### Essential Test Categories

#### 1. Unit Tests
- **Individual functions**: Test single functions in isolation
- **Class methods**: Test class behavior with mocked dependencies
- **Configuration**: Test ConfigManager with various settings

#### 2. Integration Tests
- **Audio pipeline**: Test recording → processing → transcription flow
- **FastWhisper integration**: Test model loading and transcription
- **File I/O**: Test file operations and caching

#### 3. Performance Tests
- **⚠️ CRITICAL**: Test performance-sensitive configurations
- **Benchmark tests**: Validate optimized settings don't regress
- **Memory usage**: Test for memory leaks in long-running operations

#### 4. GUI Tests (Limited)
- **Settings dialog**: Test configuration changes
- **Main window**: Test basic UI functionality
- **Error handling**: Test UI error states

## Mocking Strategy

### Required Mocks
```python
# Audio hardware mocking
@patch('sounddevice.default')
@patch('sounddevice.InputStream')

# FastWhisper model mocking
@patch('faster_whisper.WhisperModel')

# File system operations
@patch('os.path.exists')
@patch('builtins.open')

# Performance optimizations
@patch('psutil.cpu_count')
@patch('psutil.virtual_memory')
```

### Mock Templates
```python
# FastWhisper model mock
@pytest.fixture
def mock_whisper_model():
    with patch('faster_whisper.WhisperModel') as mock:
        mock_instance = Mock()
        mock_instance.transcribe.return_value = (
            [Mock(text="test transcription", start=0.0, end=1.0)],
            Mock(language="pt")
        )
        mock.return_value = mock_instance
        yield mock_instance

# Audio device mock
@pytest.fixture
def mock_audio_device():
    with patch('sounddevice.default') as mock:
        mock.device = [0, 1]  # Input, output device IDs
        yield mock
```

## Performance-Critical Testing

### ⚠️ MANDATORY: Performance Protection in Tests

**Before testing any performance-related changes:**

1. **Baseline Performance Tests**: Always include performance benchmarks
2. **Configuration Validation**: Test optimized settings are preserved
3. **Regression Detection**: Alert if performance degrades

```python
def test_performance_configuration_preserved():
    """Critical test: Ensure optimized settings are not accidentally changed"""
    config = ConfigManager()
    
    # Test critical performance settings
    assert config.get('beam_size') == 1, "beam_size must remain 1 for optimal performance"
    assert config.get('best_of') == 1, "best_of must remain 1 for optimal performance"
    assert config.get('batch_threshold') == 2, "batch_threshold must remain 2 for aggressive batching"
    assert config.get('conservative_mode') == False, "conservative_mode must be False"
    
def test_transcription_performance_regression():
    """Test that transcription performance doesn't regress"""
    # This test should fail if performance drops significantly
    with mock_whisper_model():
        start_time = time.time()
        # Perform transcription test
        duration = time.time() - start_time
        assert duration < MAX_ACCEPTABLE_TIME, f"Transcription too slow: {duration}s"
```

## Test Data and Fixtures

### Audio Test Files
- **Short audio** (5s): Quick functional tests
- **Medium audio** (30s): Integration tests  
- **Long audio** (5min): Performance and memory tests
- **Various formats**: WAV, MP4, different sample rates

### Configuration Test Data
```python
# Test configurations
OPTIMAL_CONFIG = {
    "beam_size": 1,
    "best_of": 1,
    "model_size": "base",
    "conservative_mode": False,
    "batch_threshold": 2
}

FALLBACK_CONFIG = {
    "beam_size": 1,
    "best_of": 1,
    "model_size": "tiny",
    "conservative_mode": True,
    "batch_threshold": 3
}
```

## Common Test Patterns

### Testing Async Operations
```python
@pytest.mark.asyncio
async def test_async_transcription():
    # Test async transcription operations
    pass

# Or for QThread testing
def test_recording_thread_signals(qtbot):
    thread = RecordingThread()
    with qtbot.waitSignal(thread.finished, timeout=1000):
        thread.start()
```

### Testing Error Handling
```python
def test_graceful_error_handling():
    """Test that errors are handled gracefully without crashing"""
    with patch('core.transcription.WhisperModel') as mock:
        mock.side_effect = Exception("Model loading failed")
        
        # Should not raise exception
        thread = TranscriptionThread()
        thread.run()
        
        # Should emit error signal or log error
        assert thread.error_occurred or "error logged"
```

### Testing Configuration Changes
```python
def test_configuration_updates():
    """Test that configuration changes are properly applied"""
    config = ConfigManager()
    
    # Test setting update
    config.set('model_size', 'medium')
    assert config.get('model_size') == 'medium'
    
    # Test persistence
    config.save_settings()
    new_config = ConfigManager()
    assert new_config.get('model_size') == 'medium'
```

## Performance Testing Guidelines

### Critical Performance Tests
1. **Model Loading Time**: Test model loading doesn't exceed thresholds
2. **Transcription Speed**: Test optimized configurations maintain speed
3. **Memory Usage**: Test for memory leaks in long operations
4. **Batch Processing**: Test batch performance scales correctly

### Performance Test Template
```python
@pytest.mark.performance
def test_transcription_performance():
    """Test that transcription maintains optimized performance"""
    config = ConfigManager()
    
    # Ensure optimized settings
    assert config.get('beam_size') == 1
    assert config.get('conservative_mode') == False
    
    # Performance test
    start_time = time.time()
    # ... perform transcription test
    duration = time.time() - start_time
    
    # Assert performance meets requirements
    assert duration < PERFORMANCE_THRESHOLD
```

## Test Execution Strategy

### Development Testing
```bash
# Quick tests during development
python3 -m pytest Tests/test_recording_thread.py -v

# Performance tests
python3 -m pytest Tests/ -m performance

# Full test suite before commit
python3 -m pytest Tests/ --cov=core
```

### CI/CD Testing
```bash
# Complete test suite with coverage
python3 -m pytest Tests/ --cov=core --cov-report=xml --cov-fail-under=85

# Performance regression tests
python3 -m pytest Tests/ -m performance --tb=short
```

## Best Practices

### Test Independence
- Each test should be independent and not rely on others
- Use proper setup/teardown or fixtures
- Clean up resources (files, threads, etc.)

### Test Reliability
- Mock external dependencies (audio devices, models, network)
- Use deterministic test data
- Avoid time-dependent tests (use mocking for time)

### Test Maintainability
- Keep tests simple and focused
- Use descriptive test names
- Document complex test scenarios
- Avoid testing implementation details

## Integration with Main CLAUDE.md

This file supplements the main `CLAUDE.md` with testing-specific guidance. When working on tests, Claude Code will read both files to understand:

1. **Overall project context** (from main CLAUDE.md)
2. **Testing-specific guidelines** (from this file)
3. **Performance protection protocols** (emphasized in both)

## Performance Protection Commitment for Tests

**⚠️ CRITICAL**: Any test that could validate performance-degrading changes must include warnings about the 25-180x performance gains achieved. Tests should actively protect against performance regressions.

This testing framework ensures high-quality code while maintaining the significant performance optimizations implemented in the VoxSynopsis transcription system.