"""Main entry point for VoxSynopsis application."""

import sys
from PyQt5.QtWidgets import QApplication

from .config import load_stylesheet
from .main_window import AudioRecorderApp
from .performance import setup_fastwhisper_environment, print_optimization_status


def main():
    """Initialize and run the application."""
    # Setup FastWhisper performance optimizations BEFORE importing FastWhisper
    print("🚀 Initializing VoxSynopsis with performance optimizations...")
    # Use conservative mode initially to avoid compatibility issues
    setup_fastwhisper_environment(conservative_mode=True)
    
    app = QApplication(sys.argv)
    
    # Load stylesheet
    load_stylesheet(app)
    
    # Print optimization status for user feedback
    print_optimization_status()
    
    # Create and show main window
    main_win = AudioRecorderApp()
    main_win.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()