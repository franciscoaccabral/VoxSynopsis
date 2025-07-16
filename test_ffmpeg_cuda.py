#!/usr/bin/env python3
"""
Script para testar aceleração FFmpeg CUDA com arquivo real
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path

# Adiciona o diretório do projeto ao path
sys.path.insert(0, '/home/franc/VoxSynopsis')

def create_test_mp4():
    """Cria um arquivo MP4 de teste com H.264"""
    test_file = "/tmp/test_video.mp4"
    
    print("🎬 Criando arquivo MP4 de teste...")
    
    # Cria um vídeo de teste com H.264
    cmd = [
        "ffmpeg", "-f", "lavfi", "-i", "testsrc2=duration=10:size=1280x720:rate=30",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=10",
        "-c:v", "libx264", "-c:a", "aac", "-shortest", 
        test_file, "-y"
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Arquivo criado: {test_file}")
        return test_file
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar arquivo: {e}")
        return None

def test_cuda_vs_cpu():
    """Compara performance FFmpeg CUDA vs CPU"""
    
    from core.ffmpeg_cuda import ffmpeg_cuda_optimizer
    
    # Cria arquivo de teste
    test_file = create_test_mp4()
    if not test_file:
        return
    
    print("\n🔍 Testando performance FFmpeg CUDA vs CPU...")
    
    # Teste 1: Extração de áudio com CUDA
    print("\n📊 Teste 1: Extração de áudio")
    
    output_cuda = "/tmp/test_cuda_extract.wav"
    output_cpu = "/tmp/test_cpu_extract.wav"
    
    # Comando CUDA otimizado
    cmd_cuda = ffmpeg_cuda_optimizer.optimize_audio_extraction_cmd(
        test_file, output_cuda, sample_rate=16000, channels=1
    )
    
    # Comando CPU tradicional
    cmd_cpu = [
        "ffmpeg", "-hwaccel", "auto", "-threads", "0", "-i", test_file,
        "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", 
        output_cpu, "-y"
    ]
    
    # Teste CUDA
    print("  🚀 Testando com CUDA...")
    start_time = time.time()
    try:
        result_cuda = subprocess.run(cmd_cuda, capture_output=True, text=True, check=True)
        cuda_time = time.time() - start_time
        print(f"  ✅ CUDA: {cuda_time:.2f}s")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ CUDA falhou: {e}")
        cuda_time = float('inf')
    
    # Teste CPU
    print("  💻 Testando com CPU...")
    start_time = time.time()
    try:
        result_cpu = subprocess.run(cmd_cpu, capture_output=True, text=True, check=True)
        cpu_time = time.time() - start_time
        print(f"  ✅ CPU: {cpu_time:.2f}s")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ CPU falhou: {e}")
        cpu_time = float('inf')
    
    # Comparação
    if cuda_time < float('inf') and cpu_time < float('inf'):
        speedup = cpu_time / cuda_time
        print(f"  📈 Speedup: {speedup:.2f}x (CUDA é {speedup:.1f}x mais rápido)")
    
    # Teste 2: Aceleração de áudio
    print("\n📊 Teste 2: Aceleração de áudio (1.25x)")
    
    # Usa o arquivo extraído como input
    input_audio = output_cuda if os.path.exists(output_cuda) else output_cpu
    if not os.path.exists(input_audio):
        print("  ❌ Arquivo de áudio não encontrado para teste")
        return
    
    output_cuda_tempo = "/tmp/test_cuda_tempo.wav"
    output_cpu_tempo = "/tmp/test_cpu_tempo.wav"
    
    # Comando CUDA otimizado
    cmd_cuda_tempo = ffmpeg_cuda_optimizer.optimize_audio_tempo_cmd(
        input_audio, output_cuda_tempo, 1.25
    )
    
    # Comando CPU tradicional
    cmd_cpu_tempo = [
        "ffmpeg", "-threads", "0", "-i", input_audio,
        "-filter:a", "atempo=1.25", output_cpu_tempo, "-y"
    ]
    
    # Teste CUDA
    print("  🚀 Testando aceleração com CUDA...")
    start_time = time.time()
    try:
        result_cuda_tempo = subprocess.run(cmd_cuda_tempo, capture_output=True, text=True, check=True)
        cuda_tempo_time = time.time() - start_time
        print(f"  ✅ CUDA: {cuda_tempo_time:.2f}s")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ CUDA falhou: {e}")
        cuda_tempo_time = float('inf')
    
    # Teste CPU
    print("  💻 Testando aceleração com CPU...")
    start_time = time.time()
    try:
        result_cpu_tempo = subprocess.run(cmd_cpu_tempo, capture_output=True, text=True, check=True)
        cpu_tempo_time = time.time() - start_time
        print(f"  ✅ CPU: {cpu_tempo_time:.2f}s")
    except subprocess.CalledProcessError as e:
        print(f"  ❌ CPU falhou: {e}")
        cpu_tempo_time = float('inf')
    
    # Comparação
    if cuda_tempo_time < float('inf') and cpu_tempo_time < float('inf'):
        speedup = cpu_tempo_time / cuda_tempo_time
        print(f"  📈 Speedup: {speedup:.2f}x (CUDA é {speedup:.1f}x mais rápido)")
    
    # Limpa arquivos temporários
    print("\n🧹 Limpando arquivos temporários...")
    temp_files = [
        test_file, output_cuda, output_cpu, 
        output_cuda_tempo, output_cpu_tempo
    ]
    
    for file in temp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                print(f"  ✅ Removido: {file}")
        except OSError:
            print(f"  ⚠️  Não foi possível remover: {file}")

def test_cuda_detection():
    """Testa detecção de capacidades CUDA"""
    
    from core.ffmpeg_cuda import ffmpeg_cuda_optimizer
    
    print("🔍 Testando detecção de capacidades CUDA...\n")
    
    detector = ffmpeg_cuda_optimizer.detector
    status = detector.get_cuda_status()
    
    print("📊 Status FFmpeg CUDA:")
    print(f"  ✓ CUDA disponível: {status['cuda_available']}")
    print(f"  ✓ Decoders CUVID: {len(status['supported_decoders'])}")
    print(f"  ✓ Encoders NVENC: {len(status['supported_encoders'])}")
    print(f"  ✓ Teste decode: {status['decode_test_passed']}")
    
    if status['supported_decoders']:
        print(f"\n📱 Decoders CUVID disponíveis ({len(status['supported_decoders'])}):")
        for decoder in sorted(status['supported_decoders']):
            print(f"  - {decoder}")
    
    if status['supported_encoders']:
        print(f"\n🚀 Encoders NVENC disponíveis ({len(status['supported_encoders'])}):")
        for encoder in sorted(status['supported_encoders']):
            print(f"  - {encoder}")
    
    # Testa otimizações específicas
    print(f"\n🔧 Teste de otimizações:")
    
    # Teste H.264
    h264_decoder = detector.get_optimal_decoder('h264')
    h264_encoder = detector.get_optimal_encoder('h264')
    print(f"  H.264 decoder: {h264_decoder or 'Não suportado'}")
    print(f"  H.264 encoder: {h264_encoder or 'Não suportado'}")
    
    # Teste HEVC
    hevc_decoder = detector.get_optimal_decoder('hevc')
    hevc_encoder = detector.get_optimal_encoder('hevc')
    print(f"  HEVC decoder: {hevc_decoder or 'Não suportado'}")
    print(f"  HEVC encoder: {hevc_encoder or 'Não suportado'}")

def main():
    """Função principal"""
    print("🎯 Teste de Aceleração FFmpeg CUDA - VoxSynopsis")
    print("=" * 60)
    
    # Teste 1: Detecção de capacidades
    test_cuda_detection()
    
    print("\n" + "=" * 60)
    
    # Teste 2: Performance real
    test_cuda_vs_cpu()
    
    print("\n" + "=" * 60)
    print("✅ Testes concluídos!")

if __name__ == "__main__":
    main()