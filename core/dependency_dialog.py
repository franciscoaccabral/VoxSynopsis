"""Dependency validation dialog for VoxSynopsis."""

import sys
from typing import Dict, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QScrollArea, QWidget, QFrame,
    QSplitter, QMessageBox, QProgressBar
)

from .dependency_checker import DependencyChecker, DependencyResult, DependencyStatus


class DependencyCheckThread(QThread):
    """Thread for running dependency checks without blocking UI."""
    
    check_completed = pyqtSignal(dict)
    check_progress = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.checker = DependencyChecker()
    
    def run(self):
        """Run dependency checks in background."""
        try:
            self.check_progress.emit("Checking system information...")
            
            self.check_progress.emit("Checking FFmpeg...")
            ffmpeg_result = self.checker.check_ffmpeg()
            
            self.check_progress.emit("Checking Python dependencies...")
            python_results = self.checker.check_python_dependencies()
            
            self.check_progress.emit("Checking audio system...")
            audio_result = self.checker.check_audio_system()
            
            # Combine results
            results = {"ffmpeg": ffmpeg_result, "audio_system": audio_result}
            for dep_result in python_results:
                results[dep_result.name.lower()] = dep_result
            
            self.check_completed.emit(results)
            
        except Exception as e:
            self.check_progress.emit(f"Error during validation: {str(e)}")


class DependencyStatusWidget(QFrame):
    """Widget to display status of a single dependency."""
    
    def __init__(self, name: str, result: DependencyResult):
        super().__init__()
        self.result = result
        self.init_ui(name)
    
    def init_ui(self, name: str):
        """Initialize the UI for this dependency."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Status icon and name
        status_label = QLabel()
        if self.result.status == DependencyStatus.OK:
            status_label.setText("✅")
            status_label.setStyleSheet("color: green; font-size: 16px;")
        elif self.result.status == DependencyStatus.MISSING:
            status_label.setText("❌")
            status_label.setStyleSheet("color: red; font-size: 16px;")
        elif self.result.status == DependencyStatus.ERROR:
            status_label.setText("⚠️")
            status_label.setStyleSheet("color: orange; font-size: 16px;")
        else:
            status_label.setText("❓")
            status_label.setStyleSheet("color: gray; font-size: 16px;")
        
        # Dependency name
        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 10, QFont.Bold))
        name_label.setMinimumWidth(120)
        
        # Version info
        version_info = ""
        if self.result.status == DependencyStatus.OK and self.result.version:
            version_info = f"v{self.result.version}"
        elif self.result.error_message:
            version_info = self.result.error_message
        
        version_label = QLabel(version_info)
        version_label.setFont(QFont("Arial", 9))
        version_label.setStyleSheet("color: #666;")
        
        layout.addWidget(status_label)
        layout.addWidget(name_label)
        layout.addWidget(version_label)
        layout.addStretch()
        
        # Add subtle border
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f9f9f9;
                margin: 2px;
            }
        """)


class DependencyValidationDialog(QDialog):
    """Main dialog for dependency validation."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results: Optional[Dict[str, DependencyResult]] = None
        self.check_thread = None
        self.init_ui()
        self.start_validation()
    
    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("VoxSynopsis - Dependency Validation")
        self.setFixedSize(800, 600)
        self.setModal(True)
        
        # Center on screen
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.setGeometry(x, y, self.width(), self.height())
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_label = QLabel("Dependency Validation")
        header_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header_label)
        
        description_label = QLabel(
            "VoxSynopsis requires several dependencies to function properly. "
            "Please review the status below and install any missing components."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignCenter)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        main_layout.addWidget(description_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        main_layout.addWidget(self.progress_bar)
        
        # Progress label
        self.progress_label = QLabel("Initializing validation...")
        self.progress_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.progress_label)
        
        # Splitter for dependencies and instructions
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Dependencies panel
        deps_widget = QWidget()
        deps_layout = QVBoxLayout(deps_widget)
        
        deps_title = QLabel("Dependencies Status")
        deps_title.setFont(QFont("Arial", 12, QFont.Bold))
        deps_layout.addWidget(deps_title)
        
        # Scroll area for dependencies
        self.deps_scroll = QScrollArea()
        self.deps_scroll.setWidgetResizable(True)
        self.deps_scroll.setMinimumWidth(350)
        self.deps_content = QWidget()
        self.deps_content_layout = QVBoxLayout(self.deps_content)
        self.deps_scroll.setWidget(self.deps_content)
        deps_layout.addWidget(self.deps_scroll)
        
        splitter.addWidget(deps_widget)
        
        # Instructions panel
        instructions_widget = QWidget()
        instructions_layout = QVBoxLayout(instructions_widget)
        
        instructions_title = QLabel("Installation Instructions")
        instructions_title.setFont(QFont("Arial", 12, QFont.Bold))
        instructions_layout.addWidget(instructions_title)
        
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setMinimumWidth(350)
        self.instructions_text.setFont(QFont("Consolas", 9))
        instructions_layout.addWidget(self.instructions_text)
        
        splitter.addWidget(instructions_widget)
        
        # Set splitter proportions
        splitter.setSizes([350, 350])
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.retry_button = QPushButton("Retry Validation")
        self.retry_button.clicked.connect(self.start_validation)
        self.retry_button.setEnabled(False)
        
        self.continue_button = QPushButton("Continue Anyway")
        self.continue_button.clicked.connect(self.continue_anyway)
        self.continue_button.setEnabled(False)
        
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit_application)
        
        button_layout.addWidget(self.retry_button)
        button_layout.addWidget(self.continue_button)
        button_layout.addStretch()
        button_layout.addWidget(self.exit_button)
        
        main_layout.addLayout(button_layout)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #e6e6e6;
            }
            QPushButton:pressed {
                background-color: #d9d9d9;
            }
            QPushButton:disabled {
                background-color: #f5f5f5;
                color: #999;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
                padding: 10px;
            }
        """)
    
    def start_validation(self):
        """Start the dependency validation process."""
        # Clear previous results
        self.clear_dependencies()
        self.instructions_text.clear()
        
        # Reset UI state
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.progress_label.setText("Starting validation...")
        self.retry_button.setEnabled(False)
        self.continue_button.setEnabled(False)
        
        # Start validation thread
        self.check_thread = DependencyCheckThread()
        self.check_thread.check_progress.connect(self.update_progress)
        self.check_thread.check_completed.connect(self.on_validation_complete)
        self.check_thread.start()
    
    def update_progress(self, message: str):
        """Update progress display."""
        self.progress_label.setText(message)
    
    def on_validation_complete(self, results: Dict[str, DependencyResult]):
        """Handle completion of validation."""
        self.results = results
        
        # Hide progress
        self.progress_bar.setVisible(False)
        self.progress_label.setText("Validation complete")
        
        # Enable buttons
        self.retry_button.setEnabled(True)
        
        # Display results
        self.display_dependencies(results)
        self.update_instructions(results)
        
        # Check if all critical dependencies are OK
        critical_deps = ["ffmpeg", "pyqt5", "sounddevice", "faster_whisper"]
        all_critical_ok = all(
            results.get(dep, DependencyResult("", DependencyStatus.MISSING)).status == DependencyStatus.OK
            for dep in critical_deps
        )
        
        if all_critical_ok:
            self.continue_button.setText("Continue")
            self.continue_button.setEnabled(True)
            self.progress_label.setText("✅ All critical dependencies are available!")
            self.progress_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.continue_button.setText("Continue Anyway (Not Recommended)")
            self.continue_button.setEnabled(True)
            self.progress_label.setText("⚠️ Some dependencies are missing. Install them for full functionality.")
            self.progress_label.setStyleSheet("color: orange; font-weight: bold;")
    
    def clear_dependencies(self):
        """Clear the dependencies display."""
        for i in reversed(range(self.deps_content_layout.count())):
            self.deps_content_layout.itemAt(i).widget().setParent(None)
    
    def display_dependencies(self, results: Dict[str, DependencyResult]):
        """Display dependency status widgets."""
        self.clear_dependencies()
        
        # Sort results: critical first, then alphabetical
        critical_order = ["ffmpeg", "pyqt5", "sounddevice", "faster_whisper", "torch", "numpy", "psutil", "audio_system"]
        
        ordered_results = []
        for dep in critical_order:
            if dep in results:
                ordered_results.append((dep, results[dep]))
        
        # Add remaining dependencies
        for dep, result in results.items():
            if dep not in critical_order:
                ordered_results.append((dep, result))
        
        for dep_name, result in ordered_results:
            widget = DependencyStatusWidget(dep_name.replace("_", " ").title(), result)
            self.deps_content_layout.addWidget(widget)
        
        self.deps_content_layout.addStretch()
    
    def update_instructions(self, results: Dict[str, DependencyResult]):
        """Update installation instructions based on missing dependencies."""
        missing_deps = [
            (name, result) for name, result in results.items()
            if result.status in [DependencyStatus.MISSING, DependencyStatus.ERROR] and result.install_instructions
        ]
        
        if not missing_deps:
            self.instructions_text.setHtml("""
                <h3 style='color: green;'>✅ All Dependencies Available</h3>
                <p>All required dependencies are properly installed and configured.</p>
                <p>You can proceed to use VoxSynopsis.</p>
            """)
            return
        
        instructions_html = "<h3>📋 Installation Instructions</h3>"
        instructions_html += "<p>Please install the missing dependencies below:</p>"
        
        for dep_name, result in missing_deps:
            instructions_html += f"""
                <h4 style='color: #d32f2f;'>❌ {dep_name.replace('_', ' ').title()}</h4>
                <div style='background-color: #f5f5f5; padding: 10px; border-left: 3px solid #ccc; margin: 10px 0;'>
                    <strong>Error:</strong> {result.error_message or 'Not installed'}<br>
                    <strong>Solution:</strong>
                    <pre style='background-color: #fff; padding: 10px; border: 1px solid #ddd; margin-top: 5px; white-space: pre-wrap;'>{result.install_instructions}</pre>
                </div>
            """
        
        instructions_html += """
            <hr>
            <p><strong>💡 Tips:</strong></p>
            <ul>
                <li>Run commands in Terminal/Command Prompt as administrator if needed</li>
                <li>Restart VoxSynopsis after installing dependencies</li>
                <li>Contact support if you encounter issues</li>
            </ul>
        """
        
        self.instructions_text.setHtml(instructions_html)
    
    def continue_anyway(self):
        """Continue to main application despite missing dependencies."""
        if self.results:
            critical_deps = ["ffmpeg", "pyqt5", "sounddevice"] 
            missing_critical = [
                dep for dep in critical_deps 
                if self.results.get(dep, DependencyResult("", DependencyStatus.MISSING)).status != DependencyStatus.OK
            ]
            
            if missing_critical:
                reply = QMessageBox.question(
                    self,
                    "Continue with Missing Dependencies?",
                    f"Critical dependencies are missing: {', '.join(missing_critical)}\n\n"
                    "VoxSynopsis may not function properly. Continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return
        
        self.accept()
    
    def exit_application(self):
        """Exit the application."""
        self.reject()
        sys.exit(0)


def run_dependency_validation() -> bool:
    """
    Run dependency validation dialog.
    
    Returns:
        bool: True if user chose to continue, False if user chose to exit
    """
    # Create QApplication if it doesn't exist
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    dialog = DependencyValidationDialog()
    result = dialog.exec_()
    
    return result == QDialog.Accepted


if __name__ == "__main__":
    # Test the dependency validation dialog
    success = run_dependency_validation()
    if success:
        print("User chose to continue")
    else:
        print("User chose to exit")