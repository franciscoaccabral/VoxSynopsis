"""Configuration management for VoxSynopsis."""

import json
import os
from typing import Any

# Global constants
SAMPLE_RATE = 48000
OUTPUT_DIR = "gravacoes"
MAX_WORKERS = min(4, (os.cpu_count() or 1) + 1)  # Limite de workers para threads


class ConfigManager:
    """Gerencia configurações do FastWhisper"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        # Configuração automática baseada no hardware
        import psutil

        physical_cores = psutil.cpu_count(logical=False) or 1
        memory_gb = psutil.virtual_memory().total / (1024**3)

        # Configuração otimizada baseada no hardware detectado
        self.default_settings = {
            "model_size": "base" if memory_gb >= 8 else "tiny",
            "device": "cpu",
            "compute_type": "int8",
            "vad_filter": True,
            "vad_threshold": 0.6,  # Otimizado para melhor detecção
            "vad_min_speech_duration_ms": 250,
            "vad_max_speech_duration_s": 30,
            "vad_min_silence_duration_ms": 500,  # Otimizado: 2000→500 (menos tempo)
            "vad_speech_pad_ms": 400,
            "language": "pt",
            "temperature": 0.0,
            "beam_size": 1,  # Otimizado: 5 → 1 (5x menos computação)
            "best_of": 1,  # Otimizado: 5 → 1 (5x menos tentativas)
            "condition_on_previous_text": False,  # Otimizado: processamento mais rápido
            "patience": 1.0,
            "parallel_processes": min(
                4, physical_cores
            ),  # Otimizado: usa cores físicos
            "cpu_threads": physical_cores,  # Otimizado: usa todos os cores físicos
            "chunk_duration_seconds": 30,
            # Configurações de batch processing otimizadas
            "use_batch_processing": True,
            "batch_threshold": 2,  # Otimizado: 3 → 2 (batch mais agressivo)
            "batch_size": min(16, physical_cores * 2)
            if memory_gb >= 16
            else min(8, physical_cores),
            "auto_batch_size": True,
            # Configurações de pré-processamento
            "enable_audio_preprocessing": True,
            "enable_model_caching": True,
            "target_sample_rate": 16000,  # Otimizado: 16kHz para melhor performance
            "enable_noise_reduction": True,
            "enable_normalization": True,
            "threading_optimized": True,
            "conservative_mode": False,  # Otimizado: desabilita modo conservativo
        }
        self.settings = self.load_settings()

    def load_settings(self) -> dict[str, Any]:
        """Carrega configurações do arquivo"""
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                settings = json.load(f)
                # Garante que todas as chaves padrão existam
                for key, value in self.default_settings.items():
                    if key not in settings:
                        settings[key] = value
                return settings
        except FileNotFoundError:
            return self.default_settings.copy()

    def save_settings(self) -> None:
        """Salva configurações no arquivo"""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        """Obtém valor de configuração"""
        return self.settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Define valor de configuração"""
        self.settings[key] = value

    def get_settings(self) -> dict[str, Any]:
        """Retorna cópia das configurações atuais"""
        return self.settings.copy()


def load_stylesheet(app: Any) -> None:
    """Carrega o stylesheet da aplicação"""
    try:
        with open("style.qss", "r") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Arquivo style.qss não encontrado. Usando estilo padrão.")
