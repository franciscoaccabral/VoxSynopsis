"""Real-time performance monitoring during transcription processing."""

import threading
import time
import statistics
import psutil
from typing import Dict, List, Any, Optional


class PerformanceMonitor:
    """Monitor system and process performance in real-time."""
    
    def __init__(self, monitoring_interval: float = 0.5):
        self.monitoring_interval = monitoring_interval
        self.monitoring_thread: Optional[threading.Thread] = None
        self.is_monitoring = False
        self.process = psutil.Process()
        
        # Performance data storage
        self.performance_data: Dict[str, List] = {
            'timestamps': [],
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': [],
            'process_stats': []
        }
        
        # Initial baselines
        self._initial_disk_io = psutil.disk_io_counters()
    
    def start_monitoring(self) -> None:
        """Start performance monitoring in background thread."""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.performance_data = {key: [] for key in self.performance_data.keys()}
        self._initial_disk_io = psutil.disk_io_counters()
        
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop monitoring and return performance summary."""
        if not self.is_monitoring:
            return {}
            
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        
        return self.get_performance_summary()
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop running in background thread."""
        while self.is_monitoring:
            try:
                timestamp = time.time()
                
                # System CPU usage
                cpu_percent = psutil.cpu_percent(interval=None, percpu=False)
                cpu_percpu = psutil.cpu_percent(interval=None, percpu=True)
                
                # Process CPU usage
                try:
                    process_cpu = self.process.cpu_percent()
                    process_memory = self.process.memory_info()
                    process_threads = self.process.num_threads()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    process_cpu = 0
                    process_memory = None
                    process_threads = 0
                
                # System memory
                memory = psutil.virtual_memory()
                
                # Disk I/O
                current_disk_io = psutil.disk_io_counters()
                
                # Store data
                self.performance_data['timestamps'].append(timestamp)
                
                self.performance_data['cpu_usage'].append({
                    'system_total': cpu_percent,
                    'system_per_cpu': cpu_percpu,
                    'process_cpu': process_cpu
                })
                
                self.performance_data['memory_usage'].append({
                    'system_percent': memory.percent,
                    'system_used_gb': memory.used / (1024**3),
                    'system_available_gb': memory.available / (1024**3),
                    'process_rss_mb': process_memory.rss / (1024**2) if process_memory else 0,
                    'process_vms_mb': process_memory.vms / (1024**2) if process_memory else 0
                })
                
                if current_disk_io and self._initial_disk_io:
                    self.performance_data['disk_io'].append({
                        'read_bytes_delta': current_disk_io.read_bytes - self._initial_disk_io.read_bytes,
                        'write_bytes_delta': current_disk_io.write_bytes - self._initial_disk_io.write_bytes,
                        'read_count_delta': current_disk_io.read_count - self._initial_disk_io.read_count,
                        'write_count_delta': current_disk_io.write_count - self._initial_disk_io.write_count,
                        'current_read_bytes': current_disk_io.read_bytes,
                        'current_write_bytes': current_disk_io.write_bytes
                    })
                
                self.performance_data['process_stats'].append({
                    'threads': process_threads,
                    'cpu_percent': process_cpu
                })
                
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                # Log error but continue monitoring
                print(f"Warning: Performance monitoring error: {e}")
                time.sleep(self.monitoring_interval)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Calculate comprehensive performance summary."""
        if not self.performance_data['timestamps']:
            return {'error': 'No performance data collected'}
        
        duration = self.performance_data['timestamps'][-1] - self.performance_data['timestamps'][0]
        
        # CPU statistics
        cpu_data = self.performance_data['cpu_usage']
        cpu_stats = self._calculate_cpu_stats(cpu_data)
        
        # Memory statistics  
        memory_data = self.performance_data['memory_usage']
        memory_stats = self._calculate_memory_stats(memory_data)
        
        # Disk I/O statistics
        disk_stats = self._calculate_disk_stats()
        
        # Process statistics
        process_stats = self._calculate_process_stats()
        
        return {
            'monitoring_duration_seconds': duration,
            'data_points_collected': len(self.performance_data['timestamps']),
            'cpu_statistics': cpu_stats,
            'memory_statistics': memory_stats,
            'disk_statistics': disk_stats,
            'process_statistics': process_stats,
            'resource_efficiency': self._calculate_resource_efficiency(cpu_stats, memory_stats)
        }
    
    def _calculate_cpu_stats(self, cpu_data: List[Dict]) -> Dict[str, Any]:
        """Calculate CPU usage statistics."""
        if not cpu_data:
            return {}
        
        system_usage = [d['system_total'] for d in cpu_data]
        process_usage = [d['process_cpu'] for d in cpu_data]
        
        # Per-CPU statistics
        per_cpu_stats = {}
        if cpu_data[0]['system_per_cpu']:
            num_cpus = len(cpu_data[0]['system_per_cpu'])
            for cpu_idx in range(num_cpus):
                cpu_usage = [d['system_per_cpu'][cpu_idx] for d in cpu_data if len(d['system_per_cpu']) > cpu_idx]
                if cpu_usage:
                    per_cpu_stats[f'cpu_{cpu_idx}'] = {
                        'average': statistics.mean(cpu_usage),
                        'max': max(cpu_usage),
                        'min': min(cpu_usage)
                    }
        
        return {
            'system_average_percent': statistics.mean(system_usage),
            'system_max_percent': max(system_usage),
            'system_min_percent': min(system_usage),
            'system_stddev': statistics.stdev(system_usage) if len(system_usage) > 1 else 0,
            'process_average_percent': statistics.mean(process_usage),
            'process_max_percent': max(process_usage),
            'per_cpu_statistics': per_cpu_stats
        }
    
    def _calculate_memory_stats(self, memory_data: List[Dict]) -> Dict[str, Any]:
        """Calculate memory usage statistics."""
        if not memory_data:
            return {}
        
        system_percent = [d['system_percent'] for d in memory_data]
        system_used = [d['system_used_gb'] for d in memory_data]
        process_rss = [d['process_rss_mb'] for d in memory_data]
        
        return {
            'system_average_percent': statistics.mean(system_percent),
            'system_max_percent': max(system_percent),
            'system_average_used_gb': statistics.mean(system_used),
            'system_max_used_gb': max(system_used),
            'process_average_rss_mb': statistics.mean(process_rss),
            'process_max_rss_mb': max(process_rss),
            'process_peak_memory_gb': max(process_rss) / 1024
        }
    
    def _calculate_disk_stats(self) -> Dict[str, Any]:
        """Calculate disk I/O statistics."""
        disk_data = self.performance_data['disk_io']
        if not disk_data:
            return {'available': False}
        
        total_read_mb = disk_data[-1]['read_bytes_delta'] / (1024**2) if disk_data else 0
        total_write_mb = disk_data[-1]['write_bytes_delta'] / (1024**2) if disk_data else 0
        total_operations = (disk_data[-1]['read_count_delta'] + disk_data[-1]['write_count_delta']) if disk_data else 0
        
        return {
            'available': True,
            'total_read_mb': round(total_read_mb, 2),
            'total_write_mb': round(total_write_mb, 2),
            'total_io_mb': round(total_read_mb + total_write_mb, 2),
            'total_operations': total_operations
        }
    
    def _calculate_process_stats(self) -> Dict[str, Any]:
        """Calculate process-specific statistics."""
        process_data = self.performance_data['process_stats']
        if not process_data:
            return {}
        
        thread_counts = [d['threads'] for d in process_data]
        
        return {
            'average_threads': statistics.mean(thread_counts),
            'max_threads': max(thread_counts),
            'thread_stability': statistics.stdev(thread_counts) if len(thread_counts) > 1 else 0
        }
    
    def _calculate_resource_efficiency(self, cpu_stats: Dict, memory_stats: Dict) -> Dict[str, Any]:
        """Calculate overall resource efficiency metrics."""
        if not cpu_stats or not memory_stats:
            return {}
        
        # Efficiency scoring (0-1 scale)
        cpu_efficiency = min(cpu_stats['process_average_percent'] / 100, 1.0)
        memory_efficiency = min(memory_stats['process_peak_memory_gb'] / 8.0, 1.0)  # Assume 8GB as good baseline
        
        return {
            'cpu_efficiency_score': round(cpu_efficiency, 3),
            'memory_efficiency_score': round(memory_efficiency, 3),
            'overall_efficiency_score': round((cpu_efficiency + memory_efficiency) / 2, 3),
            'resource_usage_category': self._categorize_resource_usage(cpu_efficiency, memory_efficiency)
        }
    
    def _categorize_resource_usage(self, cpu_eff: float, memory_eff: float) -> str:
        """Categorize resource usage pattern."""
        if cpu_eff > 0.8 and memory_eff > 0.8:
            return "Heavy"
        elif cpu_eff > 0.6 or memory_eff > 0.6:
            return "Moderate"
        elif cpu_eff > 0.3 or memory_eff > 0.3:
            return "Light"
        else:
            return "Minimal"
    
    def get_real_time_stats(self) -> Dict[str, Any]:
        """Get current real-time performance statistics."""
        if not self.performance_data['timestamps']:
            return {}
        
        # Get latest data point
        latest_cpu = self.performance_data['cpu_usage'][-1] if self.performance_data['cpu_usage'] else {}
        latest_memory = self.performance_data['memory_usage'][-1] if self.performance_data['memory_usage'] else {}
        
        return {
            'current_cpu_system': latest_cpu.get('system_total', 0),
            'current_cpu_process': latest_cpu.get('process_cpu', 0),
            'current_memory_system_percent': latest_memory.get('system_percent', 0),
            'current_memory_process_mb': latest_memory.get('process_rss_mb', 0),
            'monitoring_active': self.is_monitoring,
            'data_points': len(self.performance_data['timestamps'])
        }