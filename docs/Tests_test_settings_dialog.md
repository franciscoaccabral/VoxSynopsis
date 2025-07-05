# Documentação de `Tests/test_settings_dialog.py`

**Explicação Geral:**

Este arquivo contém testes unitários para a classe `FastWhisperSettingsDialog`, que é definida em `vox_synopsis_fast_whisper.py`. O objetivo destes testes é garantir que o diálogo de configurações do FastWhisper funcione corretamente, incluindo:

*   A inicialização dos campos do formulário com as configurações atuais.
*   A atualização correta das configurações quando o usuário interage com os campos (ComboBoxes, Sliders, CheckBoxes, etc.).
*   O retorno das configurações modificadas quando o diálogo é aceito.
*   O funcionamento da funcionalidade de "Configuração Automática".

Os testes são provavelmente escritos usando `pytest`, aproveitando fixtures para configurar a `QApplication` necessária para instanciar widgets PyQt e para simular interações do usuário.

**Estrutura Típica de um Arquivo de Teste (usando `pytest` como exemplo):**

```python
import pytest
from PyQt5.QtWidgets import QApplication, QDialogButtonBox
from unittest.mock import patch, MagicMock

# Supondo que FastWhisperSettingsDialog esteja acessível
from vox_synopsis_fast_whisper import FastWhisperSettingsDialog

# Fixture para QApplication (necessária para testes de UI com PyQt)
@pytest.fixture(scope="session")
def qapp():
    """Cria uma instância de QApplication para os testes."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def default_settings():
    """Retorna um dicionário de configurações padrão para os testes."""
    return {
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


@pytest.fixture
def settings_dialog(qapp, default_settings):
    """Cria uma instância de FastWhisperSettingsDialog com configurações padrão."""
    dialog = FastWhisperSettingsDialog(default_settings.copy())
    return dialog


def test_dialog_initialization(settings_dialog, default_settings):
    """Testa se o diálogo é inicializado corretamente com as configurações fornecidas."""
    assert settings_dialog.model_combo.currentText() == default_settings["model"]
    assert settings_dialog.language_combo.currentText() == default_settings["language"]
    assert settings_dialog.device_combo.currentText() == default_settings["device"]
    assert settings_dialog.compute_type_combo.currentText() == default_settings["compute_type"]
    assert settings_dialog.vad_filter_checkbox.isChecked() == default_settings["vad_filter"]
    assert settings_dialog.temperature_slider.value() / 10.0 == default_settings["temperature"]
    assert settings_dialog.best_of_slider.value() == default_settings["best_of"]
    assert settings_dialog.beam_size_slider.value() == default_settings["beam_size"]
    assert settings_dialog.condition_checkbox.isChecked() == default_settings["condition_on_previous_text"]
    assert settings_dialog.initial_prompt_edit.text() == default_settings["initial_prompt"]
    assert settings_dialog.acceleration_spinbox.value() == default_settings["acceleration_factor"]


def test_get_settings_returns_modified_values(settings_dialog):
    """Testa se get_settings() retorna os valores modificados pelo usuário."""
    # Simular modificações do usuário
    new_model = "large-v3"
    new_lang = "en"
    new_temp = 0.5
    new_accel = 2.0

    settings_dialog.model_combo.setCurrentText(new_model)
    settings_dialog.language_combo.setCurrentText(new_lang)
    settings_dialog.temperature_slider.setValue(int(new_temp * 10))
    settings_dialog.vad_filter_checkbox.setChecked(False)
    settings_dialog.acceleration_spinbox.setValue(new_accel)

    retrieved_settings = settings_dialog.get_settings()

    assert retrieved_settings["model"] == new_model
    assert retrieved_settings["language"] == new_lang
    assert retrieved_settings["temperature"] == new_temp
    assert not retrieved_settings["vad_filter"] # Verificando a modificação do checkbox
    assert retrieved_settings["acceleration_factor"] == new_accel
    # Outras configurações devem permanecer as mesmas que as iniciais se não foram alteradas
    assert retrieved_settings["device"] == settings_dialog.settings["device"]


def test_dialog_accept_and_reject(settings_dialog, qtbot):
    """Testa os botões OK e Cancelar."""
    # Simular clique no botão OK
    # qtbot.mouseClick(settings_dialog.button_box.button(QDialogButtonBox.Ok), Qt.LeftButton)
    # assert settings_dialog.result() == QDialog.Accepted
    # settings_dialog.done(QDialog.Accepted) # Maneira mais programática de fechar

    # Para testar o resultado sem realmente mostrar o diálogo, podemos chamar accept() diretamente
    # Note: Isso não testa a interação do usuário, mas a lógica interna de accept/reject
    settings_dialog.accept()
    assert settings_dialog.result() == 1 # QDialog.Accepted é 1

    # Resetar e testar reject
    # Precisaria recriar o diálogo ou resetar seu estado para um novo teste de reject
    # new_dialog = FastWhisperSettingsDialog(default_settings.copy())
    # new_dialog.reject()
    # assert new_dialog.result() == 0 # QDialog.Rejected é 0


@patch('psutil.virtual_memory')
@patch('torch.cuda.is_available')
@patch('torch.cuda.get_device_properties')
@patch('PyQt5.QtWidgets.QMessageBox.information') # Mockar para não mostrar pop-ups
def test_auto_configure_gpu(mock_msgbox, mock_gpu_props, mock_cuda_avail, mock_psutil_mem, settings_dialog, qapp):
    """Testa a funcionalidade de configuração automática com GPU disponível."""
    mock_psutil_mem.return_value.total = 16 * (1024**3)  # 16 GB RAM
    mock_cuda_avail.return_value = True

    # Simular diferentes VRAMs
    # Caso 1: VRAM >= 10 GB
    mock_gpu_props.return_value.total_memory = 12 * (1024**3) # 12 GB VRAM
    settings_dialog.auto_configure()
    settings = settings_dialog.get_settings()
    assert settings["device"] == "cuda"
    assert settings["model"] == "large-v3"
    assert settings["compute_type"] == "int8_float16"

    # Caso 2: VRAM >= 5 GB
    mock_gpu_props.return_value.total_memory = 6 * (1024**3) # 6 GB VRAM
    settings_dialog.auto_configure() # Chama de novo para reconfigurar
    settings = settings_dialog.get_settings()
    assert settings["device"] == "cuda"
    assert settings["model"] == "medium"
    assert settings["compute_type"] == "int8_float16"

    # Caso 3: VRAM < 5 GB
    mock_gpu_props.return_value.total_memory = 4 * (1024**3) # 4 GB VRAM
    settings_dialog.auto_configure()
    settings = settings_dialog.get_settings()
    assert settings["device"] == "cuda"
    assert settings["model"] == "small"
    assert settings["compute_type"] == "int8_float16"
    mock_msgbox.assert_called() # Verifica se o QMessageBox.information foi chamado


@patch('psutil.virtual_memory')
@patch('torch.cuda.is_available')
@patch('PyQt5.QtWidgets.QMessageBox.information') # Mockar para não mostrar pop-ups
def test_auto_configure_cpu(mock_msgbox, mock_cuda_avail, mock_psutil_mem, settings_dialog, qapp):
    """Testa a funcionalidade de configuração automática para CPU."""
    mock_cuda_avail.return_value = False # GPU não disponível

    # Caso 1: RAM >= 8 GB
    mock_psutil_mem.return_value.total = 16 * (1024**3)  # 16 GB RAM
    settings_dialog.auto_configure()
    settings = settings_dialog.get_settings()
    assert settings["device"] == "cpu"
    assert settings["model"] == "medium"
    assert settings["compute_type"] == "int8"

    # Caso 2: RAM >= 4 GB
    mock_psutil_mem.return_value.total = 6 * (1024**3)  # 6 GB RAM
    settings_dialog.auto_configure()
    settings = settings_dialog.get_settings()
    assert settings["device"] == "cpu"
    assert settings["model"] == "small"

    # Caso 3: RAM < 4 GB
    mock_psutil_mem.return_value.total = 2 * (1024**3)  # 2 GB RAM
    settings_dialog.auto_configure()
    settings = settings_dialog.get_settings()
    assert settings["device"] == "cpu"
    assert settings["model"] == "base"
    mock_msgbox.assert_called()

# Mais testes podem ser adicionados para:
# - Interações específicas com cada tipo de controle (sliders, comboboxes, lineedits).
# - Validação de entrada (se houver).
# - Comportamento quando 'torch' não está disponível (para o device_combo e compute_type_combo).
# - Testar os limites dos sliders e spinboxes.
```

**Funções e Fixtures Comuns:**

*   **`qapp` (fixture `pytest`)**:
    *   **Descrição**: Fornece uma instância de `QApplication`. É essencial para qualquer teste que instancie widgets PyQt, pois eles dependem de uma `QApplication` existente. `scope="session"` significa que é criada uma vez por sessão de teste.
*   **`default_settings` (fixture `pytest`)**:
    *   **Descrição**: Retorna um dicionário com um conjunto de configurações padrão. Isso ajuda a manter os testes consistentes e a reduzir a duplicação de código.
*   **`settings_dialog` (fixture `pytest`)**:
    *   **Descrição**: Cria e retorna uma instância de `FastWhisperSettingsDialog`, inicializada com as `default_settings`. Usa a fixture `qapp`.
*   **`test_dialog_initialization`**:
    *   **Descrição**: Verifica se todos os campos do formulário no diálogo são preenchidos corretamente com os valores das configurações passadas para o construtor.
    *   **Asserções**: Compara o valor de cada widget (ex: `model_combo.currentText()`, `vad_filter_checkbox.isChecked()`) com o valor correspondente nas `default_settings`.
*   **`test_get_settings_returns_modified_values`**:
    *   **Descrição**: Simula a modificação de alguns campos no diálogo e depois chama `get_settings()` para verificar se os valores retornados refletem essas modificações.
    *   **Asserções**: Compara os valores no dicionário retornado por `get_settings()` com os valores que foram programaticamente alterados nos widgets.
*   **`test_dialog_accept_and_reject`**:
    *   **Descrição**: Testa a lógica dos botões "OK" (aceitar) e "Cancelar" (rejeitar) do diálogo.
    *   **Asserções**: Verifica se `dialog.result()` retorna `QDialog.Accepted` ou `QDialog.Rejected` apropriadamente. Pode usar `qtbot` (uma fixture do plugin `pytest-qt`) para simular cliques de mouse, ou chamar os métodos `accept()` e `reject()` programaticamente.
*   **`test_auto_configure_gpu` / `test_auto_configure_cpu`**:
    *   **Descrição**: Testa a função `auto_configure()`. Usa `@patch` para mockar dependências externas como `psutil.virtual_memory`, `torch.cuda.is_available`, e `torch.cuda.get_device_properties` para simular diferentes configurações de hardware (RAM, disponibilidade de GPU, VRAM).
    *   **Asserções**: Verifica se as configurações no diálogo são ajustadas conforme o esperado para cada cenário de hardware simulado. Também mocka `QMessageBox.information` para evitar que pop-ups apareçam durante os testes.

**Execução dos Testes:**

Para executar estes testes (assumindo `pytest` e `pytest-qt` instalados):

1.  Navegue até o diretório raiz do projeto no terminal.
2.  Execute o comando: `pytest` ou `python -m pytest`.

**Importância para Agentes de IA:**

*   **Manutenção da Lógica de Configuração**: Se o agente precisar modificar as opções de configuração disponíveis ou a lógica da `FastWhisperSettingsDialog` (incluindo `auto_configure`), esses testes são vitais para garantir que o diálogo continue funcionando como esperado.
*   **Entendimento das Opções**: Os testes demonstram quais configurações são controladas pelo diálogo e como elas são mapeadas para os widgets da UI.
*   **Prevenção de Regressões**: Se novas opções forem adicionadas ou a lógica de `auto_configure` for alterada, os testes existentes (e novos testes) ajudarão a prevenir que funcionalidades anteriores sejam quebradas.

Este conjunto de testes é crucial para assegurar que os usuários possam configurar corretamente as opções de transcrição do FastWhisper através da interface gráfica.
