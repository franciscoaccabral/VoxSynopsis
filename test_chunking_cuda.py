#!/usr/bin/env python3
"""
Script para testar performance da criação de chunks com CUDA
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, '/home/franc/VoxSynopsis')

def create_test_audio():
    """Cria um arquivo de áudio de teste"""
    test_file = "/tmp/test_audio_long.wav"
    
    print("🎵 Criando arquivo de áudio de teste (60 segundos)...")
    
    # Cria um arquivo de áudio de teste com 60 segundos
    cmd = [
        "ffmpeg", "-f", "lavfi", "-i", "sine=frequency=440:duration=60",
        "-c:a", "pcm_s16le", "-ar", "16000", "-ac", "1",
        test_file, "-y"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Arquivo criado: {test_file}")
        return test_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar arquivo: {e}")
        return None

def test_chunking_performance():
    """Testa performance de chunking CUDA vs CPU"""
    
    from core.ffmpeg_cuda import ffmpeg_cuda_optimizer
    
    # Cria arquivo de teste
    test_file = create_test_audio()
    if not test_file:
        return
    
    print("\n🔍 Testando performance de chunking CUDA vs CPU...")
    
    # Configurações do teste
    chunk_duration = 10  # 10 segundos por chunk
    total_chunks = 6  # 6 chunks de 10s = 60s total
    
    # Teste 1: Chunking com CUDA
    print("\n📊 Teste 1: Chunking com CUDA")
    cuda_chunks = []
    
    start_time = time.time()
    for i in range(total_chunks):
        start_pos = i * chunk_duration
        output_file = f"/tmp/chunk_cuda_{i:03d}.wav"
        
        cmd = ffmpeg_cuda_optimizer.optimize_audio_chunking_cmd(
            test_file, output_file, start_pos, chunk_duration, 
            sample_rate=16000, channels=1
        )
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            cuda_chunks.append(output_file)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erro no chunk {i}: {e}")
    
    cuda_time = time.time() - start_time
    print(f"  ✅ CUDA: {cuda_time:.2f}s ({len(cuda_chunks)} chunks criados)")
    
    # Teste 2: Chunking com CPU (método tradicional)
    print("\n📊 Teste 2: Chunking com CPU")
    cpu_chunks = []
    
    start_time = time.time()
    for i in range(total_chunks):
        start_pos = i * chunk_duration
        output_file = f"/tmp/chunk_cpu_{i:03d}.wav"
        
        cmd = [
            "ffmpeg", "-threads", "0", "-i", test_file,
            "-ss", str(start_pos), "-t", str(chunk_duration),
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            output_file, "-y"
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            cpu_chunks.append(output_file)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Erro no chunk {i}: {e}")
    
    cpu_time = time.time() - start_time
    print(f"  ✅ CPU: {cpu_time:.2f}s ({len(cpu_chunks)} chunks criados)")
    
    # Comparação
    if cuda_time > 0 and cpu_time > 0:
        speedup = cpu_time / cuda_time
        print(f"\n📈 Resultado:")
        print(f"  CUDA: {cuda_time:.2f}s")
        print(f"  CPU:  {cpu_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x (CUDA é {speedup:.1f}x mais rápido)")
    
    # Limpa arquivos temporários
    print("\n🧹 Limpando arquivos temporários...")
    temp_files = [test_file] + cuda_chunks + cpu_chunks
    
    for file in temp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"  ✅ Removido: {os.path.basename(file)}")
        except OSError:
            print(f"  ⚠️  Não foi possível remover: {file}")

def test_silence_detection_performance():
    """Testa performance de detecção de silêncio CUDA vs CPU"""
    
    from core.ffmpeg_cuda import ffmpeg_cuda_optimizer
    
    # Cria arquivo de teste com silêncios
    test_file = "/tmp/test_audio_silence.wav"
    
    print("\n🔇 Criando arquivo de áudio com silêncios...")
    
    # Cria arquivo com padrão de fala e silêncio
    cmd = [
        "ffmpeg", "-f", "lavfi", "-i", 
        "sine=frequency=440:duration=5, aevalsrc=0:duration=2, sine=frequency=880:duration=5, aevalsrc=0:duration=2, sine=frequency=1320:duration=5",
        "-c:a", "pcm_s16le", "-ar", "16000", "-ac", "1",
        test_file, "-y"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Arquivo com silêncios criado: {test_file}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar arquivo: {e}")
        return
    
    print("\n🔍 Testando performance de detecção de silêncio CUDA vs CPU...")
    
    # Teste 1: Detecção com CUDA
    print("\n📊 Teste 1: Detecção de silêncio com CUDA")
    
    start_time = time.time()
    cmd_cuda = ffmpeg_cuda_optimizer.optimize_silence_detection_cmd(
        test_file, threshold_db=-40.0, min_duration=0.5
    )
    
    try:
        result_cuda = subprocess.run(cmd_cuda, capture_output=True, text=True, check=True)
        cuda_silence_time = time.time() - start_time
        
        # Conta silêncios detectados
        cuda_silences = len([line for line in result_cuda.stderr.split('\n') if 'silence_start' in line])
        print(f"  ✅ CUDA: {cuda_silence_time:.2f}s ({cuda_silences} silêncios detectados)")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ CUDA falhou: {e}")
        cuda_silence_time = float('inf')
        cuda_silences = 0
    
    # Teste 2: Detecção com CPU
    print("\n📊 Teste 2: Detecção de silêncio com CPU")
    
    start_time = time.time()
    cmd_cpu = [
        "ffmpeg", "-threads", "0", "-i", test_file,
        "-af", "silencedetect=noise=-40dB:d=0.5",
        "-f", "null", "-"
    ]
    
    try:
        result_cpu = subprocess.run(cmd_cpu, capture_output=True, text=True, check=True)
        cpu_silence_time = time.time() - start_time
        
        # Conta silêncios detectados
        cpu_silences = len([line for line in result_cpu.stderr.split('\n') if 'silence_start' in line])
        print(f"  ✅ CPU: {cpu_silence_time:.2f}s ({cpu_silences} silêncios detectados)")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ CPU falhou: {e}")
        cpu_silence_time = float('inf')
        cpu_silences = 0
    
    # Comparação
    if cuda_silence_time < float('inf') and cpu_silence_time < float('inf'):
        speedup = cpu_silence_time / cuda_silence_time
        print(f"\n📈 Resultado:")
        print(f"  CUDA: {cuda_silence_time:.2f}s")
        print(f"  CPU:  {cpu_silence_time:.2f}s")
        print(f"  Speedup: {speedup:.2f}x (CUDA é {speedup:.1f}x mais rápido)")
        
        if cuda_silences == cpu_silences:
            print(f"  ✅ Mesma detecção: {cuda_silences} silêncios")
        else:
            print(f"  ⚠️  Diferença na detecção: CUDA={cuda_silences}, CPU={cpu_silences}")
    
    # Limpa arquivo temporário
    try:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n✅ Arquivo temporário removido: {os.path.basename(test_file)}")
    except OSError:
        print(f"\n⚠️  Não foi possível remover: {test_file}")

def test_cuda_status():
    """Testa status das otimizações CUDA"""
    
    from core.ffmpeg_cuda import ffmpeg_cuda_optimizer
    
    print("🔍 Testando status das otimizações CUDA...\n")
    
    info = ffmpeg_cuda_optimizer.get_optimization_info()
    
    print("📊 Status das otimizações:")
    print(f"  ✓ CUDA habilitado: {info['cuda_enabled']}")
    print(f"  ✓ Otimização ativa: {info['optimization_active']}")
    
    status = info['cuda_status']
    print(f"  ✓ CUDA disponível: {status['cuda_available']}")
    print(f"  ✓ Decoders CUVID: {len(status['supported_decoders'])}")
    print(f"  ✓ Encoders NVENC: {len(status['supported_encoders'])}")
    print(f"  ✓ Teste decode: {status['decode_test_passed']}")
    
    # Testa comandos otimizados
    print(f"\n🔧 Testando comandos otimizados:")
    
    # Teste chunking
    chunking_cmd = ffmpeg_cuda_optimizer.optimize_audio_chunking_cmd(
        "/tmp/test.wav", "/tmp/chunk.wav", 0, 10, 16000, 1
    )
    print(f"  Chunking: {' '.join(chunking_cmd[:5])}...")
    
    # Teste silence detection
    silence_cmd = ffmpeg_cuda_optimizer.optimize_silence_detection_cmd(
        "/tmp/test.wav", -40.0, 0.5
    )
    print(f"  Silence: {' '.join(silence_cmd[:5])}...")
    
    # Teste probe
    probe_cmd = ffmpeg_cuda_optimizer.optimize_audio_probe_cmd("/tmp/test.wav")
    print(f"  Probe: {' '.join(probe_cmd[:5])}...")

def main():
    """Função principal"""
    print("🎯 Teste de Performance - Chunking CUDA vs CPU")
    print("=" * 60)
    
    # Teste 1: Status CUDA
    test_cuda_status()
    
    print("\n" + "=" * 60)
    
    # Teste 2: Performance chunking
    test_chunking_performance()
    
    print("\n" + "=" * 60)
    
    # Teste 3: Performance silence detection
    test_silence_detection_performance()
    
    print("\n" + "=" * 60)
    print("✅ Todos os testes concluídos!")

if __name__ == "__main__":
    main()