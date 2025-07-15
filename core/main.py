"""Main entry point for VoxSynopsis application."""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox

from .config import load_stylesheet
from .main_window import AudioRecorderApp
from .performance import setup_fastwhisper_environment, print_optimization_status


def main(skip_validation: bool = False):
    """Initialize and run the application.
    
    Args:
        skip_validation: If True, skip dependency validation (for development)
    """
    # Create QApplication early for dependency validation dialog
    app = QApplication(sys.argv)
    
    # Check if we should skip validation (development mode)
    if "--skip-validation" in sys.argv:
        skip_validation = True
        print("⚠️ Skipping dependency validation (development mode)")
    
    # Run dependency validation unless skipped
    if not skip_validation:
        print("🔍 Validating system dependencies...")
        
        try:
            from .dependency_dialog import run_dependency_validation
            
            validation_passed = run_dependency_validation()
            if not validation_passed:
                print("❌ Dependency validation failed or user chose to exit")
                sys.exit(0)
            
            print("✅ Dependency validation completed")
            
        except ImportError as e:
            # If dependency validation itself fails due to missing PyQt5, show error
            print(f"❌ Critical error: Cannot load dependency validation: {e}")
            print("Please ensure PyQt5 is installed: pip install PyQt5")
            sys.exit(1)
        except Exception as e:
            # If validation fails for any other reason, ask user what to do
            print(f"⚠️ Dependency validation error: {e}")
            
            try:
                reply = QMessageBox.question(
                    None,
                    "Dependency Validation Error",
                    f"Dependency validation failed with error:\n{str(e)}\n\n"
                    "Do you want to continue anyway?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    sys.exit(0)
                    
                print("⚠️ Continuing despite validation error...")
                
            except Exception:
                # If even the message box fails, just continue
                print("⚠️ Continuing despite validation error (unable to show dialog)...")
    
    # Setup FastWhisper performance optimizations BEFORE importing FastWhisper
    print("🚀 Initializing VoxSynopsis with performance optimizations...")
    # Use conservative mode initially to avoid compatibility issues
    setup_fastwhisper_environment(conservative_mode=True)
    
    # Load stylesheet
    load_stylesheet(app)
    
    # Print optimization status for user feedback
    print_optimization_status()
    
    # Create and show main window
    try:
        main_win = AudioRecorderApp()
        main_win.show()
        
        print("🎉 VoxSynopsis started successfully!")
        
        # Run the application
        sys.exit(app.exec_())
        
    except ImportError as e:
        error_msg = f"Failed to start VoxSynopsis due to missing dependency: {e}"
        print(f"❌ {error_msg}")
        
        try:
            QMessageBox.critical(
                None,
                "Startup Error",
                f"{error_msg}\n\nPlease install the missing dependencies and restart the application."
            )
        except Exception:
            pass
            
        sys.exit(1)
    except Exception as e:
        error_msg = f"Unexpected error during startup: {e}"
        print(f"❌ {error_msg}")
        
        try:
            QMessageBox.critical(
                None,
                "Startup Error", 
                f"{error_msg}\n\nPlease check the console output for more details."
            )
        except Exception:
            pass
            
        sys.exit(1)


if __name__ == "__main__":
    main()