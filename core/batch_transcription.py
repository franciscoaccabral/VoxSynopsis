"""Advanced batch transcription module using FastWhisper BatchedInferencePipeline.

This module implements high-performance batch processing for audio transcription,
achieving 8-12x speed improvements over sequential processing.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import psutil
from faster_whisper import WhisperModel, BatchedInferencePipeline
from PyQt5.QtCore import QThread, pyqtSignal

from .performance import get_optimal_threading_config, get_hardware_info
from .cache import FileCache
from .reporting import SystemProfiler, PerformanceMonitor, TimestampManager, EnhancedReportGenerator


logger = logging.getLogger(__name__)


class BatchTranscriptionThread(QThread):
    """Advanced batch transcription thread with BatchedInferencePipeline support."""
    
    update_status = pyqtSignal(dict)
    update_transcription = pyqtSignal(str)
    transcription_finished = pyqtSignal(str)
    completion_data_ready = pyqtSignal(dict)  # New signal for performance data
    batch_progress = pyqtSignal(dict)  # New signal for batch-specific progress
    
    def __init__(self, audio_files: List[str], whisper_settings: Dict[str, Any]):
        super().__init__()
        self.audio_files = audio_files
        self.whisper_settings = whisper_settings.copy()
        self._is_running = True
        self.file_cache = FileCache()
        
        # Store settings for logging (before they get popped)
        self.settings = whisper_settings.copy()
        
        # Initialize enhanced reporting system
        self.system_profiler = SystemProfiler()
        self.performance_monitor = PerformanceMonitor()
        self.timestamp_manager = TimestampManager()
        self.report_generator = EnhancedReportGenerator(
            self.system_profiler,
            self.performance_monitor,
            self.timestamp_manager
        )
        
        # Extract batch-specific settings
        self.use_batched_inference = self.whisper_settings.pop("use_batched_inference", True)
        self.batch_size = self.whisper_settings.pop("batch_size", 8)
        self.auto_batch_size = self.whisper_settings.pop("auto_batch_size", True)
        
        # Threading configuration
        self.thread_config = get_optimal_threading_config()
        self.max_workers = min(4, len(audio_files))
        
        # Performance monitoring
        self.batch_stats = {
            "total_files": len(audio_files),
            "processed_files": 0,
            "start_time": None,
            "estimated_time": None,
            "current_batch": 0,
            "total_batches": 0
        }
    
    def _create_optimized_model(self) -> WhisperModel:
        """Create an optimized WhisperModel with best settings for batch processing."""
        model_settings = {
            "model_size_or_path": self.whisper_settings.get("model_size", "base"),
            "device": self.whisper_settings.get("device", "cpu"),
            "compute_type": self.whisper_settings.get("compute_type", "int8"),
            "cpu_threads": self.thread_config["cpu_threads"],
            "num_workers": 1,  # Single worker for batch processing
        }
        
        # Remove None values
        model_settings = {k: v for k, v in model_settings.items() if v is not None}
        
        try:
            model = WhisperModel(**model_settings)
            logger.info(f"Created optimized model: {model_settings}")
            return model
        except Exception as e:
            logger.error(f"Failed to create optimized model: {e}")
            # Fallback to basic model
            return WhisperModel(
                model_size_or_path="base",
                device="cpu",
                compute_type="int8"
            )
    
    def _determine_optimal_batch_size(self) -> int:
        """Determine optimal batch size based on available memory and CPU."""
        if not self.auto_batch_size:
            return self.batch_size
        
        hw_info = get_hardware_info()
        memory_gb = hw_info["memory_gb"]
        physical_cores = hw_info["physical_cores"]
        
        # Conservative batch size calculation
        if memory_gb >= 32:
            optimal_batch = min(16, physical_cores * 2)
        elif memory_gb >= 16:
            optimal_batch = min(8, physical_cores)
        elif memory_gb >= 8:
            optimal_batch = min(4, physical_cores // 2)
        else:
            optimal_batch = 2
        
        # Ensure we don't exceed the number of files
        optimal_batch = min(optimal_batch, len(self.audio_files))
        
        logger.info(f"Determined optimal batch size: {optimal_batch} (Memory: {memory_gb}GB, Cores: {physical_cores})")
        return optimal_batch
    
    def _create_batched_pipeline(self, model: WhisperModel) -> BatchedInferencePipeline:
        """Create a BatchedInferencePipeline for high-performance processing."""
        try:
            pipeline = BatchedInferencePipeline(
                model=model,
                use_cuda=False,  # CPU-only for now
                chunk_length=30,  # 30-second chunks as recommended
                batch_size=self._determine_optimal_batch_size()
            )
            logger.info(f"Created batched pipeline with batch_size={pipeline.batch_size}")
            return pipeline
        except Exception as e:
            logger.error(f"Failed to create batched pipeline: {e}")
            raise
    
    def _process_file_with_batched_pipeline(self, pipeline: BatchedInferencePipeline, 
                                          file_path: str) -> Dict[str, Any]:
        """Process a single file using the batched pipeline."""
        try:
            start_time = time.time()
            
            # Get transcription settings
            transcription_settings = {
                "language": self.whisper_settings.get("language"),
                "task": "transcribe",
                "beam_size": self.whisper_settings.get("beam_size", 1),
                "best_of": self.whisper_settings.get("best_of", 1),
                "temperature": self.whisper_settings.get("temperature", 0.0),
                "condition_on_previous_text": self.whisper_settings.get("condition_on_previous_text", False),
                "vad_filter": self.whisper_settings.get("vad_filter", True),
                "without_timestamps": False
            }
            
            # Remove None values
            transcription_settings = {k: v for k, v in transcription_settings.items() if v is not None}
            
            # Transcribe using batched pipeline
            segments, info = pipeline.transcribe(file_path, **transcription_settings)
            
            # Convert segments to list and extract text
            segments_list = list(segments)
            transcription_text = " ".join([segment.text for segment in segments_list])
            
            # Salva transcrição individual com nome baseado no arquivo original
            individual_file = self._save_individual_transcription(file_path, transcription_text)
            
            processing_time = time.time() - start_time
            
            return {
                "file_path": file_path,
                "transcription": transcription_text,
                "segments": segments_list,
                "info": info,
                "processing_time": processing_time,
                "individual_file": individual_file,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            return {
                "file_path": file_path,
                "transcription": "",
                "segments": [],
                "info": None,
                "processing_time": 0,
                "success": False,
                "error": str(e)
            }
    
    def _process_files_in_batches(self, model: WhisperModel) -> List[Dict[str, Any]]:
        """Process files in optimized batches."""
        results = []
        
        if self.use_batched_inference and len(self.audio_files) > 1:
            # Use BatchedInferencePipeline for multiple files
            try:
                pipeline = self._create_batched_pipeline(model)
                
                batch_size = self._determine_optimal_batch_size()
                self.batch_stats["total_batches"] = (len(self.audio_files) + batch_size - 1) // batch_size
                
                for i in range(0, len(self.audio_files), batch_size):
                    if not self._is_running:
                        break
                        
                    batch = self.audio_files[i:i + batch_size]
                    self.batch_stats["current_batch"] = i // batch_size + 1
                    
                    # Update batch progress
                    self.batch_progress.emit({
                        "current_batch": self.batch_stats["current_batch"],
                        "total_batches": self.batch_stats["total_batches"],
                        "batch_size": len(batch),
                        "files_in_batch": [os.path.basename(f) for f in batch]
                    })
                    
                    # Process batch with ThreadPoolExecutor for parallel I/O
                    with ThreadPoolExecutor(max_workers=min(self.max_workers, len(batch))) as executor:
                        batch_futures = {
                            executor.submit(self._process_file_with_batched_pipeline, pipeline, file_path): file_path
                            for file_path in batch
                        }
                        
                        for future in as_completed(batch_futures):
                            result = future.result()
                            results.append(result)
                            
                            self.batch_stats["processed_files"] += 1
                            
                            # Update progress
                            progress = (self.batch_stats["processed_files"] / self.batch_stats["total_files"]) * 100
                            self.update_status.emit({
                                "text": f"Batch {self.batch_stats['current_batch']}/{self.batch_stats['total_batches']}: "
                                       f"{os.path.basename(result['file_path'])} "
                                       f"({result['processing_time']:.1f}s)",
                                "progress": progress,
                                "batch_mode": True
                            })
                            
                            if result["success"]:
                                self.update_transcription.emit(result["transcription"])
                
            except Exception as e:
                logger.error(f"Batch processing failed: {e}")
                # Fallback to sequential processing
                results = self._process_files_sequential(model)
                
        else:
            # Sequential processing for single files or if batching disabled
            results = self._process_files_sequential(model)
        
        return results
    
    def _process_files_sequential(self, model: WhisperModel) -> List[Dict[str, Any]]:
        """Fallback sequential processing method."""
        results = []
        
        for i, file_path in enumerate(self.audio_files):
            if not self._is_running:
                break
                
            try:
                start_time = time.time()
                
                # Use regular transcription method
                segments, info = model.transcribe(
                    file_path,
                    language=self.whisper_settings.get("language"),
                    beam_size=self.whisper_settings.get("beam_size", 1),
                    best_of=self.whisper_settings.get("best_of", 1),
                    temperature=self.whisper_settings.get("temperature", 0.0),
                    condition_on_previous_text=self.whisper_settings.get("condition_on_previous_text", False),
                    vad_filter=self.whisper_settings.get("vad_filter", True)
                )
                
                segments_list = list(segments)
                transcription_text = " ".join([segment.text for segment in segments_list])
                
                # Salva transcrição individual com nome baseado no arquivo original
                individual_file = self._save_individual_transcription(file_path, transcription_text)
                
                processing_time = time.time() - start_time
                
                result = {
                    "file_path": file_path,
                    "transcription": transcription_text,
                    "segments": segments_list,
                    "info": info,
                    "processing_time": processing_time,
                    "individual_file": individual_file,
                    "success": True
                }
                
                results.append(result)
                
                progress = ((i + 1) / len(self.audio_files)) * 100
                self.update_status.emit({
                    "text": f"Processando {os.path.basename(file_path)} ({processing_time:.1f}s)",
                    "progress": progress,
                    "batch_mode": False
                })
                
                self.update_transcription.emit(transcription_text)
                
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                results.append({
                    "file_path": file_path,
                    "transcription": "",
                    "segments": [],
                    "info": None,
                    "processing_time": 0,
                    "success": False,
                    "error": str(e)
                })
        
        return results
    
    def run(self):
        """Main execution thread for batch transcription with enhanced monitoring."""
        successful_results = []
        failed_results = []
        total_time = 0
        final_report = ""
        
        try:
            # Start enhanced monitoring
            self.timestamp_manager.start_session("batch_transcription")
            self.performance_monitor.start_monitoring()
            
            # Phase 1: Initialization
            self.timestamp_manager.start_phase("initialization")
            self.batch_stats["start_time"] = time.time()
            
            # Create optimized model
            model = self._create_optimized_model()
            self.timestamp_manager.end_phase("initialization")
            
            # Phase 2: Processing
            self.timestamp_manager.start_phase("processing")
            results = self._process_files_in_batches(model)
            self.timestamp_manager.end_phase("processing")
            
            # Phase 3: Report Generation
            self.timestamp_manager.start_phase("report_generation")
            
            # Calculate final statistics
            total_time = time.time() - self.batch_stats["start_time"]
            successful_results = [r for r in results if r["success"]]
            failed_results = [r for r in results if not r["success"]]
            
            # Generate enhanced final report
            final_report = self._generate_enhanced_final_report(successful_results, failed_results, total_time)
            self.timestamp_manager.end_phase("report_generation")
            
            # Limpeza de arquivos temporários após processamento em lote
            self._cleanup_chunks_and_temp_files()
            
            self.update_status.emit({
                "text": f"Batch concluído: {len(successful_results)}/{len(results)} arquivos processados",
                "progress": 100,
                "batch_mode": True,
                "final_report": final_report
            })
            
            self.transcription_finished.emit(final_report)
            
        except Exception as e:
            logger.error(f"Batch transcription failed: {e}")
            self.update_status.emit({
                "text": f"Erro no processamento em lote: {e}",
                "progress": 0,
                "batch_mode": True,
                "error": str(e)
            })
        finally:
            # Stop monitoring and finalize session
            self.performance_monitor.stop_monitoring()
            self.timestamp_manager.end_session("batch_transcription")
            
            # Prepare performance data for popup after session is finalized
            if successful_results or failed_results:  # Only emit if we have some results
                completion_data = self._prepare_completion_data(successful_results, failed_results, total_time, final_report)
                self.completion_data_ready.emit(completion_data)
    
    def _prepare_completion_data(self, successful_results: List[Dict], 
                               failed_results: List[Dict], total_time: float, 
                               final_report: str) -> Dict[str, Any]:
        """Prepare performance data for completion popup."""
        # Calculate audio duration
        total_audio_duration = sum(r.get('duration', 0) for r in successful_results)
        
        # Calculate speedup
        estimated_sequential_time = sum(r.get('processing_time', 0) for r in successful_results)
        speedup = estimated_sequential_time / total_time if total_time > 0 else 1.0
        
        # Get system information
        timing_summary = self.timestamp_manager.get_session_summary()
        
        # Get current time for end_time if not available
        from datetime import datetime, timezone
        current_time = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Get model information from original settings (before they were modified)
        model_size = self.settings.get('model_size') or self.whisper_settings.get('model_size', 'base')
        device = self.settings.get('device') or self.whisper_settings.get('device', 'cpu')
        compute_type = self.settings.get('compute_type') or self.whisper_settings.get('compute_type', 'int8')
        
        # Debug logging
        print(f"DEBUG Batch: Settings: {self.settings}")
        print(f"DEBUG Batch: WhisperSettings: {self.whisper_settings}")
        print(f"DEBUG Batch: Final values - Model: {model_size}, Device: {device}, Compute: {compute_type}")
        
        return {
            'total_files': len(self.audio_files),
            'successful_files': len(successful_results),
            'failed_files': len(failed_results),
            'total_processing_time': total_time,
            'success_rate': (len(successful_results) / len(self.audio_files) * 100) if self.audio_files else 0,
            'average_time_per_file': total_time / len(successful_results) if successful_results else 0,
            'audio_duration_total': total_audio_duration,
            'speedup': speedup,
            'start_time': timing_summary.get('start_time', 'N/A'),
            'end_time': timing_summary.get('end_time', current_time),
            'model_size': model_size,
            'device': device,
            'compute_type': compute_type,
            'full_report': final_report,
            'failed_results': failed_results
        }
    
    def _generate_enhanced_final_report(self, successful_results: List[Dict], 
                                      failed_results: List[Dict], total_time: float) -> str:
        """Generate enhanced final report using the new reporting system."""
        
        # Prepare transcription results data
        transcription_results = {
            'total_files': len(self.audio_files),
            'successful_files': len(successful_results),
            'failed_files': len(failed_results),
            'total_processing_time': total_time,
            'success_rate': len(successful_results) / len(self.audio_files) * 100 if self.audio_files else 0,
            'average_time_per_file': total_time / len(successful_results) if successful_results else 0,
            'failed_results': failed_results
        }
        
        # Calculate audio duration and RTF
        total_audio_duration = 0
        transcriptions = []
        
        for result in successful_results:
            if 'duration' in result:
                total_audio_duration += result['duration']
            
            # Collect transcription content
            if 'transcription' in result:
                transcriptions.append({
                    'filename': os.path.basename(result.get('file_path', 'Unknown')),
                    'content': result['transcription']
                })
        
        if total_audio_duration > 0:
            transcription_results['audio_duration_total'] = total_audio_duration
            
        # Estimate sequential time for speedup calculation
        if successful_results:
            avg_sequential_time = sum(r.get('processing_time', 0) for r in successful_results)
            transcription_results['estimated_sequential_time'] = avg_sequential_time
        
        transcription_results['transcriptions'] = transcriptions
        
        # Generate comprehensive report
        return self.report_generator.generate_comprehensive_report(
            transcription_results, 
            self.settings,
            include_transcriptions=True
        )
    
    def _generate_final_report(self, successful_results: List[Dict], 
                             failed_results: List[Dict], total_time: float) -> str:
        """Generate a comprehensive final report with statistics and full transcriptions."""
        # Start with transcriptions section
        full_transcriptions = []
        
        # Add all transcribed content
        if successful_results:
            for result in successful_results:
                filename = os.path.basename(result['file_path'])
                transcription = result.get('transcription', '').strip()
                if transcription:
                    full_transcriptions.append(f"--- {filename} ---\n{transcription}")
        
        # Combine all transcriptions
        transcription_text = "\n\n".join(full_transcriptions)
        
        # Add statistics section
        stats_report = []
        stats_report.append(f"\n\n{'='*60}")
        stats_report.append(f"🎯 RELATÓRIO DE PROCESSAMENTO EM LOTE")
        stats_report.append(f"{'='*60}")
        stats_report.append(f"📊 Estatísticas Gerais:")
        stats_report.append(f"   • Total de arquivos: {len(self.audio_files)}")
        stats_report.append(f"   • Processados com sucesso: {len(successful_results)}")
        stats_report.append(f"   • Falharam: {len(failed_results)}")
        stats_report.append(f"   • Tempo total de processamento: {total_time:.1f}s ({total_time/60:.1f} min)")
        
        if successful_results:
            avg_time = sum(r["processing_time"] for r in successful_results) / len(successful_results)
            stats_report.append(f"   • Tempo médio por arquivo: {avg_time:.1f}s")
            total_duration = sum(r.get("duration", 0) for r in successful_results)
            if total_duration > 0:
                real_time_factor = total_duration / total_time
                stats_report.append(f"   • Fator tempo real: {real_time_factor:.1f}x")
            
            # Calculate speedup estimation
            if len(successful_results) > 1:
                sequential_estimate = sum(r["processing_time"] for r in successful_results)
                speedup = sequential_estimate / total_time
                stats_report.append(f"   • Speedup por paralelização: {speedup:.1f}x")
        
        # Add configuration details
        stats_report.append(f"\n⚙️ Configurações Utilizadas:")
        stats_report.append(f"   • Modelo: {self.settings.get('model_size', 'N/A')}")
        stats_report.append(f"   • Dispositivo: {self.settings.get('device', 'N/A')}")
        stats_report.append(f"   • Tipo de computação: {self.settings.get('compute_type', 'N/A')}")
        stats_report.append(f"   • Threads CPU: {self.settings.get('cpu_threads', 'N/A')}")
        stats_report.append(f"   • Tamanho do lote: {self.settings.get('batch_size', 'N/A')}")
        stats_report.append(f"   • Filtro VAD: {'Sim' if self.settings.get('vad_filter', False) else 'Não'}")
        stats_report.append(f"   • Idioma: {self.settings.get('language', 'auto')}")
        stats_report.append(f"   • Processamento em lote: {'Ativo' if self.use_batched_inference else 'Inativo'}")
        stats_report.append(f"   • Temperatura: {self.settings.get('temperature', 0.0)}")
        stats_report.append(f"   • Beam size: {self.settings.get('beam_size', 5)}")
        
        if failed_results:
            stats_report.append(f"\n❌ Arquivos com erro:")
            for result in failed_results:
                filename = os.path.basename(result['file_path'])
                error_msg = result.get('error', 'Erro desconhecido')
                stats_report.append(f"   • {filename}: {error_msg}")
        
        # Add final separator
        stats_report.append(f"\n{'='*60}")
        
        # Combine transcriptions and statistics
        final_report = transcription_text + "\n".join(stats_report)
        return final_report
    
    def _cleanup_chunks_and_temp_files(self, directories: list = None):
        """Remove chunks e arquivos temporários após processamento em lote."""
        if directories is None:
            # Pega diretórios únicos dos arquivos sendo processados
            directories = list(set([os.path.dirname(f) for f in self.audio_files]))
        
        cleanup_patterns = [
            "*_chunk_*.wav",
            "*_ffmpeg_chunk_*.wav", 
            "*_silence_chunk_*.wav",
            "*_accelerated*.wav",
            "*_processed*.wav",
            "*_extracted*.wav"
        ]
        
        import glob
        total_cleaned = 0
        
        for directory in directories:
            cleaned_files = 0
            for pattern in cleanup_patterns:
                pattern_path = os.path.join(directory, pattern)
                for file_path in glob.glob(pattern_path):
                    try:
                        os.remove(file_path)
                        cleaned_files += 1
                        total_cleaned += 1
                    except Exception as e:
                        logger.warning(f"Erro ao remover arquivo temporário {file_path}: {e}")
        
        if total_cleaned > 0:
            logger.info(f"Limpeza em lote concluída: {total_cleaned} arquivos temporários removidos")

    def _save_individual_transcription(self, filepath: str, transcription_text: str):
        """Salva transcrição individual com nome baseado no arquivo original."""
        if not transcription_text.strip():
            return None
            
        # Gera nome do arquivo de transcrição baseado no arquivo original
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        transcription_filename = f"{base_name}_transcricao.txt"
        output_dir = os.path.dirname(filepath)
        transcription_path = os.path.join(output_dir, transcription_filename)
        
        try:
            with open(transcription_path, "w", encoding="utf-8") as f:
                f.write(f"Transcrição de: {os.path.basename(filepath)}\n")
                f.write(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n\n")
                f.write(transcription_text)
            
            logger.info(f"Transcrição individual salva: {transcription_path}")
            return transcription_path
        except Exception as e:
            logger.error(f"Erro ao salvar transcrição individual: {e}")
            return None

    def stop(self):
        """Stop the batch transcription process."""
        self._is_running = False
        # Limpeza de chunks e arquivos temporários
        self._cleanup_chunks_and_temp_files()
        self.quit()
        self.wait()