import datetime
import glob
import os
import subprocess
import sys
import time

import noisereduce as nr
import numpy as np
import psutil
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,  # Adicionado QPushButton, QScrollArea, QWidget
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

# Importa a classe da UI a partir do arquivo separado
from ui_vox_synopsis import Ui_MainWindow

try:
    import torch
except ImportError:
    torch = None

# --- Configurações Globais ---
SAMPLE_RATE = 48000
CHUNK_DURATION_SECONDS = 60
OUTPUT_DIR = "gravacoes"


# --- Função para carregar o stylesheet ---
from typing import Any


def load_stylesheet(app: Any) -> None:
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Arquivo style.qss não encontrado. Usando estilo padrão.")


# --- Threads de Trabalho (sem alteração) ---
class RecordingThread(QThread):
    status_update = pyqtSignal(dict)
    recording_error = pyqtSignal(str)

    def __init__(
        self,
        device_index: int,
        channels: int,
        output_path: str,
        apply_processing: bool,
    ) -> None:
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
                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    device=self.device_index,
                    channels=self.channels,
                    dtype="float32",
                ) as stream:
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
                        self.status_update.emit(
                            {
                                "total_time": self.total_recorded_time,
                                "chunk_time_remaining": CHUNK_DURATION_SECONDS
                                - time_in_chunk,
                                "volume": volume_level * 100,
                            }
                        )
                    if not self._is_running and len(current_chunk_data) > 0:
                        print("Gravação interrompida, salvando trecho parcial.")
                        sf.write(
                            filename, np.concatenate(current_chunk_data), SAMPLE_RATE
                        )
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

    def process_audio(self, original_filepath: str, audio_data: np.ndarray) -> None:
        try:
            print(f"Aplicando pós-processamento em {original_filepath}...")
            noise_sample_len = int(0.5 * SAMPLE_RATE)
            noise_clip = audio_data[:noise_sample_len]
            reduced_noise_audio = nr.reduce_noise(
                y=audio_data,
                sr=SAMPLE_RATE,
                y_noise=noise_clip,
                prop_decrease=1.0,
                stationary=True,
            )
            peak_level = np.max(np.abs(reduced_noise_audio))
            if peak_level > 0:
                target_peak_dbfs = -1.0
                target_peak_linear = 10 ** (target_peak_dbfs / 20.0)
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


class TranscriptionThread(QThread):
    update_status = pyqtSignal(dict)
    update_transcription = pyqtSignal(str)
    transcription_finished = pyqtSignal(str)

    def __init__(self, audio_folder: str, whisper_settings: dict[str, Any]) -> None:
        super().__init__()
        self.audio_folder = audio_folder
        self.whisper_settings = whisper_settings.copy()
        self._is_running = True

    def run(self):
        # ... (lógica da thread de transcrição permanece a mesma)
        model = None
        last_file_time = 0
        try:
            model_size = self.whisper_settings.pop("model")
            device = self.whisper_settings.pop("device")
            compute_type = self.whisper_settings.pop("compute_type")
            acceleration_factor = self.whisper_settings.pop("acceleration_factor", 1.5)
            transcribe_params = self.whisper_settings

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
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            self.update_status.emit(
                {
                    "text": "Modelo carregado. Procurando arquivos...",
                    "last_time": 0,
                    "total_time": 0,
                }
            )

            all_files = []
            mp4_files = sorted(glob.glob(os.path.join(self.audio_folder, "*.mp4")))
            for mp4_path in mp4_files:
                base_name = os.path.splitext(os.path.basename(mp4_path))[0]
                accelerated_wav_path = os.path.join(
                    self.audio_folder, f"{base_name}_{acceleration_factor}x.wav"
                )

                if not os.path.exists(accelerated_wav_path):
                    self.update_status.emit(
                        {
                            "text": (
                                f"Extraindo áudio de {os.path.basename(mp4_path)}..."
                            ),
                            "last_time": 0,
                            "total_time": 0,
                        }
                    )
                    try:
                        command = [
                            "ffmpeg",
                            "-i",
                            mp4_path,
                            "-vn",
                            "-acodec",
                            "pcm_s16le",
                            "-ar",
                            "16000",
                            "-ac",
                            "1",
                            "-filter:a",
                            f"atempo={acceleration_factor}",
                            accelerated_wav_path,
                        ]
                        subprocess.run(
                            command, check=True, capture_output=True, text=True
                        )
                        self.update_status.emit(
                            {
                                "text": (
                                    "Áudio extraído e salvo como "
                                    f"{os.path.basename(accelerated_wav_path)}"
                                ),
                                "last_time": 0,
                                "total_time": 0,
                            }
                        )
                        all_files.append(accelerated_wav_path)
                    except subprocess.CalledProcessError as e:
                        error_msg = (
                            "Erro ao processar "
                            f"{os.path.basename(mp4_path)} com FFmpeg: {e.stderr}"
                        )
                        self.update_status.emit(
                            {"text": error_msg, "last_time": 0, "total_time": 0}
                        )
                        continue
                    except FileNotFoundError:
                        self.update_status.emit(
                            {
                                "text": (
                                    "Erro: FFmpeg não encontrado. Certifique-se "
                                    "de que está instalado e no PATH do sistema."
                                ),
                                "last_time": 0,
                                "total_time": 0,
                            }
                        )
                        self.transcription_finished.emit("")
                        return
                else:
                    all_files.append(accelerated_wav_path)

            processed_wavs = sorted(
                glob.glob(os.path.join(self.audio_folder, "*_processed.wav"))
            )
            original_wavs = sorted(glob.glob(os.path.join(self.audio_folder, "*.wav")))

            all_files.extend(processed_wavs)

            processed_originals = {
                f.replace("_processed.wav", ".wav") for f in processed_wavs
            }

            for wav_file in original_wavs:
                if wav_file not in processed_originals and not wav_file.endswith(
                    ".wav"
                ):
                    all_files.append(wav_file)

            files_to_transcribe = sorted(list(set(all_files)))

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

            full_transcription = []
            total_files = len(files_to_transcribe)
            total_processing_time = 0

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
                segments, info = model.transcribe(filepath, **transcribe_params)
                transcription_text = "".join(segment.text for segment in segments)
                end_time = time.time()

                last_file_time = end_time - start_time
                total_processing_time += last_file_time

                self.update_transcription.emit(
                    f"--- {os.path.basename(filepath)} ---\n{transcription_text}\n\n"
                )
                full_transcription.append(
                    f"--- {os.path.basename(filepath)} ---\n{transcription_text}"
                )

            final_text = "\n\n".join(full_transcription)
            self.transcription_finished.emit(final_text)
            self.update_status.emit(
                {
                    "text": "Transcrição concluída!",
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

    def stop(self):
        self._is_running = False


# --- Janela Principal da Aplicação ---
class AudioRecorderApp(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        # Configura a UI a partir da classe importada
        self.setupUi(self)

        # --- Inicialização da Lógica da Aplicação ---
        self.output_path = os.path.join(os.getcwd(), OUTPUT_DIR)
        self.ensure_output_path_exists()
        self.path_textbox.setText(self.output_path)

        self.recording_thread = None
        self.transcription_thread = None

        self.whisper_settings = {
            "model": "medium",
            "language": "pt",
            "device": "cpu",
            "compute_type": "int8",
            "vad_filter": True,
            "temperature": 0.0,
            "best_of": 5,
            "beam_size": 5,
            "condition_on_previous_text": True,
            "initial_prompt": "",
            "acceleration_factor": 1.5,
        }

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

    def connect_signals(self):
        """Conecta todos os sinais da UI aos seus respectivos slots."""
        self.browse_button.clicked.connect(self.browse_folder)
        self.start_button.clicked.connect(self.start_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.transcribe_button.clicked.connect(self.start_transcription)
        self.settings_button.clicked.connect(self.open_settings_dialog)

    # --- Métodos de Lógica da Aplicação (Slots) ---
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
        if not self.recording_thread or not self.recording_thread.isRunning():
            self.stop_button.setEnabled(False)
        if full_text:
            save_path = os.path.join(self.output_path, "transcricao_completa.txt")
            try:
                with open(save_path, "w", encoding="utf-8") as f:
                    f.write(full_text)
                    self.update_transcription_status(
                        {
                            "text": (
                                "Transcrição concluída! Resultado salvo em "
                                f"{save_path}"
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

    def populate_devices(self):
        self.device_combo.clear()
        self.devices = sd.query_devices()
        self.input_devices = []
        found_loopback = False
        try:
            default_output = sd.query_devices(kind="output")  # type: ignore[call-arg]
            loopback_device = sd.query_devices(
                default_output["name"], kind="input"  # type: ignore[index]
            )  # type: ignore[call-arg]
            loopback_index = int(loopback_device["index"])  # type: ignore[index]
            self.device_combo.addItem(
                f"Áudio do Sistema ({loopback_device['name']})",  # type: ignore[index]
                loopback_index,
            )
            self.input_devices.append((loopback_index, loopback_device))
            found_loopback = True
            print(
                f"Dispositivo de loopback encontrado: {loopback_device['name']}"  # type: ignore[index]
            )
        except (ValueError, sd.PortAudioError, KeyError) as e:
            print(f"Dispositivo de loopback não encontrado. Erro: {e}")
        for i, device in enumerate(self.devices):
            if device["max_input_channels"] > 0:  # type: ignore[index]
                if not any(i == d[0] for d in self.input_devices):
                    self.device_combo.addItem(f"({i}) {device['name']}", i)  # type: ignore[index]
                    self.input_devices.append((i, device))
        if not found_loopback:
            self.device_combo.addItem("Áudio do Sistema (Não disponível)")
            last_item_index = self.device_combo.count() - 1
            self.device_combo.model().item(last_item_index).setEnabled(False)  # type: ignore[attr-defined]

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
            device_index, channels_to_use, self.output_path, apply_processing
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

    def update_resource_usage(self):
        try:
            cpu_percent = self.process.cpu_percent(interval=None)
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()
            self.cpu_bar.setValue(int(cpu_percent))
            self.mem_bar.setValue(int(mem_percent))
            mem_mb = mem_info.rss / (1024 * 1024)
            self.mem_bar.setFormat(f"{mem_mb:.1f} MB (%p%)")
        except psutil.NoSuchProcess:
            self.cpu_bar.setValue(0)
            self.mem_bar.setValue(0)
        except Exception as e:
            print(f"Erro ao monitorar recursos: {e}")
            self.cpu_bar.setValue(0)
            self.mem_bar.setValue(0)

    def open_settings_dialog(self):
        settings_dialog = FastWhisperSettingsDialog(self.whisper_settings, self)
        if settings_dialog.exec_():
            self.whisper_settings = settings_dialog.get_settings()
            QMessageBox.information(
                self,
                "Configurações Salvas",
                "As configurações do FastWhisper foram salvas com sucesso!",
            )

    def closeEvent(self, a0: QCloseEvent) -> None:  # type: ignore[override]
        if self.recording_thread and self.recording_thread.isRunning():
            self.stop_recording()
            self.recording_thread.wait()
        a0.accept()


# --- Diálogo de Configurações (sem alteração) ---
class FastWhisperSettingsDialog(QDialog):
    # ... (lógica do diálogo de configurações permanece a mesma)
    def __init__(self, current_settings: dict[str, Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurações do FastWhisper")
        self.setFixedSize(600, 650)
        self.settings = current_settings.copy()

        self.main_layout = QVBoxLayout(self)
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        self.main_layout.addWidget(scroll_area)
        scroll_content = QWidget()
        self.form_layout = QFormLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        self.model_combo = QComboBox()
        self.model_combo.addItems(
            ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
        )
        self.model_combo.setCurrentText(self.settings.get("model", "medium"))
        self.form_layout.addRow("Modelo:", self.model_combo)
        self.form_layout.addRow(
            "",
            QLabel(
                (
                    "Modelos maiores são mais precisos, porém mais lentos. "
                    "'large-v3' é o mais preciso."
                )
            ),
        )

        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda"])
        gpu_available = torch is not None and torch.cuda.is_available()
        if not gpu_available:
            self.device_combo.model().item(1).setEnabled(False)  # type: ignore[attr-defined]
        self.device_combo.setCurrentText(self.settings.get("device", "cpu"))
        self.form_layout.addRow("Dispositivo:", self.device_combo)
        self.form_layout.addRow("", QLabel("'cuda' (GPU) é muito mais rápido."))

        self.compute_type_combo = QComboBox()
        if gpu_available:
            self.compute_type_combo.addItems(
                ["int8_float16", "float16", "int8", "float32"]
            )
        else:
            self.compute_type_combo.addItems(["int8", "float32"])
        self.compute_type_combo.setCurrentText(
            self.settings.get("compute_type", "int8")
        )
        self.form_layout.addRow("Tipo de Computação:", self.compute_type_combo)
        self.form_layout.addRow(
            "",
            QLabel(
                (
                    "'int8' é o mais rápido (CPU). "
                    "'int8_float16' é o ideal para GPUs (velocidade/precisão)."
                )
            ),
        )

        self.vad_filter_checkbox = QCheckBox("Usar Filtro VAD (Pular Silêncio)")
        self.vad_filter_checkbox.setChecked(self.settings.get("vad_filter", True))
        self.form_layout.addRow("", self.vad_filter_checkbox)
        self.form_layout.addRow(
            "",
            QLabel(
                (
                    "Detecta e pula partes sem fala no áudio, "
                    "acelerando muito a transcrição."
                )
            ),
        )

        self.language_combo = QComboBox()
        self.language_combo.addItems(["pt", "en", "auto"])
        self.language_combo.setCurrentText(self.settings.get("language", "pt"))
        self.form_layout.addRow("Idioma:", self.language_combo)
        self.form_layout.addRow(
            "", QLabel("Idioma do áudio. 'auto' para detecção automática.")
        )

        self.temperature_slider = QSlider(Qt.Horizontal)  # type: ignore[attr-defined]
        self.temperature_slider.setRange(0, 10)
        self.temperature_slider.setValue(
            int(self.settings.get("temperature", 0.0) * 10)
        )
        self.temperature_label = QLabel(
            f"Temperatura: {self.temperature_slider.value() / 10.0}"
        )
        self.temperature_slider.valueChanged.connect(
            lambda v: self.temperature_label.setText(f"Temperatura: {v / 10.0}")
        )
        self.form_layout.addRow(self.temperature_label, self.temperature_slider)
        self.best_of_slider = QSlider(Qt.Horizontal)  # type: ignore[attr-defined]
        self.best_of_slider.setRange(1, 10)
        self.best_of_slider.setValue(self.settings.get("best_of", 5))
        self.best_of_label = QLabel(f"Best Of: {self.best_of_slider.value()}")
        self.best_of_slider.valueChanged.connect(
            lambda v: self.best_of_label.setText(f"Best Of: {v}")
        )
        self.form_layout.addRow(self.best_of_label, self.best_of_slider)
        self.beam_size_slider = QSlider(Qt.Horizontal)  # type: ignore[attr-defined]
        self.beam_size_slider.setRange(1, 10)
        self.beam_size_slider.setValue(self.settings.get("beam_size", 5))
        self.beam_size_label = QLabel(f"Beam Size: {self.beam_size_slider.value()}")
        self.beam_size_slider.valueChanged.connect(
            lambda v: self.beam_size_label.setText(f"Beam Size: {v}")
        )
        self.form_layout.addRow(self.beam_size_label, self.beam_size_slider)

        self.condition_checkbox = QCheckBox("Condicionar no texto anterior")
        self.condition_checkbox.setChecked(
            self.settings.get("condition_on_previous_text", True)
        )
        self.form_layout.addRow("", self.condition_checkbox)
        self.initial_prompt_edit = QLineEdit(self.settings.get("initial_prompt", ""))
        self.form_layout.addRow("Prompt Inicial:", self.initial_prompt_edit)

        self.acceleration_spinbox = QDoubleSpinBox()
        self.acceleration_spinbox.setRange(1.0, 5.0)
        self.acceleration_spinbox.setSingleStep(0.1)
        self.acceleration_spinbox.setValue(
            self.settings.get("acceleration_factor", 1.5)
        )
        self.form_layout.addRow(
            "Fator de Aceleração (Vídeo):", self.acceleration_spinbox
        )
        self.form_layout.addRow(
            "",
            QLabel("Velocidade do áudio extraído de arquivos de vídeo. 1.0 = normal."),
        )

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.auto_cfg_button = QPushButton("Cfg. Automática")
        self.auto_cfg_button.clicked.connect(self.auto_configure)
        self.button_box.addButton(self.auto_cfg_button, QDialogButtonBox.ActionRole)
        self.main_layout.addWidget(self.button_box)

    def auto_configure(self):
        total_ram_gb = psutil.virtual_memory().total / (1024**3)
        gpu_available = torch and torch.cuda.is_available()

        info_msg = (
            f"RAM Total: {total_ram_gb:.2f} GB\nGPU disponível: "
            f"{'Sim' if gpu_available else 'Não'}\n\n"
            "Ajustando configurações para o melhor equilíbrio "
            "entre desempenho e precisão."
        )
        QMessageBox.information(self, "Análise de Hardware", info_msg)

        self.vad_filter_checkbox.setChecked(True)
        self.condition_checkbox.setChecked(True)
        self.temperature_slider.setValue(0)
        self.initial_prompt_edit.clear()
        self.acceleration_spinbox.setValue(1.5)

        if gpu_available:
            assert torch is not None
            vram_gb = (
                torch.cuda.get_device_properties(0).total_memory / (1024**3)
            )  # type: ignore[call-arg]
            self.device_combo.setCurrentText("cuda")
            self.compute_type_combo.setCurrentText("int8_float16")

            if vram_gb >= 10:
                self.model_combo.setCurrentText("large-v3")
                self.beam_size_slider.setValue(5)
                self.best_of_slider.setValue(5)
                rec_msg = (
                    "GPU potente detectada (>10GB VRAM)! "
                    "Sugerindo 'large-v3' com 'int8_float16'."
                )
            elif vram_gb >= 5:
                self.model_combo.setCurrentText("medium")
                self.beam_size_slider.setValue(5)
                self.best_of_slider.setValue(5)
                rec_msg = (
                    "GPU intermediária detectada (5-10GB VRAM). "
                    "Sugerindo 'medium' com 'int8_float16'."
                )
            else:
                self.model_combo.setCurrentText("small")
                self.beam_size_slider.setValue(2)
                self.best_of_slider.setValue(2)
                rec_msg = (
                    "GPU com pouca VRAM (<5GB). "
                    "Sugerindo 'small' com 'int8_float16' para evitar erros de memória."
                )
            QMessageBox.information(self, "Configuração Automática (GPU)", rec_msg)
        else:  # CPU-only
            self.device_combo.setCurrentText("cpu")
            self.compute_type_combo.setCurrentText("int8")

            if total_ram_gb >= 8:
                self.model_combo.setCurrentText("medium")
                self.beam_size_slider.setValue(5)
                self.best_of_slider.setValue(5)
                rec_msg = (
                    "Hardware potente (CPU). "
                    "Sugerindo modelo 'medium' com 'int8' para melhor precisão."
                )
            elif total_ram_gb >= 4:
                self.model_combo.setCurrentText("small")
                self.beam_size_slider.setValue(3)
                self.best_of_slider.setValue(3)
                rec_msg = (
                    "Hardware intermediário (CPU). Sugerindo 'small' com 'int8'."
                )
            else:
                self.model_combo.setCurrentText("base")
                self.beam_size_slider.setValue(2)
                self.best_of_slider.setValue(2)
                rec_msg = (
                    "Hardware de baixo desempenho (CPU). "
                    "Sugerindo 'base' com 'int8' para garantir execução."
                )
            QMessageBox.information(self, "Configuração Automática (CPU)", rec_msg)

        self.temperature_label.setText(
            f"Temperatura: {self.temperature_slider.value() / 10.0}"
        )
        self.best_of_label.setText(f"Best Of: {self.best_of_slider.value()}")
        self.beam_size_label.setText(f"Beam Size: {self.beam_size_slider.value()}")

    def get_settings(self) -> dict[str, Any]:
        self.settings["model"] = self.model_combo.currentText()
        self.settings["language"] = self.language_combo.currentText()
        self.settings["device"] = self.device_combo.currentText()
        self.settings["compute_type"] = self.compute_type_combo.currentText()
        self.settings["vad_filter"] = self.vad_filter_checkbox.isChecked()
        self.settings["temperature"] = self.temperature_slider.value() / 10.0
        self.settings["best_of"] = self.best_of_slider.value()
        self.settings["beam_size"] = self.beam_size_slider.value()
        self.settings["condition_on_previous_text"] = (
            self.condition_checkbox.isChecked()
        )
        self.settings["initial_prompt"] = self.initial_prompt_edit.text()
        self.settings["acceleration_factor"] = self.acceleration_spinbox.value()
        return self.settings


# --- Ponto de Entrada da Aplicação ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_stylesheet(app)
    main_win = AudioRecorderApp()
    main_win.show()
    sys.exit(app.exec_())
