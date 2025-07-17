"""System profiling for comprehensive hardware and OS information."""

import platform
import time
import psutil
from datetime import datetime
from typing import Dict, Any

# Import existing hardware info function
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from performance import get_hardware_info


class SystemProfiler:
    """Collects comprehensive system and hardware information."""
    
    def __init__(self):
        self.system_info = self._gather_system_info()
        self.hardware_info = self._gather_enhanced_hardware_info()
    
    def _gather_system_info(self) -> Dict[str, Any]:
        """Collect operating system information."""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'hostname': platform.node(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat(),
            'timezone': time.tzname[0],
            'platform_full': platform.platform()
        }
    
    def _gather_enhanced_hardware_info(self) -> Dict[str, Any]:
        """Collect detailed hardware information."""
        # Use existing hardware info as base
        base_info = get_hardware_info()
        
        # Enhance with additional details
        cpu_info = self._get_detailed_cpu_info()
        memory_info = self._get_detailed_memory_info()
        disk_info = self._get_disk_info()
        gpu_info = self._get_gpu_info()
        
        return {
            **base_info,  # Include existing hardware info
            'cpu_detailed': cpu_info,
            'memory_detailed': memory_info,
            'disk': disk_info,
            'gpu': gpu_info
        }
    
    def _get_detailed_cpu_info(self) -> Dict[str, Any]:
        """Get detailed CPU information."""
        cpu_freq = psutil.cpu_freq()
        cpu_stats = psutil.cpu_stats()
        
        return {
            'model': platform.processor() or 'Unknown',
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'max_frequency_mhz': cpu_freq.max if cpu_freq else None,
            'current_frequency_mhz': cpu_freq.current if cpu_freq else None,
            'architecture': platform.machine(),
            'byte_order': platform.architecture()[1],
            'cpu_stats': {
                'ctx_switches': cpu_stats.ctx_switches,
                'interrupts': cpu_stats.interrupts,
                'soft_interrupts': cpu_stats.soft_interrupts,
                'syscalls': cpu_stats.syscalls if hasattr(cpu_stats, 'syscalls') else None
            }
        }
    
    def _get_detailed_memory_info(self) -> Dict[str, Any]:
        """Get detailed memory information."""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total_gb': round(memory.total / (1024**3), 2),
            'available_gb': round(memory.available / (1024**3), 2),
            'used_gb': round(memory.used / (1024**3), 2),
            'free_gb': round(memory.free / (1024**3), 2),
            'usage_percent': memory.percent,
            'swap_total_gb': round(swap.total / (1024**3), 2),
            'swap_used_gb': round(swap.used / (1024**3), 2),
            'swap_percent': swap.percent
        }
    
    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage information."""
        try:
            disk_usage = psutil.disk_usage('/')
            disk_io = psutil.disk_io_counters()
            
            return {
                'total_gb': round(disk_usage.total / (1024**3), 1),
                'used_gb': round(disk_usage.used / (1024**3), 1),
                'free_gb': round(disk_usage.free / (1024**3), 1),
                'usage_percent': round((disk_usage.used / disk_usage.total) * 100, 1),
                'io_stats': {
                    'read_bytes': disk_io.read_bytes if disk_io else 0,
                    'write_bytes': disk_io.write_bytes if disk_io else 0,
                    'read_count': disk_io.read_count if disk_io else 0,
                    'write_count': disk_io.write_count if disk_io else 0
                } if disk_io else None
            }
        except (OSError, AttributeError):
            return {'available': False, 'error': 'Disk info not accessible'}
    
    def _get_gpu_info(self) -> Dict[str, Any]:
        """Detect GPU information for FastWhisper acceleration."""
        gpu_info = {
            'cuda_available': False,
            'cuda_version': None,
            'gpu_count': 0,
            'gpu_models': [],
            'total_vram_gb': 0,
            'driver_version': None
        }
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_info['cuda_available'] = True
                gpu_info['cuda_version'] = torch.version.cuda
                gpu_info['gpu_count'] = torch.cuda.device_count()
                
                total_vram = 0
                for i in range(gpu_info['gpu_count']):
                    props = torch.cuda.get_device_properties(i)
                    vram_gb = props.total_memory / (1024**3)
                    total_vram += vram_gb
                    
                    gpu_info['gpu_models'].append({
                        'index': i,
                        'name': props.name,
                        'vram_gb': round(vram_gb, 1),
                        'compute_capability': f"{props.major}.{props.minor}",
                        'multi_processor_count': props.multi_processor_count
                    })
                
                gpu_info['total_vram_gb'] = round(total_vram, 1)
                
                # Try to get driver version
                try:
                    import pynvml
                    pynvml.nvmlInit()
                    driver_version = pynvml.nvmlSystemGetDriverVersion()
                    if isinstance(driver_version, bytes):
                        gpu_info['driver_version'] = driver_version.decode()
                    else:
                        gpu_info['driver_version'] = driver_version
                except ImportError:
                    pass
                    
        except ImportError:
            gpu_info['torch_available'] = False
        
        return gpu_info
    
    def get_system_summary(self) -> str:
        """Return formatted system summary."""
        cpu = self.hardware_info['cpu_detailed']
        memory = self.hardware_info['memory_detailed']
        disk = self.hardware_info['disk']
        gpu = self.hardware_info['gpu']
        
        summary_lines = [
            "🖥️  INFORMAÇÕES DO SISTEMA:",
            f"   • OS: {self.system_info['os']} {self.system_info['os_release']}",
            f"   • Arquitetura: {self.system_info['architecture']}",
            f"   • Hostname: {self.system_info['hostname']}",
            f"   • Python: {self.system_info['python_version']}",
            "",
            "💻 HARDWARE:",
            f"   • CPU: {cpu['model'][:50]}..." if len(cpu['model']) > 50 else f"   • CPU: {cpu['model']}",
            f"   • Cores: {cpu['physical_cores']} físicos / {cpu['logical_cores']} lógicos",
        ]
        
        if cpu['current_frequency_mhz']:
            summary_lines.append(f"   • Frequência: {cpu['current_frequency_mhz']:.0f}MHz / {cpu['max_frequency_mhz']:.0f}MHz")
        
        summary_lines.extend([
            f"   • RAM: {memory['total_gb']}GB total, {memory['available_gb']}GB disponível ({memory['usage_percent']:.1f}% uso)",
            f"   • Disco: {disk['free_gb']}GB livres de {disk['total_gb']}GB ({disk['usage_percent']:.1f}% uso)" if disk.get('total_gb') else "   • Disco: Informações não disponíveis"
        ])
        
        if gpu['cuda_available']:
            gpu_models = ", ".join([g['name'] for g in gpu['gpu_models']])
            summary_lines.extend([
                f"   • GPU: {gpu_models}",
                f"   • VRAM: {gpu['total_vram_gb']}GB total",
                f"   • CUDA: {gpu['cuda_version']}"
            ])
        else:
            summary_lines.append("   • GPU: CUDA não disponível")
        
        return "\n".join(summary_lines)
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment variables relevant to FastWhisper."""
        ct2_vars = {k: v for k, v in os.environ.items() if k.startswith('CT2_')}
        omp_vars = {k: v for k, v in os.environ.items() if k.startswith('OMP_')}
        cuda_vars = {k: v for k, v in os.environ.items() if k.startswith('CUDA_')}
        
        return {
            'ct2_variables': ct2_vars,
            'omp_variables': omp_vars,
            'cuda_variables': cuda_vars,
            'total_env_vars': len(os.environ)
        }