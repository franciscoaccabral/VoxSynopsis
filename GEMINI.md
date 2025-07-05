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
*   **Type Hinting and `pyright`:**
    *   **Initialize Variables:** Always initialize variables that might be conditionally assigned (e.g., `model = None`) to avoid `possibly unbound variable` errors.
    *   **PyQt5 Method Overrides:** When overriding PyQt5 methods (e.g., `closeEvent`), if `pyright` reports `incompatible method override` errors despite correct signature, consider adding `# type: ignore` to the method definition as a last resort.
    *   **Layout Management in PyQt5:** For `QDialog` and `QMainWindow`, set the main layout using `self.setLayout(layout_object)` rather than directly assigning to `self.layout`. Ensure `addWidget` and `addLayout` calls are made on the correct layout object.
    *   **`QComboBox` Item Access:** When accessing items from `QComboBox` models (e.g., `self.device_combo.model().item(index)`), always check if the returned item is `None` before attempting to call methods on it. If `pyright` still complains about attribute access on `QStandardItem`, use `# type: ignore` for that specific line.
    *   **`sounddevice` Device Information:** When working with `sounddevice.query_devices()`, explicitly cast the returned dictionaries to a `TypedDict` (e.g., `DeviceInfo`) using `typing.cast` to provide better type information to `pyright`.
    *   **Handling `None` from `psutil`:** When using `psutil` functions that might return `None` (e.g., `psutil.cpu_count()`), always check for `None` and provide a default value or handle the `None` case explicitly before performing operations like comparisons.
*   **`subprocess` Module:** Always ensure `import subprocess` is present at the top of any file that uses the `subprocess` module to avoid `possibly unbound variable` errors.

## Documentação do Projeto e Modificações de Código

Este projeto utiliza uma estrutura de documentação localizada na pasta `docs/`. O arquivo `docs/index.md` serve como ponto de entrada para a documentação técnica detalhada de cada arquivo fonte principal.

**Antes de realizar qualquer modificação em um arquivo fonte (arquivos `.py`, `.qss`, etc.):**

1.  **Consulte a Documentação Existente:** Navegue até `docs/index.md` e localize o link para o arquivo de documentação específico do fonte que você pretende alterar (ex: `docs/vox_synopsis_fast_whisper.md` para `vox_synopsis_fast_whisper.py`).
2.  **Analise o Conteúdo:** Leia atentamente a documentação do arquivo para entender sua finalidade, a lógica das suas classes/funções, os parâmetros esperados, os retornos e os possíveis efeitos colaterais. Utilize esta informação para guiar o planejamento da sua alteração.

**Após implementar modificações no código fonte:**

1.  **Atualize a Documentação Correspondente:** Se as suas alterações impactarem o funcionamento, a interface (parâmetros, retornos), ou a estrutura de qualquer classe ou função documentada, você **DEVE** atualizar o arquivo de documentação `.md` correspondente na pasta `docs/`.
2.  **Seja Específico:** As atualizações devem refletir claramente as mudanças. Por exemplo:
    *   Adicionou um novo parâmetro a uma função? Documente-o.
    *   Alterou o tipo de retorno? Atualize a descrição do retorno.
    *   Modificou a lógica interna de forma significativa que afeta como o componente deve ser entendido ou usado? Explique a mudança.
    *   Adicionou uma nova função ou classe? Crie a seção de documentação para ela.
3.  **Consistência:** Mantenha o estilo e o nível de detalhe da documentação existente.

Manter a documentação sincronizada com o código é crucial para a manutenibilidade do projeto e para a eficiência de futuros desenvolvimentos, especialmente ao colaborar com outros desenvolvedores ou agentes de IA.
