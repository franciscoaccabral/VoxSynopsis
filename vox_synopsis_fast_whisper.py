"""VoxSynopsis - Audio Recording and Transcription Application

This file maintains backward compatibility with the original application.
The main functionality has been modularized into the core package.
"""

# Wrapper imports for backward compatibility
from core.main import main
from core.main_window import AudioRecorderApp
from core.recording import RecordingThread
from core.transcription import TranscriptionThread
from core.settings_dialog import FastWhisperSettingsDialog
from core.cache import AudioFileInfo, FileCache
from core.config import ConfigManager, SAMPLE_RATE, OUTPUT_DIR, MAX_WORKERS, load_stylesheet

# Make all classes available at module level for compatibility
__all__ = [
    'main',
    'AudioRecorderApp',
    'RecordingThread', 
    'TranscriptionThread',
    'FastWhisperSettingsDialog',
    'AudioFileInfo',
    'FileCache',
    'ConfigManager',
    'SAMPLE_RATE',
    'OUTPUT_DIR',
    'MAX_WORKERS',
    'load_stylesheet'
]

if __name__ == "__main__":
    main()