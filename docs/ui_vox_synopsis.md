# Documentação de `ui_vox_synopsis.py`

**Explicação Geral:**

Este módulo define a estrutura básica da interface gráfica do VoxSynopsis. Ele é um arquivo gerado automaticamente a partir do Qt Designer (formato `.ui`) e serve como o esqueleto da UI. Normalmente não é editado manualmente; alterações visuais devem ser feitas no Qt Designer e o `.py` deve ser regenerado.

**Principais Widgets e Funções:**

- **Grupo de Configurações de Gravação**
  - `device_combo` (`QComboBox`): lista de dispositivos de entrada de áudio disponíveis.
  - `path_textbox` (`QLineEdit`) e `browse_button` (`QPushButton`): permitem escolher a pasta onde as gravações serão salvas.
  - `processing_checkbox` (`QCheckBox`): habilita ou desabilita o pós-processamento (redução de ruído).
- **Grupo de Controles**
  - `start_button` e `stop_button` (`QPushButton`): iniciam e param a gravação.
  - `transcribe_button` (`QPushButton`): inicia a transcrição dos áudios gravados.
  - `settings_button` (`QPushButton`): abre a janela de configurações do FastWhisper.
- **Grupo de Status da Gravação**
  - Labels (`status_label`, `total_time_label`, `chunk_time_label`) exibem o estado atual e os tempos de gravação.
  - `volume_bar` (`QProgressBar`): mostra o nível de volume do microfone em tempo real.
- **Grupo de Monitor de Recursos**
  - `cpu_bar` e `mem_bar` (`QProgressBar`): indicam o uso de CPU e memória da máquina.
- **Grupo de Transcrição**
  - Labels (`transcription_status_label`, `last_file_time_label`, `total_transcription_time_label`) informam o andamento da transcrição.
  - `transcription_area` (`QTextEdit`): exibe o texto resultante da transcrição.

Por ser um arquivo auto-gerado, todas as ligações de sinais e a lógica de funcionamento estão em `vox_synopsis_fast_whisper.py`. O `ui_vox_synopsis.py` apenas constrói os widgets e organiza os layouts que compõem a janela principal.
