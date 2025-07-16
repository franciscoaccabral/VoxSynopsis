"""GPU monitoring utilities for VoxSynopsis CUDA interface."""

import logging
from typing import Dict, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class GPUInfo:
    """GPU information structure."""
    name: str
    total_memory: int  # MB
    used_memory: int   # MB
    free_memory: int   # MB
    utilization: int   # %
    temperature: int   # °C
    available: bool


class GPUMonitor:
    """Monitors GPU usage and status for CUDA operations."""
    
    def __init__(self):
        self._pynvml_available = False
        self._cuda_available = False
        self._device_count = 0
        self._initialize()
    
    def _initialize(self):
        """Initialize GPU monitoring."""
        try:
            import pynvml
            pynvml.nvmlInit()
            self._pynvml_available = True
            self._device_count = pynvml.nvmlDeviceGetCount()
            logger.info(f"GPU monitoring initialized: {self._device_count} devices found")
        except (ImportError, Exception) as e:
            logger.warning(f"GPU monitoring not available: {e}")
            self._pynvml_available = False
        
        # Check CUDA availability
        try:
            import torch
            self._cuda_available = torch.cuda.is_available()
            if self._cuda_available:
                logger.info("CUDA detected and available")
            else:
                logger.info("CUDA not available")
        except ImportError:
            logger.warning("PyTorch not available, CUDA status unknown")
    
    def is_gpu_monitoring_available(self) -> bool:
        """Check if GPU monitoring is available."""
        return self._pynvml_available and self._device_count > 0
    
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        return self._cuda_available
    
    def get_gpu_info(self, device_index: int = 0) -> Optional[GPUInfo]:
        """Get GPU information for specified device."""
        if not self.is_gpu_monitoring_available():
            return None
        
        try:
            import pynvml
            
            handle = pynvml.nvmlDeviceGetHandleByIndex(device_index)
            
            # Get device name
            name_bytes = pynvml.nvmlDeviceGetName(handle)
            name = name_bytes.decode('utf-8') if isinstance(name_bytes, bytes) else name_bytes
            
            # Get memory info
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            total_memory = mem_info.total // (1024 * 1024)  # Convert to MB
            used_memory = mem_info.used // (1024 * 1024)    # Convert to MB
            free_memory = mem_info.free // (1024 * 1024)    # Convert to MB
            
            # Get utilization
            try:
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                utilization = util.gpu
            except pynvml.NVMLError:
                utilization = 0
            
            # Get temperature
            try:
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except pynvml.NVMLError:
                temperature = 0
            
            return GPUInfo(
                name=name,
                total_memory=total_memory,
                used_memory=used_memory,
                free_memory=free_memory,
                utilization=utilization,
                temperature=temperature,
                available=True
            )
            
        except Exception as e:
            logger.error(f"Error getting GPU info: {e}")
            return None
    
    def get_all_gpu_info(self) -> Dict[int, GPUInfo]:
        """Get information for all available GPUs."""
        gpu_info = {}
        
        if not self.is_gpu_monitoring_available():
            return gpu_info
        
        for i in range(self._device_count):
            info = self.get_gpu_info(i)
            if info:
                gpu_info[i] = info
        
        return gpu_info
    
    def get_cuda_device_info(self) -> Optional[Dict[str, Any]]:
        """Get CUDA device information from PyTorch."""
        if not self._cuda_available:
            return None
        
        try:
            import torch
            
            if not torch.cuda.is_available():
                return None
            
            device_info = {
                'device_count': torch.cuda.device_count(),
                'current_device': torch.cuda.current_device(),
                'device_name': torch.cuda.get_device_name(0),
                'device_capability': torch.cuda.get_device_capability(0),
                'memory_allocated': torch.cuda.memory_allocated(0) // (1024 * 1024),  # MB
                'memory_reserved': torch.cuda.memory_reserved(0) // (1024 * 1024),    # MB
                'max_memory_allocated': torch.cuda.max_memory_allocated(0) // (1024 * 1024),  # MB
            }
            
            return device_info
            
        except Exception as e:
            logger.error(f"Error getting CUDA device info: {e}")
            return None
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get comprehensive device status."""
        status = {
            'gpu_monitoring_available': self.is_gpu_monitoring_available(),
            'cuda_available': self.is_cuda_available(),
            'device_count': self._device_count,
            'primary_gpu': None,
            'cuda_info': None
        }
        
        # Get primary GPU info
        if self.is_gpu_monitoring_available():
            status['primary_gpu'] = self.get_gpu_info(0)
        
        # Get CUDA info
        if self.is_cuda_available():
            status['cuda_info'] = self.get_cuda_device_info()
        
        return status
    
    def get_memory_usage_percentage(self, device_index: int = 0) -> int:
        """Get GPU memory usage as percentage."""
        gpu_info = self.get_gpu_info(device_index)
        if gpu_info and gpu_info.total_memory > 0:
            return int((gpu_info.used_memory / gpu_info.total_memory) * 100)
        return 0
    
    def get_utilization_percentage(self, device_index: int = 0) -> int:
        """Get GPU utilization as percentage."""
        gpu_info = self.get_gpu_info(device_index)
        if gpu_info:
            return gpu_info.utilization
        return 0
    
    def format_memory_info(self, device_index: int = 0) -> str:
        """Format memory information for display."""
        gpu_info = self.get_gpu_info(device_index)
        if gpu_info:
            return f"{gpu_info.used_memory}MB / {gpu_info.total_memory}MB"
        return "N/A"
    
    def get_temperature_status(self, device_index: int = 0) -> tuple[int, str]:
        """Get temperature and status color."""
        gpu_info = self.get_gpu_info(device_index)
        if not gpu_info:
            return 0, "gray"
        
        temp = gpu_info.temperature
        if temp < 60:
            return temp, "green"
        elif temp < 80:
            return temp, "orange"
        else:
            return temp, "red"


# Global instance for use throughout the application
gpu_monitor = GPUMonitor()