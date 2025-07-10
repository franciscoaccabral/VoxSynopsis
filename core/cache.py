"""Cache system for FFmpeg operations."""

import os
from dataclasses import dataclass


@dataclass
class AudioFileInfo:
    """Informações sobre arquivos de áudio para cache"""
    filepath: str
    duration: float
    size: int
    modified_time: float

    @classmethod
    def from_file(cls, filepath: str) -> "AudioFileInfo":
        """Cria AudioFileInfo a partir de um arquivo"""
        stat = os.stat(filepath)
        return cls(
            filepath=filepath,
            duration=0.0,  # Será preenchido posteriormente
            size=stat.st_size,
            modified_time=stat.st_mtime
        )


class FileCache:
    """Sistema de cache para operações FFmpeg"""

    def __init__(self):
        self._duration_cache: dict[str, float] = {}
        self._file_info_cache: dict[str, AudioFileInfo] = {}

    def get_duration(self, filepath: str) -> float | None:
        """Obtém duração do cache se arquivo não foi modificado"""
        if not os.path.exists(filepath):
            return None

        current_mtime = os.path.getmtime(filepath)
        cached_info = self._file_info_cache.get(filepath)

        if cached_info and cached_info.modified_time == current_mtime:
            return cached_info.duration

        return None

    def set_duration(self, filepath: str, duration: float) -> None:
        """Armazena duração no cache"""
        if os.path.exists(filepath):
            info = AudioFileInfo.from_file(filepath)
            info.duration = duration
            self._file_info_cache[filepath] = info
            self._duration_cache[filepath] = duration

    def clear_stale_entries(self) -> None:
        """Remove entradas antigas do cache"""
        stale_keys = []
        for filepath, info in self._file_info_cache.items():
            if (not os.path.exists(filepath) or
                os.path.getmtime(filepath) != info.modified_time):
                stale_keys.append(filepath)

        for key in stale_keys:
            self._file_info_cache.pop(key, None)
            self._duration_cache.pop(key, None)

    def clear(self) -> None:
        """Limpa todo o cache"""
        self._duration_cache.clear()
        self._file_info_cache.clear()