import sys
import sounddevice as sd
import numpy as np
import soundfile as sf
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QComboBox, QProgressBar, QMessageBox,
                             QLineEdit, QFileDialog, QCheckBox, QTextEdit, QDialog, QFormLayout,
                             QSlider, QDialogButtonBox)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
import datetime
import os
import noisereduce as nr
import whisper
import glob
import time
import psutil

# --- Configurações de Áudio ---
SAMPLE_RATE = 48000  # Qualidade de estúdio (44.1kHz é qualidade de CD)
CHUNK_DURATION_SECONDS = 60 # Duração de cada arquivo de áudio
OUTPUT_DIR = "gravacoes" # Pasta para salvar os arquivos

class RecordingThread(QThread):
    """
    Thread para lidar com a gravação de áudio em segundo plano,
    evitando que a interface gráfica congele.
    """
    # Sinais para comunicar com a thread principal (GUI)
    status_update = pyqtSignal(dict)
    recording_error = pyqtSignal(str)

    def __init__(self, device_index, channels, output_path, apply_processing):
        super().__init__()
        self.device_index = device_index
        self.channels = channels
        self.output_path = output_path
        self.apply_processing = apply_processing # Novo
        self._is_running = False
        self.total_recorded_time = 0

    def run(self):
        """
        Lógica principal da thread de gravação.
        """
        self._is_running = True

        try:
            # Loop principal de gravação
            while self._is_running:
                current_chunk_data = []
                chunk_start_time = self.total_recorded_time
                
                # Gera um nome de arquivo único para este trecho
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(self.output_path, f"gravacao_{timestamp}.wav")

                # Abre o stream de áudio para gravar um trecho de 60s
                with sd.InputStream(samplerate=SAMPLE_RATE, 
                                    device=self.device_index, 
                                    channels=self.channels, 
                                    dtype='float32') as stream:
                    
                    print(f"Iniciando novo trecho. Salvando em: {filename}")
                    
                    # Grava por CHUNK_DURATION_SECONDS
                    for i in range(int(SAMPLE_RATE * CHUNK_DURATION_SECONDS / 1024)): # Loop para atualizar a UI
                        if not self._is_running:
                            break
                        
                        # Pega um bloco de áudio do stream
                        audio_chunk, overflowed = stream.read(1024) # Lê 1024 frames
                        if overflowed:
                            print("Aviso: Overflow de buffer de áudio detectado.")
                        
                        current_chunk_data.append(audio_chunk)
                        
                        # Calcula o volume (RMS) e emite o sinal de atualização
                        volume_level = np.sqrt(np.mean(audio_chunk**2))
                        
                        # Atualiza os tempos
                        time_in_chunk = (len(current_chunk_data) * 1024) / SAMPLE_RATE
                        self.total_recorded_time = chunk_start_time + time_in_chunk
                        
                        self.status_update.emit({
                            "total_time": self.total_recorded_time,
                            "chunk_time_remaining": CHUNK_DURATION_SECONDS - time_in_chunk,
                            "volume": volume_level * 100 # Escala para a barra de progresso
                        })

                    if not self._is_running and len(current_chunk_data) > 0:
                        # Salva o que foi gravado se o usuário parou no meio de um trecho
                        print("Gravação interrompida, salvando trecho parcial.")
                        sf.write(filename, np.concatenate(current_chunk_data), SAMPLE_RATE)
                        break # Sai do loop principal

                # Salva o trecho completo de 60 segundos
                if self._is_running:
                    print(f"Trecho de {CHUNK_DURATION_SECONDS}s completo. Salvando...")
                    full_audio_data = np.concatenate(current_chunk_data)
                    sf.write(filename, full_audio_data, SAMPLE_RATE)

                    # Aplica pós-processamento se a opção estiver marcada
                    if self.apply_processing:
                        self.process_audio(filename, full_audio_data)

        except Exception as e:
            error_message = f"Erro durante a gravação: {e}"
            print(error_message)
            self.recording_error.emit(error_message)

    def process_audio(self, original_filepath, audio_data):
        """
        Aplica redução de ruído e normalização ao arquivo de áudio.
        """
        try:
            print(f"Aplicando pós-processamento em {original_filepath}...")
            
            # --- 1. Redução de Ruído ---
            # Usa os primeiros 0.5 segundos como amostra de ruído
            noise_sample_len = int(0.5 * SAMPLE_RATE)
            noise_clip = audio_data[:noise_sample_len]
            # Realiza a redução de ruído
            reduced_noise_audio = nr.reduce_noise(y=audio_data, sr=SAMPLE_RATE, y_noise=noise_clip, prop_decrease=1.0, stationary=True)

            # --- 2. Normalização de Volume ---
            # Normaliza o áudio para o pico máximo de -1.0 dBFS (evita clipping)
            peak_level = np.max(np.abs(reduced_noise_audio))
            if peak_level > 0:
                # Target de -1 dBFS para evitar clipping digital
                target_peak_dbfs = -1.0
                target_peak_linear = 10**(target_peak_dbfs / 20.0)
                normalization_factor = target_peak_linear / peak_level
                normalized_audio = reduced_noise_audio * normalization_factor
            else:
                normalized_audio = reduced_noise_audio # É silêncio

            # Gera o novo nome do arquivo
            base, ext = os.path.splitext(original_filepath)
            processed_filepath = f"{base}_processed{ext}"

            # Salva o arquivo processado
            sf.write(processed_filepath, normalized_audio, SAMPLE_RATE)
            print(f"Arquivo processado salvo em: {processed_filepath}")

        except Exception as e:
            # Não emite um erro crítico, apenas avisa no console
            print(f"Falha no pós-processamento de {original_filepath}: {e}")

    def stop(self):
        """
        Sinaliza para a thread parar a gravação.
        """
        self._is_running = False
        print("Sinal de parada recebido.")


class AudioRecorderApp(QMainWindow):
    """
    Classe principal da aplicação GUI.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("VoxSynopsis")
        self.setGeometry(100, 100, 450, 300) # Ajusta o tamanho da janela

        # Define o caminho de saída padrão
        self.output_path = os.path.join(os.getcwd(), OUTPUT_DIR)
        self.ensure_output_path_exists()

        self.recording_thread = None
        self.transcription_thread = None # Inicializa a thread de transcrição

        # Configurações do Whisper (valores padrão)
        self.whisper_settings = {
            "model": "medium",
            "language": "pt",
            "temperature": 0.0,
            "best_of": 5,
            "beam_size": 5,
            "condition_on_previous_text": True,
            "initial_prompt": ""
        }

        # Monitoramento de recursos
        self.process = psutil.Process(os.getpid()) # Obtém o processo atual
        self.resource_timer = QTimer(self)
        self.resource_timer.setInterval(1000) # Atualiza a cada 1 segundo
        self.resource_timer.timeout.connect(self.update_resource_usage)
        self.resource_timer.start()

        # Configura a interface gráfica
        self.setup_ui()

    def setup_ui(self):
        """Configura todos os componentes da interface gráfica."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Seção de dispositivos
        device_layout = QHBoxLayout()
        device_layout.addWidget(QLabel("Dispositivo de Entrada:"))
        self.device_combo = QComboBox()
        device_layout.addWidget(self.device_combo)
        main_layout.addLayout(device_layout)
        
        # Seção de caminho de saída
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Pasta de Saída:"))
        self.path_textbox = QLineEdit(self.output_path)
        path_layout.addWidget(self.path_textbox)
        self.browse_button = QPushButton("Procurar")
        self.browse_button.clicked.connect(self.browse_folder)
        path_layout.addWidget(self.browse_button)
        main_layout.addLayout(path_layout)
        
        # Checkbox para processamento
        self.processing_checkbox = QCheckBox("Aplicar pós-processamento (redução de ruído)")
        self.processing_checkbox.setChecked(True)
        main_layout.addWidget(self.processing_checkbox)
        
        # Botões de controle
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

        self.settings_button = QPushButton("Configurações")
        self.settings_button.clicked.connect(self.open_settings_dialog)
        button_layout.addWidget(self.transcribe_button)
        
        main_layout.addLayout(button_layout)
        
        # Status e informações
        self.status_label = QLabel("Status: Parado")
        main_layout.addWidget(self.status_label)
        
        self.total_time_label = QLabel("Tempo Total Gravado: 00:00:00")
        main_layout.addWidget(self.total_time_label)
        
        self.chunk_time_label = QLabel("Tempo Restante no Trecho: 60.0s")
        main_layout.addWidget(self.chunk_time_label)
        
        # Barra de volume
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        volume_layout.addWidget(self.volume_bar)
        main_layout.addLayout(volume_layout)
        
        # Monitoramento de recursos
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
        
        # Status da transcrição
        self.transcription_status_label = QLabel("Status da Transcrição: --")
        main_layout.addWidget(self.transcription_status_label)
        
        self.last_file_time_label = QLabel("Tempo do Último Arquivo: --")
        main_layout.addWidget(self.last_file_time_label)
        
        self.total_transcription_time_label = QLabel("Tempo Total de Transcrição: --")
        main_layout.addWidget(self.total_transcription_time_label)
        
        # Área de transcrição
        self.transcription_area = QTextEdit()
        self.transcription_area.setMaximumHeight(150)
        main_layout.addWidget(self.transcription_area)
        
        # Popula os dispositivos de áudio
        self.populate_devices()

    def ensure_output_path_exists(self):
        """Garante que a pasta de saída exista."""
        try:
            os.makedirs(self.output_path, exist_ok=True)
        except OSError as e:
            QMessageBox.critical(self, "Erro de Diretório", f"Não foi possível criar a pasta:\n{self.output_path}\n\n{e}")

    def browse_folder(self):
        """Abre o seletor de pastas e atualiza o caminho."""
        directory = QFileDialog.getExistingDirectory(self, "Selecionar Pasta", self.output_path)
        if directory: # Se o usuário selecionou uma pasta
            self.output_path = directory
            self.path_textbox.setText(self.output_path)
            self.ensure_output_path_exists()

    def start_transcription(self):
        """Inicia a thread de transcrição."""
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
        """Atualiza os labels de status da transcrição."""
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
        """Adiciona texto à área de transcrição."""
        self.transcription_area.append(text)

    def on_transcription_finished(self, full_text):
        """Chamado quando a transcrição termina."""
        # self.transcription_area.setText(full_text) # Opcional: substituir em vez de apendar
        self.transcribe_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        if not self.recording_thread or not self.recording_thread.isRunning():
            self.stop_button.setEnabled(False)

        # Salva o resultado compilado em um arquivo .txt
        if full_text:
            save_path = os.path.join(self.output_path, "transcricao_completa.txt")
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(full_text)
                self.update_transcription_status({"text": f"Transcrição concluída! Resultado salvo em {save_path}", "last_time": 0, "total_time": 0})
            except Exception as e:
                self.update_transcription_status({"text": f"Erro ao salvar arquivo de transcrição: {e}", "last_time": 0, "total_time": 0})

    def populate_devices(self):
        """
        Preenche o ComboBox com os dispositivos de entrada de áudio disponíveis.
        """
        self.devices = sd.query_devices()
        self.input_devices = [(i, d) for i, d in enumerate(self.devices) if d['max_input_channels'] > 0]
        
        for i, device in self.input_devices:
            self.device_combo.addItem(f"({i}) {device['name']}", i)
        
        # Adiciona opção para gravar microfone + som do sistema (requer configuração manual)
        # Esta é uma funcionalidade avançada. Por simplicidade, este código não
        # implementa a mixagem de múltiplos streams. O usuário deve selecionar
        # um dispositivo agregado como "Stereo Mix" ou "BlackHole".
        self.device_combo.addItem("Microfone + Som do Sistema (Requer Dispositivo Agregado)")


    def start_recording(self):
        """
        Inicia a thread de gravação.
        """
        selected_text = self.device_combo.currentText()
        if "Microfone + Som" in selected_text:
            QMessageBox.information(self, "Aviso", 
                                      "Para gravar áudio do microfone e do sistema simultaneamente, "
                                      "você deve selecionar um dispositivo de áudio agregado (como 'Stereo Mix' no Windows "
                                      "ou 'BlackHole' no macOS) que já faça essa mixagem.")
            return

        device_index = self.device_combo.currentData()
        channels = self.devices[device_index]['max_input_channels']
        
        # Usa o máximo de canais, mas limita a 2 (estéreo) para compatibilidade
        channels_to_use = min(channels, 2)

        # Passa o caminho de saída e o estado do processamento para a thread
        apply_processing = self.processing_checkbox.isChecked()
        self.recording_thread = RecordingThread(device_index, channels_to_use, self.output_path, apply_processing)
        self.recording_thread.status_update.connect(self.update_status)
        self.recording_thread.recording_error.connect(self.show_error_message)
        self.recording_thread.finished.connect(self.on_recording_finished)
        
        self.recording_thread.start()

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.device_combo.setEnabled(False)
        self.browse_button.setEnabled(False) # Desabilita o botão de procurar
        self.processing_checkbox.setEnabled(False) # Desabilita a checkbox
        self.status_label.setText("Status: Gravando...")

    def stop_recording(self):
        """
        Para a thread de gravação.
        """
        if self.recording_thread:
            self.recording_thread.stop()
            self.status_label.setText("Status: Parando...")
            self.stop_button.setEnabled(False) # Desabilita para evitar cliques duplos

    def on_recording_finished(self):
        """
        Chamado quando a thread termina.
        """
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.device_combo.setEnabled(True)
        self.browse_button.setEnabled(True) # Reabilita o botão de procurar
        self.processing_checkbox.setEnabled(True) # Reabilita a checkbox
        self.status_label.setText("Status: Parado")
        self.volume_bar.setValue(0)
        QMessageBox.information(self, "Gravação Finalizada", "A gravação foi interrompida.")


    def update_status(self, status_dict):
        """
        Atualiza a interface com os dados recebidos da thread.
        """
        # Atualiza tempo total
        total_seconds = int(status_dict["total_time"])
        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60
        self.total_time_label.setText(f"Tempo Total Gravado: {h:02d}:{m:02d}:{s:02d}")

        # Atualiza tempo restante no trecho
        remaining = max(0, status_dict["chunk_time_remaining"])
        self.chunk_time_label.setText(f"Tempo Restante no Trecho: {remaining:.1f}s")

        # Atualiza barra de volume
        self.volume_bar.setValue(int(status_dict["volume"]))

    def show_error_message(self, message):
        """
        Exibe uma caixa de diálogo de erro.
        """
        self.stop_recording() # Para tudo em caso de erro
        QMessageBox.critical(self, "Erro de Gravação", message)

    def update_resource_usage(self):
        """
        Atualiza os labels de uso de CPU e memória.
        """
        try:
            cpu_percent = self.process.cpu_percent(interval=None) # Non-blocking
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent() # Uso de memória em porcentagem

            self.cpu_bar.setValue(int(cpu_percent))
            self.mem_bar.setValue(int(mem_percent))

            # Opcional: exibir o valor em MB no formato da barra de progresso
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
        Abre a caixa de diálogo de configurações do VoxSynopsis.
        """
        settings_dialog = SettingsDialog(self.whisper_settings, self)
        if settings_dialog.exec_(): # Se o usuário clicou em OK
            self.whisper_settings = settings_dialog.get_settings()
            QMessageBox.information(self, "Configurações Salvas", "As configurações do VoxSynopsis foram salvas com sucesso!")

    def closeEvent(self, event):
        """
        Garante que a thread de gravação seja finalizada ao fechar a janela.
        """
        if self.recording_thread and self.recording_thread.isRunning():
            self.stop_recording()
            self.recording_thread.wait() # Espera a thread terminar
        event.accept()


class SettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações do VoxSynopsis")
        self.setGeometry(200, 200, 600, 500)
        self.settings = current_settings.copy() # Trabalha com uma cópia

        self.layout = QVBoxLayout(self)

        # Formulário de configurações
        self.form_layout = QFormLayout()

        # Modelo
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium"])
        self.model_combo.setCurrentText(self.settings.get("model", "medium"))
        self.form_layout.addRow("Modelo:", self.model_combo)
        self.form_layout.addRow("", QLabel("""Escolha o tamanho do modelo. Modelos maiores (como 'large') são mais precisos, mas exigem significativamente mais CPU e RAM, resultando em transcrições mais lentas. Modelos menores (como 'tiny', 'base', 'small') são mais rápidos, mas menos precisos. 'medium' oferece um bom equilíbrio entre precisão e desempenho para a maioria das CPUs."""))

        # Idioma
        self.language_combo = QComboBox()
        self.language_combo.addItems(["pt", "en", "auto"])
        self.language_combo.setCurrentText(self.settings.get("language", "pt"))
        self.form_layout.addRow("Idioma:", self.language_combo)
        self.form_layout.addRow("", QLabel("\nIdioma do áudio. 'auto' tenta detectar automaticamente.\n"))

        # Temperatura
        self.temperature_slider = QSlider(Qt.Horizontal)
        self.temperature_slider.setRange(0, 10) # 0.0 a 1.0 com passo de 0.1
        self.temperature_slider.setSingleStep(1)
        self.temperature_slider.setValue(int(self.settings.get("temperature", 0.0) * 10))
        self.temperature_label = QLabel(f"Temperatura: {self.temperature_slider.value() / 10.0}")
        self.temperature_slider.valueChanged.connect(lambda v: self.temperature_label.setText(f"Temperatura: {v / 10.0}"))
        self.form_layout.addRow(self.temperature_label, self.temperature_slider)
        self.form_layout.addRow("", QLabel("\nControla a 'criatividade' da transcrição. 0.0 é mais determinístico (menos erros, mas menos flexível), 1.0 é mais 'criativo'.\n"))

        # Best Of
        self.best_of_slider = QSlider(Qt.Horizontal)
        self.best_of_slider.setRange(1, 10)
        self.best_of_slider.setSingleStep(1)
        self.best_of_slider.setValue(self.settings.get("best_of", 5))
        self.best_of_label = QLabel(f"Best Of: {self.best_of_slider.value()}")
        self.best_of_slider.valueChanged.connect(lambda v: self.best_of_label.setText(f"Best Of: {v}"))
        self.form_layout.addRow(self.best_of_label, self.best_of_slider)
        self.form_layout.addRow("", QLabel("\nNúmero de candidatos a considerar. Valores maiores podem aumentar a precisão, mas também o tempo de processamento.\n"))

        # Beam Size
        self.beam_size_slider = QSlider(Qt.Horizontal)
        self.beam_size_slider.setRange(1, 10)
        self.beam_size_slider.setSingleStep(1)
        self.beam_size_slider.setValue(self.settings.get("beam_size", 5))
        self.beam_size_label = QLabel(f"Beam Size: {self.beam_size_slider.value()}")
        self.beam_size_slider.valueChanged.connect(lambda v: self.beam_size_label.setText(f"Beam Size: {v}"))
        self.form_layout.addRow(self.beam_size_label, self.beam_size_slider)
        self.form_layout.addRow("", QLabel("\nNúmero de 'caminhos' de transcrição a explorar simultaneamente. Valores maiores podem melhorar a precisão, mas aumentam o uso de CPU e RAM.\n"))

        # Condition on Previous Text
        self.condition_checkbox = QCheckBox("Condicionar no texto anterior")
        self.condition_checkbox.setChecked(self.settings.get("condition_on_previous_text", True))
        self.form_layout.addRow("", self.condition_checkbox)
        self.form_layout.addRow("", QLabel("\nSe marcado, o Whisper usará o texto da transcrição anterior para ajudar na coerência do texto atual. Recomendado para áudios longos.\n"))

        # Initial Prompt
        self.initial_prompt_edit = QLineEdit(self.settings.get("initial_prompt", ""))
        self.form_layout.addRow("Prompt Inicial:", self.initial_prompt_edit)
        self.form_layout.addRow("", QLabel("\nUm texto que pode ser usado para guiar o modelo no início da transcrição (ex: 'O áudio é sobre reunião de negócios.').\n"))

        self.layout.addLayout(self.form_layout)

        # Botões de controle
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        self.auto_cfg_button = QPushButton("Cfg. Automática")
        self.auto_cfg_button.clicked.connect(self.auto_configure)
        self.button_box.addButton(self.auto_cfg_button, QDialogButtonBox.ActionRole)

        self.layout.addWidget(self.button_box)

    def auto_configure(self):
        """
        Analisa as configurações da máquina e ajusta as configurações do Whisper
        para o máximo de desempenho/qualidade de acordo com as heurísticas.
        """
        cpu_count = psutil.cpu_count(logical=True)
        total_ram_gb = psutil.virtual_memory().total / (1024**3) # RAM em GB

        QMessageBox.information(self, "Análise de Hardware", 
                                  f"CPU Cores (lógicos): {cpu_count}\nRAM Total: {total_ram_gb:.2f} GB\n\n" \
                                  "Ajustando configurações do Whisper com base nesta análise.")

        # Heurísticas para configuração automática
        if total_ram_gb < 4 or cpu_count < 2: # Máquinas mais fracas
            self.model_combo.setCurrentText("small")
            self.temperature_slider.setValue(0) # 0.0
            self.best_of_slider.setValue(1)
            self.beam_size_slider.setValue(1)
            self.condition_checkbox.setChecked(False)
            self.initial_prompt_edit.clear()
            QMessageBox.information(self, "Configuração Automática", "Detectado hardware de baixo desempenho. Sugerindo modelo 'small' e configurações mais rápidas.")
        elif total_ram_gb < 8 or cpu_count < 4: # Máquinas intermediárias
            self.model_combo.setCurrentText("medium")
            self.temperature_slider.setValue(0) # 0.0
            self.best_of_slider.setValue(3)
            self.beam_size_slider.setValue(3)
            self.condition_checkbox.setChecked(True)
            self.initial_prompt_edit.clear()
            QMessageBox.information(self, "Configuração Automática", "Detectado hardware intermediário. Sugerindo modelo 'medium' e configurações balanceadas.")
        else: # Máquinas mais potentes
            self.model_combo.setCurrentText("medium") # 'large' é muito pesado para CPU na maioria dos casos
            self.temperature_slider.setValue(0) # 0.0
            self.best_of_slider.setValue(5)
            self.beam_size_slider.setValue(5)
            self.condition_checkbox.setChecked(True)
            self.initial_prompt_edit.clear()
            QMessageBox.information(self, "Configuração Automática", "Detectado hardware potente. Sugerindo modelo 'medium' e configurações padrão para alta precisão.")

        # Atualiza o label da temperatura e outros sliders
        self.temperature_label.setText(f"Temperatura: {self.temperature_slider.value() / 10.0}")
        self.best_of_label.setText(f"Best Of: {self.best_of_slider.value()}")
        self.beam_size_label.setText(f"Beam Size: {self.beam_size_slider.value()}")

    def get_settings(self):
        """
        Retorna as configurações atuais da caixa de diálogo.
        """
        self.settings["model"] = self.model_combo.currentText()
        self.settings["language"] = self.language_combo.currentText()
        self.settings["temperature"] = self.temperature_slider.value() / 10.0
        self.settings["best_of"] = self.best_of_slider.value()
        self.settings["beam_size"] = self.beam_size_slider.value()
        self.settings["condition_on_previous_text"] = self.condition_checkbox.isChecked()
        self.settings["initial_prompt"] = self.initial_prompt_edit.text()
        return self.settings


class TranscriptionThread(QThread):
    """
    Thread para lidar com a transcrição de áudio em segundo plano.
    """
    update_status = pyqtSignal(dict) # Alterado para dict
    update_transcription = pyqtSignal(str)
    transcription_finished = pyqtSignal(str)

    def __init__(self, audio_folder, whisper_settings):
        super().__init__()
        self.audio_folder = audio_folder
        self.whisper_settings = whisper_settings
        self._is_running = True

    def run(self):
        try:
            self.update_status.emit({"text": f"Carregando modelo Whisper ({self.whisper_settings['model']})... Isso pode levar um tempo.", "last_time": 0, "total_time": 0})
            model = whisper.load_model(self.whisper_settings["model"])
            self.update_status.emit({"text": "Modelo carregado. Procurando arquivos...", "last_time": 0, "total_time": 0})

            # Procura por arquivos .wav, dando preferência aos processados
            processed_files = sorted(glob.glob(os.path.join(self.audio_folder, "*_processed.wav")))
            original_files = sorted(glob.glob(os.path.join(self.audio_folder, "*.wav")))
            
            # Cria uma lista de arquivos a transcrever, evitando duplicatas
            files_to_transcribe = []
            processed_originals = {f.replace("_processed.wav", ".wav") for f in processed_files}
            files_to_transcribe.extend(processed_files)
            files_to_transcribe.extend([f for f in original_files if f not in processed_originals and not f.endswith("_processed.wav")])

            if not files_to_transcribe:
                self.update_status.emit({"text": "Nenhum arquivo .wav encontrado na pasta.", "last_time": 0, "total_time": 0})
                self.transcription_finished.emit("")
                return

            full_transcription = []
            total_files = len(files_to_transcribe)
            total_processing_time = 0

            for i, filepath in enumerate(files_to_transcribe):
                if not self._is_running:
                    self.update_status.emit({"text": "Transcrição cancelada.", "last_time": 0, "total_time": total_processing_time})
                    break
                
                status_text = f"Transcrevendo arquivo {i+1} de {total_files}: {os.path.basename(filepath)}"
                self.update_status.emit({"text": status_text, "last_time": 0, "total_time": total_processing_time})
                
                # Cronometra a transcrição
                start_time = time.time()
                result = model.transcribe(filepath, **self.whisper_settings, fp16=False) # fp16=False para CPU
                end_time = time.time()

                last_file_time = end_time - start_time
                total_processing_time += last_file_time
                
                # Emite o status com os tempos atualizados
                self.update_status.emit({"text": status_text, "last_time": last_file_time, "total_time": total_processing_time})

                transcription_text = result["text"]
                self.update_transcription.emit(f"--- {os.path.basename(filepath)} ---\n{transcription_text}\n\n")
                full_transcription.append(transcription_text)

            final_text = "\n".join(full_transcription)
            self.transcription_finished.emit(final_text)
            self.update_status.emit({"text": "Transcrição concluída!", "last_time": 0, "total_time": total_processing_time})

        except Exception as e:
            self.update_status.emit({"text": f"Erro durante a transcrição: {e}", "last_time": 0, "total_time": 0})
            self.transcription_finished.emit("") # Emite sinal vazio em caso de erro

    def stop(self):
        self._is_running = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_win = AudioRecorderApp()
    main_win.show()
    sys.exit(app.exec_())
