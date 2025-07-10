"""Main entry point for VoxSynopsis application."""

import sys
from PyQt5.QtWidgets import QApplication

from .config import load_stylesheet
from .main_window import AudioRecorderApp


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    
    # Load stylesheet
    load_stylesheet(app)
    
    # Create and show main window
    main_win = AudioRecorderApp()
    main_win.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()