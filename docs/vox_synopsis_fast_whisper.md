# Documentação de `vox_synopsis_fast_whisper.py`

**Explicação Geral:**

Este é o script principal da aplicação VoxSynopsis. Ele gerencia a interface gráfica do usuário (GUI) construída com PyQt5, lida com a gravação de áudio em tempo real, realiza a transcrição de áudio utilizando o modelo Fast Whisper e permite o gerenciamento das gravações e configurações da transcrição. O script também inclui funcionalidades para pós-processamento de áudio (redução de ruído e normalização) e extração de áudio de arquivos de vídeo para transcrição.

**Classes Principais:**

1.  **`RecordingThread(QThread)`**:
    *   **Propósito e Caso de Uso**: Esta thread é fundamental para permitir que a gravação de áudio ocorra em segundo plano sem bloquear a interface do usuário. Ela lida com a captura contínua de áudio, segmentando-o em arquivos menores para gerenciamento e processamento facilitados. O pós-processamento opcional (redução de ruído, normalização) visa melhorar a qualidade do áudio para transcrição ou arquivamento.
    *   **Descrição**: Thread responsável por gravar áudio do dispositivo de entrada selecionado em blocos (chunks) de duração definida. Salva cada bloco como um arquivo WAV. Opcionalmente, aplica pós-processamento ao áudio gravado.
    *   **Sinais Emitidos**:
        *   `status_update (dict)`: Emite um dicionário com o tempo total gravado, tempo restante no chunk atual e nível de volume.
        *   `recording_error (str)`: Emite uma mensagem de erro caso ocorra um problema durante a gravação.
    *   **Métodos Principais**:
        *   `__init__(self, device_index: int, channels: int, output_path: str, apply_processing: bool)`:
            *   `device_index`: Índice do dispositivo de áudio a ser usado.
            *   `channels`: Número de canais de áudio.
            *   `output_path`: Caminho para salvar os arquivos de áudio gravados.
            *   `apply_processing`: Booleano indicando se o pós-processamento deve ser aplicado.
        *   `run(self)`: Loop principal da thread. Captura áudio em chunks, salva em arquivos WAV e emite atualizações de status. Chama `process_audio` se `apply_processing` for `True`.
        *   `process_audio(self, original_filepath: str, audio_data: np.ndarray)`:
            *   `original_filepath`: Caminho do arquivo WAV original.
            *   `audio_data`: Array NumPy com os dados do áudio.
            *   **Efeitos**: Aplica redução de ruído e normalização ao `audio_data`. Salva o áudio processado com o sufixo `_processed.wav`.
            *   **Retorno**: Nenhum.
        *   `stop(self)`: Sinaliza para a thread parar a gravação.
            *   **Retorno**: Nenhum.

2.  **`TranscriptionThread(QThread)`**:
    *   **Propósito e Caso de Uso**: Similar à `RecordingThread`, esta thread executa a tarefa computacionalmente intensiva de transcrição de áudio em segundo plano, prevenindo o congelamento da UI. Ela automatiza o processo de encontrar arquivos de áudio, prepará-los (extração de áudio de MP4, aceleração) e alimentá-los ao modelo Fast Whisper, fornecendo feedback contínuo sobre o progresso.
    *   **Descrição**: Thread responsável por transcrever arquivos de áudio (.wav, .mp4) de uma pasta especificada usando o modelo Fast Whisper. Extrai áudio de arquivos MP4 e pode acelerá-los antes da transcrição.
    *   **Sinais Emitidos**:
        *   `update_status (dict)`: Emite um dicionário com o status atual da transcrição (arquivo sendo processado, tempo, etc.).
        *   `update_transcription (str)`: Emite o texto transcrito de cada arquivo processado.
        *   `transcription_finished (str)`: Emite o texto completo da transcrição de todos os arquivos ao finalizar.
    *   **Métodos Principais**:
        *   `__init__(self, audio_folder: str, whisper_settings: dict[str, Any])`:
            *   `audio_folder`: Caminho da pasta contendo os arquivos de áudio.
            *   `whisper_settings`: Dicionário com as configurações para o Fast Whisper (modelo, idioma, dispositivo, etc.).
        *   `run(self)`: Carrega o modelo Fast Whisper. Itera sobre os arquivos na `audio_folder`. Para arquivos MP4, extrai o áudio (e opcionalmente acelera) usando FFmpeg. Transcreve cada arquivo de áudio e emite atualizações e o texto transcrito.
        *   `stop(self)`: Sinaliza para a thread parar a transcrição.
            *   **Retorno**: Nenhum.

3.  **`AudioRecorderApp(QMainWindow, Ui_MainWindow)`**:
    *   **Propósito e Caso de Uso**: Esta é a classe central que orquestra toda a aplicação. Ela conecta a interface gráfica (definida em `Ui_MainWindow`) com a lógica de backend (gravação, transcrição, configurações). Seu propósito é fornecer um ponto de controle unificado para todas as funcionalidades da VoxSynopsis, respondendo às ações do usuário e atualizando a UI com o estado atual do sistema.
    *   **Descrição**: Classe principal da aplicação que herda de `QMainWindow` (para a janela principal) e `Ui_MainWindow` (para a interface gráfica definida no Qt Designer). Gerencia a lógica da aplicação, interações do usuário, inicialização das threads de gravação e transcrição, e atualização da UI.
    *   **Atributos Principais**:
        *   `output_path (str)`: Caminho onde as gravações são salvas.
        *   `recording_thread (RecordingThread | None)`: Instância da thread de gravação.
        *   `transcription_thread (TranscriptionThread | None)`: Instância da thread de transcrição.
        *   `whisper_settings (dict)`: Dicionário contendo as configurações atuais do Fast Whisper.
    *   **Métodos Principais (seleção)**:
        *   `__init__(self)`: Configura a UI, inicializa variáveis, conecta sinais e slots, popula a lista de dispositivos de áudio e inicia o timer de monitoramento de recursos.
        *   `connect_signals(self)`: Conecta os botões e outros widgets da UI aos seus respectivos métodos de tratamento (slots).
        *   `populate_devices(self)`: Lista os dispositivos de entrada de áudio disponíveis e os adiciona ao ComboBox na UI, tentando identificar um dispositivo de loopback de áudio do sistema.
        *   `start_recording(self)`: Inicia a `RecordingThread` com as configurações selecionadas. Atualiza o estado da UI.
        *   `stop_recording(self)`: Para a `RecordingThread` em execução. Atualiza o estado da UI.
        *   `on_recording_finished(self)`: Slot chamado quando a `RecordingThread` finaliza. Atualiza a UI.
        *   `start_transcription(self)`: Inicia a `TranscriptionThread` para a pasta de saída atual e com as configurações de Whisper definidas. Atualiza o estado da UI.
        *   `update_transcription_status(self, status_dict: dict)`: Atualiza os labels de status da transcrição na UI.
        *   `append_transcription(self, text: str)`: Adiciona o texto transcrito à área de texto na UI.
        *   `on_transcription_finished(self, full_text: str)`: Slot chamado quando a `TranscriptionThread` finaliza. Salva a transcrição completa em um arquivo de texto e atualiza a UI.
        *   `open_settings_dialog(self)`: Abre a janela de diálogo `FastWhisperSettingsDialog` para modificar as configurações do Whisper.
        *   `update_status(self, status_dict: dict)`: Atualiza os labels de status da gravação (tempo total, tempo do chunk, volume) na UI.
        *   `show_error_message(self, message: str)`: Exibe uma mensagem de erro crítica.
        *   `update_resource_usage(self)`: Atualiza as barras de progresso de uso de CPU e memória na UI.
        *   `closeEvent(self, event: QCloseEvent)`: Garante que a thread de gravação seja parada antes de fechar a aplicação.

4.  **`FastWhisperSettingsDialog(QDialog)`**:
    *   **Propósito e Caso de Uso**: Este diálogo permite que os usuários personalizem os parâmetros do modelo Fast Whisper para otimizar a performance e a precisão da transcrição de acordo com seu hardware e necessidades específicas. A funcionalidade de "Configuração Automática" simplifica esse processo para usuários menos experientes.
    *   **Descrição**: Janela de diálogo para configurar os parâmetros do modelo Fast Whisper, como tamanho do modelo, dispositivo (CPU/GPU), tipo de computação, idioma, filtro VAD, temperatura, etc. Inclui uma funcionalidade de "Configuração Automática" baseada no hardware detectado.
    *   **Métodos Principais**:
        *   `__init__(self, current_settings: dict[str, Any], parent: QWidget | None = None)`:
            *   `current_settings`: Dicionário com as configurações atuais do Whisper a serem exibidas e modificadas.
            *   `parent`: Widget pai do diálogo.
        *   `auto_configure(self)`: Tenta detectar o hardware (RAM, GPU VRAM) e sugere configurações otimizadas para o Fast Whisper.
        *   `get_settings(self) -> dict[str, Any]`:
            *   **Retorno**: Um dicionário contendo as configurações selecionadas pelo usuário no diálogo.

**Funções Globais:**

1.  **`load_stylesheet(app: Any) -> None`**:
    *   **Descrição**: Carrega um arquivo de folha de estilos Qt (`style.qss`) e o aplica à aplicação.
    *   **Parâmetros**:
        *   `app`: A instância da `QApplication`.
    *   **Retorno**: Nenhum.
    *   **Efeitos Colaterais**: Modifica o estilo da aplicação se `style.qss` for encontrado.

**Constantes Globais:**

*   `SAMPLE_RATE (int)`: Taxa de amostragem para gravação de áudio (padrão: 48000 Hz).
*   `CHUNK_DURATION_SECONDS (int)`: Duração de cada bloco de gravação em segundos (padrão: 60).
*   `OUTPUT_DIR (str)`: Nome do diretório padrão para salvar as gravações (padrão: "gravacoes").

**Fluxo de Execução Principal (`if __name__ == "__main__":`)**

1.  Cria uma instância da `QApplication`.
2.  Chama `load_stylesheet()` para aplicar o estilo customizado.
3.  Cria uma instância da `AudioRecorderApp` (a janela principal).
4.  Exibe a janela principal.
5.  Inicia o loop de eventos da aplicação Qt.
