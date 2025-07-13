# Documentação de `Tests/test_recording_thread.py`

**Explicação Geral:**

Este arquivo contém testes unitários para a classe `RecordingThread`, que é definida em `vox_synopsis_fast_whisper.py`. O objetivo desses testes é verificar se a funcionalidade de gravação de áudio em uma thread separada está operando corretamente, incluindo o início, a parada, a criação de arquivos e o tratamento de erros.

Os testes são escritos utilizando um framework de testes Python, como `unittest` ou `pytest`. Dada a estrutura comum de projetos Python, é provável que `pytest` seja o framework utilizado ou compatível.

**Estrutura Típica de um Arquivo de Teste (usando `pytest` como exemplo):**

Arquivos de teste com `pytest` geralmente contêm funções de teste prefixadas com `test_`. Elas podem usar fixtures para configurar o ambiente de teste e asserções (`assert`) para verificar os resultados.

**Exemplo de Conteúdo (Ilustrativo, pois o conteúdo real do arquivo não foi fornecido):**

```python
import os
import time
import wave
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import sounddevice as sd

# Supondo que RecordingThread esteja acessível (pode precisar de ajuste no sys.path)
from vox_synopsis_fast_whisper import RecordingThread, SAMPLE_RATE, CHUNK_DURATION_SECONDS

# Diretório temporário para arquivos de teste
TEST_OUTPUT_DIR = "test_recordings"


@pytest.fixture(scope="module", autouse=True)
def setup_test_environment():
    """Cria e limpa o diretório de saída dos testes."""
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
    yield
    # Limpeza: remover arquivos e diretório após os testes do módulo
    for f in os.listdir(TEST_OUTPUT_DIR):
        os.remove(os.path.join(TEST_OUTPUT_DIR, f))
    if os.path.exists(TEST_OUTPUT_DIR):
        os.rmdir(TEST_OUTPUT_DIR)


@pytest.fixture
def mock_sounddevice():
    """Fixture para mockar sounddevice."""
    with patch('sounddevice.InputStream') as mock_input_stream, \
         patch('sounddevice.query_devices') as mock_query_devices:
        # Configurar mocks básicos
        mock_query_devices.return_value = {'name': 'Test Mic', 'index': 0, 'max_input_channels': 1}

        # Simular dados de áudio para stream.read()
        # Criar um array de silêncio que corresponde a 1024 amostras
        mock_audio_chunk = np.zeros((1024, 1), dtype='float32')
        mock_input_stream.return_value.__enter__.return_value.read.return_value = (mock_audio_chunk, False)
        mock_input_stream.return_value.__enter__.return_value.samplerate = SAMPLE_RATE
        mock_input_stream.return_value.__enter__.return_value.channels = 1

        yield mock_input_stream, mock_query_devices


def test_recording_thread_starts_and_stops(mock_sounddevice):
    """Testa se a thread de gravação inicia e para corretamente."""
    mock_status_update = MagicMock()
    mock_recording_error = MagicMock()

    # Usar um dispositivo virtual ou mockado
    # Para este exemplo, supomos que o mock_sounddevice já configura um dispositivo válido
    device_index = 0 # Índice do dispositivo mockado
    channels = 1

    thread = RecordingThread(device_index, channels, TEST_OUTPUT_DIR, apply_processing=False)
    thread.status_update.connect(mock_status_update)
    thread.recording_error.connect(mock_recording_error)

    assert not thread.isRunning()
    thread.start()
    time.sleep(0.5) # Dar tempo para a thread iniciar
    assert thread.isRunning()

    thread.stop()
    thread.wait(2000) # Esperar a thread finalizar
    assert not thread.isRunning()
    mock_recording_error.assert_not_called()


def test_recording_creates_wav_file(mock_sounddevice):
    """Testa se a gravação cria um arquivo WAV válido."""
    # Reduzir a duração do chunk para o teste ser mais rápido
    original_chunk_duration = CHUNK_DURATION_SECONDS
    try:
        # Acessar e modificar globalmente para o teste (não ideal, mas para exemplificar)
        # Em um cenário real, seria melhor tornar CHUNK_DURATION_SECONDS um parâmetro
        # ou usar um mock mais sofisticado se RecordingThread o lê internamente.
        # Para este exemplo, vamos assumir que podemos influenciar o tempo de gravação.
        # Este teste precisaria que a RecordingThread grave por um curto período.

        # Para simplificar, vamos focar em verificar se *algum* arquivo é criado
        # após um curto período de gravação.
        temp_chunk_duration_for_test = 1 # Grava por 1 segundo

        with patch('vox_synopsis_fast_whisper.CHUNK_DURATION_SECONDS', temp_chunk_duration_for_test):
            thread = RecordingThread(0, 1, TEST_OUTPUT_DIR, apply_processing=False)
            thread.start()
            # Esperar um pouco mais que a duração do chunk de teste + processamento
            time.sleep(temp_chunk_duration_for_test + 0.5)
            thread.stop()
            thread.wait(2000)

        files = os.listdir(TEST_OUTPUT_DIR)
        assert any(f.startswith("gravacao_") and f.endswith(".wav") for f in files)

        if any(f.startswith("gravacao_") and f.endswith(".wav") for f in files):
            # Validar o primeiro arquivo WAV encontrado
            wav_filepath = os.path.join(TEST_OUTPUT_DIR, next(f for f in files if f.startswith("gravacao_") and f.endswith(".wav")))
            with wave.open(wav_filepath, 'rb') as wf:
                assert wf.getnchannels() == 1
                assert wf.getframerate() == SAMPLE_RATE
                assert wf.getsampwidth() == 2 # float32 é geralmente salvo como PCM 16-bit ou 32-bit por soundfile
                assert wf.getnframes() > 0
    finally:
        # Restaurar a duração original do chunk
        # Esta abordagem de patch global tem suas limitações e riscos em testes complexos.
        # Idealmente, a duração do chunk seria injetável na RecordingThread para testes.
        pass # Em um cenário real, restaurar CHUNK_DURATION_SECONDS se modificado.


def test_recording_status_update_emitted(mock_sounddevice):
    """Testa se o sinal status_update é emitido."""
    mock_status_update_handler = MagicMock()
    thread = RecordingThread(0, 1, TEST_OUTPUT_DIR, apply_processing=False)
    thread.status_update.connect(mock_status_update_handler)

    thread.start()
    time.sleep(0.2) # Esperar um pouco para a thread emitir alguns sinais
    thread.stop()
    thread.wait()

    mock_status_update_handler.assert_called()
    # Verificar se o dicionário emitido contém as chaves esperadas
    if mock_status_update_handler.call_args_list:
        last_call_args = mock_status_update_handler.call_args_list[0][0][0] # Pega o dict do primeiro call
        assert "total_time" in last_call_args
        assert "chunk_time_remaining" in last_call_args
        assert "volume" in last_call_args


@patch('sounddevice.InputStream', side_effect=Exception("Erro de dispositivo simulado"))
def test_recording_error_emitted_on_stream_error(mock_sd_error):
    """Testa se recording_error é emitido quando há um erro no InputStream."""
    mock_error_handler = MagicMock()
    thread = RecordingThread(0, 1, TEST_OUTPUT_DIR, apply_processing=False)
    thread.recording_error.connect(mock_error_handler)

    thread.start()
    thread.wait(1000) # Dar tempo para o erro ocorrer e ser tratado

    mock_error_handler.assert_called_once()
    call_args = mock_error_handler.call_args[0][0]
    assert "Erro de dispositivo simulado" in call_args


# Mais testes podem ser adicionados para:
# - Gravação com pós-processamento (apply_processing=True)
# - Diferentes números de canais
# - Comportamento quando o diretório de saída não existe (embora a app principal o crie)
# - Overflow de buffer (se possível simular e verificar o aviso)
```

**Funções e Fixtures Comuns:**

*   **`setup_test_environment` (fixture `pytest`)**:
    *   **Descrição**: Configura o ambiente antes da execução dos testes do módulo (ex: cria um diretório temporário para gravações de teste) e limpa o ambiente após a execução (ex: remove arquivos e diretórios temporários). O `autouse=True` faz com que seja executado automaticamente para o módulo.
    *   **Parâmetros**: Nenhum.
    *   **Retorno**: `yield` para separar a configuração da limpeza.
*   **`mock_sounddevice` (fixture `pytest`)**:
    *   **Descrição**: Cria mocks para as funções e classes do `sounddevice` que `RecordingThread` utiliza. Isso permite testar a lógica da thread sem depender de hardware de áudio real ou causar gravações reais durante os testes.
    *   **Parâmetros**: Nenhum.
    *   **Retorno**: `yield` tupla com os objetos mockados (ex: `mock_input_stream`, `mock_query_devices`).
*   **`test_recording_thread_starts_and_stops`**:
    *   **Descrição**: Verifica se a `RecordingThread` pode ser iniciada (`start()`) e parada (`stop()`) corretamente.
    *   **Asserções**: Checa `thread.isRunning()` antes de iniciar, após iniciar e após parar. Verifica se não houve emissão de `recording_error`.
*   **`test_recording_creates_wav_file`**:
    *   **Descrição**: Verifica se, após um período de gravação, um arquivo `.wav` é criado no diretório de saída especificado. Pode também verificar propriedades básicas do arquivo WAV (taxa de amostragem, número de canais), se possível com os mocks.
    *   **Asserções**: Checa a existência do arquivo, nome e extensão. Opcionalmente, valida o conteúdo ou metadados do WAV.
*   **`test_recording_status_update_emitted`**:
    *   **Descrição**: Verifica se o sinal `status_update` é emitido pela thread durante a gravação.
    *   **Asserções**: Usa `MagicMock` para verificar se o handler conectado ao sinal foi chamado e se os dados emitidos têm a estrutura esperada.
*   **`test_recording_error_emitted_on_stream_error`**:
    *   **Descrição**: Simula um erro durante a inicialização do `sd.InputStream` (usando `@patch` com `side_effect`) e verifica se o sinal `recording_error` é emitido corretamente.
    *   **Asserções**: Usa `MagicMock` para verificar se o handler de erro foi chamado e se a mensagem de erro é a esperada.

**Execução dos Testes:**

Para executar estes testes (assumindo `pytest`):

1.  Navegue até o diretório raiz do projeto no terminal.
2.  Execute o comando: `pytest` ou `python -m pytest`.

Pytest descobrirá automaticamente os arquivos e funções de teste e reportará os resultados.

**Importância para Agentes de IA:**

*   **Verificação de Funcionalidade**: Se o agente modificar `RecordingThread`, executar estes testes é crucial para garantir que as mudanças não quebraram a funcionalidade de gravação.
*   **Entendimento do Comportamento**: Ler os testes pode ajudar o agente a entender como `RecordingThread` deve se comportar em diferentes cenários, incluindo casos de erro.
*   **Criação de Novos Testes**: Se o agente adicionar novas funcionalidades à `RecordingThread` (ex: um novo tipo de pós-processamento, diferentes formatos de saída), ele deve também adicionar novos testes unitários para cobrir essas funcionalidades.

Este arquivo é fundamental para manter a robustez e a corretude da funcionalidade de gravação da aplicação VoxSynopsis.
