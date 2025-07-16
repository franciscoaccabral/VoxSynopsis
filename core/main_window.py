"""Main window application class."""

import json
import os
import time
from typing import Any

import psutil
import sounddevice as sd
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QCloseEvent, QCursor
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow, QMessageBox

from ui_vox_synopsis import Ui_MainWindow

from .config import OUTPUT_DIR, ConfigManager
from .recording import RecordingThread, DeviceInfo
from .transcription import TranscriptionThread
from .settings_dialog import FastWhisperSettingsDialog
from .completion_popup import CompletionPopup
from .gpu_monitor import gpu_monitor
from .ffmpeg_cuda import ffmpeg_cuda_optimizer


class AudioRecorderApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # Configura a UI a partir da classe importada
        self.setupUi(self)

        # --- Inicialização da Lógica da Aplicação ---
        self.config_manager = ConfigManager()
        self.whisper_settings = self.config_manager.settings

        self.output_path = os.path.join(os.getcwd(), OUTPUT_DIR)
        self.ensure_output_path_exists()
        self.path_textbox.setText(self.output_path)

        self.recording_thread = None
        self.transcription_thread = None

        # Conecta os sinais dos widgets (da UI) aos slots (métodos de lógica)
        self.connect_signals()

        # Preenche a lista de dispositivos
        self.populate_devices()

        # Inicia o timer para monitorar recursos
        self.process = psutil.Process(os.getpid())
        self.resource_timer = QTimer(self)
        self.resource_timer.setInterval(1000)
        self.resource_timer.timeout.connect(self.update_resource_usage)
        self.resource_timer.start()
        
        # Inicializa interface CUDA
        self.initialize_cuda_interface()

    def center_window(self):
        # Obtém a tela onde o cursor do mouse está
        screen = QApplication.screenAt(QCursor.pos())
        if not screen:
            # Se não for possível determinar a tela, usa a primária como fallback
            screen = QApplication.primaryScreen()

        if not screen:
            # Se ainda assim não houver tela, não podemos centralizar
            return

        # Obtém a geometria da tela disponível
        screen_geometry = screen.availableGeometry()
        # Obtém a geometria da janela
        window_geometry = self.frameGeometry()
        # Move o centro da janela para o centro da tela
        window_geometry.moveCenter(screen_geometry.center())
        # Move o canto superior esquerdo da janela para a nova posição
        self.move(window_geometry.topLeft())

    def showEvent(self, event):
        # Chama o método original para garantir o comportamento padrão
        super().showEvent(event)
        # Centraliza a janela apenas na primeira vez que ela é exibida
        if not hasattr(self, "_is_centered"):
            self.center_window()
            self._is_centered = True

    def connect_signals(self):
        """Conecta todos os sinais da UI aos seus respectivos slots."""
        self.browse_button.clicked.connect(self.browse_folder)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.transcribe_button.clicked.connect(self.start_transcription)
        self.settings_button.clicked.connect(self.open_settings_dialog)

    def ensure_output_path_exists(self):
        try:
            os.makedirs(self.output_path, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(
                self,
                "Erro de Diretório",
                f"Não foi possível criar a pasta:\n{self.output_path}\n\n{e}",
            )

    def browse_folder(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta", self.output_path
        )
        if directory:
            self.output_path = directory
            self.path_textbox.setText(self.output_path)
            self.ensure_output_path_exists()

    def start_transcription(self):
        self.transcription_area.clear()
        self.transcribe_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.browse_button.setEnabled(False)

        # Atualiza o label de threads na UI
        cpu_threads_count = self.whisper_settings.get("cpu_threads", "N/A")
        self.threads_label.setText(f"Threads: {cpu_threads_count}")

        self.transcription_thread = TranscriptionThread(
            self.output_path, self.whisper_settings
        )
        self.transcription_thread.update_status.connect(
            self.update_transcription_status
        )
        self.transcription_thread.update_transcription.connect(
            self.append_transcription
        )
        self.transcription_thread.transcription_finished.connect(
            self.on_transcription_finished
        )
        # Connect to completion data signal for popup
        if hasattr(self.transcription_thread, 'completion_data_ready'):
            self.transcription_thread.completion_data_ready.connect(
                self.show_completion_popup
            )
        self.transcription_thread.start()

    def update_transcription_status(self, status_dict):
        self.transcription_status_label.setText(status_dict.get("text", ""))
        last_time = status_dict.get("last_time", 0)
        if last_time > 0:
            self.last_file_time_label.setText(
                f"Tempo do Último Arquivo: {last_time:.2f} segundos"
            )
        else:
            self.last_file_time_label.setText("Tempo do Último Arquivo: --")
        total_time = status_dict.get("total_time", 0)
        if total_time > 0:
            self.total_transcription_time_label.setText(
                f"Tempo Total de Transcrição: {total_time:.2f} segundos"
            )
        else:
            self.total_transcription_time_label.setText(
                "Tempo Total de Transcrição: --"
            )

    def append_transcription(self, text):
        self.transcription_area.append(text)

    def on_transcription_finished(self, full_text):
        self.transcribe_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.threads_label.setText("Threads: N/A")
        if not self.recording_thread or not self.recording_thread.isRunning():
            self.stop_button.setEnabled(False)
        if full_text:
            # Gera nome do arquivo com timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            save_path = os.path.join(self.output_path, f"transcricao_completa_{timestamp}.txt")
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(f"Transcrição Completa - VoxSynopsis\n")
                    f.write(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(full_text)
                    self.update_transcription_status(
                        {
                            "text": (
                                f"Transcrição concluída! Resultado salvo em {save_path}"
                            ),
                            "last_time": 0,
                            "total_time": 0,
                        }
                    )
            except Exception as e:
                self.update_transcription_status(
                    {
                        "text": f"Erro ao salvar arquivo de transcrição: {e}",
                        "last_time": 0,
                        "total_time": 0,
                    }
                )

    def show_completion_popup(self, performance_data: dict):
        """Exibe popup de conclusão com informações de desempenho."""
        try:
            # Show completion popup
            CompletionPopup.show_completion_popup(performance_data, self)
        except Exception as e:
            print(f"Erro ao exibir popup de conclusão: {e}")
            # Fallback to simple message
            QMessageBox.information(
                self, 
                "Transcrição Concluída", 
                f"Processamento concluído!\n"
                f"Arquivos processados: {performance_data.get('successful_files', 0)}/{performance_data.get('total_files', 0)}\n"
                f"Tempo total: {performance_data.get('total_processing_time', 0):.1f}s"
            )

    def populate_devices(self):
        self.device_combo.clear()
        self.devices = sd.query_devices()
        self.input_devices = []
        found_loopback = False
        try:
            default_output = sd.query_devices(kind="output")
            loopback_device = sd.query_devices(
                default_output["name"],
                kind="input",
            )
            loopback_index = int(loopback_device["index"])
            self.device_combo.addItem(
                f"Áudio do Sistema ({loopback_device['name']})",
                loopback_index,
            )
            self.input_devices.append((loopback_index, loopback_device))
            found_loopback = True
            print(
                f"Dispositivo de loopback encontrado: {loopback_device['name']}"
            )
        except (ValueError, sd.PortAudioError, KeyError) as e:
            print(f"Dispositivo de loopback não encontrado. Erro: {e}")
        for i, device_info in enumerate(self.devices):
            if device_info["max_input_channels"] > 0:
                if not any(i == d[0] for d in self.input_devices):
                    self.device_combo.addItem(f"({i}) {device_info['name']}", i)
                    self.input_devices.append((i, device_info))
        if not found_loopback:
            self.device_combo.addItem("Áudio do Sistema (Não disponível)")
            last_item_index = self.device_combo.count() - 1
            self.device_combo.model().item(last_item_index).setEnabled(False)

    def start_recording(self):
        device_index = self.device_combo.currentData()
        if device_index is None:
            QMessageBox.warning(
                self,
                "Dispositivo Inválido",
                "O dispositivo selecionado não está disponível.",
            )
            return
        channels = self.devices[device_index]["max_input_channels"]
        channels_to_use = min(channels, 2)
        apply_processing = self.processing_checkbox.isChecked()
        self.recording_thread = RecordingThread(
            device_index,
            channels_to_use,
            self.output_path,
            apply_processing,
            self.whisper_settings.get("chunk_duration_seconds", 30),
        )
        self.recording_thread.status_update.connect(self.update_status)
        self.recording_thread.recording_error.connect(self.show_error_message)
        self.recording_thread.finished.connect(self.on_recording_finished)
        self.recording_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.device_combo.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.processing_checkbox.setEnabled(False)
        self.status_label.setText("Gravando...")

    def stop_recording(self):
        if self.recording_thread:
            self.recording_thread.stop()
            self.status_label.setText("Parando...")
            self.stop_button.setEnabled(False)

    def on_recording_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.processing_checkbox.setEnabled(True)
        self.status_label.setText("Parado")
        self.volume_bar.setValue(0)
        QMessageBox.information(
            self, "Gravação Finalizada", "A gravação foi interrompida."
        )

    def update_status(self, status_dict):
        total_seconds = int(status_dict["total_time"])
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        self.total_time_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
        remaining = max(0, status_dict["chunk_time_remaining"])
        self.chunk_time_label.setText(f"{remaining:.1f}s")
        self.volume_bar.setValue(int(status_dict["volume"]))

    def show_error_message(self, message):
        self.stop_recording()
        QMessageBox.critical(self, "Erro de Gravação", message)

    def initialize_cuda_interface(self):
        """Initialize CUDA interface components."""
        # Update device status
        self.update_device_status()
        
        # Show/hide GPU elements based on CUDA availability
        cuda_available = gpu_monitor.is_cuda_available()
        gpu_monitoring = gpu_monitor.is_gpu_monitoring_available()
        
        if cuda_available and gpu_monitoring:
            self.gpu_label.show()
            self.gpu_bar.show()
            self.vram_label.show()
            self.vram_bar.show()
        else:
            self.gpu_label.hide()
            self.gpu_bar.hide()
            self.vram_label.hide()
            self.vram_bar.hide()
        
        # Set tooltips
        self.setup_tooltips()
    
    def setup_tooltips(self):
        """Setup informative tooltips for monitoring widgets."""
        device_status = gpu_monitor.get_device_status()
        
        if device_status['cuda_available']:
            cuda_info = device_status.get('cuda_info', {})
            gpu_name = cuda_info.get('device_name', 'GPU desconhecida')
            self.device_status_label.setToolTip(
                f"Dispositivo CUDA ativo: {gpu_name}\n"
                f"Capacidade CUDA: {cuda_info.get('device_capability', 'N/A')}\n"
                f"Dispositivos: {cuda_info.get('device_count', 0)}"
            )
            
            if device_status['gpu_monitoring_available']:
                primary_gpu = device_status.get('primary_gpu')
                if primary_gpu:
                    self.gpu_bar.setToolTip(
                        f"Utilização da GPU: {primary_gpu.name}\n"
                        f"Temperatura: {primary_gpu.temperature}°C"
                    )
                    self.vram_bar.setToolTip(
                        f"Memória VRAM: {primary_gpu.name}\n"
                        f"Total: {primary_gpu.total_memory}MB\n"
                        f"Livre: {primary_gpu.free_memory}MB"
                    )
        else:
            self.device_status_label.setToolTip("CUDA não disponível - usando CPU")
    
    def update_device_status(self):
        """Update device status display."""
        device = self.whisper_settings.get("device", "cpu")
        compute_type = self.whisper_settings.get("compute_type", "int8")
        
        if device == "cuda" and gpu_monitor.is_cuda_available():
            cuda_info = gpu_monitor.get_cuda_device_info()
            if cuda_info:
                gpu_name = cuda_info.get('device_name', 'GPU')
                # Extract short name (e.g., "GTX 1050 Ti" from "NVIDIA GeForce GTX 1050 Ti")
                short_name = gpu_name.replace("NVIDIA GeForce ", "").replace("NVIDIA ", "")
                self.device_status_label.setText(f"🚀 CUDA ({short_name}) | {compute_type}")
                self.device_status_label.setStyleSheet("font-weight: bold; color: #27ae60; padding: 4px;")
            else:
                self.device_status_label.setText(f"🚀 CUDA | {compute_type}")
                self.device_status_label.setStyleSheet("font-weight: bold; color: #27ae60; padding: 4px;")
        elif device == "cuda":
            # CUDA configured but not available
            self.device_status_label.setText(f"⚠️ CUDA (Indisponível) | {compute_type}")
            self.device_status_label.setStyleSheet("font-weight: bold; color: #e67e22; padding: 4px;")
        else:
            # CPU mode
            self.device_status_label.setText(f"🖥️ CPU | {compute_type}")
            self.device_status_label.setStyleSheet("font-weight: bold; color: #3498db; padding: 4px;")
        
        # Update acceleration status
        ffmpeg_status = "Ativo" if ffmpeg_cuda_optimizer.cuda_enabled else "CPU"
        if device == "cuda" and gpu_monitor.is_cuda_available():
            self.acceleration_status_label.setText(f"⚡ FFmpeg+Whisper: {ffmpeg_status}")
            self.acceleration_status_label.setStyleSheet("color: #27ae60;")
        else:
            self.acceleration_status_label.setText(f"⚡ CPU Mode")
            self.acceleration_status_label.setStyleSheet("color: #7f8c8d;")

    def update_resource_usage(self):
        try:
            # CPU and RAM monitoring
            cpu_percent = self.process.cpu_percent(interval=None)
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()
            self.cpu_bar.setValue(int(cpu_percent))
            self.mem_bar.setValue(int(mem_percent))
            mem_mb = mem_info.rss / (1024 * 1024)
            self.mem_bar.setFormat(f"{mem_mb:.1f} MB (%p%)")
            
            # GPU monitoring (if available)
            if gpu_monitor.is_gpu_monitoring_available():
                gpu_util = gpu_monitor.get_utilization_percentage(0)
                vram_percent = gpu_monitor.get_memory_usage_percentage(0)
                vram_info = gpu_monitor.format_memory_info(0)
                
                self.gpu_bar.setValue(gpu_util)
                self.vram_bar.setValue(vram_percent)
                self.vram_bar.setFormat(f"{vram_info} (%p%)")
                
                # Color coding based on usage
                if gpu_util > 80:
                    self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
                elif gpu_util > 50:
                    self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
                else:
                    self.gpu_bar.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
                
                if vram_percent > 80:
                    self.vram_bar.setStyleSheet("QProgressBar::chunk { background-color: #e74c3c; }")
                elif vram_percent > 60:
                    self.vram_bar.setStyleSheet("QProgressBar::chunk { background-color: #f39c12; }")
                else:
                    self.vram_bar.setStyleSheet("QProgressBar::chunk { background-color: #27ae60; }")
            
        except psutil.NoSuchProcess:
            self.cpu_bar.setValue(0)
            self.mem_bar.setValue(0)
            if gpu_monitor.is_gpu_monitoring_available():
                self.gpu_bar.setValue(0)
                self.vram_bar.setValue(0)
        except Exception as e:
            print(f"Erro ao monitorar recursos: {e}")
            self.cpu_bar.setValue(0)
            self.mem_bar.setValue(0)

    def open_settings_dialog(self):
        settings_dialog = FastWhisperSettingsDialog(self.whisper_settings, self)
        if settings_dialog.exec_():
            self.whisper_settings = settings_dialog.get_settings()
            self.config_manager.settings = self.whisper_settings
            self.config_manager.save_settings()
            
            # Update CUDA interface after settings change
            self.update_device_status()
            self.initialize_cuda_interface()
            
            QMessageBox.information(
                self,
                "Configurações Salvas",
                "As configurações do FastWhisper foram salvas com sucesso!",
            )

    def closeEvent(self, a0: QCloseEvent) -> None:
        if self.recording_thread and self.recording_thread.isRunning():
            self.stop_recording()
            self.recording_thread.wait()
        a0.accept()