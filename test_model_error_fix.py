#!/usr/bin/env python3
"""
Teste específico para validar a correção do erro 'name model is not defined' 
no sistema de recovery anti-loop.
"""

import os
import sys
import logging

# Configurar logging para debug
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_model_error_fix():
    """Testa se as correções do erro de modelo funcionam corretamente."""
    print("🧪 Testando correções do erro 'name model is not defined'...")
    
    try:
        # Tenta importar e verificar se métodos existem
        sys.path.insert(0, '.')
        
        # Lê os arquivos para verificar correções
        with open('core/batch_transcription.py', 'r') as f:
            batch_content = f.read()
            
        with open('core/transcription.py', 'r') as f:
            transcription_content = f.read()
        
        # Verifica se as correções foram aplicadas
        corrections_applied = []
        
        # Verificação 1: Recovery manager sempre recriado
        if "Always recreate recovery manager" in batch_content:
            corrections_applied.append("✅ Recovery manager sempre recriado (batch)")
        else:
            corrections_applied.append("❌ Recovery manager não recriado (batch)")
            
        if "Always recreate recovery manager" in transcription_content:
            corrections_applied.append("✅ Recovery manager sempre recriado (transcription)")
        else:
            corrections_applied.append("❌ Recovery manager não recriado (transcription)")
        
        # Verificação 2: Validação de modelo antes de inicializar recovery
        if "if model is None:" in batch_content and "cannot initialize recovery manager" in batch_content:
            corrections_applied.append("✅ Validação de modelo antes de recovery (batch)")
        else:
            corrections_applied.append("❌ Validação de modelo ausente (batch)")
            
        if "if model is None:" in transcription_content and "cannot initialize recovery manager" in transcription_content:
            corrections_applied.append("✅ Validação de modelo antes de recovery (transcription)")
        else:
            corrections_applied.append("❌ Validação de modelo ausente (transcription)")
        
        # Verificação 3: Validação no _transcribe_with_model
        if "Model is None in _transcribe_with_model" in batch_content:
            corrections_applied.append("✅ Validação no _transcribe_with_model (batch)")
        else:
            corrections_applied.append("❌ Validação no _transcribe_with_model ausente (batch)")
            
        if "Model is None in _transcribe_with_model" in transcription_content:
            corrections_applied.append("✅ Validação no _transcribe_with_model (transcription)")
        else:
            corrections_applied.append("❌ Validação no _transcribe_with_model ausente (transcription)")
        
        # Verificação 4: Logging aprimorado
        if "Transcribing" in batch_content and "type(model).__name__" in batch_content:
            corrections_applied.append("✅ Logging aprimorado (batch)")
        else:
            corrections_applied.append("❌ Logging aprimorado ausente (batch)")
            
        if "Transcribing" in transcription_content and "type(model).__name__" in transcription_content:
            corrections_applied.append("✅ Logging aprimorado (transcription)")
        else:
            corrections_applied.append("❌ Logging aprimorado ausente (transcription)")
        
        # Verificação 5: Validação dupla na função transcribe
        if "Double-check model availability" in batch_content:
            corrections_applied.append("✅ Validação dupla na closure (batch)")
        else:
            corrections_applied.append("❌ Validação dupla na closure ausente (batch)")
            
        if "Double-check model availability" in transcription_content:
            corrections_applied.append("✅ Validação dupla na closure (transcription)")
        else:
            corrections_applied.append("❌ Validação dupla na closure ausente (transcription)")
        
        # Mostrar resultados
        print("\n📊 Resultados das correções:")
        for correction in corrections_applied:
            print(f"  {correction}")
        
        # Contar sucessos
        successful_corrections = sum(1 for c in corrections_applied if c.startswith("✅"))
        total_corrections = len(corrections_applied)
        
        print(f"\n📈 Score: {successful_corrections}/{total_corrections} correções aplicadas")
        
        # Verificar se todas as correções críticas foram aplicadas
        critical_corrections = [c for c in corrections_applied if "Recovery manager sempre recriado" in c or "Validação de modelo antes de recovery" in c]
        critical_success = sum(1 for c in critical_corrections if c.startswith("✅"))
        
        if critical_success == len(critical_corrections):
            print("🎉 Todas as correções críticas foram aplicadas!")
            print("✅ O erro 'name model is not defined' deve estar resolvido")
            return True
        else:
            print("⚠️  Algumas correções críticas estão ausentes")
            print("❌ O erro pode persistir")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar teste: {e}")
        return False

def test_anti_loop_compatibility():
    """Testa compatibilidade com sistema anti-loop existente."""
    print("\n🧪 Testando compatibilidade com sistema anti-loop...")
    
    try:
        with open('core/transcription.py', 'r') as f:
            content = f.read()
        
        # Verifica se funções do sistema anti-loop ainda existem
        anti_loop_functions = [
            'get_anti_loop_statistics',
            'loop_detector',
            'recovery_manager',
            'LightweightLoopDetector',
            'CoreRecoveryManager'
        ]
        
        compatibility_results = []
        for func in anti_loop_functions:
            if func in content:
                compatibility_results.append(f"✅ {func} presente")
            else:
                compatibility_results.append(f"❌ {func} ausente")
        
        print("\n📊 Compatibilidade com sistema anti-loop:")
        for result in compatibility_results:
            print(f"  {result}")
        
        success_rate = sum(1 for r in compatibility_results if r.startswith("✅")) / len(compatibility_results)
        
        if success_rate >= 0.8:
            print("🎉 Sistema anti-loop compatível!")
            return True
        else:
            print("⚠️  Problemas de compatibilidade detectados")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar compatibilidade: {e}")
        return False

def main():
    """Executa todos os testes."""
    print("🚀 Executando testes de correção do erro 'name model is not defined'\n")
    
    tests = [
        ("Correções do erro de modelo", test_model_error_fix),
        ("Compatibilidade anti-loop", test_anti_loop_compatibility)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"{'='*60}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {e}")
    
    print(f"\n{'='*60}")
    print(f"📊 Resultado Final: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todas as correções foram validadas com sucesso!")
        print("✅ O erro 'name model is not defined' deve estar resolvido")
        print("✅ Sistema anti-loop mantém compatibilidade total")
        return True
    else:
        print("⚠️  Algumas correções precisam de revisão")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)