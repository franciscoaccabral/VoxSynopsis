"""FastWhisper settings dialog."""

from typing import Any

import psutil
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFrame,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QFormLayout,
)

try:
    import torch
except ImportError:
    torch = None


class FastWhisperSettingsDialog(QDialog):
    def __init__(
        self, current_settings: dict[str, Any], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configurações do FastWhisper")
        self.settings = current_settings.copy()

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Scroll Area para o conteúdo
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)  # Remove a borda
        self.main_layout.addWidget(scroll_area)

        # Container para o formulário
        form_container = QWidget()
        self.form_layout = QFormLayout(form_container)
        self.form_layout.setContentsMargins(10, 10, 10, 10)
        self.form_layout.setSpacing(15)
        scroll_area.setWidget(form_container)

        def create_wrapping_label(text: str) -> QLabel:
            label = QLabel(text)
            label.setWordWrap(True)
            return label

        # --- Controles do Formulário ---
        self.model_combo = QComboBox()
        self.model_combo.addItems(
            ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
        )
        self.model_combo.setCurrentText(self.settings.get("model_size", "medium"))
        self.form_layout.addRow("Modelo:", self.model_combo)
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Modelos maiores são mais precisos, porém mais lentos. "
                "'large-v3' é o mais preciso."
            ),
        )

        self.device_combo = QComboBox()
        self.device_combo.addItems(["cpu", "cuda"])
        gpu_available = torch is not None and torch.cuda.is_available()
        if not gpu_available:
            self.device_combo.model().item(1).setEnabled(False)
        self.device_combo.setCurrentText(self.settings.get("device", "cpu"))
        self.form_layout.addRow("Dispositivo:", self.device_combo)
        self.form_layout.addRow(
            "", create_wrapping_label("'cuda' (GPU) é muito mais rápido.")
        )

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
            create_wrapping_label(
                "'int8' é o mais rápido (CPU). "
                "'int8_float16' é o ideal para GPUs (velocidade/precisão)."
            ),
        )

        self.cpu_threads_spinbox = QSpinBox()
        cpu_physical_cores = psutil.cpu_count(logical=False) or 1
        cpu_logical_cores = psutil.cpu_count(logical=True) or 1
        self.cpu_threads_spinbox.setRange(1, cpu_logical_cores)
        self.cpu_threads_spinbox.setValue(
            self.settings.get("cpu_threads", cpu_physical_cores)
        )
        self.form_layout.addRow("Threads (CPU):", self.cpu_threads_spinbox)
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                f"Número de threads para usar na transcrição via CPU. "
                f"Recomendado: {cpu_physical_cores} (núcleos físicos). "
                f"Máximo: {cpu_logical_cores}."
            ),
        )

        self.vad_filter_checkbox = QCheckBox("Usar Filtro VAD (Pular Silêncio)")
        self.vad_filter_checkbox.setChecked(self.settings.get("vad_filter", True))
        self.form_layout.addRow("", self.vad_filter_checkbox)
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Detecta e pula partes sem fala no áudio, "
                "acelerando muito a transcrição."
            ),
        )

        self.language_combo = QComboBox()
        self.language_combo.addItems(["pt", "en", "auto"])
        self.language_combo.setCurrentText(self.settings.get("language", "pt"))
        self.form_layout.addRow("Idioma:", self.language_combo)
        self.form_layout.addRow(
            "",
            create_wrapping_label("Idioma do áudio. 'auto' para detecção automática."),
        )

        self.temperature_slider = QSlider(Qt.Horizontal)
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
        self.best_of_slider = QSlider(Qt.Horizontal)
        self.best_of_slider.setRange(1, 10)
        self.best_of_slider.setValue(self.settings.get("best_of", 5))
        self.best_of_label = QLabel(f"Best Of: {self.best_of_slider.value()}")
        self.best_of_slider.valueChanged.connect(
            lambda v: self.best_of_label.setText(f"Best Of: {v}")
        )
        self.form_layout.addRow(self.best_of_label, self.best_of_slider)
        self.beam_size_slider = QSlider(Qt.Horizontal)
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
            self.settings.get("acceleration_factor", 1.25)
        )
        self.form_layout.addRow(
            "Fator de Aceleração (Vídeo):", self.acceleration_spinbox
        )
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Velocidade do áudio extraído de arquivos de vídeo. 1.0 = normal."
            ),
        )

        self.chunk_duration_spinbox = QSpinBox()
        self.chunk_duration_spinbox.setRange(10, 300)  # Min 10s, Max 300s (5 min)
        self.chunk_duration_spinbox.setSingleStep(10)
        self.chunk_duration_spinbox.setValue(
            self.settings.get("chunk_duration_seconds", 60)
        )
        self.form_layout.addRow(
            "Duração do Trecho (segundos):", self.chunk_duration_spinbox
        )
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Tempo em segundos para quebrar arquivos de áudio/gravações "
                "(divisão simples baseada em tempo)."
            ),
        )

        # --- Configurações de Smart Chunking ---
        self.form_layout.addRow(QLabel("--- Divisão Inteligente por Silêncio ---"))

        self.enable_smart_chunking_checkbox = QCheckBox(
            "Habilitar Divisão Inteligente por Silêncio"
        )
        self.enable_smart_chunking_checkbox.setChecked(
            self.settings.get("enable_smart_chunking", False)
        )
        self.form_layout.addRow("", self.enable_smart_chunking_checkbox)
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Quebra o áudio em momentos de silêncio, tentando preservar "
                "palavras. Se habilitado, as configurações abaixo serão usadas. "
                "Caso contrário, a 'Duração do Trecho (segundos)' acima será "
                "usada para uma divisão simples."
            ),
        )

        self.smart_chunk_duration_spinbox = QSpinBox()
        self.smart_chunk_duration_spinbox.setRange(10, 600)  # Max 10 minutos
        self.smart_chunk_duration_spinbox.setSingleStep(10)
        self.smart_chunk_duration_spinbox.setValue(
            self.settings.get("smart_chunk_duration_seconds", 60)
        )
        self.form_layout.addRow(
            "Duração Máx. do Trecho Inteligente (s):",
            self.smart_chunk_duration_spinbox,
        )
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Duração máxima de um trecho ao usar a divisão inteligente. "
                "Segmentos de fala mais longos que isso serão divididos."
            ),
        )

        self.silence_threshold_spinbox = QSpinBox()
        self.silence_threshold_spinbox.setRange(-70, -20)  # dBFS
        self.silence_threshold_spinbox.setSingleStep(1)
        self.silence_threshold_spinbox.setValue(
            self.settings.get("silence_threshold_dbfs", -40)
        )
        self.form_layout.addRow(
            "Limiar de Silêncio (dBFS):", self.silence_threshold_spinbox
        )
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Nível de áudio abaixo do qual é considerado silêncio. "
                "Valores mais baixos (e.g. -50) detectam silêncios mais sutis."
            ),
        )

        self.min_silence_len_spinbox = QSpinBox()
        self.min_silence_len_spinbox.setRange(100, 5000)  # ms
        self.min_silence_len_spinbox.setSingleStep(50)
        self.min_silence_len_spinbox.setValue(
            self.settings.get("min_silence_duration_ms", 500)
        )
        self.form_layout.addRow(
            "Duração Mínima do Silêncio (ms):", self.min_silence_len_spinbox
        )
        self.form_layout.addRow(
            "",
            create_wrapping_label(
                "Duração mínima de um período de silêncio para que o áudio "
                "seja dividido nesse ponto."
            ),
        )

        # --- Botões ---
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.auto_cfg_button = QPushButton("Cfg. Automática")
        self.auto_cfg_button.clicked.connect(self.auto_configure)
        self.button_box.addButton(self.auto_cfg_button, QDialogButtonBox.ActionRole)
        self.main_layout.addWidget(self.button_box)

        # Define um tamanho inicial razoável
        self.resize(600, 400)

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
        self.acceleration_spinbox.setValue(1.25)

        if gpu_available:
            assert torch is not None
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
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
                rec_msg = "Hardware intermediário (CPU). Sugerindo 'small' com 'int8'."
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
        self.settings["model_size"] = self.model_combo.currentText()
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
        # Original chunk duration
        self.settings["chunk_duration_seconds"] = self.chunk_duration_spinbox.value()

        # Get new smart chunking settings
        self.settings["enable_smart_chunking"] = (
            self.enable_smart_chunking_checkbox.isChecked()
        )
        self.settings["smart_chunk_duration_seconds"] = (
            self.smart_chunk_duration_spinbox.value()
        )
        self.settings["silence_threshold_dbfs"] = self.silence_threshold_spinbox.value()
        self.settings["min_silence_duration_ms"] = self.min_silence_len_spinbox.value()
        self.settings["cpu_threads"] = self.cpu_threads_spinbox.value()
        return self.settings