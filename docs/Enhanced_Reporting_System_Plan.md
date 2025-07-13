# Plano de Sistema de Relatórios Avançado - VoxSynopsis

**Data de Criação:** Janeiro 2025  
**Status:** 📋 PLANEJAMENTO  
**Versão:** 1.0  
**Autor:** Claude Code Analysis  

## 📊 Resumo Executivo

Este documento especifica a implementação de um **Sistema de Relatórios Avançado** para resolver as deficiências atuais nos relatórios de transcrição, incluindo valores N/A, falta de timestamps, informações de sistema e métricas de performance em tempo real.

### 🎯 Objetivos
- **Informações Completas:** Eliminar todos os valores N/A dos relatórios
- **Timestamps Precisos:** Horário de início, fim e duração detalhados
- **Profiling de Sistema:** CPU, RAM, disk I/O durante processamento
- **Métricas Avançadas:** Speedup real, eficiência, throughput
- **Análise de Performance:** Dados para otimização futura

---

## 🔍 Análise dos Problemas Atuais

### ❌ **Problemas Identificados:**

1. **Configurações N/A**
   ```
   • Modelo: N/A              ← Deveria ser 'base', 'large-v3', etc.
   • Dispositivo: N/A          ← Deveria ser 'cpu', 'cuda', etc.
   • Tipo de computação: N/A   ← Deveria ser 'int8', 'float16', etc.
   • Threads CPU: N/A          ← Deveria ser número real (6, 8, etc.)
   ```

2. **Falta de Timestamps**
   ```
   ❌ Ausente: Horário de início
   ❌ Ausente: Horário de fim  
   ❌ Ausente: Duração total com precisão
   ❌ Ausente: Breakdown por fase (loading, processing, saving)
   ```

3. **Informações de Sistema Ausentes**
   ```
   ❌ Ausente: Specs da máquina (CPU model, cores, RAM)
   ❌ Ausente: Sistema operacional e arquitetura
   ❌ Ausente: Uso de recursos durante processamento
   ❌ Ausente: Temperatura CPU, frequência
   ```

4. **Métricas de Performance Limitadas**
   ```
   ❌ Speedup incorreto (1.0x quando deveria ser maior)
   ❌ Ausente: Throughput (arquivos/min, MB/s)
   ❌ Ausente: Eficiência de paralelização
   ❌ Ausente: Gargalos identificados
   ```

---

## 🏗️ Arquitetura da Solução

### Componentes Principais

```
┌─────────────────────────────────────────────────────────────┐
│                   Enhanced Reporting System                 │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ System Profiler │    │ Performance     │                │
│  │ & Hardware Info │───▶│ Monitor         │                │
│  │                 │    │                 │                │
│  └─────────────────┘    └─────────────────┘                │
│           │                       │                         │
│           ▼                       ▼                         │
│  ┌─────────────────┐    ┌─────────────────┐                │
│  │ Timestamp       │    │ Enhanced Report │                │
│  │ Manager         │    │ Generator       │                │
│  └─────────────────┘    └─────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### Módulos a Implementar

1. **SystemProfiler** (`core/system_profiler.py`)
   - Detecção de hardware (CPU, RAM, GPU)
   - Informações do SO e arquitetura
   - Monitoramento de recursos em tempo real

2. **PerformanceMonitor** (`core/performance_monitor.py`)
   - Tracking de CPU/RAM durante processamento
   - Cálculo de throughput e eficiência
   - Identificação de gargalos

3. **TimestampManager** (`core/timestamp_manager.py`)
   - Timestamps precisos para cada fase
   - Breakdown detalhado de tempo
   - Cálculo de overhead e processamento líquido

4. **EnhancedReportGenerator** (`core/enhanced_report.py`)
   - Templates de relatório estruturados
   - Formatação consistente e legível
   - Export para múltiplos formatos (JSON, HTML, MD)

---

## 📋 Fase 1: SystemProfiler - Informações de Sistema

### 1.1 Detecção de Hardware

```python
class SystemProfiler:
    def __init__(self):
        self.system_info = self._gather_system_info()
        self.hardware_info = self._gather_hardware_info()
    
    def _gather_system_info(self) -> dict:
        """Coleta informações do sistema operacional"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'os_release': platform.release(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'hostname': platform.node(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()),
            'timezone': time.tzname[0]
        }
    
    def _gather_hardware_info(self) -> dict:
        """Coleta informações de hardware"""
        cpu_info = self._get_cpu_details()
        memory_info = self._get_memory_details()
        disk_info = self._get_disk_details()
        gpu_info = self._get_gpu_details()
        
        return {
            'cpu': cpu_info,
            'memory': memory_info,
            'disk': disk_info,
            'gpu': gpu_info
        }
    
    def _get_cpu_details(self) -> dict:
        """Informações detalhadas da CPU"""
        return {
            'model': self._get_cpu_model(),
            'physical_cores': psutil.cpu_count(logical=False),
            'logical_cores': psutil.cpu_count(logical=True),
            'max_frequency': psutil.cpu_freq().max if psutil.cpu_freq() else None,
            'current_frequency': psutil.cpu_freq().current if psutil.cpu_freq() else None,
            'architecture': platform.machine(),
            'cache_info': self._get_cpu_cache_info()
        }
    
    def _get_memory_details(self) -> dict:
        """Informações de memória"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total_ram_gb': round(memory.total / (1024**3), 1),
            'available_ram_gb': round(memory.available / (1024**3), 1),
            'ram_usage_percent': memory.percent,
            'swap_total_gb': round(swap.total / (1024**3), 1),
            'swap_used_gb': round(swap.used / (1024**3), 1)
        }
    
    def get_system_summary(self) -> str:
        """Retorna resumo formatado do sistema"""
        cpu = self.hardware_info['cpu']
        memory = self.hardware_info['memory']
        
        return f"""
🖥️  INFORMAÇÕES DO SISTEMA:
   • OS: {self.system_info['os']} {self.system_info['os_release']}
   • Arquitetura: {self.system_info['architecture']}
   • CPU: {cpu['model']} ({cpu['physical_cores']}C/{cpu['logical_cores']}T)
   • RAM: {memory['total_ram_gb']}GB total, {memory['available_ram_gb']}GB disponível
   • Frequência CPU: {cpu['current_frequency']:.0f}MHz / {cpu['max_frequency']:.0f}MHz
   • Python: {self.system_info['python_version']}
   • Hostname: {self.system_info['hostname']}
        """.strip()
```

### 1.2 Detecção de GPU e Aceleração

```python
def _get_gpu_details(self) -> dict:
    """Detecta informações de GPU para FastWhisper"""
    gpu_info = {
        'cuda_available': False,
        'cuda_version': None,
        'gpu_count': 0,
        'gpu_models': [],
        'total_vram_gb': 0
    }
    
    try:
        import torch
        if torch.cuda.is_available():
            gpu_info['cuda_available'] = True
            gpu_info['cuda_version'] = torch.version.cuda
            gpu_info['gpu_count'] = torch.cuda.device_count()
            
            for i in range(gpu_info['gpu_count']):
                gpu_name = torch.cuda.get_device_name(i)
                vram = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                gpu_info['gpu_models'].append({
                    'index': i,
                    'name': gpu_name,
                    'vram_gb': round(vram, 1)
                })
                gpu_info['total_vram_gb'] += vram
    except ImportError:
        pass
    
    return gpu_info
```

---

## 📋 Fase 2: PerformanceMonitor - Monitoramento em Tempo Real

### 2.1 Monitoramento de Recursos

```python
class PerformanceMonitor:
    def __init__(self, monitoring_interval: float = 0.5):
        self.monitoring_interval = monitoring_interval
        self.monitoring_thread = None
        self.is_monitoring = False
        self.performance_data = {
            'cpu_usage': [],
            'memory_usage': [],
            'disk_io': [],
            'network_io': [],
            'timestamps': []
        }
    
    def start_monitoring(self):
        """Inicia monitoramento de performance"""
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Para monitoramento e retorna dados coletados"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        return self.get_performance_summary()
    
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        process = psutil.Process()
        
        while self.is_monitoring:
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=None)
                process_cpu = process.cpu_percent()
                
                # Memory usage
                memory = psutil.virtual_memory()
                process_memory = process.memory_info()
                
                # Disk I/O
                disk_io = psutil.disk_io_counters()
                
                # Network I/O
                network_io = psutil.net_io_counters()
                
                # Store data
                timestamp = time.time()
                self.performance_data['timestamps'].append(timestamp)
                self.performance_data['cpu_usage'].append({
                    'system': cpu_percent,
                    'process': process_cpu
                })
                self.performance_data['memory_usage'].append({
                    'system_percent': memory.percent,
                    'system_used_gb': memory.used / (1024**3),
                    'process_rss_mb': process_memory.rss / (1024**2),
                    'process_vms_mb': process_memory.vms / (1024**2)
                })
                
                if disk_io:
                    self.performance_data['disk_io'].append({
                        'read_bytes': disk_io.read_bytes,
                        'write_bytes': disk_io.write_bytes,
                        'read_count': disk_io.read_count,
                        'write_count': disk_io.write_count
                    })
                
                if network_io:
                    self.performance_data['network_io'].append({
                        'bytes_sent': network_io.bytes_sent,
                        'bytes_recv': network_io.bytes_recv
                    })
                
                time.sleep(self.monitoring_interval)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
    
    def get_performance_summary(self) -> dict:
        """Calcula resumo de performance"""
        if not self.performance_data['timestamps']:
            return {}
        
        cpu_data = self.performance_data['cpu_usage']
        memory_data = self.performance_data['memory_usage']
        
        return {
            'duration_seconds': self.performance_data['timestamps'][-1] - self.performance_data['timestamps'][0],
            'cpu_stats': {
                'avg_system_percent': statistics.mean([d['system'] for d in cpu_data]),
                'max_system_percent': max([d['system'] for d in cpu_data]),
                'avg_process_percent': statistics.mean([d['process'] for d in cpu_data]),
                'max_process_percent': max([d['process'] for d in cpu_data])
            },
            'memory_stats': {
                'avg_system_percent': statistics.mean([d['system_percent'] for d in memory_data]),
                'max_system_percent': max([d['system_percent'] for d in memory_data]),
                'avg_process_mb': statistics.mean([d['process_rss_mb'] for d in memory_data]),
                'max_process_mb': max([d['process_rss_mb'] for d in memory_data]),
                'peak_memory_gb': max([d['process_rss_mb'] for d in memory_data]) / 1024
            },
            'resource_efficiency': self._calculate_efficiency()
        }
```

---

## 📋 Fase 3: TimestampManager - Timestamps Precisos

### 3.1 Gerenciamento de Timestamps

```python
class TimestampManager:
    def __init__(self):
        self.timestamps = {}
        self.phases = {}
        self.start_time = None
        self.end_time = None
    
    def start_session(self, session_name: str = "transcription"):
        """Inicia uma sessão de timestamp"""
        self.start_time = time.time()
        self.timestamps[session_name] = {
            'start': self.start_time,
            'start_formatted': datetime.now().isoformat(),
            'phases': {}
        }
    
    def start_phase(self, phase_name: str):
        """Inicia uma fase específica"""
        if not self.start_time:
            raise ValueError("Session not started. Call start_session() first.")
        
        phase_start = time.time()
        self.phases[phase_name] = {
            'start': phase_start,
            'start_formatted': datetime.now().isoformat()
        }
    
    def end_phase(self, phase_name: str):
        """Finaliza uma fase específica"""
        if phase_name not in self.phases:
            raise ValueError(f"Phase '{phase_name}' was not started.")
        
        phase_end = time.time()
        self.phases[phase_name].update({
            'end': phase_end,
            'end_formatted': datetime.now().isoformat(),
            'duration_seconds': phase_end - self.phases[phase_name]['start']
        })
    
    def end_session(self, session_name: str = "transcription"):
        """Finaliza a sessão"""
        self.end_time = time.time()
        if session_name in self.timestamps:
            self.timestamps[session_name].update({
                'end': self.end_time,
                'end_formatted': datetime.now().isoformat(),
                'total_duration_seconds': self.end_time - self.start_time,
                'phases': self.phases.copy()
            })
    
    def get_timing_summary(self) -> str:
        """Retorna resumo formatado dos tempos"""
        if not self.start_time or not self.end_time:
            return "Session not completed"
        
        total_duration = self.end_time - self.start_time
        start_dt = datetime.fromtimestamp(self.start_time)
        end_dt = datetime.fromtimestamp(self.end_time)
        
        summary = f"""
⏰ INFORMAÇÕES DE TEMPO:
   • Início: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}
   • Fim: {end_dt.strftime('%Y-%m-%d %H:%M:%S')}
   • Duração Total: {total_duration:.1f}s ({total_duration/60:.1f} min)
        """
        
        if self.phases:
            summary += "\n📊 BREAKDOWN POR FASE:"
            for phase_name, phase_data in self.phases.items():
                if 'duration_seconds' in phase_data:
                    duration = phase_data['duration_seconds']
                    percentage = (duration / total_duration) * 100
                    summary += f"\n   • {phase_name}: {duration:.1f}s ({percentage:.1f}%)"
        
        return summary.strip()
```

---

## 📋 Fase 4: EnhancedReportGenerator - Relatórios Completos

### 4.1 Gerador de Relatórios Avançado

```python
class EnhancedReportGenerator:
    def __init__(self, system_profiler: SystemProfiler, 
                 performance_monitor: PerformanceMonitor,
                 timestamp_manager: TimestampManager):
        self.system_profiler = system_profiler
        self.performance_monitor = performance_monitor
        self.timestamp_manager = timestamp_manager
    
    def generate_comprehensive_report(self, 
                                    transcription_results: dict,
                                    whisper_settings: dict) -> str:
        """Gera relatório completo com todas as informações"""
        
        # Seções do relatório
        header = self._generate_header()
        system_info = self.system_profiler.get_system_summary()
        timing_info = self.timestamp_manager.get_timing_summary()
        configuration_info = self._generate_configuration_section(whisper_settings)
        performance_info = self._generate_performance_section()
        results_info = self._generate_results_section(transcription_results)
        analysis_info = self._generate_analysis_section(transcription_results)
        
        # Combinar todas as seções
        report = f"""
{header}
{system_info}

{timing_info}

{configuration_info}

{performance_info}

{results_info}

{analysis_info}

{'='*80}
""".strip()
        
        return report
    
    def _generate_header(self) -> str:
        """Cabeçalho do relatório"""
        return f"""
{'='*80}
🎯 RELATÓRIO DETALHADO DE TRANSCRIÇÃO - VOXSYNOPSIS
{'='*80}
📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 Versão: VoxSynopsis v2.0 com FastWhisper
{'='*80}
        """.strip()
    
    def _generate_configuration_section(self, settings: dict) -> str:
        """Seção de configurações sem N/A"""
        config_lines = ["⚙️  CONFIGURAÇÕES DE TRANSCRIÇÃO:"]
        
        # Mapear configurações com valores padrão inteligentes
        config_mapping = {
            'model_size': ('Modelo FastWhisper', settings.get('model_size', 'base')),
            'device': ('Dispositivo de Processamento', settings.get('device', 'cpu')),
            'compute_type': ('Tipo de Computação', settings.get('compute_type', 'int8')),
            'cpu_threads': ('Threads CPU', settings.get('cpu_threads', psutil.cpu_count(logical=False))),
            'batch_size': ('Tamanho do Lote', settings.get('batch_size', 8)),
            'language': ('Idioma', settings.get('language', 'pt')),
            'temperature': ('Temperatura', settings.get('temperature', 0.0)),
            'beam_size': ('Beam Size', settings.get('beam_size', 1)),
            'vad_filter': ('Filtro VAD', 'Sim' if settings.get('vad_filter', True) else 'Não'),
            'condition_on_previous_text': ('Condicionamento Texto Anterior', 'Sim' if settings.get('condition_on_previous_text', False) else 'Não')
        }
        
        for key, (label, value) in config_mapping.items():
            config_lines.append(f"   • {label}: {value}")
        
        return "\n".join(config_lines)
    
    def _generate_performance_section(self) -> str:
        """Seção de performance com métricas detalhadas"""
        perf_data = self.performance_monitor.get_performance_summary()
        
        if not perf_data:
            return "⚡ PERFORMANCE: Dados não disponíveis"
        
        cpu_stats = perf_data['cpu_stats']
        memory_stats = perf_data['memory_stats']
        
        return f"""
⚡ PERFORMANCE DO SISTEMA:
   • CPU Média (Sistema): {cpu_stats['avg_system_percent']:.1f}%
   • CPU Pico (Sistema): {cpu_stats['max_system_percent']:.1f}%
   • CPU Média (Processo): {cpu_stats['avg_process_percent']:.1f}%
   • CPU Pico (Processo): {cpu_stats['max_process_percent']:.1f}%
   • RAM Média (Sistema): {memory_stats['avg_system_percent']:.1f}%
   • RAM Pico (Sistema): {memory_stats['max_system_percent']:.1f}%
   • RAM Média (Processo): {memory_stats['avg_process_mb']:.0f}MB
   • RAM Pico (Processo): {memory_stats['max_process_mb']:.0f}MB
   • Pico de Memória: {memory_stats['peak_memory_gb']:.1f}GB
        """.strip()
    
    def _generate_analysis_section(self, results: dict) -> str:
        """Seção de análise e recomendações"""
        analysis_lines = ["🔍 ANÁLISE E RECOMENDAÇÕES:"]
        
        # Análise de eficiência
        total_files = results.get('total_files', 0)
        processing_time = results.get('total_processing_time', 0)
        
        if total_files > 0 and processing_time > 0:
            throughput = total_files / (processing_time / 60)  # arquivos por minuto
            analysis_lines.append(f"   • Throughput: {throughput:.1f} arquivos/min")
            
            if throughput < 5:
                analysis_lines.append("   • ⚠️  Throughput baixo - considere otimizações")
            elif throughput > 20:
                analysis_lines.append("   • ✅ Throughput excelente")
            else:
                analysis_lines.append("   • ✅ Throughput adequado")
        
        return "\n".join(analysis_lines)
```

---

## 📋 Integração com Sistema Existente

### 5.1 Modificações no BatchTranscriptionThread

```python
class BatchTranscriptionThread(QThread):
    def __init__(self, audio_files: List[str], whisper_settings: dict[str, Any]) -> None:
        super().__init__()
        
        # Inicializar componentes de relatório avançado
        self.system_profiler = SystemProfiler()
        self.performance_monitor = PerformanceMonitor()
        self.timestamp_manager = TimestampManager()
        self.report_generator = EnhancedReportGenerator(
            self.system_profiler, 
            self.performance_monitor, 
            self.timestamp_manager
        )
        
        # Configurações preservadas (sem pop)
        self.original_settings = whisper_settings.copy()
        
    def run(self):
        """Executa transcrição com monitoramento completo"""
        try:
            # Iniciar monitoramento
            self.timestamp_manager.start_session("batch_transcription")
            self.performance_monitor.start_monitoring()
            
            # Fase 1: Inicialização
            self.timestamp_manager.start_phase("initialization")
            # ... código de inicialização ...
            self.timestamp_manager.end_phase("initialization")
            
            # Fase 2: Processamento
            self.timestamp_manager.start_phase("processing")
            # ... código de processamento ...
            self.timestamp_manager.end_phase("processing")
            
            # Fase 3: Finalização
            self.timestamp_manager.start_phase("finalization")
            # ... código de finalização ...
            self.timestamp_manager.end_phase("finalization")
            
        finally:
            # Parar monitoramento
            self.performance_monitor.stop_monitoring()
            self.timestamp_manager.end_session("batch_transcription")
    
    def _generate_final_report(self, successful_results: List[Dict], 
                             failed_results: List[Dict], total_time: float) -> str:
        """Gera relatório final completo"""
        
        # Dados de resultado
        transcription_results = {
            'total_files': len(self.audio_files),
            'successful_files': len(successful_results),
            'failed_files': len(failed_results),
            'total_processing_time': total_time,
            'success_rate': len(successful_results) / len(self.audio_files) * 100,
            'average_time_per_file': total_time / len(successful_results) if successful_results else 0
        }
        
        # Gerar relatório completo
        return self.report_generator.generate_comprehensive_report(
            transcription_results, 
            self.original_settings
        )
```

---

## 🎯 Exemplo de Relatório Final Esperado

```
================================================================================
🎯 RELATÓRIO DETALHADO DE TRANSCRIÇÃO - VOXSYNOPSIS
================================================================================
📅 Data/Hora: 2025-01-15 14:32:18
🔧 Versão: VoxSynopsis v2.0 com FastWhisper
================================================================================

🖥️  INFORMAÇÕES DO SISTEMA:
   • OS: Linux 6.6.87.2-microsoft-standard-WSL2
   • Arquitetura: x86_64
   • CPU: Intel(R) Core(TM) i7-10750H CPU @ 2.60GHz (6C/12T)
   • RAM: 16.0GB total, 12.3GB disponível
   • Frequência CPU: 2600MHz / 4800MHz
   • Python: 3.12.3
   • Hostname: DESKTOP-ABC123

⏰ INFORMAÇÕES DE TEMPO:
   • Início: 2025-01-15 14:25:30
   • Fim: 2025-01-15 14:32:18
   • Duração Total: 408.0s (6.8 min)

📊 BREAKDOWN POR FASE:
   • initialization: 12.3s (3.0%)
   • processing: 380.5s (93.3%)
   • finalization: 15.2s (3.7%)

⚙️  CONFIGURAÇÕES DE TRANSCRIÇÃO:
   • Modelo FastWhisper: large-v3
   • Dispositivo de Processamento: cpu
   • Tipo de Computação: int8
   • Threads CPU: 6
   • Tamanho do Lote: 8
   • Idioma: pt
   • Temperatura: 0.0
   • Beam Size: 1
   • Filtro VAD: Sim
   • Condicionamento Texto Anterior: Não

⚡ PERFORMANCE DO SISTEMA:
   • CPU Média (Sistema): 45.2%
   • CPU Pico (Sistema): 78.9%
   • CPU Média (Processo): 67.8%
   • CPU Pico (Processo): 95.2%
   • RAM Média (Sistema): 32.1%
   • RAM Pico (Sistema): 48.7%
   • RAM Média (Processo): 2.3GB
   • RAM Pico (Processo): 3.8GB
   • Pico de Memória: 3.8GB

📊 RESULTADOS DE TRANSCRIÇÃO:
   • Total de arquivos: 130
   • Processados com sucesso: 130
   • Falharam: 0
   • Taxa de sucesso: 100.0%
   • Tempo total de processamento: 408.0s (6.8 min)
   • Tempo médio por arquivo: 3.1s
   • Speedup por paralelização: 4.2x
   • Fator tempo real médio: 8.7x

🔍 ANÁLISE E RECOMENDAÇÕES:
   • Throughput: 19.1 arquivos/min
   • ✅ Throughput adequado
   • ✅ Uso eficiente de CPU (67.8% média)
   • ✅ Uso de memória controlado (3.8GB pico)
   • 💡 Consideração: CPU teve picos de 95% - modelo menor pode ser mais eficiente

================================================================================
```

---

## 🚀 Próximos Passos

### Implementação Proposta (6-8 horas):

1. **Fase 1 (2h):** SystemProfiler - Informações de sistema e hardware
2. **Fase 2 (2h):** PerformanceMonitor - Monitoramento em tempo real  
3. **Fase 3 (1h):** TimestampManager - Timestamps precisos
4. **Fase 4 (2h):** EnhancedReportGenerator - Relatórios completos
5. **Fase 5 (1h):** Integração e testes

### Benefícios Esperados:

- ✅ **Zero valores N/A** nos relatórios
- ✅ **Timestamps precisos** com breakdown por fase
- ✅ **Informações completas** do sistema e hardware
- ✅ **Métricas de performance** em tempo real
- ✅ **Análise actionable** para otimizações futuras

---

## 📚 Dependências Adicionais

```python
# Não requer novas dependências - usa apenas bibliotecas já disponíveis:
import psutil      # ✅ Já presente
import platform    # ✅ Built-in Python
import threading   # ✅ Built-in Python  
import statistics  # ✅ Built-in Python
import datetime    # ✅ Built-in Python
import time        # ✅ Built-in Python
```

---

## ✅ Validação com Gemini CLI

**Próximo passo:** Enviar este plano para o Gemini CLI para validação e sugestões de melhoria, focando em:

1. Completude das informações coletadas
2. Eficiência do monitoramento em tempo real
3. Qualidade e utilidade dos relatórios gerados
4. Possíveis melhorias na análise de performance
5. Sugestões de métricas adicionais relevantes