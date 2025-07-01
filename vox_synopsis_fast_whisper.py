import sys
import sounddevice as sd
import numpy as np
import soundfile as sf
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QProgressBar, QMessageBox,
                             QLineEdit, QFileDialog, QCheckBox, QTextEdit, QDialog, QFormLayout,
                             QSlider, QDialogButtonBox, QScrollArea)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
import datetime
import os
import noisereduce as nr
# --- MODIFICAÇÃO: Importar fast_whisper em vez de whisper ---
from faster_whisper import WhisperModel
import glob
import time
import psutil
try:
    import torch
except ImportError:
    torch = None

# --- Configurações de Áudio ---
SAMPLE_RATE = 48000  # Qualidade de estúdio (fast-whisper internamente reamostra para 16kHz)
CHUNK_DURATION_SECONDS = 60 # Duração de cada arquivo de áudio
OUTPUT_DIR = "gravacoes" # Pasta para salvar os arquivos

class RecordingThread(QThread):
    """
    Thread para lidar com a gravação de áudio em segundo plano,
    evitando que a interface gráfica congele.
    (Nenhuma alteração nesta classe)
    """
    status_update = pyqtSignal(dict)
    recording_error = pyqtSignal(str)

    def __init__(self, device_index, channels, output_path, apply_processing):
        super().__init__()
        self.device_index = device_index
        self.channels = channels
        self.output_path = output_path
        self.apply_processing = apply_processing
        self._is_running = False
        self.total_recorded_time = 0

    def run(self):
        self._is_running = True
        try:
            while self._is_running:
                current_chunk_data = []
                chunk_start_time = self.total_recorded_time
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(self.output_path, f"gravacao_{timestamp}.wav")
                with sd.InputStream(samplerate=SAMPLE_RATE,
                                    device=self.device_index,
                                    channels=self.channels,
                                    dtype='float32') as stream:
                    print(f"Iniciando novo trecho. Salvando em: {filename}")
                    for i in range(int(SAMPLE_RATE * CHUNK_DURATION_SECONDS / 1024)):
                        if not self._is_running:
                            break
                        audio_chunk, overflowed = stream.read(1024)
                        if overflowed:
                            print("Aviso: Overflow de buffer de áudio detectado.")
                        current_chunk_data.append(audio_chunk)
                        volume_level = np.sqrt(np.mean(audio_chunk**2))
                        time_in_chunk = (len(current_chunk_data) * 1024) / SAMPLE_RATE
                        self.total_recorded_time = chunk_start_time + time_in_chunk
                        self.status_update.emit({
                            "total_time": self.total_recorded_time,
                            "chunk_time_remaining": CHUNK_DURATION_SECONDS - time_in_chunk,
                            "volume": volume_level * 100
                        })
                    if not self._is_running and len(current_chunk_data) > 0:
                        print("Gravação interrompida, salvando trecho parcial.")
                        sf.write(filename, np.concatenate(current_chunk_data), SAMPLE_RATE)
                        break
                if self._is_running:
                    print(f"Trecho de {CHUNK_DURATION_SECONDS}s completo. Salvando...")
                    full_audio_data = np.concatenate(current_chunk_data)
                    sf.write(filename, full_audio_data, SAMPLE_RATE)
                    if self.apply_processing:
                        self.process_audio(filename, full_audio_data)
        except Exception as e:
            error_message = f"Erro durante a gravação: {e}"
            print(error_message)
            self.recording_error.emit(error_message)

    def process_audio(self, original_filepath, audio_data):
        try:
            print(f"Aplicando pós-processamento em {original_filepath}...")
            noise_sample_len = int(0.5 * SAMPLE_RATE)
            noise_clip = audio_data[:noise_sample_len]
            reduced_noise_audio = nr.reduce_noise(y=audio_data, sr=SAMPLE_RATE, y_noise=noise_clip, prop_decrease=1.0, stationary=True)
            peak_level = np.max(np.abs(reduced_noise_audio))
            if peak_level > 0:
                target_peak_dbfs = -1.0
                target_peak_linear = 10**(target_peak_dbfs / 20.0)
                normalization_factor = target_peak_linear / peak_level
                normalized_audio = reduced_noise_audio * normalization_factor
            else:
                normalized_audio = reduced_noise_audio
            base, ext = os.path.splitext(original_filepath)
            processed_filepath = f"{base}_processed{ext}"
            sf.write(processed_filepath, normalized_audio, SAMPLE_RATE)
            print(f"Arquivo processado salvo em: {processed_filepath}")
        except Exception as e:
            print(f"Falha no pós-processamento de {original_filepath}: {e}")

    def stop(self):
        self._is_running = False
        print("Sinal de parada recebido.")


class AudioRecorderApp(QMainWindow):
    """
    Classe principal da aplicação GUI.
    """
    def __init__(self):
        super().__init__()
        # --- MODIFICAÇÃO: Título da janela ---
        self.setWindowTitle("VoxSynopsis (FastWhisper)")
        self.setGeometry(100, 100, 450, 300)

        self.output_path = os.path.join(os.getcwd(), OUTPUT_DIR)
        self.ensure_output_path_exists()
        self.recording_thread = None
        self.transcription_thread = None

        # --- MODIFICAÇÃO: Configurações padrão para fast-whisper ---
        self.whisper_settings = {
            "model": "medium",
            "language": "pt",
            "device": "cpu",
            "compute_type": "int8", # int8 para CPU, int8_float16 ou float16 para GPU
            "vad_filter": True, # Voice Activity Detection para pular silêncio (grande ganho de performance)
            "temperature": 0.0,
            "best_of": 5,
            "beam_size": 5,
            "condition_on_previous_text": True,
            "initial_prompt": "",
        }

        self.process = psutil.Process(os.getpid())
        self.resource_timer = QTimer(self)
        self.resource_timer.setInterval(1000)
        self.resource_timer.timeout.connect(self.update_resource_usage)
        self.resource_timer.start()
        self.setup_ui()

    # --- NENHUMA ALTERAÇÃO ATÉ open_settings_dialog ---
    # As funções setup_ui, ensure_output_path_exists, browse_folder, start_transcription, etc.
    # permanecem as mesmas, pois a lógica da GUI não muda.
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Dispositivo de Entrada:"))
        self.device_combo = QComboBox()
        device_layout.addWidget(self.device_combo)
        main_layout.addLayout(device_layout)
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Pasta de Saída:"))
        self.path_textbox = QLineEdit(self.output_path)
        path_layout.addWidget(self.path_textbox)
        self.browse_button = QPushButton("Procurar")
        self.browse_button.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.browse_button)
        main_layout.addLayout(path_layout)
        self.processing_checkbox = QCheckBox("Aplicar pós-processamento (redução de ruído)")
        self.processing_checkbox.setChecked(True)
        main_layout.addWidget(self.processing_checkbox)
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Gravação")
        self.start_button.clicked.connect(self.start_recording)
        button_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("Parar Gravação")
        self.stop_button.clicked.connect(self.stop_recording)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        self.transcribe_button = QPushButton("Transcrever Áudio")
        self.transcribe_button.clicked.connect(self.start_transcription)
        self.settings_button = QPushButton("Cfg.FastWhisper")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        button_layout.addWidget(self.transcribe_button)
        button_layout.addWidget(self.settings_button)
        main_layout.addLayout(button_layout)
        self.status_label = QLabel("Status: Parado")
        main_layout.addWidget(self.status_label)
        self.total_time_label = QLabel("Tempo Total Gravado: 00:00:00")
        main_layout.addWidget(self.total_time_label)
        self.chunk_time_label = QLabel("Tempo Restante no Trecho: 60.0s")
        main_layout.addWidget(self.chunk_time_label)
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        volume_layout.addWidget(self.volume_bar)
        main_layout.addLayout(volume_layout)
        resource_layout = QHBoxLayout()
        cpu_layout = QVBoxLayout()
        cpu_layout.addWidget(QLabel("CPU:"))
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        cpu_layout.addWidget(self.cpu_bar)
        resource_layout.addLayout(cpu_layout)
        mem_layout = QVBoxLayout()
        mem_layout.addWidget(QLabel("Memória:"))
        self.mem_bar = QProgressBar()
        self.mem_bar.setRange(0, 100)
        mem_layout.addWidget(self.mem_bar)
        resource_layout.addLayout(mem_layout)
        main_layout.addLayout(resource_layout)
        self.transcription_status_label = QLabel("Status da Transcrição: --")
        main_layout.addWidget(self.transcription_status_label)
        self.last_file_time_label = QLabel("Tempo do Último Arquivo: --")
        main_layout.addWidget(self.last_file_time_label)
        self.total_transcription_time_label = QLabel("Tempo Total de Transcrição: --")
        main_layout.addWidget(self.total_transcription_time_label)
        self.transcription_area = QTextEdit()
        self.transcription_area.setMaximumHeight(150)
        main_layout.addWidget(self.transcription_area)
        self.populate_devices()
    def ensure_output_path_exists(self):
        try:
            os.makedirs(self.output_path, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Erro de Diretório", f"Não foi possível criar a pasta:\n{self.output_path}\n\n{e}")
    def browse_folder(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Pasta", self.output_path)
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
        self.transcription_thread = TranscriptionThread(self.output_path, self.whisper_settings)
        self.transcription_thread.update_status.connect(self.update_transcription_status)
        self.transcription_thread.update_transcription.connect(self.append_transcription)
        self.transcription_thread.transcription_finished.connect(self.on_transcription_finished)
        self.transcription_thread.start()
    def update_transcription_status(self, status_dict):
        self.transcription_status_label.setText(status_dict.get("text", ""))
        last_time = status_dict.get("last_time", 0)
        if last_time > 0:
            self.last_file_time_label.setText(f"Tempo do Último Arquivo: {last_time:.2f} segundos")
        else:
            self.last_file_time_label.setText("Tempo do Último Arquivo: --")
        total_time = status_dict.get("total_time", 0)
        if total_time > 0:
            self.total_transcription_time_label.setText(f"Tempo Total de Transcrição: {total_time:.2f} segundos")
        else:
            self.total_transcription_time_label.setText("Tempo Total de Transcrição: --")
    def append_transcription(self, text):
        self.transcription_area.append(text)
    def on_transcription_finished(self, full_text):
        self.transcribe_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        if not self.recording_thread or not self.recording_thread.isRunning():
            self.stop_button.setEnabled(False)
        if full_text:
            save_path = os.path.join(self.output_path, "transcricao_completa.txt")
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                self.update_transcription_status({"text": f"Transcrição concluída! Resultado salvo em {save_path}", "last_time": 0, "total_time": 0})
            except Exception as e:
                self.update_transcription_status({"text": f"Erro ao salvar arquivo de transcrição: {e}", "last_time": 0, "total_time": 0})
    def populate_devices(self):
        self.devices = sd.query_devices()
        self.input_devices = [(i, d) for i, d in enumerate(self.devices) if d['max_input_channels'] > 0]
        for i, device in self.input_devices:
            self.device_combo.addItem(f"({i}) {device['name']}", i)
        self.device_combo.addItem("Microfone + Som do Sistema (Requer Dispositivo Agregado)")
    def start_recording(self):
        selected_text = self.device_combo.currentText()
        if "Microfone + Som" in selected_text:
            QMessageBox.information(self, "Aviso",
                                      "Para gravar áudio do microfone e do sistema simultaneamente, "
                                      "você deve selecionar um dispositivo de áudio agregado (como 'Stereo Mix' no Windows "
                                      "ou 'BlackHole' no macOS) que já faça essa mixagem.")
            return
        device_index = self.device_combo.currentData()
        channels = self.devices[device_index]['max_input_channels']
        channels_to_use = min(channels, 2)
        apply_processing = self.processing_checkbox.isChecked()
        self.recording_thread = RecordingThread(device_index, channels_to_use, self.output_path, apply_processing)
        self.recording_thread.status_update.connect(self.update_status)
        self.recording_thread.recording_error.connect(self.show_error_message)
        self.recording_thread.finished.connect(self.on_recording_finished)
        self.recording_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.device_combo.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.processing_checkbox.setEnabled(False)
        self.status_label.setText("Status: Gravando...")
    def stop_recording(self):
        if self.recording_thread:
            self.recording_thread.stop()
            self.status_label.setText("Status: Parando...")
            self.stop_button.setEnabled(False)
    def on_recording_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.browse_button.setEnabled(True)
        self.processing_checkbox.setEnabled(True)
        self.status_label.setText("Status: Parado")
        self.volume_bar.setValue(0)
        QMessageBox.information(self, "Gravação Finalizada", "A gravação foi interrompida.")
    def update_status(self, status_dict):
        total_seconds = int(status_dict["total_time"])
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        self.total_time_label.setText(f"Tempo Total Gravado: {h:02d}:{m:02d}:{s:02d}")
        remaining = max(0, status_dict["chunk_time_remaining"])
        self.chunk_time_label.setText(f"Tempo Restante no Trecho: {remaining:.1f}s")
        self.volume_bar.setValue(int(status_dict["volume"]))
    def show_error_message(self, message):
        self.stop_recording()
        QMessageBox.critical(self, "Erro de Gravação", message)
    def update_resource_usage(self):
        try:
            cpu_percent = self.process.cpu_percent(interval=None)
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()
            self.cpu_bar.setValue(int(cpu_percent))
            self.mem_bar.setValue(int(mem_percent))
            mem_mb = mem_info.rss / (1024 * 1024)
            self.mem_bar.setFormat(f"Memória: {mem_mb:.1f} MB (%p%)")
        except psutil.NoSuchProcess:
            self.cpu_bar.setValue(0)
            self.cpu_bar.setFormat("CPU: N/A")
            self.mem_bar.setValue(0)
            self.mem_bar.setFormat("Memória: N/A")
        except Exception as e:
            print(f"Erro ao monitorar recursos: {e}")
            self.cpu_bar.setValue(0)
            self.cpu_bar.setFormat("CPU: Erro")
            self.mem_bar.setValue(0)
            self.mem_bar.setFormat("Memória: Erro")

    def open_settings_dialog(self):
        """
        Abre a caixa de diálogo de configurações do FastWhisper.
        """
        # --- MODIFICAÇÃO: Passa a classe de diálogo correta ---
        settings_dialog = FastWhisperSettingsDialog(self.whisper_settings, self)
        if settings_dialog.exec_():
            self.whisper_settings = settings_dialog.get_settings()
            QMessageBox.information(self, "Configurações Salvas", "As configurações do FastWhisper foram salvas com sucesso!")

    def closeEvent(self, event):
        if self.recording_thread and self.recording_thread.isRunning():
            self.stop_recording()
            self.recording_thread.wait()
        event.accept()

# --- MODIFICAÇÃO PRINCIPAL: Diálogo de Configurações para FastWhisper ---
class FastWhisperSettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações do FastWhisper")
        self.setFixedSize(600, 650)
        self.settings = current_settings.copy()

        self.layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        self.layout.addWidget(scroll_area)
        scroll_content = QWidget()
        self.form_layout = QFormLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        # --- NOVOS E MODIFICADOS PARÂMETROS ---
        # Modelo
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large-v2", "large-v3"])
        self.model_combo.setCurrentText(self.settings.get("model", "medium"))
        self.form_layout.addRow("Modelo:", self.model_combo)
        self.form_layout.addRow("", QLabel("Modelos maiores são mais precisos, porém mais lentos. 'large-v3' é o mais preciso."))

        # Dispositivo
        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda"])
        gpu_available = torch and torch.cuda.is_available()
        if not gpu_available:
            self.device_combo.model().item(1).setEnabled(False)
        self.device_combo.setCurrentText(self.settings.get("device", "cpu"))
        self.form_layout.addRow("Dispositivo:", self.device_combo)
        self.form_layout.addRow("", QLabel("'cuda' (GPU) é muito mais rápido."))
        
        # Compute Type (NOVO e CRÍTICO para performance)
        self.compute_type_combo = QComboBox()
        if gpu_available:
            self.compute_type_combo.addItems(["int8_float16", "float16", "int8", "float32"])
        else:
            self.compute_type_combo.addItems(["int8", "float32"])
        self.compute_type_combo.setCurrentText(self.settings.get("compute_type", "int8"))
        self.form_layout.addRow("Tipo de Computação:", self.compute_type_combo)
        self.form_layout.addRow("", QLabel("'int8' é o mais rápido (CPU). 'int8_float16' é o ideal para GPUs (velocidade/precisão)."))

        # VAD Filter (NOVO para performance)
        self.vad_filter_checkbox = QCheckBox("Usar Filtro VAD (Pular Silêncio)")
        self.vad_filter_checkbox.setChecked(self.settings.get("vad_filter", True))
        self.form_layout.addRow("", self.vad_filter_checkbox)
        self.form_layout.addRow("", QLabel("Detecta e pula partes sem fala no áudio, acelerando muito a transcrição."))

        # Idioma
        self.language_combo = QComboBox()
        self.language_combo.addItems(["pt", "en", "auto"])
        self.language_combo.setCurrentText(self.settings.get("language", "pt"))
        self.form_layout.addRow("Idioma:", self.language_combo)
        self.form_layout.addRow("", QLabel("Idioma do áudio. 'auto' para detecção automática."))

        # Parâmetros de Beam Search (sem alteração na lógica, mas importantes)
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 10)
        self.temperature_slider.setValue(int(self.settings.get("temperature", 0.0) * 10))
        self.temperature_label = QLabel(f"Temperatura: {self.temperature_slider.value() / 10.0}")
        self.temperature_slider.valueChanged.connect(lambda v: self.temperature_label.setText(f"Temperatura: {v / 10.0}"))
        self.form_layout.addRow(self.temperature_label, self.temperature_slider)
        self.best_of_slider = QSlider(Qt.Horizontal)
        self.best_of_slider.setRange(1, 10)
        self.best_of_slider.setValue(self.settings.get("best_of", 5))
        self.best_of_label = QLabel(f"Best Of: {self.best_of_slider.value()}")
        self.best_of_slider.valueChanged.connect(lambda v: self.best_of_label.setText(f"Best Of: {v}"))
        self.form_layout.addRow(self.best_of_label, self.best_of_slider)
        self.beam_size_slider = QSlider(Qt.Horizontal)
        self.beam_size_slider.setRange(1, 10)
        self.beam_size_slider.setValue(self.settings.get("beam_size", 5))
        self.beam_size_label = QLabel(f"Beam Size: {self.beam_size_slider.value()}")
        self.beam_size_slider.valueChanged.connect(lambda v: self.beam_size_label.setText(f"Beam Size: {v}"))
        self.form_layout.addRow(self.beam_size_label, self.beam_size_slider)
        
        # Parâmetros de Contexto
        self.condition_checkbox = QCheckBox("Condicionar no texto anterior")
        self.condition_checkbox.setChecked(self.settings.get("condition_on_previous_text", True))
        self.form_layout.addRow("", self.condition_checkbox)
        self.initial_prompt_edit = QLineEdit(self.settings.get("initial_prompt", ""))
        self.form_layout.addRow("Prompt Inicial:", self.initial_prompt_edit)

        # Botões
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.auto_cfg_button = QPushButton("Cfg. Automática")
        self.auto_cfg_button.clicked.connect(self.auto_configure)
        self.button_box.addButton(self.auto_cfg_button, QDialogButtonBox.ActionRole)
        self.layout.addWidget(self.button_box)

    def auto_configure(self):
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        gpu_available = torch and torch.cuda.is_available()

        info_msg = (f"RAM Total: {total_ram_gb:.2f} GB\nGPU disponível: {'Sim' if gpu_available else 'Não'}\n\n"
                    "Ajustando configurações para o melhor equilíbrio entre desempenho e precisão.")
        QMessageBox.information(self, "Análise de Hardware", info_msg)

        self.vad_filter_checkbox.setChecked(True) # Quase sempre a melhor opção
        self.condition_checkbox.setChecked(True)
        self.temperature_slider.setValue(0)
        self.initial_prompt_edit.clear()
        
        if gpu_available:
            # GPU VRAM é o fator limitante
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            self.device_combo.setCurrentText("cuda")
            self.compute_type_combo.setCurrentText("int8_float16")
            
            if vram_gb >= 10:
                self.model_combo.setCurrentText("large-v3")
                self.beam_size_slider.setValue(5)
                self.best_of_slider.setValue(5)
                rec_msg = "GPU potente detectada (>10GB VRAM)! Sugerindo 'large-v3' com 'int8_float16'."
            elif vram_gb >= 5:
                self.model_combo.setCurrentText("medium")
                self.beam_size_slider.setValue(5)
                self.best_of_slider.setValue(5)
                rec_msg = "GPU intermediária detectada (5-10GB VRAM). Sugerindo 'medium' com 'int8_float16'."
            else:
                self.model_combo.setCurrentText("small")
                self.beam_size_slider.setValue(2)
                self.best_of_slider.setValue(2)
                rec_msg = "GPU com pouca VRAM (<5GB). Sugerindo 'small' com 'int8_float16' para evitar erros de memória."
            QMessageBox.information(self, "Configuração Automática (GPU)", rec_msg)
        else: # CPU-only
            self.device_combo.setCurrentText("cpu")
            self.compute_type_combo.setCurrentText("int8")
            
            if total_ram_gb >= 8:
                self.model_combo.setCurrentText("medium")
                self.beam_size_slider.setValue(5)
                self.best_of_slider.setValue(5)
                rec_msg = "Hardware potente (CPU). Sugerindo modelo 'medium' com 'int8' para melhor precisão."
            elif total_ram_gb >= 4:
                self.model_combo.setCurrentText("small")
                self.beam_size_slider.setValue(3)
                self.best_of_slider.setValue(3)
                rec_msg = "Hardware intermediário (CPU). Sugerindo 'small' com 'int8'."
            else:
                self.model_combo.setCurrentText("base")
                self.beam_size_slider.setValue(2)
                self.best_of_slider.setValue(2)
                rec_msg = "Hardware de baixo desempenho (CPU). Sugerindo 'base' com 'int8' para garantir execução."
            QMessageBox.information(self, "Configuração Automática (CPU)", rec_msg)
            
        # Atualiza labels dos sliders
        self.temperature_label.setText(f"Temperatura: {self.temperature_slider.value() / 10.0}")
        self.best_of_label.setText(f"Best Of: {self.best_of_slider.value()}")
        self.beam_size_label.setText(f"Beam Size: {self.beam_size_slider.value()}")

    def get_settings(self):
        self.settings["model"] = self.model_combo.currentText()
        self.settings["language"] = self.language_combo.currentText()
        self.settings["device"] = self.device_combo.currentText()
        self.settings["compute_type"] = self.compute_type_combo.currentText()
        self.settings["vad_filter"] = self.vad_filter_checkbox.isChecked()
        self.settings["temperature"] = self.temperature_slider.value() / 10.0
        self.settings["best_of"] = self.best_of_slider.value()
        self.settings["beam_size"] = self.beam_size_slider.value()
        self.settings["condition_on_previous_text"] = self.condition_checkbox.isChecked()
        self.settings["initial_prompt"] = self.initial_prompt_edit.text()
        return self.settings

# --- MODIFICAÇÃO PRINCIPAL: Lógica de Transcrição ---
class TranscriptionThread(QThread):
    """
    Thread para lidar com a transcrição de áudio em segundo plano usando fast-whisper.
    """
    update_status = pyqtSignal(dict)
    update_transcription = pyqtSignal(str)
    transcription_finished = pyqtSignal(str)

    def __init__(self, audio_folder, whisper_settings):
        super().__init__()
        self.audio_folder = audio_folder
        self.whisper_settings = whisper_settings.copy() # Usa uma cópia para poder modificar
        self._is_running = True

    def run(self):
        model = None
        last_file_time = 0
        try:
            # Separa os parâmetros: os para carregar o modelo e os para a transcrição
            model_size = self.whisper_settings.pop("model")
            device = self.whisper_settings.pop("device")
            compute_type = self.whisper_settings.pop("compute_type")
            # O restante dos parâmetros em whisper_settings será usado na função transcribe()
            transcribe_params = {
                "language": self.whisper_settings.get("language"),
                "temperature": self.whisper_settings.get("temperature"),
                "best_of": self.whisper_settings.get("best_of"),
                "beam_size": self.whisper_settings.get("beam_size"),
                "condition_on_previous_text": self.whisper_settings.get("condition_on_previous_text"),
                "initial_prompt": self.whisper_settings.get("initial_prompt"),
                "vad_filter": self.whisper_settings.get("vad_filter"),
            }
            
            self.update_status.emit({"text": f"Carregando modelo FastWhisper ({model_size}) no dispositivo {device} ({compute_type})...", "last_time": 0, "total_time": 0})
            
            # Carrega o modelo fast-whisper
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            
            self.update_status.emit({"text": "Modelo carregado. Procurando arquivos...", "last_time": 0, "total_time": 0})
            
            # Lógica de busca de arquivos (inalterada)
            processed_files = sorted(glob.glob(os.path.join(self.audio_folder, "*_processed.wav")))
            original_files = sorted(glob.glob(os.path.join(self.audio_folder, "*.wav")))
            files_to_transcribe = []
            processed_originals = {f.replace("_processed.wav", ".wav") for f in processed_files}
            files_to_transcribe.extend(processed_files)
            files_to_transcribe.extend([f for f in original_files if f not in processed_originals and not f.endswith("_processed.wav")])
            
            if not files_to_transcribe:
                self.update_status.emit({"text": "Nenhum arquivo .wav encontrado.", "last_time": 0, "total_time": 0})
                self.transcription_finished.emit("")
                return
            
            full_transcription = []
            total_files = len(files_to_transcribe)
            total_processing_time = 0

            for i, filepath in enumerate(files_to_transcribe):
                if not self._is_running:
                    self.update_status.emit({"text": "Transcrição cancelada.", "last_time": 0, "total_time": total_processing_time})
                    break
                
                status_text = f"Transcrevendo {i+1}/{total_files}: {os.path.basename(filepath)}"
                
                start_time = time.time()
                
                # --- MODIFICAÇÃO: Chamada de transcrição do fast-whisper ---
                # Retorna um iterador de segmentos, não um dicionário
                segments, info = model.transcribe(filepath, **transcribe_params)
                
                # Junta os segmentos para obter o texto completo
                transcription_text = "".join(segment.text for segment in segments)
                
                end_time = time.time()

                last_file_time = end_time - start_time
                total_processing_time += last_file_time
                
                self.update_status.emit({"text": status_text, "last_time": last_file_time, "total_time": total_processing_time})
                self.update_transcription.emit(f"--- {os.path.basename(filepath)} ---\n{transcription_text}\n\n")
                full_transcription.append(transcription_text)

            final_text = "\n".join(full_transcription)
            self.transcription_finished.emit(final_text)
            self.update_status.emit({"text": "Transcrição concluída!", "last_time": 0, "total_time": total_processing_time})

        except Exception as e:
            error_message = f"Erro na transcrição: {e}. Verifique se as dependências (cuBLAS, CTranslate2) estão instaladas corretamente para o seu dispositivo."
            self.update_status.emit({"text": error_message, "last_time": 0, "total_time": 0})
            self.transcription_finished.emit("")

    def stop(self):
        self._is_running = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = AudioRecorderApp()
    main_win.show()
    sys.exit(app.exec_())