from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class Ui_MainWindow(object):
    def setupUi(self, MainWindow: QMainWindow) -> None:
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("VoxSynopsis (FastWhisper)")
        MainWindow.setGeometry(100, 100, 600, 750)

        self.central_widget = QWidget(MainWindow)
        MainWindow.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # --- Grupo de Configurações ---
        config_group = QGroupBox("Configurações de Gravação")
        config_layout = QFormLayout()

        self.device_combo = QComboBox()
        config_layout.addRow("Dispositivo de Entrada:", self.device_combo)

        path_layout = QHBoxLayout()
        self.path_textbox = QLineEdit()
        self.browse_button = QPushButton("Procurar")
        path_layout.addWidget(self.path_textbox)
        path_layout.addWidget(self.browse_button)
        config_layout.addRow("Pasta de Saída:", path_layout)

        self.processing_checkbox = QCheckBox(
            "Aplicar pós-processamento (redução de ruído)"
        )
        self.processing_checkbox.setChecked(True)
        config_layout.addRow(self.processing_checkbox)

        config_group.setLayout(config_layout)
        self.main_layout.addWidget(config_group)

        # --- Grupo de Controles ---
        controls_group = QGroupBox("Controles")
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar Gravação")
        self.stop_button = QPushButton("Parar Gravação")
        self.stop_button.setEnabled(False)
        self.transcribe_button = QPushButton("Transcrever Áudios")
        self.settings_button = QPushButton("Cfg. FastWhisper")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.transcribe_button)
        button_layout.addWidget(self.settings_button)
        controls_group.setLayout(button_layout)
        self.main_layout.addWidget(controls_group)

        # --- Grupo de Status da Gravação ---
        status_group = QGroupBox("Status da Gravação")
        status_layout = QFormLayout()
        self.status_label = QLabel("Parado")
        status_layout.addRow("Status:", self.status_label)
        self.total_time_label = QLabel("00:00:00")
        status_layout.addRow("Tempo Total Gravado:", self.total_time_label)
        self.chunk_time_label = QLabel("60.0s")  # Valor inicial
        status_layout.addRow("Tempo Restante no Trecho:", self.chunk_time_label)
        self.volume_bar = QProgressBar()
        self.volume_bar.setRange(0, 100)
        self.volume_bar.setTextVisible(False)
        status_layout.addRow("Volume:", self.volume_bar)
        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group)

        # --- Grupo de Monitor de Recursos ---
        resource_group = QGroupBox("Monitor de Recursos")
        resource_layout = QHBoxLayout()
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setRange(0, 100)
        self.cpu_bar.setFormat("CPU %p%")
        self.mem_bar = QProgressBar()
        self.mem_bar.setRange(0, 100)
        self.mem_bar.setFormat("Memória %p%")
        resource_layout.addWidget(QLabel("CPU:"))
        resource_layout.addWidget(self.cpu_bar)
        resource_layout.addWidget(QLabel("Memória:"))
        resource_layout.addWidget(self.mem_bar)
        resource_group.setLayout(resource_layout)
        self.main_layout.addWidget(resource_group)

        # --- Grupo de Transcrição ---
        transcription_group = QGroupBox("Transcrição")
        transcription_layout = QVBoxLayout()
        self.transcription_status_label = QLabel("Aguardando...")
        self.last_file_time_label = QLabel("Tempo do Último Arquivo: --")
        self.total_transcription_time_label = QLabel("Tempo Total de Transcrição: --")
        self.transcription_area = QTextEdit()
        self.transcription_area.setReadOnly(True)
        transcription_layout.addWidget(self.transcription_status_label)
        transcription_layout.addWidget(self.last_file_time_label)
        transcription_layout.addWidget(self.total_transcription_time_label)
        transcription_layout.addWidget(self.transcription_area)
        transcription_group.setLayout(transcription_layout)
        self.main_layout.addWidget(transcription_group)
