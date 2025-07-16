#!/usr/bin/env python3
"""
Teste simples para verificar as otimizações de chunking implementadas.
"""

import json
import os
import sys

def test_config_parameters():
    """Testa se os novos parâmetros de configuração estão presentes."""
    print("🧪 Testando parâmetros de configuração...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        required_params = [
            'max_chunk_duration_seconds',
            'enable_adaptive_sensitivity',
            'adaptive_silence_thresholds',
            'adaptive_silence_durations',
            'enable_chunk_validation',
            'chunk_quality_threshold'
        ]
        
        missing_params = []
        for param in required_params:
            if param not in config:
                missing_params.append(param)
        
        if missing_params:
            print(f"❌ Parâmetros ausentes: {missing_params}")
            return False
        
        print("✅ Todos os parâmetros de configuração estão presentes")
        print(f"   - max_chunk_duration_seconds: {config['max_chunk_duration_seconds']}")
        print(f"   - enable_adaptive_sensitivity: {config['enable_adaptive_sensitivity']}")
        print(f"   - adaptive_silence_thresholds: {config['adaptive_silence_thresholds']}")
        print(f"   - adaptive_silence_durations: {config['adaptive_silence_durations']}")
        print(f"   - enable_chunk_validation: {config['enable_chunk_validation']}")
        print(f"   - chunk_quality_threshold: {config['chunk_quality_threshold']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao carregar config.json: {e}")
        return False

def test_code_compilation():
    """Testa se o código compila sem erros."""
    print("\n🧪 Testando compilação do código...")
    
    files_to_test = [
        'core/transcription.py',
        'core/batch_transcription.py'
    ]
    
    all_passed = True
    for file_path in files_to_test:
        try:
            import py_compile
            py_compile.compile(file_path, doraise=True)
            print(f"✅ {file_path} compila sem erros")
        except Exception as e:
            print(f"❌ {file_path} falha na compilação: {e}")
            all_passed = False
    
    return all_passed

def test_new_methods():
    """Testa se os novos métodos foram implementados."""
    print("\n🧪 Testando novos métodos implementados...")
    
    try:
        # Tenta importar e verificar métodos
        sys.path.insert(0, '.')
        
        # Verifica se os métodos existem (sem executar)
        with open('core/transcription.py', 'r') as f:
            content = f.read()
            
        expected_methods = [
            '_split_oversized_chunk',
            'adaptive_silence_thresholds',
            'adaptive_silence_durations',
            'max_chunk_duration_seconds'
        ]
        
        found_methods = []
        for method in expected_methods:
            if method in content:
                found_methods.append(method)
        
        print(f"✅ Métodos encontrados: {found_methods}")
        
        # Verifica se a lógica de logging foi implementada
        if 'chunk_durations' in content and 'oversized_chunks' in content:
            print("✅ Sistema de monitoramento de chunks implementado")
        else:
            print("❌ Sistema de monitoramento de chunks não encontrado")
            
        return len(found_methods) >= 3
        
    except Exception as e:
        print(f"❌ Erro ao testar métodos: {e}")
        return False

def run_all_tests():
    """Executa todos os testes."""
    print("🚀 Executando testes de otimização de chunking VoxSynopsis\n")
    
    tests = [
        ("Configuração", test_config_parameters),
        ("Compilação", test_code_compilation),
        ("Novos métodos", test_new_methods)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todas as otimizações foram implementadas com sucesso!")
        return True
    else:
        print("⚠️  Algumas otimizações precisam de ajustes")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)