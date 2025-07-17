#!/usr/bin/env python3
"""
Script para testar disponibilidade e funcionalidade do CUDA
"""

import sys
import subprocess
import os

def test_nvidia_driver():
    """Testa se o driver NVIDIA está instalado"""
    print("=== Testando Driver NVIDIA ===")
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Driver NVIDIA detectado")
            print(result.stdout)
            return True
        else:
            print("✗ Driver NVIDIA não encontrado")
            return False
    except FileNotFoundError:
        print("✗ nvidia-smi não encontrado")
        return False

def test_cuda_runtime():
    """Testa CUDA runtime"""
    print("\n=== Testando CUDA Runtime ===")
    try:
        result = subprocess.run(['nvcc', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ CUDA Toolkit detectado")
            print(result.stdout)
            return True
        else:
            print("✗ CUDA Toolkit não encontrado")
            return False
    except FileNotFoundError:
        print("✗ nvcc não encontrado")
        return False

def test_pytorch_cuda():
    """Testa PyTorch com CUDA"""
    print("\n=== Testando PyTorch CUDA ===")
    try:
        import torch
        
        print(f"PyTorch versão: {torch.__version__}")
        
        if torch.cuda.is_available():
            print("✓ CUDA disponível no PyTorch")
            print(f"Dispositivos CUDA: {torch.cuda.device_count()}")
            print(f"Dispositivo atual: {torch.cuda.current_device()}")
            print(f"Nome do dispositivo: {torch.cuda.get_device_name()}")
            print(f"Capacidade CUDA: {torch.cuda.get_device_capability()}")
            
            # Teste básico de operação
            x = torch.rand(3, 3).cuda()
            y = torch.rand(3, 3).cuda()
            z = x + y
            print("✓ Operação básica CUDA funcionando")
            
            return True
        else:
            print("✗ CUDA não disponível no PyTorch")
            return False
            
    except ImportError:
        print("✗ PyTorch não instalado")
        return False
    except Exception as e:
        print(f"✗ Erro ao testar PyTorch CUDA: {e}")
        return False

def test_faster_whisper_cuda():
    """Testa faster-whisper com CUDA"""
    print("\n=== Testando faster-whisper CUDA ===")
    try:
        from faster_whisper import WhisperModel
        
        print("✓ faster-whisper importado com sucesso")
        
        # Tenta criar modelo com CUDA usando int8 (compatível com GTX 1050 Ti)
        try:
            model = WhisperModel("tiny", device="cuda", compute_type="int8")
            print("✓ Modelo faster-whisper criado com CUDA")
            
            # Cleanup
            del model
            return True
            
        except Exception as e:
            print(f"✗ Erro ao criar modelo CUDA: {e}")
            
            # Tenta com CPU como fallback
            try:
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                print("✓ Modelo faster-whisper criado com CPU (fallback)")
                del model
                return False
            except Exception as e2:
                print(f"✗ Erro também com CPU: {e2}")
                return False
                
    except ImportError:
        print("✗ faster-whisper não instalado")
        return False

def test_environment_variables():
    """Verifica variáveis de ambiente CUDA"""
    print("\n=== Variáveis de Ambiente CUDA ===")
    
    cuda_vars = [
        'CUDA_HOME',
        'CUDA_PATH',
        'CUDA_ROOT',
        'CUDA_VISIBLE_DEVICES',
        'NVIDIA_VISIBLE_DEVICES'
    ]
    
    for var in cuda_vars:
        value = os.environ.get(var)
        if value:
            print(f"✓ {var} = {value}")
        else:
            print(f"- {var} não definida")

def main():
    """Executa todos os testes"""
    print("🔍 Testando disponibilidade e funcionalidade do CUDA")
    print("=" * 60)
    
    results = []
    
    # Testes individuais
    results.append(("Driver NVIDIA", test_nvidia_driver()))
    results.append(("CUDA Runtime", test_cuda_runtime()))
    results.append(("PyTorch CUDA", test_pytorch_cuda()))
    results.append(("faster-whisper CUDA", test_faster_whisper_cuda()))
    
    # Variáveis de ambiente
    test_environment_variables()
    
    # Resumo
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    cuda_available = True
    for test_name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name:<25} {status}")
        if not result and test_name in ["Driver NVIDIA", "PyTorch CUDA"]:
            cuda_available = False
    
    print("\n" + "=" * 60)
    if cuda_available and results[2][1]:  # PyTorch CUDA passou
        print("🎉 CUDA está funcionando corretamente!")
        print("💡 Pode usar device='cuda' nas configurações do VoxSynopsis")
    else:
        print("⚠️  CUDA não está totalmente funcional")
        print("💡 Use device='cpu' nas configurações do VoxSynopsis")
    
    print("=" * 60)

if __name__ == "__main__":
    main()