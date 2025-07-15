"""Transcription thread for FastWhisper integration."""

import concurrent.futures
import glob
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, List

import psutil
from faster_whisper import WhisperModel
from PyQt5.QtCore import QThread, pyqtSignal

from .cache import FileCache
from .config import MAX_WORKERS
from .batch_transcription import BatchTranscriptionThread
from .loop_detector import LightweightLoopDetector, QuickQualityValidator
from .recovery_manager import CoreRecoveryManager


class TranscriptionThread(QThread):
    update_status = pyqtSignal(dict)
    update_transcription = pyqtSignal(str)
    transcription_finished = pyqtSignal(str)
    completion_data_ready = pyqtSignal(dict)  # Forward completion data signal
    
    # Anti-loop system signals
    loop_detected = pyqtSignal(dict)         # When loop is detected
    recovery_started = pyqtSignal(dict)      # Recovery process begins
    recovery_completed = pyqtSignal(dict)    # Recovery process ends

    def __init__(self, audio_folder: str, whisper_settings: dict[str, Any]) -> None:
        super().__init__()
        self.audio_folder = audio_folder
        self.whisper_settings = whisper_settings.copy()
        self._is_running = True
        self.file_cache = FileCache()

        # Extrai cpu_threads e remove do dicionário principal para evitar erros
        self.cpu_threads = self.whisper_settings.pop(
            "cpu_threads", psutil.cpu_count(logical=False) or 4
        )

        # Configurações de paralelização
        self.parallel_processes = self.whisper_settings.pop(
            "parallel_processes", min(2, max(1, (os.cpu_count() or 1) // 2))
        )
        self.max_workers = min(MAX_WORKERS, self.parallel_processes)

        # Batch processing settings
        self.use_batch_processing = self.whisper_settings.pop("use_batch_processing", True)
        self.batch_threshold = self.whisper_settings.pop("batch_threshold", 3)  # Min files for batch mode
        self.batch_size = self.whisper_settings.pop("batch_size", 8)
        
        # Smart chunking settings
        
        # Anti-loop recovery system
        self.loop_detector = LightweightLoopDetector()
        self.quality_validator = QuickQualityValidator()
        self.recovery_manager = None  # Will be initialized with transcription function
        self.enable_smart_chunking = self.whisper_settings.pop(
            "enable_smart_chunking", False
        )
        self.smart_chunk_duration_seconds = self.whisper_settings.pop(
            "smart_chunk_duration_seconds", 60
        )
        self.silence_threshold_dbfs = self.whisper_settings.pop(
            "silence_threshold_dbfs", -40
        )
        self.min_silence_duration_ms = self.whisper_settings.pop(
            "min_silence_duration_ms", 500
        )
        # Regular chunk duration for fallback or when smart chunking is off
        self.regular_chunk_duration_seconds = self.whisper_settings.get(
            "chunk_duration_seconds", 60
        )
    
    def _check_batch_support(self) -> bool:
        """Check if BatchedInferencePipeline is available and system supports batch processing."""
        try:
            from faster_whisper import BatchedInferencePipeline
            # Check minimum memory requirement (8GB for batch processing)
            memory_gb = psutil.virtual_memory().total / (1024**3)
            return memory_gb >= 8
        except ImportError:
            return False

    def _split_audio_with_ffmpeg(self, filepath: str, chunk_duration: int) -> list[str]:
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        output_dir = os.path.dirname(filepath)
        chunk_prefix = os.path.join(output_dir, f"{base_name}_ffmpeg_chunk_")
        chunk_files = []

        try:
            probe_command = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                filepath,
            ]
            duration_str = subprocess.check_output(probe_command, text=True).strip()
            total_duration = float(duration_str)
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
            self.update_status.emit(
                {
                    "text": (
                        f"Erro (ffprobe) ao obter duração de "
                        f"{os.path.basename(filepath)}: {e}"
                    ),
                    "last_time": 0,
                    "total_time": 0,
                }
            )
            return []

        num_chunks = int(total_duration // chunk_duration) + (
            1 if total_duration % chunk_duration > 0 else 0
        )
        # if total_duration is less than chunk_duration
        if num_chunks == 0 and total_duration > 0:
            num_chunks = 1

        for i in range(num_chunks):
            start_time = i * chunk_duration
            # For the last chunk, ensure it doesn't try to read past the end of the file
            current_chunk_duration = min(chunk_duration, total_duration - start_time)
            if current_chunk_duration <= 0:  # Should not happen if logic is correct
                break

            chunk_filepath = f"{chunk_prefix}{i:03d}.wav"
            command = [
                "ffmpeg",
                "-threads",
                "0",
                "-i",
                filepath,
                "-ss",
                str(start_time),
                "-t",
                str(current_chunk_duration),
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                chunk_filepath,
                "-y",  # -y to overwrite
            ]
            try:
                subprocess.run(command, check=True, capture_output=True, text=True)
                chunk_files.append(chunk_filepath)
            except subprocess.CalledProcessError as e:
                self.update_status.emit(
                    {
                        "text": (
                            f"Erro (ffmpeg) ao dividir {os.path.basename(filepath)} "
                            f"(chunk {i}): {e.stderr}"
                        ),
                        "last_time": 0,
                        "total_time": 0,
                    }
                )
                # Clean up already created chunks for this file if one fails
                for cf in chunk_files:
                    if os.path.exists(cf):
                        os.remove(cf)
                return []
            except FileNotFoundError:
                self.update_status.emit(
                    {
                        "text": "Erro: FFmpeg não encontrado. Verifique a instalação.",
                        "last_time": 0,
                        "total_time": 0,
                    }
                )
                return []
        return chunk_files

    def _split_audio_with_ffmpeg_silence(
        self, filepath: str, target_chunk_duration: int
    ) -> list[str]:
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        output_dir = os.path.dirname(filepath)
        chunk_prefix = os.path.join(output_dir, f"{base_name}_silence_chunk_")
        chunk_files = []

        # 1. Detectar silêncios e gravar timestamps
        self.update_status.emit(
            {
                "text": (
                    f"Detectando silêncios em {os.path.basename(filepath)} "
                    "com FFmpeg..."
                )
            }
        )
        silence_cmd = [
            "ffmpeg",
            "-hwaccel",
            "auto",
            "-threads",
            "0",
            "-i",
            filepath,
            "-af",
            "silencedetect=noise=-35dB:d=0.7",
            "-f",
            "null",
            "-",
        ]
        try:
            # A saída do silencedetect vai para o stderr
            result = subprocess.run(
                silence_cmd, capture_output=True, text=True, check=True
            )
            ffmpeg_output = result.stderr
        except subprocess.CalledProcessError as e:
            ffmpeg_output = e.stderr
            if "No such file or directory" in ffmpeg_output:
                self.update_status.emit(
                    {"text": f"Erro: Arquivo não encontrado - {filepath}"}
                )
                return []
        except FileNotFoundError:
            self.update_status.emit({"text": "Erro: FFmpeg não encontrado."})
            return []

        # 2. Analisar os timestamps de silêncio
        silence_starts = [
            float(t) for t in re.findall(r"silence_start: (\d+\.?\d*)", ffmpeg_output)
        ]
        if not silence_starts:
            self.update_status.emit(
                {
                    "text": (
                        f"Nenhum silêncio detectado em {os.path.basename(filepath)}. "
                        "Usando divisão por tempo."
                    )
                }
            )
            return self._split_audio_with_ffmpeg(filepath, target_chunk_duration)

        # 3. Calcular pontos de corte (lógica "60s ± silêncio")
        try:
            duration_str = (
                subprocess.check_output(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-show_entries",
                        "format=duration",
                        "-of",
                        "default=noprint_wrappers=1:nokey=1",
                        filepath,
                    ]
                )
                .decode("utf-8")
                .strip()
            )
            total_duration = float(duration_str)
        except Exception as e:
            self.update_status.emit({"text": f"Erro ao obter duração do arquivo: {e}"})
            return [
                filepath
            ]  # Retorna o arquivo original se não conseguir obter a duração

        cut_points = []
        current_pos = 0.0
        while current_pos < total_duration:
            next_target = current_pos + target_chunk_duration
            if next_target >= total_duration:
                cut_points.append(total_duration)
                break

            # Encontra o primeiro silêncio após o nosso alvo de 60s
            best_cut = -1.0
            for start_time in silence_starts:
                if start_time > next_target:
                    best_cut = start_time
                    break

            # Se encontrou um ponto de corte, usa. Senão, corta no alvo.
            cut_point = best_cut if best_cut != -1.0 else next_target
            cut_points.append(cut_point)
            current_pos = cut_point

        # 4. Criar os chunks com base nos pontos de corte
        last_start = 0.0
        for i, end_time in enumerate(cut_points):
            chunk_filepath = f"{chunk_prefix}{i:03d}.wav"
            self.update_status.emit(
                {
                    "text": (
                        f"Criando chunk {i + 1}/{len(cut_points)} "
                        f"(duração: {end_time - last_start:.2f}s)..."
                    )
                }
            )
            cut_cmd = [
                "ffmpeg",
                "-hwaccel",
                "auto",
                "-threads",
                "0",
                "-i",
                filepath,
                "-ss",
                str(last_start),
                "-to",
                str(end_time),
                "-vn",
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                chunk_filepath,
                "-y",
            ]
            try:
                subprocess.run(cut_cmd, check=True, capture_output=True, text=True)
                chunk_files.append(chunk_filepath)
            except subprocess.CalledProcessError as e:
                self.update_status.emit({"text": f"Erro ao criar chunk: {e.stderr}"})
                # Não retorna aqui, tenta criar os outros chunks
            last_start = end_time

        return chunk_files

    def _get_audio_duration_ffmpeg(self, filepath: str) -> float:
        """Usa ffprobe para obter a duração de um arquivo de áudio com cache."""
        if not os.path.exists(filepath):
            return 0.0

        # Verifica o cache primeiro
        cached_duration = self.file_cache.get_duration(filepath)
        if cached_duration is not None:
            return cached_duration

        try:
            probe_command = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                filepath,
            ]
            duration_str = subprocess.check_output(
                probe_command, text=True, stderr=subprocess.PIPE
            ).strip()
            duration = float(duration_str)

            # Armazena no cache
            self.file_cache.set_duration(filepath, duration)
            return duration

        except (subprocess.CalledProcessError, FileNotFoundError, ValueError) as e:
            print(f"Erro ao obter duração de {os.path.basename(filepath)}: {e}")
            return 0.0

    def _process_media_files_parallel(self, media_files: list[str]) -> list[str]:
        """Processa arquivos de mídia em paralelo"""
        files_to_process = []

        def extract_audio(media_path: str) -> str | None:
            """Extrai áudio de um arquivo MP4"""
            if not self._is_running:
                return None

            if media_path.lower().endswith(".mp4"):
                base_name = os.path.splitext(os.path.basename(media_path))[0]
                extracted_wav_path = os.path.join(
                    self.audio_folder, f"{base_name}_extracted.wav"
                )
                if not os.path.exists(extracted_wav_path):
                    try:
                        extract_cmd = [
                            "ffmpeg",
                            "-hwaccel", "auto",
                            "-threads", "0",
                            "-i", media_path,
                            "-vn", "-acodec", "pcm_s16le",
                            "-ar", "16000", "-ac", "1",
                            extracted_wav_path, "-y",
                        ]
                        subprocess.run(
                            extract_cmd, check=True, capture_output=True, text=True
                        )
                        return extracted_wav_path
                    except Exception as e:
                        self.update_status.emit({"text": f"Erro ao extrair áudio: {e}"})
                        return None
                else:
                    return extracted_wav_path
            elif media_path.lower().endswith(".wav"):
                return media_path
            return None

        # Processa em paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            self.update_status.emit({"text": "Extraindo áudio dos arquivos..."})
            future_to_file = {
                executor.submit(extract_audio, media): media
                for media in media_files
            }

            for future in concurrent.futures.as_completed(future_to_file):
                if not self._is_running:
                    break

                result = future.result()
                if result:
                    files_to_process.append(result)

        return files_to_process

    def _accelerate_chunks_parallel(self, chunks: list[str]) -> list[str]:
        """Acelera chunks em paralelo"""
        acceleration_factor = self.whisper_settings.get("acceleration_factor", 1.0)

        if acceleration_factor <= 1.0:
            return chunks

        final_files = []

        def accelerate_chunk(chunk_path: str) -> str:
            """Acelera um chunk individual"""
            if not self._is_running:
                return chunk_path

            base_name = os.path.splitext(os.path.basename(chunk_path))[0]
            accelerated_chunk_path = os.path.join(
                self.audio_folder,
                f"{base_name}_accelerated_{acceleration_factor}x.wav",
            )

            if not os.path.exists(accelerated_chunk_path):
                try:
                    accel_cmd = [
                        "ffmpeg", "-threads", "0", "-i", chunk_path,
                        "-filter:a", f"atempo={acceleration_factor}",
                        accelerated_chunk_path, "-y"
                    ]
                    subprocess.run(
                        accel_cmd, check=True, capture_output=True, text=True
                    )
                    # Exclui o chunk original após o sucesso
                    os.remove(chunk_path)
                    return accelerated_chunk_path
                except Exception as e:
                    self.update_status.emit(
                        {"text": f"Erro ao acelerar chunk: {e}"}
                    )
                    return chunk_path
            else:
                # Exclui o chunk original se o acelerado já existe
                try:
                    os.remove(chunk_path)
                except OSError:
                    pass
                return accelerated_chunk_path

        # Processa chunks em paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            self.update_status.emit({"text": f"Acelerando {len(chunks)} chunks..."})
            future_to_chunk = {
                executor.submit(accelerate_chunk, chunk): chunk
                for chunk in chunks
            }

            for future in concurrent.futures.as_completed(future_to_chunk):
                if not self._is_running:
                    break

                result = future.result()
                if result:
                    final_files.append(result)

        return final_files

    def _get_files_to_transcribe(self) -> list[str]:
        """Otimizado com processamento paralelo"""
        # Limpa cache antigo
        self.file_cache.clear_stale_entries()

        # 1. Coletar todos os arquivos de mídia (MP4 e WAV)
        all_media_files = sorted(
            glob.glob(os.path.join(self.audio_folder, "*.mp4"))
        ) + sorted(glob.glob(os.path.join(self.audio_folder, "*.wav")))

        # Filtra arquivos que já são chunks ou processados para evitar reprocessamento
        all_media_files = [
            f for f in all_media_files
            if not any(pattern in os.path.basename(f) for pattern in
                      ["_chunk_", "_processed", "_accelerated", "_extracted"])
        ]

        # 2. Processa arquivos em paralelo
        files_to_process = self._process_media_files_parallel(all_media_files)

        if not files_to_process:
            return []

        # 3. Dividir os arquivos de áudio usando a detecção de silêncio do FFmpeg
        chunks_to_accelerate = []
        for audio_file in files_to_process:
            if not self._is_running:
                break

            self.update_status.emit(
                {"text": f"Dividindo {os.path.basename(audio_file)} por silêncio..."}
            )
            chunks = self._split_audio_with_ffmpeg_silence(
                audio_file, self.smart_chunk_duration_seconds
            )
            chunks_to_accelerate.extend(chunks)

            # Se o arquivo de áudio foi um WAV extraído de um MP4, exclui-o agora
            if "_extracted.wav" in os.path.basename(audio_file):
                try:
                    os.remove(audio_file)
                except OSError as e:
                    self.update_status.emit(
                        {"text": f"Erro ao excluir arquivo intermediário: {e}"}
                    )

        # 4. Acelerar chunks em paralelo
        final_files_for_transcription = self._accelerate_chunks_parallel(
            chunks_to_accelerate
        )

        return sorted(list(set(final_files_for_transcription)))

    def run(self):
        model = None
        last_file_time = 0
        try:
            # Critical settings for WhisperModel initialization
            model_size = self.whisper_settings.pop("model_size", self.whisper_settings.pop("model", "medium"))
            device = self.whisper_settings.pop("device", "cpu")
            compute_type = self.whisper_settings.pop("compute_type", "int8")

            # Whitelist de argumentos válidos para o método model.transcribe().
            # Isso evita passar argumentos de palavra-chave inesperados.
            valid_transcribe_args = [
                "language",
                "vad_filter",
                "temperature",
                "best_of",
                "beam_size",
                "condition_on_previous_text",
                "initial_prompt",
            ]
            # Cria um dicionário limpo apenas com os argumentos válidos.
            transcribe_params = {
                key: self.whisper_settings[key]
                for key in valid_transcribe_args
                if key in self.whisper_settings
            }

            self.update_status.emit(
                {
                    "text": (
                        f"Carregando modelo FastWhisper ({model_size}) "
                        f"no dispositivo {device} ({compute_type})..."
                    ),
                    "last_time": 0,
                    "total_time": 0,
                }
            )
            # Try optimized configuration first, fallback to safe config if needed
            try:
                model = WhisperModel(
                    model_size,
                    device=device,
                    compute_type=compute_type,
                    cpu_threads=self.cpu_threads,
                    num_workers=1,  # Otimizado: single worker para estabilidade CPU
                )
            except Exception as e:
                # Clear potentially problematic environment variables
                from .performance import clear_problematic_environment_vars
                clear_problematic_environment_vars()
                
                # Fallback to conservative configuration
                self.update_status.emit({
                    "text": f"Tentativa otimizada falhou ({str(e)[:50]}...), usando configuração conservadora...",
                    "last_time": 0,
                    "total_time": 0,
                })
                
                try:
                    model = WhisperModel(
                        model_size,
                        device="cpu",  # Force CPU
                        compute_type="int8",  # Safe compute type
                        cpu_threads=min(4, self.cpu_threads),  # Conservative thread count
                    )
                except Exception as e2:
                    # Ultimate fallback with minimal configuration
                    self.update_status.emit({
                        "text": f"Configuração conservadora também falhou, usando configuração mínima...",
                        "last_time": 0,
                        "total_time": 0,
                    })
                    model = WhisperModel(
                        "base",  # Force base model
                        device="cpu",
                        compute_type="int8",
                    )
            self.update_status.emit(
                {
                    "text": "Modelo carregado. Coletando e preparando arquivos...",
                    "last_time": 0,
                    "total_time": 0,
                }
            )

            files_to_transcribe = self._get_files_to_transcribe()

            if not files_to_transcribe:
                self.update_status.emit(
                    {
                        "text": "Nenhum arquivo de áudio (.wav, .mp4) encontrado.",
                        "last_time": 0,
                        "total_time": 0,
                    }
                )
                self.transcription_finished.emit("")
                return

            # Check if we should use batch processing
            total_files = len(files_to_transcribe)
            should_use_batch = (
                self.use_batch_processing and 
                total_files >= self.batch_threshold and
                hasattr(self, '_check_batch_support') and self._check_batch_support()
            )
            
            if should_use_batch:
                # Use advanced batch processing
                self.update_status.emit({
                    "text": f"🚀 Usando processamento em lote para {total_files} arquivos...",
                    "last_time": 0,
                    "total_time": 0,
                })
                
                # Create batch processing settings
                batch_settings = self.whisper_settings.copy()
                batch_settings.update({
                    "use_batched_inference": True,
                    "batch_size": self.batch_size,
                    "auto_batch_size": True
                })
                
                # Start batch transcription thread
                batch_thread = BatchTranscriptionThread(files_to_transcribe, batch_settings)
                
                # Connect signals
                batch_thread.update_status.connect(self.update_status.emit)
                batch_thread.update_transcription.connect(self.update_transcription.emit)
                batch_thread.transcription_finished.connect(self.transcription_finished.emit)
                batch_thread.completion_data_ready.connect(self.completion_data_ready.emit)
                
                # Run batch processing
                batch_thread.run()
                return

            # Fallback to sequential processing
            full_transcription = []
            total_processing_time = 0
            processing_start_time = time.time()
            
            # Log detailed configuration info
            config_info = [
                f"\n{'='*60}",
                f"🚀 INICIAÇÃO DO PROCESSAMENTO SEQUENCIAL",
                f"{'='*60}",
                f"⚙️ Configurações do FastWhisper:",
                f"   • Modelo: {model_size}",
                f"   • Dispositivo: {device}",
                f"   • Tipo de computação: {compute_type}",
                f"   • Threads CPU: {self.cpu_threads}",
                f"   • Filtro VAD: {'Sim' if transcribe_params.get('vad_filter', False) else 'Não'}",
                f"   • Idioma: {transcribe_params.get('language', 'auto')}",
                f"   • Temperatura: {transcribe_params.get('temperature', 0.0)}",
                f"   • Beam size: {transcribe_params.get('beam_size', 5)}",
                f"   • Total de arquivos: {total_files}",
                f"{'='*60}\n"
            ]
            self.update_transcription.emit("\n".join(config_info))

            for i, filepath in enumerate(files_to_transcribe):
                if not self._is_running:
                    self.update_status.emit(
                        {
                            "text": "Transcrição cancelada.",
                            "last_time": 0,
                            "total_time": total_processing_time,
                        }
                    )
                    break

                status_text = (
                    f"Transcrevendo {i + 1}/{total_files}: {os.path.basename(filepath)}"
                )
                self.update_status.emit(
                    {
                        "text": status_text,
                        "last_time": last_file_time,
                        "total_time": total_processing_time,
                    }
                )

                start_time = time.time()
                segments, _ = model.transcribe(filepath, **transcribe_params)
                transcription_text = "".join(segment.text for segment in segments)
                end_time = time.time()

                last_file_time = end_time - start_time
                total_processing_time += last_file_time

                # Calculate file duration for metrics
                file_duration = self._get_audio_duration_ffmpeg(filepath)
                
                # Anti-loop detection and recovery
                transcription_text = self._apply_anti_loop_recovery(
                    transcription_text, filepath, file_duration, 
                    transcribe_params, model
                )
                real_time_factor = file_duration / last_file_time if last_file_time > 0 else 0
                
                transcription_with_metrics = (
                    f"--- {os.path.basename(filepath)} ---\n"
                    f"[Processado em {last_file_time:.1f}s | "
                    f"Duração: {file_duration:.1f}s | "
                    f"Fator tempo real: {real_time_factor:.1f}x]\n"
                    f"{transcription_text}\n\n"
                )
                
                # Salva transcrição individual com nome baseado no arquivo original
                individual_file = self._save_individual_transcription(filepath, transcription_text)
                
                self.update_transcription.emit(transcription_with_metrics)
                full_transcription.append(
                    f"--- {os.path.basename(filepath)} ---\n{transcription_text}"
                )

            # Generate comprehensive final report
            processing_end_time = time.time()
            total_elapsed_time = processing_end_time - processing_start_time
            
            # Combine transcriptions
            transcription_content = "\n\n".join(full_transcription)
            
            # Add detailed processing statistics
            stats_report = [
                f"\n\n{'='*60}",
                f"🎯 RELATÓRIO DE PROCESSAMENTO SEQUENCIAL",
                f"{'='*60}",
                f"📊 Estatísticas de Performance:",
                f"   • Total de arquivos processados: {total_files}",
                f"   • Tempo total de processamento: {total_processing_time:.1f}s ({total_processing_time/60:.1f} min)",
                f"   • Tempo total decorrido: {total_elapsed_time:.1f}s ({total_elapsed_time/60:.1f} min)",
                f"   • Tempo médio por arquivo: {total_processing_time/max(1, total_files):.1f}s",
                f"   • Velocidade de processamento: {total_files/(total_processing_time/60):.1f} arquivos/min",
                f"\n⚙️ Configurações Utilizadas:",
                f"   • Modelo FastWhisper: {model_size}",
                f"   • Dispositivo de processamento: {device}",
                f"   • Tipo de computação: {compute_type}",
                f"   • Threads CPU utilizadas: {self.cpu_threads}",
                f"   • Filtro VAD ativo: {'Sim' if transcribe_params.get('vad_filter', False) else 'Não'}",
                f"   • Idioma de transcrição: {transcribe_params.get('language', 'auto')}",
                f"   • Temperatura: {transcribe_params.get('temperature', 0.0)}",
                f"   • Beam size: {transcribe_params.get('beam_size', 5)}",
                f"   • Condição no texto anterior: {'Sim' if transcribe_params.get('condition_on_previous_text', True) else 'Não'}",
                f"\n💾 Processamento de Arquivos:",
                f"   • Aceleração aplicada: {self.whisper_settings.get('acceleration_factor', 1.0)}x",
                f"   • Chunking inteligente: {'Ativo' if self.enable_smart_chunking else 'Inativo'}",
                f"   • Duração do chunk: {self.smart_chunk_duration_seconds}s",
                f"   • Processos paralelos: {self.parallel_processes}",
                f"{'='*60}"
            ]
            
            # Combine transcriptions and statistics
            final_text = transcription_content + "\n".join(stats_report)
            
            # Limpeza de arquivos temporários após processamento
            self._cleanup_chunks_and_temp_files()
            
            self.transcription_finished.emit(final_text)
            self.update_status.emit(
                {
                    "text": f"Transcrição concluída! {total_files} arquivos em {total_processing_time:.1f}s",
                    "last_time": 0,
                    "total_time": total_processing_time,
                }
            )

        except Exception as e:
            error_message = (
                f"Erro na transcrição: {e}. "
                "Verifique se as dependências (cuBLAS, CTranslate2) "
                "estão instaladas corretamente para o seu dispositivo."
            )
            self.update_status.emit(
                {"text": error_message, "last_time": 0, "total_time": 0}
            )
            self.transcription_finished.emit("")

    def _cleanup_chunks_and_temp_files(self, directory: str = None):
        """Remove chunks e arquivos temporários após processamento."""
        if directory is None:
            directory = self.audio_folder
        
        cleanup_patterns = [
            "*_chunk_*.wav",
            "*_ffmpeg_chunk_*.wav", 
            "*_silence_chunk_*.wav",
            "*_accelerated*.wav",
            "*_processed*.wav",
            "*_extracted*.wav"
        ]
        
        import glob
        cleaned_files = 0
        
        for pattern in cleanup_patterns:
            pattern_path = os.path.join(directory, pattern)
            for file_path in glob.glob(pattern_path):
                try:
                    os.remove(file_path)
                    cleaned_files += 1
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo temporário {file_path}: {e}")
        
        if cleaned_files > 0:
            logger.info(f"Limpeza concluída: {cleaned_files} arquivos temporários removidos")
            self.update_status.emit({
                "text": f"Limpeza: {cleaned_files} arquivos temporários removidos",
                "last_time": 0,
                "total_time": 0,
            })

    def _save_individual_transcription(self, filepath: str, transcription_text: str):
        """Salva transcrição individual com nome baseado no arquivo original."""
        if not transcription_text.strip():
            return None
            
        # Gera nome do arquivo de transcrição baseado no arquivo original
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        transcription_filename = f"{base_name}_transcricao.txt"
        transcription_path = os.path.join(self.audio_folder, transcription_filename)
        
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

    def _apply_anti_loop_recovery(self, 
                                transcription_text: str, 
                                audio_path: str, 
                                audio_duration: float,
                                transcribe_params: dict,
                                model) -> str:
        """
        Apply anti-loop detection and recovery to transcription result.
        
        Args:
            transcription_text: Original transcription result
            audio_path: Path to the audio file
            audio_duration: Duration of the audio
            transcribe_params: Transcription parameters
            model: FastWhisper model instance
            
        Returns:
            Corrected transcription text (original if no issues found)
        """
        if not transcription_text or not transcription_text.strip():
            return transcription_text
        
        # Initialize recovery manager with transcription function
        if self.recovery_manager is None:
            self.recovery_manager = CoreRecoveryManager(
                lambda path, settings: self._transcribe_with_model(model, path, settings)
            )
        
        # Detect potential loops
        detection_result = self.loop_detector.detect(transcription_text, audio_duration)
        
        if detection_result.has_loop:
            # Emit loop detected signal
            self.loop_detected.emit({
                'file': os.path.basename(audio_path),
                'loop_type': detection_result.loop_type,
                'confidence': detection_result.confidence,
                'pattern': detection_result.pattern
            })
            
            self.update_status.emit({
                "text": f"🔄 Loop detectado em {os.path.basename(audio_path)} - Iniciando recuperação...",
                "last_time": 0,
                "total_time": 0,
            })
            
            # Emit recovery started signal
            self.recovery_started.emit({
                'file': os.path.basename(audio_path),
                'original_text': transcription_text[:100] + "..." if len(transcription_text) > 100 else transcription_text,
                'problem': detection_result.loop_type
            })
            
            # Attempt recovery
            recovery_result = self.recovery_manager.recover_transcription(
                audio_path, transcription_text, transcribe_params, audio_duration
            )
            
            # Emit recovery completed signal
            self.recovery_completed.emit({
                'file': os.path.basename(audio_path),
                'success': recovery_result.success,
                'strategy_used': recovery_result.strategy_used.value,
                'attempts_made': recovery_result.attempts_made,
                'processing_time': recovery_result.processing_time,
                'quality_score': recovery_result.quality_score
            })
            
            if recovery_result.success:
                self.update_status.emit({
                    "text": f"✅ Recuperação bem-sucedida para {os.path.basename(audio_path)} "
                           f"(Estratégia: {recovery_result.strategy_used.value})",
                    "last_time": 0,
                    "total_time": 0,
                })
                return recovery_result.text
            else:
                self.update_status.emit({
                    "text": f"⚠️ Recuperação falhou para {os.path.basename(audio_path)} - "
                           f"Usando resultado original",
                    "last_time": 0,
                    "total_time": 0,
                })
                return transcription_text
        
        # No loop detected, check quality
        quality_score = self.quality_validator.validate(transcription_text, audio_duration)
        if quality_score < 0.4:  # Very low quality threshold
            self.update_status.emit({
                "text": f"⚠️ Qualidade baixa detectada em {os.path.basename(audio_path)} "
                       f"(Score: {quality_score:.2f})",
                "last_time": 0,
                "total_time": 0,
            })
        
        return transcription_text
    
    def _transcribe_with_model(self, model, audio_path: str, settings: dict) -> str:
        """
        Transcribe audio using the provided model and settings.
        Used by recovery manager for re-transcription attempts.
        """
        try:
            segments, _ = model.transcribe(audio_path, **settings)
            return "".join(segment.text for segment in segments)
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def get_anti_loop_statistics(self) -> dict:
        """Get statistics from the anti-loop system."""
        stats = {
            'loop_detector': self.loop_detector.get_statistics(),
            'recovery_manager': None
        }
        
        if self.recovery_manager:
            stats['recovery_manager'] = self.recovery_manager.get_statistics()
        
        return stats
    
    def reset_anti_loop_statistics(self):
        """Reset all anti-loop system statistics."""
        self.loop_detector.reset_statistics()
        if self.recovery_manager:
            self.recovery_manager.reset_statistics()

    def stop(self):
        self._is_running = False
        # Limpa chunks e arquivos temporários
        self._cleanup_chunks_and_temp_files()
        # Limpa o cache ao parar
        self.file_cache.clear_stale_entries()