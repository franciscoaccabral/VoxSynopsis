# VoxSynopsis (com FastWhisper)

Este é um aplicativo de desktop simples, construído com Python e PyQt5, que permite gravar áudio de alta qualidade, aplicar pós-processamento e transcrever automaticamente áudios e vídeos usando o modelo **FastWhisper** (uma versão otimizada do Whisper da OpenAI).

## Funcionalidades

*   **Gravação de Áudio:**
    *   Grava áudio em trechos contínuos de 60 segundos.
    *   Salva automaticamente os trechos em arquivos WAV de alta qualidade (48kHz).
    *   Detecta e permite selecionar a fonte de áudio, incluindo microfones e o áudio do sistema (via "Mixagem Estéreo" no Windows).
    *   Exibe tempo total de gravação, tempo restante no trecho e nível de volume em tempo real.
*   **Pós-processamento de Áudio:**
    *   Opcionalmente, aplica redução de ruído e normalização de volume aos arquivos gravados para otimizar a qualidade para transcrição.
    *   Salva uma versão processada do áudio (`_processed.wav`).
*   **Transcrição com FastWhisper:**
    *   **Processa arquivos de áudio (.wav) e vídeo (.mp4)** da pasta de destino.
    *   Para arquivos `.mp4`, extrai o áudio, acelera para 1.5x e salva como `.wav` antes de transcrever.
    *   Utiliza o modelo **FastWhisper**, que oferece desempenho significativamente superior (até 4x mais rápido) e menor uso de memória.
    *   **VAD (Voice Activity Detection):** Filtra silêncios do áudio para transcrições mais rápidas e limpas.
    *   Exibe o progresso da transcrição (arquivo atual, tempo do último arquivo, tempo total).
    *   Compila todas as transcrições em um único arquivo de texto (`transcricao_completa.txt`).
*   **Monitoramento de Recursos:**
    *   Exibe o uso de CPU e memória da aplicação em tempo real.

## Pré-requisitos

Antes de começar, você precisará ter o Python e o FFmpeg instalados no seu computador.

### 1. Python

*   **Instalação:**
    1.  Acesse [python.org/downloads](https://www.python.org/downloads/) e baixe a versão mais recente (3.10+).
    2.  **MUITO IMPORTANTE:** No instalador do Windows, marque a caixa **"Add Python.exe to PATH"**.
    3.  Para verificar a instalação, abra um novo terminal (Prompt de Comando, PowerShell ou Terminal) e digite `python --version`.

### 2. FFmpeg

O FFmpeg é essencial para processar arquivos de áudio e vídeo.

*   **Instalação no Windows (Recomendado: Chocolatey):**
    1.  Instale o gerenciador de pacotes **Chocolatey** seguindo as instruções em [chocolatey.org/install](https://chocolatey.org/install).
    2.  Abra o PowerShell **como administrador** e execute: `choco install ffmpeg`
*   **Instalação no macOS (Homebrew):**
    1.  Instale o **Homebrew** a partir de [brew.sh](https://brew.sh/).
    2.  No terminal, execute: `brew install ffmpeg`
*   **Instalação no Linux (Ubuntu/Debian):**
    1.  No terminal, execute: `sudo apt update && sudo apt install ffmpeg`

Para verificar a instalação do FFmpeg, abra um novo terminal e digite `ffmpeg -version`.

## Instalação do Aplicativo

### 1. Baixe o Código

Baixe o arquivo `vox_synopsis_fast_whisper.py` para uma pasta em seu computador.

### 2. Instale as Dependências do Python

Abra um terminal, navegue até a pasta onde você salvou o arquivo e instale as bibliotecas necessárias com o seguinte comando:

```powershell
pip install PyQt5 sounddevice numpy soundfile noisereduce scipy faster-whisper psutil torch
```

*   **`PyQt5`**: Para a interface gráfica.
*   **`sounddevice`**: Para gravar e gerenciar áudio.
*   **`numpy`, `scipy`**: Para manipulação de dados de áudio e redução de ruído.
*   **`soundfile`**: Para ler e escrever arquivos de áudio.
*   **`noisereduce`**: Para a função de pós-processamento.
*   **`faster-whisper`**: A biblioteca otimizada para transcrição de áudio.
*   **`psutil`**: Para monitorar o uso de CPU e memória.
*   **`torch`**: Dependência do FastWhisper. A instalação de uma versão compatível com CUDA/GPU é recomendada para melhor desempenho.

## Como Usar o Aplicativo

1.  Abra um terminal e navegue até a pasta onde o script foi salvo.
2.  Execute o aplicativo com o comando:
    ```powershell
    python vox_synopsis_fast_whisper.py
    ```

### Interface do Aplicativo:

*   **Dispositivo de Entrada:** Selecione o microfone ou o dispositivo de áudio do sistema (se disponível).
*   **Pasta de Saída:** Escolha onde salvar as gravações.
*   **Aplicar pós-processamento:** Altamente recomendado para melhorar a qualidade da transcrição.
*   **Iniciar/Parar Gravação:** Controla o processo de gravação.
*   **Transcrever Áudio:** Inicia a transcrição. O programa buscará por arquivos `.wav` e `.mp4` na pasta de destino.
*   **Cfg.FastWhisper:** Abre uma janela de configurações avançadas para o modelo FastWhisper, onde você pode ajustar:
    *   **Modelo:** Tamanho do modelo (ex: `medium`, `large-v3`).
    *   **Dispositivo:** `cpu` ou `cuda` (GPU).
    *   **Tipo de Computação:** Precisão dos cálculos (`int8`, `float16`, etc.). Afeta velocidade e uso de memória.
    *   **Usar Filtro VAD:** Detecta e pula partes sem fala no áudio.
    *   Outros parâmetros como idioma, temperatura, beam size, etc.
    *   **Cfg. Automática:** Analisa seu hardware e sugere configurações otimizadas.

### Fluxo de Trabalho Recomendado:

1.  Selecione seu dispositivo de entrada.
2.  Mantenha "Aplicar Pós-processamento" marcado.
3.  Clique em **"Iniciar Gravação"**.
4.  Quando terminar, clique em **"Parar Gravação"**.
5.  Coloque quaisquer arquivos de vídeo `.mp4` que deseje transcrever na mesma pasta de gravação.
6.  Clique em **"Transcrever Áudio"**.
7.  A transcrição completa será salva em `transcricao_completa.txt` na pasta de destino.

## Solução de Problemas Comuns

*   **"FFmpeg não encontrado"**: Certifique-se de que o FFmpeg foi instalado e está acessível no PATH do sistema. Feche e reabra o terminal após a instalação.
*   **"Áudio do Sistema" não aparece:** No Windows, você pode precisar habilitar a "Mixagem Estéreo" (Stereo Mix) manualmente nas configurações de som do painel de controle.
*   **Desempenho lento na transcrição:** A transcrição é uma tarefa intensiva. Para melhor desempenho, use uma GPU NVIDIA (selecionando o dispositivo `cuda` e um `compute_type` como `float16`) e ative o filtro VAD.

