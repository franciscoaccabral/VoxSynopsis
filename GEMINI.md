This file is used by the Gemini CLI to store project-specific context and information.

## Code Quality Checks

Before committing any changes, please run the following commands to ensure code quality and consistency:

1.  **Ruff:** For linting and formatting.
    ```bash
    ruff check .
    ```

2.  **Pyright:** For static type checking.
    ```bash
    pyright
    ```

## Guidelines for Code Quality and Type Safety

To maintain high code quality and prevent common issues, please adhere to the following guidelines:

*   **Ruff Configuration:** Ensure `ruff` configurations in `pyproject.toml` are correctly placed. `line-length` should be directly under `[tool.ruff]`, not `[tool.ruff.lint]`.
*   **Line Length (`E501`):** Always keep lines within the configured limit (currently 88 characters). Break long lines into multiple, more readable lines.
*   **Blank Lines (`W293`):** Ensure blank lines do not contain any whitespace.
*   **Type Hinting and `pyright`:**
    *   **Initialize Variables:** Always initialize variables that might be conditionally assigned (e.g., `model = None`) to avoid `possibly unbound variable` errors.
    *   **PyQt5 Method Overrides:** When overriding PyQt5 methods (e.g., `closeEvent`), if `pyright` reports `incompatible method override` errors despite correct signature, consider adding `# type: ignore` to the method definition as a last resort.
    *   **Layout Management in PyQt5:** For `QDialog` and `QMainWindow`, set the main layout using `self.setLayout(layout_object)` rather than directly assigning to `self.layout`. Ensure `addWidget` and `addLayout` calls are made on the correct layout object.
    *   **`QComboBox` Item Access:** When accessing items from `QComboBox` models (e.g., `self.device_combo.model().item(index)`), always check if the returned item is `None` before attempting to call methods on it. If `pyright` still complains about attribute access on `QStandardItem`, use `# type: ignore` for that specific line.
    *   **`sounddevice` Device Information:** When working with `sounddevice.query_devices()`, explicitly cast the returned dictionaries to a `TypedDict` (e.g., `DeviceInfo`) using `typing.cast` to provide better type information to `pyright`.
    *   **Handling `None` from `psutil`:** When using `psutil` functions that might return `None` (e.g., `psutil.cpu_count()`), always check for `None` and provide a default value or handle the `None` case explicitly before performing operations like comparisons.
*   **`subprocess` Module:** Always ensure `import subprocess` is present at the top of any file that uses the `subprocess` module to avoid `possibly unbound variable` errors.

## Princípios de Design e Depuração

As seguintes lições foram aprendidas durante o desenvolvimento e devem ser aplicadas a projetos futuros para garantir a robustez e a manutenibilidade do código.

*   **Evite Limiares Estáticos; Use Adaptação Dinâmica:**
    *   **Problema:** Usar valores fixos e "mágicos" (ex: um limiar de silêncio de -40 dBFS) torna o sistema frágil, pois ele falha quando os dados do mundo real não correspondem ao cenário ideal.
    *   **Solução:** Projete sistemas que se adaptam aos dados. Em vez de um limiar estático, calcule um limiar dinâmico com base nas características do próprio dado (ex: `limiar_de_silencio = volume_medio_do_arquivo + margem`). Isso torna o algoritmo resiliente a diferentes condições de entrada (ex: áudio limpo vs. ruidoso).

*   **Tornar o Invisível, Visível (Telemetria é Essencial):**
    *   **Problema:** É impossível depurar um sistema "caixa-preta" cujo estado interno é desconhecido.
    *   **Solução:** Adicione logs e mensagens de status que exponham os valores internos críticos que influenciam o comportamento do algoritmo (ex: "Usando limiar dinâmico de -35.4dBFS baseado em piso de ruído de -39.4dBFS"). Sem telemetria, a depuração é um jogo de adivinhação.

*   **Considere os Efeitos em Cascata das Transformações:**
    *   **Problema:** Uma transformação nos dados (ex: acelerar um áudio) pode ter efeitos secundários inesperados em parâmetros que parecem não relacionados (ex: a duração das pausas de silêncio).
    *   **Solução:** Ao aplicar uma transformação, revise todos os parâmetros e lógicas que consomem esses dados e ajuste-os conforme necessário. A lógica deve ser ciente das transformações aplicadas (ex: `duracao_minima_silencio_ajustada = duracao_original / fator_de_aceleracao`).

*   **Prefira Agregar a Descartar:**
    *   **Problema:** Descartar dados que não atendem a um critério rígido (ex: segmentos de áudio com menos de 500ms) pode levar a falhas em cascata, onde nenhum dado é processado.
    *   **Solução:** Em vez de descartar, implemente uma lógica de agregação. Combine pequenos pedaços de dados válidos até que eles formem uma unidade de trabalho maior e ideal. Isso preserva a informação e torna o sistema mais eficiente.
