# Sistema de Validação de Dependências - VoxSynopsis

## Visão Geral

O VoxSynopsis implementa um sistema robusto de validação de dependências que verifica automaticamente se todos os componentes críticos estão instalados antes de iniciar a aplicação principal. Este sistema melhora significativamente a experiência do usuário ao fornecer diagnósticos claros e instruções específicas por sistema operacional.

## Arquitetura do Sistema

### Componentes Principais

#### 1. `core/dependency_checker.py`
**Módulo de verificação técnica responsável pela detecção e validação de dependências.**

```python
class DependencyChecker:
    - check_ffmpeg() -> DependencyResult
    - check_python_dependencies() -> List[DependencyResult]
    - check_audio_system() -> DependencyResult
    - run_full_check() -> Dict[str, DependencyResult]
```

**Funcionalidades:**
- **Detecção de SO**: Identificação automática de Linux, Windows, macOS
- **Verificação de FFmpeg**: Teste de instalação e versão via comando `ffmpeg -version`
- **Validação de Python**: Verificação de importação de bibliotecas críticas
- **Sistema de áudio**: Teste de funcionalidade do PortAudio/sounddevice
- **Instruções contextuais**: Comandos de instalação específicos por plataforma

#### 2. `core/dependency_dialog.py`
**Interface gráfica para apresentação visual dos resultados de validação.**

```python
class DependencyValidationDialog(QDialog):
    - Exibição visual do status de cada dependência
    - Instruções de instalação dinâmicas
    - Controles de usuário (Retry, Continue, Exit)
    - Thread assíncrono para validação não-bloqueante
```

**Características da Interface:**
- **Layout responsivo**: Split view com dependências e instruções
- **Indicadores visuais**: ✅ (OK), ❌ (Missing), ⚠️ (Error)
- **Instruções dinâmicas**: HTML formatado com comandos específicos
- **Progresso em tempo real**: Barra de progresso e status updates

#### 3. `core/main.py` (Integração)
**Entry point modificado para incluir validação obrigatória.**

```python
def main(skip_validation: bool = False):
    # 1. Criar QApplication
    # 2. Executar validação (se não pulada)
    # 3. Continuar para aplicação principal
    # 4. Tratamento robusto de erros
```

## Dependências Verificadas

### Críticas (Obrigatórias)
- **FFmpeg**: Extração de áudio de vídeos MP4
- **PyQt5**: Framework de interface gráfica
- **sounddevice**: Captura de áudio em tempo real
- **faster-whisper**: Engine de transcrição otimizada

### Importantes (Recomendadas)
- **torch**: Backend de machine learning
- **numpy**: Processamento numérico
- **psutil**: Monitoramento de recursos do sistema

### Sistema
- **Audio System**: Verificação de PortAudio e dispositivos disponíveis

## Instruções por Sistema Operacional

### Linux (Ubuntu/Debian)
```bash
# FFmpeg
sudo apt update && sudo apt install ffmpeg

# PortAudio
sudo apt install libportaudio2 portaudio19-dev

# Python dependencies
pip install PyQt5 sounddevice faster-whisper torch numpy psutil
```

### Linux (Fedora/CentOS)
```bash
# FFmpeg
sudo dnf install ffmpeg

# PortAudio
sudo dnf install portaudio-devel

# Python dependencies
pip install PyQt5 sounddevice faster-whisper torch numpy psutil
```

### macOS
```bash
# FFmpeg (via Homebrew)
brew install ffmpeg

# Python dependencies
pip install PyQt5 sounddevice faster-whisper torch numpy psutil
```

### Windows
```powershell
# FFmpeg (via Chocolatey)
choco install ffmpeg

# Ou baixar manualmente e adicionar ao PATH
# Python dependencies
pip install PyQt5 sounddevice faster-whisper torch numpy psutil
```

## Fluxo de Execução

### 1. Inicialização
```mermaid
graph TD
    A[Iniciar VoxSynopsis] --> B{--skip-validation?}
    B -->|Sim| F[Carregar App Principal]
    B -->|Não| C[Executar Validação]
    C --> D{Todas dependências OK?}
    D -->|Sim| F
    D -->|Não| E[Mostrar Dialog de Validação]
    E --> G{Usuário escolhe?}
    G -->|Continue| F
    G -->|Retry| C
    G -->|Exit| H[Sair]
```

### 2. Processo de Validação
```mermaid
sequenceDiagram
    participant U as Usuário
    participant M as Main
    participant D as Dialog
    participant C as Checker
    participant T as Thread
    
    U->>M: python3 vox_synopsis_fast_whisper.py
    M->>D: run_dependency_validation()
    D->>T: start_validation()
    T->>C: run_full_check()
    C->>T: results
    T->>D: check_completed.emit(results)
    D->>U: Mostrar status e instruções
    U->>D: Continue/Retry/Exit
    D->>M: return success/failure
```

## Estados de Dependência

### DependencyStatus Enum
- **OK**: ✅ Dependência instalada e funcionando corretamente
- **MISSING**: ❌ Dependência não encontrada/não instalada
- **ERROR**: ⚠️ Dependência instalada mas com problemas
- **OUTDATED**: 📅 Versão desatualizada (funcionalidade futura)

### DependencyResult DataClass
```python
@dataclass
class DependencyResult:
    name: str                                    # Nome da dependência
    status: DependencyStatus                     # Status atual
    version: Optional[str] = None                # Versão detectada
    error_message: Optional[str] = None          # Mensagem de erro
    install_instructions: Optional[str] = None   # Instruções de instalação
```

## Funcionalidades Avançadas

### 1. Modo de Desenvolvimento
```bash
# Pular validação para desenvolvimento/debug
python3 vox_synopsis_fast_whisper.py --skip-validation
```

### 2. Detecção Inteligente de Distribuição
O sistema detecta automaticamente a distribuição Linux e fornece comandos específicos:
- Ubuntu/Debian: `apt`
- Fedora/CentOS: `dnf`/`yum`
- Arch Linux: `pacman`

### 3. Tratamento Robusto de Erros
- **Timeout protection**: Comandos com timeout de 10 segundos
- **Graceful degradation**: Continuar mesmo com falhas parciais
- **Fallback instructions**: Instruções genéricas se detecção específica falhar

### 4. Interface Responsiva
- **Threading assíncrono**: Validação não bloqueia interface
- **Progress feedback**: Indicadores visuais de progresso
- **Split layout**: Dependências e instruções lado a lado

## Benefícios Implementados

### Para o Usuário
- **Diagnóstico claro**: Saber exatamente o que está faltando
- **Instruções específicas**: Comandos corretos para seu sistema operacional
- **Menos frustração**: Evita erros crípticos durante execução
- **Onboarding facilitado**: Setup inicial mais simples

### Para Suporte Técnico
- **Diagnóstico padronizado**: Interface consistente para troubleshooting
- **Instruções automáticas**: Reduz necessidade de suporte manual
- **Logs estruturados**: Output claro para debug

### Para Desenvolvimento
- **Modo bypass**: Flag `--skip-validation` para desenvolvimento
- **Detecção precoce**: Problemas identificados antes da execução principal
- **Modularidade**: Sistema independente e reutilizável

## Estrutura de Arquivos

```
VoxSynopsis/
├── core/
│   ├── dependency_checker.py      # Lógica de verificação
│   ├── dependency_dialog.py       # Interface de validação
│   └── main.py                    # Integração com entry point
├── docs/
│   └── Dependency_Validation_System.md  # Esta documentação
└── vox_synopsis_fast_whisper.py   # Wrapper compatível
```

## Exemplo de Uso

### Cenário 1: Primeira Instalação
```bash
$ python3 vox_synopsis_fast_whisper.py
🔍 Validating system dependencies...

# Dialog aparece mostrando:
❌ FFmpeg          - Not found in PATH
✅ PyQt5           - v5.15.9
❌ sounddevice     - Import failed
✅ numpy           - v1.24.3
⚠️ Audio System    - No devices found

# Instruções específicas aparecem no painel direito
```

### Cenário 2: Sistema Completo
```bash
$ python3 vox_synopsis_fast_whisper.py
🔍 Validating system dependencies...
✅ Dependency validation completed
🚀 Initializing VoxSynopsis with performance optimizations...
🎉 VoxSynopsis started successfully!
```

### Cenário 3: Modo Desenvolvimento
```bash
$ python3 vox_synopsis_fast_whisper.py --skip-validation
⚠️ Skipping dependency validation (development mode)
🚀 Initializing VoxSynopsis with performance optimizations...
```

## Extensibilidade

### Adicionar Nova Dependência
```python
# Em dependency_checker.py
def check_new_dependency(self) -> DependencyResult:
    try:
        import new_dependency
        return DependencyResult(
            name="New Dependency",
            status=DependencyStatus.OK,
            version=new_dependency.__version__
        )
    except ImportError:
        return DependencyResult(
            name="New Dependency",
            status=DependencyStatus.MISSING,
            install_instructions="pip install new_dependency"
        )

# Em run_full_check()
results["new_dependency"] = self.check_new_dependency()
```

### Customizar Instruções
```python
def _get_custom_instructions(self, dep_name: str) -> str:
    system = self.os_info["system"]
    
    instructions = {
        "linux": "sudo apt install package",
        "darwin": "brew install package", 
        "windows": "choco install package"
    }
    
    return instructions.get(system, "Generic instructions")
```

## Considerações Técnicas

### Performance
- **Lazy loading**: Dependências carregadas apenas quando necessário
- **Parallel checking**: Verificações podem ser paralelizadas no futuro
- **Caching**: Resultados podem ser cached para sessões subsequentes

### Segurança
- **Command injection protection**: Uso de subprocess.run com arrays
- **Timeout protection**: Prevenção de comandos travados
- **Error handling**: Tratamento seguro de exceções

### Compatibilidade
- **Cross-platform**: Testado em Linux, macOS e Windows
- **Version agnostic**: Funciona com diferentes versões de Python
- **Graceful degradation**: Funciona mesmo com dependências parciais

## Conclusão

O Sistema de Validação de Dependências do VoxSynopsis representa uma melhoria significativa na experiência do usuário, fornecendo diagnósticos claros, instruções específicas por plataforma e uma interface intuitiva para resolução de problemas de configuração. O sistema é robusto, extensível e mantém a compatibilidade com workflows de desenvolvimento existentes.