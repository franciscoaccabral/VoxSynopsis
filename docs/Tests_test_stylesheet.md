# Documentação de `Tests/test_stylesheet.py`

**Explicação Geral:**

Este arquivo contém testes unitários relacionados à funcionalidade de carregamento e aplicação da folha de estilos Qt (QSS) definida em `style.qss`. O objetivo principal desses testes é garantir que:

1.  A aplicação tente carregar o arquivo `style.qss`.
2.  Se o arquivo `style.qss` existir e for válido, ele seja aplicado corretamente à `QApplication`.
3.  Se o arquivo `style.qss` não existir, a aplicação lide com isso de forma elegante (ex: imprimindo uma mensagem e usando o estilo padrão) sem travar.
4.  Opcionalmente, pode haver testes para verificar se estilos específicos definidos no `style.qss` estão sendo aplicados a widgets específicos, embora isso possa ser mais complexo e se aproximar de testes de UI visuais.

Os testes provavelmente usarão `pytest` e `pytest-qt` para interagir com os componentes PyQt5 e mockar partes do sistema de arquivos ou da `QApplication`.

**Estrutura Típica de um Arquivo de Teste (usando `pytest` como exemplo):**

```python
import os
import sys
from unittest.mock import patch, MagicMock

import pytest
from PyQt5.QtWidgets import QApplication, QPushButton

# Adicionar o diretório raiz ao sys.path para importar vox_synopsis_fast_whisper
# Isso pode ser necessário dependendo de como os testes são executados e a estrutura do projeto
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from vox_synopsis_fast_whisper import load_stylesheet # Função a ser testada

# Fixture para QApplication (necessária para testes de UI com PyQt)
@pytest.fixture(scope="function") # 'function' scope para ter uma app limpa para cada teste
def qapp_test(request):
    """Cria uma instância de QApplication para os testes de stylesheet."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Guardar o stylesheet original para restaurá-lo depois
    original_stylesheet = app.styleSheet()

    def fin():
        # Restaurar o stylesheet original
        app.setStyleSheet(original_stylesheet)
        # Limpar a instância da app se foi criada por este fixture e não há mais testes
        # Esta parte pode ser complexa e depende de como pytest-qt gerencia a qApp globalmente
        # Muitas vezes, pytest-qt cuida da qApp principal.

    request.addfinalizer(fin)
    return app


def create_dummy_qss_file(filepath, content="QWidget { background-color: red; }"):
    """Cria um arquivo QSS temporário para testes."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(content)


def remove_dummy_qss_file(filepath):
    """Remove o arquivo QSS temporário."""
    if os.path.exists(filepath):
        os.remove(filepath)
    # Tenta remover o diretório se estiver vazio (cuidado para não remover dirs importantes)
    # dir_name = os.path.dirname(filepath)
    # if os.path.exists(dir_name) and not os.listdir(dir_name):
    # os.rmdir(dir_name)


@pytest.fixture
def temp_qss_file(tmp_path):
    """Cria um arquivo style.qss temporário e retorna seu caminho."""
    qss_content = "QPushButton { color: blue; font-size: 16px; }"
    # Nomear o arquivo como 'style.qss' porque load_stylesheet espera esse nome
    file_path = tmp_path / "style.qss"
    file_path.write_text(qss_content)
    return str(file_path) # load_stylesheet espera um nome de arquivo fixo "style.qss"


def test_load_stylesheet_applies_styles_if_file_exists(qapp_test, temp_qss_file):
    """
    Testa se load_stylesheet aplica os estilos à QApplication
    quando o arquivo style.qss existe no diretório de trabalho do teste.
    """
    # Mudar o diretório de trabalho atual para onde temp_qss_file está,
    # pois load_stylesheet("style.qss") procura no CWD.
    original_cwd = os.getcwd()
    os.chdir(os.path.dirname(temp_qss_file))

    try:
        qapp_test.setStyleSheet("") # Limpar qualquer estilo anterior
        load_stylesheet(qapp_test)
        # O conteúdo exato de temp_qss_file.read_text()
        expected_style = "QPushButton { color: blue; font-size: 16px; }"
        assert qapp_test.styleSheet() == expected_style

        # Teste mais robusto: verificar se um widget é afetado
        # (requer que o event loop processe, pode ser mais complexo)
        # button = QPushButton()
        # qapp_test.processEvents() # Processar eventos para garantir que o estilo seja aplicado
        # assert button.styleSheet() != "" # Não é uma forma direta de verificar a cor
        # Uma verificação mais profunda envolveria inspecionar propriedades de fonte/cor do widget,
        # o que pode ser não trivial sem renderizar o widget.
    finally:
        os.chdir(original_cwd) # Restaurar CWD


def test_load_stylesheet_handles_file_not_found(qapp_test, capsys):
    """
    Testa se load_stylesheet lida corretamente com a ausência do arquivo style.qss.
    """
    # Garantir que style.qss não exista no CWD do teste
    if os.path.exists("style.qss"):
        os.remove("style.qss") # Cuidado se estiver rodando do raiz do projeto

    qapp_test.setStyleSheet("") # Limpar
    load_stylesheet(qapp_test)

    assert qapp_test.styleSheet() == "" # Nenhum estilo deve ser aplicado
    captured = capsys.readouterr()
    assert "Arquivo style.qss não encontrado." in captured.out


@patch('builtins.open', side_effect=IOError("Erro de permissão simulado"))
def test_load_stylesheet_handles_io_error(mock_open, qapp_test, capsys):
    """
    Testa se load_stylesheet lida com IOError ao tentar abrir style.qss.
    (Este teste é mais para a robustez da função load_stylesheet)
    """
    # Criar um style.qss falso para que o 'open' seja tentado
    dummy_file = "style.qss"
    create_dummy_qss_file(dummy_file, "content") # Precisa existir para open ser chamado

    qapp_test.setStyleSheet("")
    load_stylesheet(qapp_test)

    assert qapp_test.styleSheet() == ""
    captured = capsys.readouterr()
    # A mensagem exata de erro pode depender de como load_stylesheet trata exceções
    # Se ele tiver um try-except genérico, pode não logar o erro específico.
    # No código fornecido, ele apenas tem FileNotFoundError.
    # Para testar IOError, a função load_stylesheet precisaria de um except IOError.
    # Assumindo que a função seja modificada para capturar IOError:
    # assert "Erro ao ler style.qss" in captured.out # Exemplo
    # Como está, FileNotFoundError é o único erro esperado e tratado.
    # Este teste, como está, faria o mock_open levantar IOError,
    # e load_stylesheet não o pegaria, fazendo o teste falhar.
    # Para o código atual, este teste não é diretamente aplicável sem modificar load_stylesheet.
    # Vamos ajustar para o comportamento atual: se open falha com IOError, ele não é pego.
    # No entanto, o `patch` acima garante que `open` não funcionará,
    # mas como `load_stylesheet` só pega `FileNotFoundError`, uma `IOError` passaria.
    # Para testar a robustez, seria melhor que `load_stylesheet` pegasse `Exception`.

    # Revisitando o teste para o código atual:
    # O patch de 'builtins.open' com IOError fará com que a função falhe internamente
    # se o arquivo existir e for tentado abrir.
    # Se o arquivo não existir, FileNotFoundError será levantado antes, e o mock não será tão relevante.

    # Vamos focar no FileNotFoundError que é explicitamente tratado.
    # O teste `test_load_stylesheet_handles_file_not_found` já cobre isso.
    # Para testar IOError, `load_stylesheet` precisaria de:
    # except IOError as e: print(f"Erro de I/O ao ler style.qss: {e}")

    remove_dummy_qss_file(dummy_file) # Limpeza


# Testes adicionais poderiam envolver:
# - Verificar se um estilo específico de um widget é aplicado.
#   Isso é mais complexo, pois requer que o widget seja renderizado e inspecionado.
#   Exemplo:
#   button = QPushButton()
#   button.setObjectName("meuBotao")
#   # ... aplicar stylesheet com #meuBotao { background-color: green; } ...
#   # ... verificar a cor de fundo do botão ... (pode ser difícil sem renderizar)

```

**Funções e Fixtures Comuns:**

*   **`qapp_test` (fixture `pytest`)**:
    *   **Descrição**: Similar à fixture `qapp` de outros arquivos de teste, fornece uma `QApplication` limpa para cada função de teste. Inclui finalizador para restaurar o stylesheet original da aplicação, garantindo que os testes não interfiram uns nos outros.
*   **`create_dummy_qss_file` / `remove_dummy_qss_file` (funções utilitárias)**:
    *   **Descrição**: Funções para criar e remover programaticamente um arquivo `style.qss` com conteúdo específico durante os testes. Isso permite controlar a existência e o conteúdo do arquivo QSS.
*   **`temp_qss_file` (fixture `pytest`)**:
    *   **Descrição**: Usa a fixture `tmp_path` do pytest para criar um arquivo `style.qss` em um diretório temporário. O `load_stylesheet` espera que `style.qss` esteja no diretório de trabalho atual, então os testes podem precisar mudar o CWD (`os.chdir`).
*   **`test_load_stylesheet_applies_styles_if_file_exists`**:
    *   **Descrição**: Cria um arquivo `style.qss` temporário, chama `load_stylesheet()`, e então verifica se o stylesheet da `QApplication` foi definido para o conteúdo do arquivo.
    *   **Asserções**: Compara `qapp_test.styleSheet()` com o conteúdo esperado do arquivo QSS.
*   **`test_load_stylesheet_handles_file_not_found`**:
    *   **Descrição**: Garante que o arquivo `style.qss` não exista, chama `load_stylesheet()`, e verifica se a aplicação não quebra e se uma mensagem apropriada é impressa (usando a fixture `capsys` do pytest para capturar stdout/stderr).
    *   **Asserções**: Verifica se `qapp_test.styleSheet()` está vazio e se a saída capturada contém a mensagem de "Arquivo style.qss não encontrado".
*   **`test_load_stylesheet_handles_io_error`**:
    *   **Descrição**: Tenta simular um `IOError` ao tentar abrir o arquivo `style.qss` (usando `@patch` para mockar `builtins.open`). Este teste verifica a robustez da função `load_stylesheet`.
    *   **Asserções**: O comportamento esperado depende de como `load_stylesheet` trata exceções além de `FileNotFoundError`. No código fornecido, apenas `FileNotFoundError` é explicitamente tratada. Se outras `IOError`s ocorrerem, elas não seriam capturadas pela função, e o teste precisaria refletir isso ou a função precisaria ser atualizada.

**Execução dos Testes:**

Para executar estes testes (assumindo `pytest` e `pytest-qt` instalados):

1.  Navegue até o diretório raiz do projeto no terminal.
2.  Execute o comando: `pytest` ou `python -m pytest`.

**Importância para Agentes de IA:**

*   **Confiabilidade da Interface**: Garante que a personalização visual da aplicação, que pode ser importante para a experiência do usuário, seja carregada de forma confiável.
*   **Tratamento de Erros**: Verifica se a aplicação não falha caso o arquivo de estilo esteja ausente ou inacessível.
*   **Contexto para Modificações**: Se o agente for solicitado a modificar o `style.qss` ou a forma como ele é carregado, esses testes fornecem um ponto de partida para verificar se as alterações são aplicadas corretamente e não introduzem erros.

Estes testes ajudam a garantir que a aplicação VoxSynopsis possa carregar e aplicar sua folha de estilos customizada, ou falhar graciosamente se não puder, contribuindo para uma experiência de usuário mais estável e visualmente consistente.
