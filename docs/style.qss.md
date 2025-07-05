# Documentação de `style.qss`

**Explicação Geral:**

Este arquivo (`style.qss`) é uma Folha de Estilos Qt (Qt Style Sheet - QSS). Ele é usado para personalizar a aparência da interface gráfica do usuário (GUI) da aplicação VoxSynopsis, que é construída com a biblioteca PyQt5. A sintaxe do QSS é muito similar à do CSS (Cascading Style Sheets) usado em desenvolvimento web.

Através deste arquivo, é possível controlar cores, fontes, bordas, preenchimentos, margens e outras propriedades visuais dos widgets da aplicação, permitindo uma customização rica e consistente da UI.

**Estrutura e Sintaxe:**

A sintaxe básica de uma regra QSS é:

```qss
Seletor {
    propriedade1: valor1;
    propriedade2: valor2;
    /* ... mais propriedades ... */
}
```

*   **Seletor**: Especifica a quais widgets a regra de estilo se aplica. Pode ser um nome de classe de widget (ex: `QPushButton`, `QLabel`), um nome de objeto (definido com `setObjectName()` no código Python, ex: `#meuBotaoEspecifico`), ou seletores mais complexos (ex: `QPushButton:hover` para um botão quando o mouse está sobre ele).
*   **Propriedade**: O atributo visual que se deseja modificar (ex: `background-color`, `font-size`, `border`).
*   **Valor**: O valor a ser atribuído à propriedade (ex: `blue`, `12px`, `2px solid black`).

**Exemplo de Conteúdo (Ilustrativo):**

```qss
/* Estilo geral para a janela principal */
QMainWindow {
    background-color: #f0f0f0;
}

/* Estilo para todos os botões */
QPushButton {
    background-color: #0078d7;
    color: white;
    border-radius: 5px;
    padding: 8px 15px;
    font-size: 14px;
}

QPushButton:hover {
    background-color: #005a9e;
}

QPushButton:pressed {
    background-color: #003c6b;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

/* Estilo para caixas de texto */
QLineEdit {
    border: 1px solid #cccccc;
    padding: 5px;
    border-radius: 3px;
    font-size: 13px;
}

/* Estilo para labels específicos */
QLabel#status_label { /* Supondo que o label de status tenha o objectName "status_label" */
    font-weight: bold;
    color: #333333;
}

/* Estilo para ComboBox */
QComboBox {
    border: 1px solid #cccccc;
    border-radius: 3px;
    padding: 1px 18px 1px 3px; /* Ajuste para a seta */
    min-width: 6em;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: darkgray;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}

QComboBox::down-arrow {
    image: url(path/to/your/dropdown-arrow.png); /* É comum usar uma imagem para a seta */
}

/* Estilo para barras de progresso */
QProgressBar {
    border: 1px solid grey;
    border-radius: 5px;
    text-align: center;
    background-color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #0078d7;
    width: 20px; /* Largura do pedaço da barra */
    margin: 0.5px;
}
```

**Como é Carregado:**

No script Python principal (`vox_synopsis_fast_whisper.py`), a função `load_stylesheet(app)` é responsável por ler este arquivo e aplicar os estilos à aplicação:

```python
# Em vox_synopsis_fast_whisper.py
def load_stylesheet(app: Any) -> None:
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Arquivo style.qss não encontrado. Usando estilo padrão.")

# ...

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_stylesheet(app) # Aplica o QSS
    main_win = AudioRecorderApp()
    main_win.show()
    sys.exit(app.exec_())
```

**Modificação:**

Para alterar a aparência da aplicação, edite este arquivo `style.qss` diretamente. As alterações geralmente são refletidas na próxima vez que a aplicação é iniciada. Para um desenvolvimento mais interativo, algumas IDEs ou ferramentas podem permitir o recarregamento dinâmico de QSS, mas o comportamento padrão é carregar no início.

**Importância para Agentes de IA:**

*   **Entendimento Visual**: Embora um agente de IA não "veja" a UI da mesma forma que um humano, entender que este arquivo controla a aparência pode ser útil para depurar problemas relacionados a como os elementos são exibidos ou se comportam visualmente (ex: um elemento pode estar "invisível" devido a uma cor de texto igual à cor de fundo).
*   **Consistência**: Se for solicitado para adicionar novos widgets à UI, o agente deve estar ciente de que os estilos podem ser aplicados globalmente ou especificamente, e tentar manter a consistência visual com o restante da aplicação.
*   **Não Modificar Programaticamente (Geralmente)**: Normalmente, um agente de IA não deve modificar este arquivo diretamente como parte de uma tarefa de codificação funcional, a menos que a tarefa seja especificamente sobre alterar o tema ou estilo da aplicação. As modificações na lógica ou estrutura da UI são feitas nos arquivos Python (`.py`) ou nos arquivos de design (`.ui`).
