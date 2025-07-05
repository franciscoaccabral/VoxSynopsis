# Documentação Técnica do Projeto VoxSynopsis

Bem-vindo à documentação técnica do VoxSynopsis! Este conjunto de documentos é destinado a **desenvolvedores e agentes de IA** que buscam entender a arquitetura interna, a estrutura do código-fonte e os detalhes de implementação dos componentes do sistema.

## Sobre o VoxSynopsis

O VoxSynopsis é uma aplicação desktop projetada para facilitar a **gravação de áudio contínua e a transcrição eficiente utilizando modelos de reconhecimento de fala de alta performance (Fast Whisper)**. Ele oferece uma interface gráfica para gerenciar gravações, ajustar configurações de transcrição e visualizar os resultados. O objetivo principal é fornecer uma ferramenta robusta para usuários que precisam converter longas sessões de áudio em texto de forma prática.

**Para informações sobre como usar a aplicação, instalar, contribuir ou sobre a licença, por favor, consulte o [`README.md`](../README.md) principal do projeto.**

## Resumo de Arquitetura

O fluxo central do VoxSynopsis envolve três componentes principais trabalhando juntos:

1. **`AudioRecorderApp`** – Janela principal que recebe as ações do usuário. É responsável por iniciar/parar a gravação e acionar a transcrição.
2. **`RecordingThread`** – Thread dedicada à captura do áudio em blocos. Ela salva os arquivos WAV na pasta de saída e envia atualizações de tempo e volume para a aplicação.
3. **`TranscriptionThread`** – Thread que lê os arquivos gravados, processa cada um com o modelo Fast Whisper e devolve o texto transcrito para a `AudioRecorderApp`.

Uma visão simplificada do fluxo é:

```
AudioRecorderApp
    ├── inicia RecordingThread ──► arquivos WAV
    └── inicia TranscriptionThread ◄── lê arquivos
            │
            └── envia texto e status para a aplicação
```


## Estrutura da Documentação Técnica

Esta documentação é organizada com base nos arquivos fonte do projeto. Cada arquivo de código principal possui um documento Markdown correspondente que detalha suas classes, funções, parâmetros e responsabilidades.

### Arquivos Fonte Principais e Sua Documentação

- **[`vox_synopsis_fast_whisper.py`](./vox_synopsis_fast_whisper.md)**: O coração da aplicação. Contém a lógica da interface gráfica (GUI), coordena a gravação de áudio, gerencia as threads de transcrição com Fast Whisper e lida com as interações do usuário.
<!-- - **[`ui_vox_synopsis.py`](./ui_vox_synopsis.md)**: Define a estrutura da interface gráfica (esqueleto da UI) gerada a partir do Qt Designer. Não deve ser editado manualmente. -->
- **[`style.qss`](./style.qss.md)**: Arquivo de folha de estilos Qt (QSS) responsável pela personalização visual e tema da aplicação.

### Documentação dos Testes Unitários

Os testes unitários são cruciais para garantir a qualidade e a estabilidade do código.
- **[`Tests/test_recording_thread.py`](./Tests_test_recording_thread.md)**: Testes para a funcionalidade de gravação de áudio em threads.
- **[`Tests/test_settings_dialog.py`](./Tests_test_settings_dialog.md)**: Testes para a caixa de diálogo de configurações do FastWhisper.
- **[`Tests/test_stylesheet.py`](./Tests_test_stylesheet.md)**: Testes relacionados ao carregamento e aplicação da folha de estilos.

### Outros Arquivos Relevantes (Sem Documentação Detalhada Aqui)

- **`GEMINI.md`**: Contém instruções específicas para agentes de IA que trabalham neste repositório.
- **`requirements.txt`**: Lista as dependências Python do projeto.
- **`README.md`**: O manual principal do projeto, cobrindo instalação, uso geral, contribuições e licença.
- **`Tests/__init__.py`**: Torna o diretório `Tests` um pacote Python.

## Navegação

Utilize os links acima para navegar até a documentação detalhada de cada componente. O objetivo é fornecer clareza suficiente para que desenvolvedores e agentes de IA possam trabalhar no código de forma eficaz, entender seu fluxo e realizar modificações ou adições com confiança.
