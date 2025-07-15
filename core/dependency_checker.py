"""Dependency validation system for VoxSynopsis."""

import platform
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class DependencyStatus(Enum):
    """Status of a dependency check."""
    OK = "ok"
    MISSING = "missing"
    OUTDATED = "outdated"
    ERROR = "error"


@dataclass
class DependencyResult:
    """Result of a dependency check."""
    name: str
    status: DependencyStatus
    version: Optional[str] = None
    error_message: Optional[str] = None
    install_instructions: Optional[str] = None


class DependencyChecker:
    """Checks system dependencies for VoxSynopsis."""
    
    def __init__(self):
        self.os_info = self._get_os_info()
        
    def _get_os_info(self) -> Dict[str, str]:
        """Get detailed OS information."""
        return {
            "system": platform.system().lower(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform()
        }
    
    def check_ffmpeg(self) -> DependencyResult:
        """Check if FFmpeg is installed and accessible."""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract version from output
                version_line = result.stdout.split('\n')[0]
                version = version_line.split(' ')[2] if len(version_line.split(' ')) > 2 else "unknown"
                
                return DependencyResult(
                    name="FFmpeg",
                    status=DependencyStatus.OK,
                    version=version,
                    install_instructions=None
                )
            else:
                return DependencyResult(
                    name="FFmpeg",
                    status=DependencyStatus.ERROR,
                    error_message="FFmpeg command failed",
                    install_instructions=self._get_ffmpeg_instructions()
                )
                
        except FileNotFoundError:
            return DependencyResult(
                name="FFmpeg",
                status=DependencyStatus.MISSING,
                error_message="FFmpeg not found in PATH",
                install_instructions=self._get_ffmpeg_instructions()
            )
        except subprocess.TimeoutExpired:
            return DependencyResult(
                name="FFmpeg",
                status=DependencyStatus.ERROR,
                error_message="FFmpeg command timed out",
                install_instructions=self._get_ffmpeg_instructions()
            )
        except Exception as e:
            return DependencyResult(
                name="FFmpeg",
                status=DependencyStatus.ERROR,
                error_message=f"Unexpected error: {str(e)}",
                install_instructions=self._get_ffmpeg_instructions()
            )
    
    def check_python_dependencies(self) -> List[DependencyResult]:
        """Check critical Python dependencies."""
        critical_deps = [
            "PyQt5",
            "sounddevice", 
            "faster_whisper",
            "torch",
            "numpy",
            "psutil"
        ]
        
        results = []
        for dep in critical_deps:
            try:
                if dep == "PyQt5":
                    import PyQt5.QtWidgets
                    version = PyQt5.Qt.PYQT_VERSION_STR
                elif dep == "sounddevice":
                    import sounddevice
                    version = sounddevice.__version__
                elif dep == "faster_whisper":
                    import faster_whisper
                    version = getattr(faster_whisper, "__version__", "unknown")
                elif dep == "torch":
                    import torch
                    version = torch.__version__
                elif dep == "numpy":
                    import numpy
                    version = numpy.__version__
                elif dep == "psutil":
                    import psutil
                    version = psutil.__version__
                
                results.append(DependencyResult(
                    name=dep,
                    status=DependencyStatus.OK,
                    version=version
                ))
                
            except ImportError as e:
                results.append(DependencyResult(
                    name=dep,
                    status=DependencyStatus.MISSING,
                    error_message=f"Import failed: {str(e)}",
                    install_instructions=self._get_python_dep_instructions(dep)
                ))
            except Exception as e:
                results.append(DependencyResult(
                    name=dep,
                    status=DependencyStatus.ERROR,
                    error_message=f"Unexpected error: {str(e)}",
                    install_instructions=self._get_python_dep_instructions(dep)
                ))
        
        return results
    
    def check_audio_system(self) -> DependencyResult:
        """Check if audio system is working."""
        try:
            import sounddevice as sd
            
            # Try to get device list
            devices = sd.query_devices()
            
            if len(devices) == 0:
                return DependencyResult(
                    name="Audio System",
                    status=DependencyStatus.ERROR,
                    error_message="No audio devices found",
                    install_instructions=self._get_audio_instructions()
                )
            
            # Try to get default device
            default_device = sd.default.device
            
            return DependencyResult(
                name="Audio System", 
                status=DependencyStatus.OK,
                version=f"{len(devices)} devices available"
            )
            
        except Exception as e:
            return DependencyResult(
                name="Audio System",
                status=DependencyStatus.ERROR,
                error_message=str(e),
                install_instructions=self._get_audio_instructions()
            )
    
    def run_full_check(self) -> Dict[str, DependencyResult]:
        """Run all dependency checks."""
        results = {}
        
        # Check FFmpeg
        results["ffmpeg"] = self.check_ffmpeg()
        
        # Check Python dependencies
        python_deps = self.check_python_dependencies()
        for dep_result in python_deps:
            results[dep_result.name.lower()] = dep_result
        
        # Check audio system
        results["audio_system"] = self.check_audio_system()
        
        return results
    
    def _get_ffmpeg_instructions(self) -> str:
        """Get FFmpeg installation instructions for current OS."""
        system = self.os_info["system"]
        
        if system == "linux":
            # Detect specific distro if possible
            try:
                with open("/etc/os-release", "r") as f:
                    os_release = f.read().lower()
                    
                if "ubuntu" in os_release or "debian" in os_release:
                    return """Ubuntu/Debian:
sudo apt update
sudo apt install ffmpeg

For older versions:
sudo apt install software-properties-common
sudo add-apt-repository ppa:jonathonf/ffmpeg-4
sudo apt update && sudo apt install ffmpeg"""
                    
                elif "fedora" in os_release or "centos" in os_release or "rhel" in os_release:
                    return """Fedora/CentOS/RHEL:
sudo dnf install ffmpeg
# or for older versions:
sudo yum install ffmpeg"""
                    
                elif "arch" in os_release:
                    return """Arch Linux:
sudo pacman -S ffmpeg"""
                    
            except FileNotFoundError:
                pass
                
            return """Linux (Generic):
# Ubuntu/Debian:
sudo apt update && sudo apt install ffmpeg

# Fedora/CentOS:
sudo dnf install ffmpeg

# Arch:
sudo pacman -S ffmpeg

# Or compile from source:
https://ffmpeg.org/download.html#build-linux"""
            
        elif system == "darwin":  # macOS
            return """macOS:
# Using Homebrew (recommended):
brew install ffmpeg

# Using MacPorts:
sudo port install ffmpeg

# If you don't have Homebrew:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install ffmpeg"""
            
        elif system == "windows":
            return """Windows:
# Method 1 - Download pre-built binary:
1. Go to https://ffmpeg.org/download.html#build-windows
2. Download Windows build
3. Extract to C:\\ffmpeg
4. Add C:\\ffmpeg\\bin to your PATH environment variable

# Method 2 - Using Chocolatey:
choco install ffmpeg

# Method 3 - Using winget:
winget install ffmpeg

# Method 4 - Using Scoop:
scoop install ffmpeg"""
            
        else:
            return f"""Unknown system ({system}):
Please visit https://ffmpeg.org/download.html for installation instructions."""
    
    def _get_python_dep_instructions(self, dep_name: str) -> str:
        """Get Python dependency installation instructions."""
        base_cmd = f"pip install {dep_name}"
        
        if dep_name == "torch":
            return """PyTorch:
# CPU version:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# CUDA version (for GPU support):
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

Visit https://pytorch.org/get-started/ for specific CUDA versions."""
            
        elif dep_name == "PyQt5":
            system = self.os_info["system"]
            if system == "linux":
                return """PyQt5 (Linux):
# Using pip:
pip install PyQt5

# Using system package manager (Ubuntu/Debian):
sudo apt install python3-pyqt5

# Using system package manager (Fedora):
sudo dnf install python3-qt5"""
            else:
                return f"pip install {dep_name}"
        
        return f"""Install {dep_name}:
{base_cmd}

# If you're using a virtual environment:
source venv/bin/activate  # Linux/macOS
# or
venv\\Scripts\\activate  # Windows
{base_cmd}"""
    
    def _get_audio_instructions(self) -> str:
        """Get audio system installation instructions."""
        system = self.os_info["system"]
        
        if system == "linux":
            return """Linux Audio System:
# Install PortAudio (required for sounddevice):
sudo apt install libportaudio2 portaudio19-dev  # Ubuntu/Debian
sudo dnf install portaudio-devel                # Fedora
sudo pacman -S portaudio                        # Arch

# For WSL2 users:
# Audio support in WSL2 requires PulseAudio setup
# Consider running VoxSynopsis natively on Windows instead"""
            
        elif system == "darwin":
            return """macOS Audio System:
# Usually works out of the box
# If issues persist, reinstall sounddevice:
pip uninstall sounddevice
pip install sounddevice

# For permission issues:
# Go to System Preferences > Security & Privacy > Privacy > Microphone
# Allow Terminal/Python to access microphone"""
            
        elif system == "windows":
            return """Windows Audio System:
# Usually works out of the box
# If issues persist:
pip uninstall sounddevice
pip install sounddevice

# For driver issues:
# Update your audio drivers
# Check Windows Sound settings"""
            
        else:
            return "Audio system configuration varies by platform. Please check your system's audio setup."