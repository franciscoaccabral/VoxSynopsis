"""Enhanced report generator for comprehensive transcription analysis."""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional

from .system_profiler import SystemProfiler
from .performance_monitor import PerformanceMonitor
from .timestamp_manager import TimestampManager


class EnhancedReportGenerator:
    """Generate comprehensive transcription reports with system analysis."""
    
    def __init__(self, 
                 system_profiler: SystemProfiler,
                 performance_monitor: PerformanceMonitor,
                 timestamp_manager: TimestampManager):
        self.system_profiler = system_profiler
        self.performance_monitor = performance_monitor
        self.timestamp_manager = timestamp_manager
    
    def generate_comprehensive_report(self,
                                    transcription_results: Dict[str, Any],
                                    whisper_settings: Dict[str, Any],
                                    include_transcriptions: bool = True) -> str:
        """Generate complete transcription report with all analysis."""
        
        # Report sections
        sections = [
            self._generate_header(),
            self.system_profiler.get_system_summary(),
            self.timestamp_manager.get_timing_report(),
            self._generate_configuration_section(whisper_settings),
            self._generate_performance_section(),
            self._generate_results_section(transcription_results),
            self._generate_analysis_section(transcription_results, whisper_settings)
        ]
        
        # Add transcriptions if requested and available
        if include_transcriptions and transcription_results.get('transcriptions'):
            sections.append(self._generate_transcription_section(transcription_results['transcriptions']))
        
        sections.append(self._generate_footer())
        
        return "\n\n".join(filter(None, sections))
    
    def _generate_header(self) -> str:
        """Generate report header with timestamp."""
        return f"""{'='*80}
🎯 RELATÓRIO DETALHADO DE TRANSCRIÇÃO - VOXSYNOPSIS
{'='*80}
📅 Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
🔧 Sistema de Relatórios Avançado v2.0
{'='*80}""".strip()
    
    def _generate_configuration_section(self, settings: Dict[str, Any]) -> str:
        """Generate configuration section with zero N/A values."""
        config_lines = ["⚙️  CONFIGURAÇÃO DE TRANSCRIÇÃO:"]
        
        # Enhanced configuration mapping with intelligent defaults
        config_mapping = [
            ('Modelo FastWhisper', settings.get('model_size', 'base')),
            ('Dispositivo de Processamento', settings.get('device', 'cpu')),
            ('Tipo de Computação', settings.get('compute_type', 'int8')),
            ('Threads CPU', settings.get('cpu_threads', self.system_profiler.hardware_info['physical_cores'])),
            ('Tamanho do Lote', settings.get('batch_size', 8)),
            ('Processamento em Lote', 'Ativo' if settings.get('use_batched_inference', True) else 'Inativo'),
            ('Idioma', settings.get('language', 'pt')),
            ('Temperatura', f"{settings.get('temperature', 0.0):.1f}"),
            ('Beam Size', settings.get('beam_size', 1)),
            ('Best Of', settings.get('best_of', 1)),
            ('Filtro VAD', 'Sim' if settings.get('vad_filter', True) else 'Não'),
            ('Condicionamento Texto Anterior', 'Sim' if settings.get('condition_on_previous_text', False) else 'Não'),
            ('Patience', f"{settings.get('patience', 1.0):.1f}"),
            ('Aceleração de Áudio', f"{settings.get('acceleration_factor', 1.0):.1f}x")
        ]
        
        for label, value in config_mapping:
            config_lines.append(f"   • {label}: {value}")
        
        # Add environment variables info
        env_info = self.system_profiler.get_environment_info()
        config_lines.extend([
            "",
            "🌍 VARIÁVEIS DE AMBIENTE:",
            f"   • Variáveis CT2: {len(env_info['ct2_variables'])}",
            f"   • Variáveis OMP: {len(env_info['omp_variables'])}",
            f"   • Variáveis CUDA: {len(env_info['cuda_variables'])}"
        ])
        
        # Show key environment variables
        for var_name, var_value in env_info['ct2_variables'].items():
            config_lines.append(f"   • {var_name}: {var_value}")
        
        return "\n".join(config_lines)
    
    def _generate_performance_section(self) -> str:
        """Generate detailed performance analysis section."""
        perf_summary = self.performance_monitor.get_performance_summary()
        
        if 'error' in perf_summary:
            return "⚡ ANÁLISE DE PERFORMANCE: Dados não disponíveis"
        
        cpu_stats = perf_summary['cpu_statistics']
        memory_stats = perf_summary['memory_statistics']
        disk_stats = perf_summary['disk_statistics']
        process_stats = perf_summary['process_statistics']
        efficiency = perf_summary['resource_efficiency']
        
        perf_lines = [
            "⚡ ANÁLISE DE PERFORMANCE:",
            f"   📊 Duração do Monitoramento: {perf_summary['monitoring_duration_seconds']:.1f}s",
            f"   📈 Pontos de Dados Coletados: {perf_summary['data_points_collected']}",
            "",
            "💻 CPU:",
            f"   • Uso Médio (Sistema): {cpu_stats['system_average_percent']:.1f}%",
            f"   • Uso Pico (Sistema): {cpu_stats['system_max_percent']:.1f}%", 
            f"   • Uso Médio (Processo): {cpu_stats['process_average_percent']:.1f}%",
            f"   • Uso Pico (Processo): {cpu_stats['process_max_percent']:.1f}%",
            f"   • Desvio Padrão CPU: {cpu_stats['system_stddev']:.1f}%",
            "",
            "🧠 MEMÓRIA:",
            f"   • Uso Médio (Sistema): {memory_stats['system_average_percent']:.1f}%",
            f"   • Uso Pico (Sistema): {memory_stats['system_max_percent']:.1f}%",
            f"   • Uso Médio (Processo): {memory_stats['process_average_rss_mb']:.0f}MB",
            f"   • Uso Pico (Processo): {memory_stats['process_max_rss_mb']:.0f}MB",
            f"   • Pico de Memória: {memory_stats['process_peak_memory_gb']:.1f}GB"
        ]
        
        # Add disk I/O if available
        if disk_stats.get('available'):
            perf_lines.extend([
                "",
                "💾 DISCO I/O:",
                f"   • Total Lido: {disk_stats['total_read_mb']:.1f}MB",
                f"   • Total Escrito: {disk_stats['total_write_mb']:.1f}MB",
                f"   • Total I/O: {disk_stats['total_io_mb']:.1f}MB",
                f"   • Operações: {disk_stats['total_operations']}"
            ])
        
        # Add process statistics
        if process_stats:
            perf_lines.extend([
                "",
                "🔄 PROCESSO:",
                f"   • Threads Médias: {process_stats['average_threads']:.1f}",
                f"   • Threads Máximas: {process_stats['max_threads']}",
                f"   • Estabilidade de Threads: {process_stats['thread_stability']:.2f}"
            ])
        
        # Add efficiency analysis
        perf_lines.extend([
            "",
            "📊 EFICIÊNCIA:",
            f"   • Score CPU: {efficiency['cpu_efficiency_score']:.3f}",
            f"   • Score Memória: {efficiency['memory_efficiency_score']:.3f}",
            f"   • Score Geral: {efficiency['overall_efficiency_score']:.3f}",
            f"   • Categoria de Uso: {efficiency['resource_usage_category']}"
        ])
        
        return "\n".join(perf_lines)
    
    def _generate_results_section(self, results: Dict[str, Any]) -> str:
        """Generate transcription results section with enhanced metrics."""
        results_lines = ["📊 RESULTADOS DA TRANSCRIÇÃO:"]
        
        # Basic statistics
        total_files = results.get('total_files', 0)
        successful_files = results.get('successful_files', 0)
        failed_files = results.get('failed_files', 0)
        processing_time = results.get('total_processing_time', 0)
        
        results_lines.extend([
            f"   • Total de Arquivos: {total_files}",
            f"   • Processados com Sucesso: {successful_files}",
            f"   • Falharam: {failed_files}",
            f"   • Taxa de Sucesso: {(successful_files/total_files*100):.1f}%" if total_files > 0 else "   • Taxa de Sucesso: N/A"
        ])
        
        # Timing statistics
        if processing_time > 0:
            results_lines.extend([
                f"   • Tempo Total: {processing_time:.1f}s ({processing_time/60:.1f} min)",
                f"   • Tempo Médio por Arquivo: {(processing_time/successful_files):.1f}s" if successful_files > 0 else "   • Tempo Médio: N/A"
            ])
        
        # Enhanced metrics
        if results.get('audio_duration_total'):
            audio_duration = results['audio_duration_total']
            rtf = audio_duration / processing_time if processing_time > 0 else 0
            results_lines.extend([
                f"   • Duração Total de Áudio: {audio_duration:.1f}s ({audio_duration/60:.1f} min)",
                f"   • Fator Tempo Real (RTF): {rtf:.1f}x"
            ])
        
        # Throughput
        if processing_time > 0 and successful_files > 0:
            throughput = successful_files / (processing_time / 60)
            results_lines.append(f"   • Throughput: {throughput:.1f} arquivos/min")
        
        # Speedup calculation
        if results.get('estimated_sequential_time'):
            sequential_time = results['estimated_sequential_time']
            speedup = sequential_time / processing_time if processing_time > 0 else 1.0
            results_lines.append(f"   • Speedup por Paralelização: {speedup:.1f}x")
        
        # Error details
        if failed_files > 0 and results.get('failed_results'):
            results_lines.append("")
            results_lines.append("❌ ARQUIVOS COM ERRO:")
            for failed_result in results['failed_results'][:5]:  # Show first 5 errors
                filename = failed_result.get('filename', 'Unknown')
                error = failed_result.get('error', 'Erro desconhecido')
                results_lines.append(f"   • {filename}: {error}")
            
            if len(results['failed_results']) > 5:
                results_lines.append(f"   • ... e mais {len(results['failed_results']) - 5} erros")
        
        return "\n".join(results_lines)
    
    def _generate_analysis_section(self, results: Dict[str, Any], settings: Dict[str, Any]) -> str:
        """Generate analysis and recommendations section."""
        analysis_lines = ["🔍 ANÁLISE E RECOMENDAÇÕES:"]
        
        total_files = results.get('total_files', 0)
        processing_time = results.get('total_processing_time', 0)
        successful_files = results.get('successful_files', 0)
        
        # Performance analysis
        if total_files > 0 and processing_time > 0:
            throughput = successful_files / (processing_time / 60)
            
            if throughput < 5:
                analysis_lines.append("   📉 Throughput baixo detectado")
                analysis_lines.append("      → Considere modelo menor ou otimizações de CPU")
            elif throughput > 20:
                analysis_lines.append("   📈 Excelente throughput alcançado")
                analysis_lines.append("      → Configuração otimizada para seu hardware")
            else:
                analysis_lines.append("   📊 Throughput adequado")
        
        # CPU analysis
        perf_summary = self.performance_monitor.get_performance_summary()
        if 'cpu_statistics' in perf_summary:
            cpu_avg = perf_summary['cpu_statistics']['process_average_percent']
            cpu_max = perf_summary['cpu_statistics']['process_max_percent']
            
            if cpu_max > 95:
                analysis_lines.append("   🔴 CPU em uso intenso (>95%)")
                analysis_lines.append("      → Considere modelo menor ou menos threads")
            elif cpu_avg < 30:
                analysis_lines.append("   🟡 CPU subutilizada (<30%)")
                analysis_lines.append("      → Pode usar modelo maior ou mais threads")
            else:
                analysis_lines.append("   🟢 Uso de CPU adequado")
        
        # Memory analysis
        if 'memory_statistics' in perf_summary:
            memory_peak = perf_summary['memory_statistics']['process_peak_memory_gb']
            
            if memory_peak > 8:
                analysis_lines.append("   🔴 Alto uso de memória (>8GB)")
                analysis_lines.append("      → Considere modelo menor ou compute_type mais eficiente")
            elif memory_peak < 2:
                analysis_lines.append("   🟢 Uso eficiente de memória")
                analysis_lines.append("      → Pode usar modelo maior se desejar mais qualidade")
        
        # Configuration recommendations
        model_size = settings.get('model_size', 'base')
        device = settings.get('device', 'cpu')
        
        if device == 'cpu' and model_size in ['large-v2', 'large-v3']:
            analysis_lines.append("   ⚠️  Modelo grande em CPU pode ser lento")
            analysis_lines.append("      → Considere 'medium' ou 'base' para CPU")
        
        if device == 'cuda' and model_size == 'tiny':
            analysis_lines.append("   💡 GPU disponível com modelo pequeno")
            analysis_lines.append("      → Pode usar modelo maior (base/medium) sem impacto")
        
        # Success rate analysis
        if total_files > 0:
            success_rate = successful_files / total_files * 100
            if success_rate < 95:
                analysis_lines.append(f"   ⚠️  Taxa de sucesso baixa ({success_rate:.1f}%)")
                analysis_lines.append("      → Verifique formatos de arquivo e configurações")
        
        return "\n".join(analysis_lines)
    
    def _generate_transcription_section(self, transcriptions: List[Dict[str, Any]]) -> str:
        """Generate transcription content section."""
        if not transcriptions:
            return ""
        
        content_lines = ["📝 CONTEÚDO TRANSCRITO:"]
        content_lines.append("=" * 60)
        
        for i, transcription in enumerate(transcriptions[:10]):  # Limit to first 10
            filename = transcription.get('filename', f'Arquivo {i+1}')
            content = transcription.get('content', '').strip()
            
            if content:
                content_lines.append(f"\n--- {filename} ---")
                content_lines.append(content)
        
        if len(transcriptions) > 10:
            content_lines.append(f"\n[... e mais {len(transcriptions) - 10} transcrições]")
        
        return "\n".join(content_lines)
    
    def _generate_footer(self) -> str:
        """Generate report footer."""
        return f"""{'='*80}
📄 Relatório gerado pelo Sistema de Relatórios Avançado VoxSynopsis
⏰ Timestamp: {datetime.now().isoformat()}
🔧 Para mais informações, consulte a documentação do projeto
{'='*80}""".strip()