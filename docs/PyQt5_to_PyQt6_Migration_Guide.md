# Guia de Migração PyQt5 → PyQt6 - VoxSynopsis

**Data de Criação:** Janeiro 2025  
**Status:** 📋 PLANEJAMENTO  
**Versão:** 1.0  
**Autor:** Gemini Pro Analysis  

## 📊 Resumo Executivo

Este documento especifica o processo completo de migração do VoxSynopsis de **PyQt5** para **PyQt6**, incluindo análise de impacto, estratégias de migração, breaking changes específicos do projeto e plano de validação.

### 🎯 Objetivos da Migração
- **Modernização:** Atualizar para a versão mais recente do Qt framework
- **Performance:** Aproveitar melhorias de performance do Qt6
- **Segurança:** Beneficiar de correções de segurança mais recentes
- **Suporte Long-term:** Garantir suporte contínuo (PyQt5 está em manutenção)
- **Compatibilidade:** Preparar para futuras dependências que exigem Qt6

### ⚠️ **Complexidade Estimada: MÉDIA-ALTA (6-10 horas)**

---

## 🔍 Análise de Impacto no Projeto

### Arquivos Afetados pela Migração

#### 1. Arquivos Python com Imports PyQt5 (9 arquivos)
```
core/main.py                    - QApplication
core/main_window.py            - QTimer, QCloseEvent, QCursor, QApplication, QFileDialog, QMainWindow, QMessageBox  
core/recording.py              - QThread, pyqtSignal
core/transcription.py          - QThread, pyqtSignal
core/batch_transcription.py    - QThread, pyqtSignal
core/audio_preprocessing.py    - QThread, pyqtSignal
core/settings_dialog.py        - Qt, QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, etc.
ui_vox_synopsis.py             - Múltiplos widgets (QMainWindow, QWidget, QVBoxLayout, etc.)
Tests/test_settings_dialog.py  - QApplication (para testes)
```

#### 2. Dependências no requirements.txt
```diff
- PyQt5
+ PyQt6==6.7.0
+ pyqt6-stubs==6.7.0.0  # Para type hinting
```

### 3. Uso Específico do PyQt5 no Projeto

#### Threading (Alto Impacto)
- **QThread e pyqtSignal:** Usado extensivamente em 4 módulos core
- **Padrão atual:** `QThread` com `pyqtSignal` para comunicação entre threads
- **Impacto:** Compatibilidade mantida, mas sintaxe de enums pode mudar

#### Widgets da Interface (Alto Impacto)
- **ui_vox_synopsis.py:** Define toda a estrutura da interface
- **Widgets usados:** QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QComboBox, QCheckBox, QTextEdit, QProgressBar
- **Impacto:** Principalmente imports e enums Qt.*

#### Dialogs e Eventos (Médio Impacto)
- **QFileDialog, QMessageBox:** Para seleção de arquivos e mensagens
- **QCloseEvent:** Para handling de fechamento da aplicação
- **Impacto:** Sintaxe de enums e alguns métodos podem mudar

---

## 🚧 Breaking Changes Específicos do Projeto

### 1. Enums Qt.* → Qt.*Flag (CRÍTICO)

#### Antes (PyQt5):
```python
# core/settings_dialog.py
Qt.AlignCenter
Qt.Checked
Qt.Unchecked
```

#### Depois (PyQt6):
```python
Qt.AlignmentFlag.AlignCenter
Qt.CheckState.Checked  
Qt.CheckState.Unchecked
```

### 2. Métodos Descontinuados

#### QDialog.exec_() → QDialog.exec()
```python
# Localização provável: core/settings_dialog.py
# Antes (PyQt5):
dialog.exec_()

# Depois (PyQt6):
dialog.exec()
```

### 3. Imports Reorganizados

#### Estrutura de Submódulos
```python
# Imports permanecem os mesmos, mas verificação necessária:
from PyQt6.QtWidgets import QApplication  # ✓ Mantido
from PyQt6.QtCore import QThread, pyqtSignal  # ✓ Mantido  
from PyQt6.QtGui import QCloseEvent, QCursor  # ✓ Mantido
```

### 4. High DPI Scaling (ATENÇÃO)

#### Comportamento Mudou:
- **PyQt5:** Scaling manual necessário
- **PyQt6:** High DPI scaling é padrão
- **Impacto:** Interface pode aparecer diferente em telas 4K/high DPI

---

## 📋 Plano de Migração Detalhado

### **Fase 1: Preparação e Backup (30 min)**

#### 1.1 Criar Branch de Migração
```bash
git checkout -b pyqt6-migration
git push -u origin pyqt6-migration
```

#### 1.2 Backup Completo
```bash
# Criar tag do estado atual
git tag pyqt5-stable
git push origin pyqt5-stable
```

#### 1.3 Documentar Estado Atual
```bash
# Testar aplicação atual para baseline
python vox_synopsis_fast_whisper.py
# Documentar funcionalidades que funcionam
```

### **Fase 2: Atualização de Dependências (20 min)**

#### 2.1 Atualizar requirements.txt
```diff
- PyQt5
+ PyQt6==6.7.0
+ pyqt6-stubs==6.7.0.0
```

#### 2.2 Criar Novo Ambiente Virtual
```bash
# Backup do ambiente atual
pip freeze > requirements_pyqt5_backup.txt

# Novo ambiente
python -m venv venv_pyqt6
source venv_pyqt6/bin/activate  # Linux/Mac
# ou
venv_pyqt6\Scripts\activate  # Windows

pip install -r requirements.txt
```

### **Fase 3: Migração Automática de Imports (30 min)**

#### 3.1 Script de Substituição Global
```bash
# Substituir todos os imports PyQt5 → PyQt6
find . -name "*.py" -type f -exec sed -i 's/from PyQt5/from PyQt6/g' {} \;
find . -name "*.py" -type f -exec sed -i 's/import PyQt5/import PyQt6/g' {} \;
```

#### 3.2 Verificação Manual dos Imports
```bash
# Verificar se todas as substituições foram corretas
grep -r "PyQt" . --include="*.py"
```

### **Fase 4: Correção de Breaking Changes (2-3 horas)**

#### 4.1 Correção de Enums Qt.* (1-2 horas)

**Arquivos prioritários:**
- `core/settings_dialog.py`
- `ui_vox_synopsis.py` 
- `core/main_window.py`

**Estratégia:**
1. Executar aplicação e capturar erros
2. Corrigir enums um por vez baseado nos erros
3. Usar pattern matching para identificar todos os usos

**Principais substituições esperadas:**
```python
# Alinhamentos
Qt.AlignCenter → Qt.AlignmentFlag.AlignCenter
Qt.AlignLeft → Qt.AlignmentFlag.AlignLeft
Qt.AlignRight → Qt.AlignmentFlag.AlignRight

# Estados de checkbox  
Qt.Checked → Qt.CheckState.Checked
Qt.Unchecked → Qt.CheckState.Unchecked

# Orientações
Qt.Horizontal → Qt.Orientation.Horizontal
Qt.Vertical → Qt.Orientation.Vertical
```

#### 4.2 Correção de Métodos Descontinuados (30 min)

**Buscar e substituir:**
```bash
# Encontrar usos de exec_()
grep -r "exec_()" . --include="*.py"

# Substituir manualmente cada ocorrência
# .exec_() → .exec()
```

#### 4.3 Correção de APIs Quebradas (1 hora)

**QAction (se usado):**
```python
# Verificar se QAction é usado
grep -r "QAction" . --include="*.py"

# PyQt5 → PyQt6: construtor mudou
# action = QAction("text", parent) → action = QAction("text")
# action.setParent(parent)
```

### **Fase 5: Testes e Validação (2-3 horas)**

#### 5.1 Teste de Inicialização (30 min)
```bash
# Testar se aplicação inicia sem erros
python vox_synopsis_fast_whisper.py
```

#### 5.2 Teste de Funcionalidades Core (1 hora)
- [ ] **Gravação de áudio:** Testar botão record/stop
- [ ] **Seleção de dispositivo:** Dropdown de dispositivos funcional
- [ ] **Configurações:** Dialog de settings abre e salva
- [ ] **Transcription:** Processar arquivo de teste
- [ ] **Batch processing:** Múltiplos arquivos

#### 5.3 Teste de Interface (1 hora)
- [ ] **Layout:** Todos os widgets visíveis e posicionados corretamente
- [ ] **Responsividade:** Redimensionamento da janela
- [ ] **High DPI:** Testar em tela 4K se disponível
- [ ] **Styling:** CSS aplicado corretamente
- [ ] **Threading:** Progress bars e status updates funcionando

#### 5.4 Teste de Compatibilidade (30 min)
- [ ] **Windows:** Teste em sistema Windows
- [ ] **Linux:** Teste em sistema Linux  
- [ ] **macOS:** Teste em sistema macOS (se disponível)

### **Fase 6: Otimização e Ajustes Finais (1-2 horas)**

#### 6.1 Ajustes de High DPI
```python
# Se necessário, em core/main.py
app = QApplication(sys.argv)
app.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)
```

#### 6.2 Performance Testing
- Comparar tempos de inicialização PyQt5 vs PyQt6
- Verificar uso de memória
- Testar responsividade da interface

#### 6.3 Code Quality
```bash
# Linting
ruff check .
ruff format .

# Type checking
pyright
```

---

## 🛡️ Estratégias de Fallback

### 1. Rollback Rápido
```bash
# Se migração falhar criticamente
git checkout pyqt5-stable
pip install -r requirements_pyqt5_backup.txt
```

### 2. Migração Gradual (Alternativa)
- **Opção:** Criar wrapper de compatibilidade
- **Tempo:** +2 horas de desenvolvimento
- **Benefício:** Permite rollback instantâneo

```python
# compatibility_layer.py
try:
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication
    PYQT_VERSION = 6
except ImportError:
    from PyQt5.QtCore import Qt  # type: ignore
    from PyQt5.QtWidgets import QApplication  # type: ignore
    PYQT_VERSION = 5

# Enum compatibility
if PYQT_VERSION == 6:
    AlignCenter = Qt.AlignmentFlag.AlignCenter
else:
    AlignCenter = Qt.AlignCenter
```

### 3. Testing Paralelo
- **Manter dois environments:** `venv_pyqt5` e `venv_pyqt6`
- **Testes A/B:** Comparar funcionalidades lado a lado
- **CI/CD:** Configurar pipelines para ambas as versões temporariamente

---

## ✅ Checklist de Validação

### **Pré-Migração**
- [ ] Backup completo realizado
- [ ] Ambiente PyQt5 documentado e funcional
- [ ] Branch pyqt6-migration criada
- [ ] Requirements backup criado

### **Durante Migração**
- [ ] Imports PyQt5→PyQt6 atualizados
- [ ] Dependencies atualizadas no requirements.txt
- [ ] Novo ambiente virtual criado e testado
- [ ] Aplicação inicia sem import errors

### **Correções de Breaking Changes**
- [ ] Enums Qt.* corrigidos
- [ ] Métodos .exec_() → .exec() corrigidos
- [ ] APIs quebradas identificadas e corrigidas
- [ ] High DPI handling verificado

### **Testes Funcionais**
- [ ] **Core Features:**
  - [ ] Gravação de áudio funcional
  - [ ] Transcription sequencial funcional
  - [ ] Batch transcription funcional
  - [ ] Settings dialog funcional
- [ ] **Interface:**
  - [ ] Layout preservado
  - [ ] Styling (CSS) aplicado
  - [ ] Threading e progress updates funcionando
  - [ ] Responsividade mantida

### **Qualidade de Código**
- [ ] Ruff linting passa sem erros
- [ ] Pyright type checking passa
- [ ] Testes unitários passando (se existirem)
- [ ] Performance comparável ao PyQt5

### **Cross-Platform**
- [ ] Windows testado
- [ ] Linux testado  
- [ ] macOS testado (se disponível)

### **Pós-Migração**
- [ ] Documentação atualizada
- [ ] Changelog criado
- [ ] Pull request criado
- [ ] Tag de release planejada

---

## ⏱️ Estimativas de Tempo Realistas

### **Cenário Optimista (6 horas)**
- Desenvolvedor experiente com PyQt
- Poucos breaking changes encontrados
- Testes básicos passam rapidamente
- Sem problemas de compatibilidade específicos

### **Cenário Realista (8 horas)**
- Alguns enums e APIs precisam de correção manual
- Testes revelam 2-3 problemas de interface
- Uma sessão de debugging para High DPI
- Validação completa em uma plataforma

### **Cenário Pessimista (10+ horas)**
- Múltiplos breaking changes não documentados
- Problemas específicos de threading ou performance
- Necessidade de fallback ou compatibility layer
- Testes em múltiplas plataformas revelam problemas

### **Distribuição por Fase:**
```
Preparação:           30 min  (5%)
Dependencies:         20 min  (4%)  
Import migration:     30 min  (6%)
Breaking changes:   2-3 horas (35%)
Testing:           2-3 horas (35%)
Optimization:      1-2 horas (15%)
```

---

## 📚 Recursos e Referências

### **Documentação Oficial**
- [PyQt6 Migration Guide](https://www.riverbankcomputing.com/static/Docs/PyQt6/pyqt5_differences.html)
- [Qt6 Breaking Changes](https://doc.qt.io/qt-6/sourcebreaks.html)
- [PyQt6 Reference](https://www.riverbankcomputing.com/static/Docs/PyQt6/)

### **Ferramentas Úteis**
- **qt5to6:** Ferramenta oficial de migração Qt
- **grep/sed:** Para substituições em massa
- **diff:** Para comparar resultados antes/depois

### **Testing**
```bash
# Comandos úteis durante migração
python -c "import PyQt6; print('PyQt6 installed successfully')"
python -c "from PyQt6.QtWidgets import QApplication; print('Widgets available')"
python vox_synopsis_fast_whisper.py --test-mode  # Se implementado
```

---

## 🚨 Riscos e Mitigações

### **Riscos Identificados**

#### 1. **Alto:** Breaking changes não documentados
- **Mitigação:** Testes incrementais e rollback preparado
- **Tempo extra:** +2 horas

#### 2. **Médio:** Performance degradation
- **Mitigação:** Benchmarks antes/depois
- **Tempo extra:** +1 hora

#### 3. **Médio:** Platform-specific issues
- **Mitigação:** Testes em múltiplas plataformas
- **Tempo extra:** +1-2 horas

#### 4. **Baixo:** Dependencies conflicts
- **Mitigação:** Ambiente virtual isolado
- **Tempo extra:** +30 min

### **Plano de Contingência**
1. **Primeiro sinal de problemas:** Documentar e continuar
2. **Problemas bloqueantes:** Ativar fallback strategy
3. **Falha crítica:** Rollback para PyQt5-stable tag

---

## 📈 Benefícios Esperados da Migração

### **Imediatos**
- **Segurança:** Patches de segurança mais recentes
- **Suporte:** Acesso ao suporte ativo da comunidade
- **Dependencies:** Compatibilidade com libs que migraram para Qt6

### **Médio Prazo**
- **Performance:** Melhorias incrementais do Qt6
- **Features:** Acesso a novas funcionalidades do framework
- **Ecosystem:** Melhor integração com ferramentas modernas

### **Longo Prazo**  
- **Sustainability:** PyQt5 entrará em End-of-Life
- **Innovation:** Possibilidade de usar Qt6-specific features
- **Recruiting:** Desenvolvedores preferem tecnologias atuais

---

## 🏁 Conclusão

A migração PyQt5→PyQt6 do VoxSynopsis é **viável e recomendada**, com complexidade média-alta mas benefícios significativos. O plano detalhado acima minimiza riscos através de:

1. **Preparação cuidadosa** com backups e branches
2. **Migração incremental** com validação em cada etapa  
3. **Estratégias de fallback** para cenários problemáticos
4. **Validação abrangente** cobrindo funcionalidade e qualidade

**Próximo passo recomendado:** Iniciar com Fase 1 (Preparação) e executar cada fase sequencialmente, documentando problemas encontrados para futuras migrações.