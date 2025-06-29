# VoxSynopsis
# VoxSynopsis

Este é um aplicativo de desktop simples, construído com Python e PyQt5, que permite gravar áudio de alta qualidade, aplicar pós-processamento (redução de ruído e normalização) e transcrever automaticamente os áudios gravados usando o modelo Whisper da OpenAI.

## Funcionalidades

*   **Gravação de Áudio:**
    *   Grava trechos de áudio de 60 segundos.
    *   Salva automaticamente os trechos em arquivos WAV de alta qualidade (48kHz).
    *   Permite selecionar a fonte de áudio (microfone, som do sistema, ou ambos via dispositivo agregado).
    *   Exibe tempo total de gravação, tempo restante no trecho e nível de volume em tempo real.
*   **Pós-processamento de Áudio:**
    *   Opcionalmente, aplica redução de ruído e normalização de volume aos arquivos gravados para otimizar a qualidade para transcrição.
    *   Salva uma versão processada do áudio (`_processed.wav`).
*   **Transcrição com Whisper:**
    *   Transcreve arquivos de áudio (preferencialmente os processados) da pasta de destino.
    *   Utiliza o modelo `medium` do Whisper, otimizado para CPU e com boa precisão para português.
    *   Exibe o progresso da transcrição (arquivo atual, tempo do último arquivo, tempo total).
    *   Compila todas as transcrições em um único arquivo de texto (`transcricao_completa.txt`).
*   **Monitoramento de Recursos:**
    *   Exibe o uso de CPU e memória da aplicação em tempo real através de barras de progresso.

## Pré-requisitos

Antes de começar, você precisará ter algumas ferramentas instaladas no seu computador. Não se preocupe, vamos explicar passo a passo.

### 1. Python

Python é a linguagem de programação que usamos para criar este aplicativo.

*   **Para Windows (Recomendado):**
    1.  Acesse o site oficial do Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    2.  Baixe a versão mais recente do Python 3 (ex: Python 3.10.x ou superior). Procure por "Windows installer (64-bit)".
    3.  Execute o instalador. **MUITO IMPORTANTE:** Na primeira tela do instalador, marque a caixa **"Add Python.exe to PATH"** (Adicionar Python.exe ao PATH), conforme a imagem abaixo (se disponível). Isso é crucial para que você possa usar o Python diretamente do Prompt de Comando ou PowerShell.
        ![Adicionar Python ao PATH](https://i.imgur.com/example_python_path.png) <!-- Substitua por uma imagem real se possível -->
    4.  Prossiga com a instalação padrão, clicando em "Install Now".
    5.  Para verificar se o Python foi instalado corretamente, abra o "Prompt de Comando" (pesquise por `cmd` no menu Iniciar) ou o "PowerShell" e digite:
        ```powershell
        python --version
        ```
        Você deverá ver a versão do Python instalada (ex: `Python 3.10.5`). Se aparecer um erro, tente fechar e reabrir o terminal.

*   **Para macOS:**
    1.  Acesse o site oficial do Python: [https://www.python.org/downloads/](https://www.python.org/downloads/)
    2.  Baixe a versão mais recente do Python 3 (ex: Python 3.10.x ou superior). Procure por "macOS 64-bit installer".
    3.  Execute o instalador e siga as instruções.
    4.  Para verificar, abra o "Terminal" (você pode encontrá-lo em Aplicativos > Utilitários) e digite:
        ```bash
        python3 --version
        ```
        Você deverá ver a versão do Python instalada.

*   **Para Linux (Ubuntu/Debian):**
    1.  A maioria das distribuições Linux já vem com Python pré-instalado. Para garantir que você tenha a versão mais recente e as ferramentas necessárias, abra o terminal e digite:
        ```bash
        sudo apt update
        sudo apt install python3 python3-pip
        ```
    2.  Para verificar:
        ```bash
        python3 --version
        ```

### 2. FFmpeg

O FFmpeg é uma ferramenta essencial para o Whisper processar arquivos de áudio. Ele precisa estar instalado e acessível pelo sistema.

*   **Para Windows (Recomendado: Chocolatey - o jeito mais fácil):**
    1.  **Instale o Chocolatey (se ainda não tiver):** O Chocolatey é um gerenciador de pacotes para Windows que facilita a instalação de programas. Abra o "Prompt de Comando" ou "PowerShell" **como administrador** (clique com o botão direito e selecione "Executar como administrador") e siga as instruções detalhadas em [https://chocolatey.org/install](https://chocolatey.org/install).
    2.  **Instale o FFmpeg com Chocolatey:** Após instalar o Chocolatey, no mesmo terminal **como administrador**, digite:
        ```powershell
        choco install ffmpeg
        ```
    3.  Feche e reabra o terminal (Prompt de Comando ou PowerShell) para que as mudanças tenham efeito.
    4.  Para verificar se o FFmpeg foi instalado corretamente, digite:
        ```powershell
        ffmpeg -version
        ```
        Você deverá ver informações sobre a versão do FFmpeg.

*   **Para Windows (Manual - para usuários avançados):**
    1.  Acesse [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) e clique no ícone do Windows.
    2.  Escolha uma das opções de download (ex: `gyan.dev` ou `BtbN`). Baixe o arquivo `.zip` da versão `release` (lançamento).
    3.  Descompacte o arquivo `.zip` em um local de sua preferência e de fácil acesso (ex: `C:\ffmpeg`). Certifique-se de que a pasta `bin` (que contém `ffmpeg.exe`) esteja dentro do diretório que você descompactou.
    4.  Você precisará adicionar o caminho completo para a pasta `bin` do FFmpeg às variáveis de ambiente do sistema (especificamente à variável `Path`). Este passo é um pouco mais complexo e envolve:
        *   Pesquisar por "Editar as variáveis de ambiente do sistema" no menu Iniciar.
        *   Clicar em "Variáveis de Ambiente...".
        *   Na seção "Variáveis do sistema", encontrar e selecionar a variável `Path` e clicar em "Editar...".
        *   Clicar em "Novo" e adicionar o caminho completo para a pasta `bin` do FFmpeg (ex: `C:\ffmpeg\bin`).
        *   Clique em "OK" em todas as janelas para salvar as alterações.
        *   Feche e reabra o terminal para que as mudanças tenham efeito.
    5.  Para verificar, digite no terminal:
        ```powershell
        ffmpeg -version
        ```

*   **Para macOS (Homebrew):**
    1.  **Instale o Homebrew (se ainda não tiver):** O Homebrew é um gerenciador de pacotes para macOS. Abra o "Terminal" e siga as instruções em [https://brew.sh/](https://brew.sh/).
    2.  **Instale o FFmpeg com Homebrew:** No terminal, digite:
        ```bash
        brew install ffmpeg
        ```
    3.  Para verificar:
        ```bash
        ffmpeg -version
        ```

*   **Para Linux (Ubuntu/Debian):**
    1.  Abra o terminal e digite:
        ```bash
        sudo apt update
        sudo apt install ffmpeg
        ```
    2.  Para verificar:
        ```bash
        ffmpeg -version
        ```

## Instalação do Aplicativo

### 1. Baixe o Código

Baixe o arquivo `vox_synopsis.py` para uma pasta em seu computador. Por exemplo, você pode criar uma pasta chamada `IA40` em `C:\Users\SeuUsuario\Documentos\IA40`.

### 2. Instale as Dependências do Python

Abra o "Prompt de Comando" ou "PowerShell" e navegue até a pasta onde você salvou o arquivo `vox_synopsis.py`. Por exemplo, se você salvou em `C:\Users\SeuUsuario\Documentos\IA40`:

```powershell
cd C:\Users\SeuUsuario\Documentos\IA40
```

Agora, instale todas as bibliotecas Python necessárias. Digite o seguinte comando e pressione Enter:

```powershell
pip install PyQt5 sounddevice numpy soundfile noisereduce scipy openai-whisper psutil torch torchaudio
```

*   **`PyQt5`**: Para a interface gráfica do aplicativo.
*   **`sounddevice`**: Para gravar e gerenciar os dispositivos de áudio.
*   **`numpy`**: Para manipulação eficiente de dados numéricos (usado pelo `sounddevice` e `noisereduce`).
*   **`soundfile`**: Para ler e escrever arquivos de áudio (WAV).
*   **`noisereduce`**: Para aplicar a redução de ruído no áudio.
*   **`scipy`**: Uma dependência do `noisereduce` para computação científica.
*   **`openai-whisper`**: A biblioteca oficial do Whisper para transcrição de áudio.
*   **`psutil`**: Para monitorar o uso de CPU e memória do aplicativo.

## Configuração da Gravação de Áudio do Sistema (Opcional)

Se você deseja gravar o "som do sistema" (áudio que está sendo reproduzido no seu computador), pode ser necessário configurar um dispositivo de áudio "loopback" ou "mixagem estéreo".

*   **No Windows (Mixagem Estéreo / Stereo Mix):**
    1.  Clique com o botão direito no ícone de volume na barra de tarefas (canto inferior direito da tela).
    2.  Selecione **"Sons"** (ou "Sound settings" e depois "Sound Control Panel").
    3.  Vá para a aba **"Gravação"**.
    4.  Clique com o botão direito em qualquer área vazia da lista de dispositivos e marque **"Mostrar Dispositivos Desabilitados"** e **"Mostrar Dispositivos Desconectados"**.
    5.  Um dispositivo chamado **"Mixagem Estéreo"** (ou "Stereo Mix") deve aparecer.
    6.  Clique com o botão direito sobre ele e selecione **"Habilitar"**.
    7.  Você pode defini-lo como dispositivo padrão se quiser que seja a fonte principal.
    8.  Após habilitar, ele deverá aparecer na lista de "Fonte de Áudio" no aplicativo.

*   **No macOS (BlackHole):**
    O macOS não possui um recurso nativo para isso. Você precisará de um software de terceiros como o [**BlackHole**](https://github.com/ExistentialAudio/BlackHole) para criar um dispositivo de áudio virtual que roteia o som do sistema para uma entrada. Após a instalação do BlackHole, ele aparecerá como um dispositivo de entrada na lista de "Fonte de Áudio" do nosso aplicativo.

*   **No Linux:**
    Geralmente, o PulseAudio ou o PipeWire já fornecem um dispositivo "Monitor" para a saída de áudio, que funciona como uma fonte de gravação do som do sistema. Ele deve aparecer na lista de dispositivos automaticamente.

## Como Usar o Aplicativo

1.  Abra o "Prompt de Comando" ou "PowerShell" e navegue até a pasta onde você salvou o arquivo `vox_synopsis.py`.
    ```powershell
    cd C:\Users\SeuUsuario\Documentos\IA40
    ```
2.  Execute o aplicativo digitando:
    ```powershell
    python vox_synopsis.py
    ```
    A janela do aplicativo será aberta.

### Interface do Aplicativo:

*   **Fonte de Áudio:** Use a lista suspensa para selecionar o microfone, "Mixagem Estéreo" (Windows), "BlackHole" (macOS) ou outro dispositivo de entrada de áudio disponível.
*   **Salvar em:** Este campo mostra a pasta onde os arquivos de áudio serão salvos. Por padrão, será criada uma pasta `gravacoes` no mesmo local do script.
    *   **Botão "Procurar..."**: Clique aqui para escolher uma pasta diferente para salvar suas gravações.
*   **Aplicar Pós-processamento (Redução de Ruído e Normalização):** Marque esta caixa para que o aplicativo aplique automaticamente técnicas de redução de ruído e normalização de volume aos seus áudios após a gravação. Isso é **altamente recomendado** para obter melhores resultados com o Whisper.
*   **Iniciar Gravação:** Clique para começar a gravar. O aplicativo gravará trechos de 60 segundos e os salvará automaticamente.
*   **Parar Gravação:** Clique para interromper a gravação.
*   **Transcrever Áudios da Pasta:** Clique neste botão para iniciar o processo de transcrição. O aplicativo irá procurar por arquivos `.wav` na pasta de destino (dando preferência aos arquivos `_processed.wav` se existirem) e transcrevê-los um por um.
*   **Status:** Mostra o estado atual do aplicativo (Parado, Gravando, Transcrevendo, etc.).
*   **Tempo Total Gravado:** Exibe o tempo total de áudio que você já gravou.
*   **Tempo Restante no Trecho:** Mostra quanto tempo falta para o trecho de 60 segundos atual ser concluído.
*   **Nível de Volume:** Uma barra de progresso que indica o volume do áudio sendo captado.
*   **Transcrição:** Uma área de texto onde as transcrições aparecerão à medida que forem concluídas.
*   **Tempo do Último Arquivo:** Mostra quanto tempo o Whisper levou para transcrever o último arquivo.
*   **Tempo Total de Transcrição:** Acumula o tempo total gasto na transcrição de todos os arquivos.
*   **CPU / Memória:** Barras de progresso que mostram o uso de CPU e memória do aplicativo em tempo real.

### Fluxo de Trabalho Recomendado:

1.  **Selecione sua Fonte de Áudio.**
2.  **Escolha a Pasta de Destino** (ou use a padrão).
3.  **Mantenha "Aplicar Pós-processamento" marcado.**
4.  **Clique em "Iniciar Gravação"** e grave seus áudios.
5.  **Clique em "Parar Gravação"** quando terminar.
6.  **Clique em "Transcrever Áudios da Pasta"** para que o Whisper processe seus arquivos.
7.  A transcrição completa será salva em um arquivo `transcricao_completa.txt` na sua pasta de destino.

## Solução de Problemas Comuns

*   **"FFmpeg não encontrado" ou erro ao transcrever:** Certifique-se de que o FFmpeg está instalado corretamente e que seu caminho está nas variáveis de ambiente do sistema (se a instalação foi manual). Feche e reabra o Prompt de Comando/PowerShell após a instalação do FFmpeg.
*   **Dispositivo de áudio não aparece na lista:** Verifique as configurações de som do seu sistema operacional (veja a seção "Configuração da Gravação de Áudio do Sistema").
*   **Desempenho lento na transcrição:** O modelo `medium` do Whisper pode ser intensivo em CPU. Transcrições de áudios muito longos levarão tempo. Certifique-se de que seu computador atende aos requisitos mínimos para o Whisper.
*   **Erros de permissão ao salvar arquivos:** Verifique se a pasta de destino selecionada tem permissões de escrita para o usuário atual.

---

Esperamos que este aplicativo seja útil para suas necessidades de gravação e transcrição!
