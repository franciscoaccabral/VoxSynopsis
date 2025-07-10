"""Advanced cache system for audio metadata, models, and features optimization."""

import os
import json
import time
import pickle
import hashlib
import tempfile
import weakref
from typing import Dict, Optional, Any, Union, List
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import psutil


@dataclass
class AudioFileInfo:
    """Stores metadata about audio files for caching."""
    filepath: str
    duration: float
    size: int
    mtime: float
    cached_at: float


@dataclass 
class ModelCacheInfo:
    """Stores metadata about cached models."""
    model_key: str
    model_size: str
    device: str
    compute_type: str
    cache_path: str
    memory_usage_mb: float
    load_time: float
    cached_at: float
    last_accessed: float
    access_count: int


class FileCache:
    """Cache system for file metadata to avoid repeated FFmpeg calls."""
    
    def __init__(self, cache_file: str = ".vox_file_cache.json"):
        self.cache_file = cache_file
        self.cache: Dict[str, AudioFileInfo] = {}
        self.load_cache()
    
    def load_cache(self) -> None:
        """Load cache from disk."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    for filepath, data in cache_data.items():
                        self.cache[filepath] = AudioFileInfo(**data)
        except Exception as e:
            print(f"Warning: Could not load cache file: {e}")
            self.cache = {}
    
    def save_cache(self) -> None:
        """Save cache to disk."""
        try:
            cache_data = {filepath: asdict(info) for filepath, info in self.cache.items()}
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache file: {e}")
    
    def get_duration(self, filepath: str) -> Optional[float]:
        """Get cached duration for a file."""
        if not os.path.exists(filepath):
            return None
            
        file_stat = os.stat(filepath)
        cache_info = self.cache.get(filepath)
        
        # Check if cache is valid (file hasn't changed)
        if (cache_info and 
            cache_info.size == file_stat.st_size and 
            abs(cache_info.mtime - file_stat.st_mtime) < 1.0):
            return cache_info.duration
        
        return None
    
    def set_duration(self, filepath: str, duration: float) -> None:
        """Cache duration for a file."""
        if not os.path.exists(filepath):
            return
            
        file_stat = os.stat(filepath)
        self.cache[filepath] = AudioFileInfo(
            filepath=filepath,
            duration=duration,
            size=file_stat.st_size,
            mtime=file_stat.st_mtime,
            cached_at=time.time()
        )
        self.save_cache()
    
    def clear_stale_entries(self, max_age_hours: int = 24) -> None:
        """Remove stale cache entries."""
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        stale_keys = []
        for filepath, info in self.cache.items():
            # Remove if file doesn't exist or cache is too old
            if (not os.path.exists(filepath) or 
                current_time - info.cached_at > max_age_seconds):
                stale_keys.append(filepath)
        
        for key in stale_keys:
            del self.cache[key]
        
        if stale_keys:
            self.save_cache()
            print(f"Cleared {len(stale_keys)} stale cache entries")


class IntelligentModelCache:
    """Advanced caching system for WhisperModel instances and features."""
    
    def __init__(self, cache_dir: Optional[str] = None, max_memory_mb: int = 4096):
        self.cache_dir = cache_dir or os.path.join(tempfile.gettempdir(), "vox_model_cache")
        self.max_memory_mb = max_memory_mb
        self.cache_info_file = os.path.join(self.cache_dir, "cache_info.json")
        
        # Thread-safe model cache using weak references
        self._model_cache: Dict[str, Any] = {}
        self._model_refs: Dict[str, weakref.ref] = {}
        self._cache_info: Dict[str, ModelCacheInfo] = {}
        self._lock = threading.RLock()
        
        # Feature cache for preprocessed audio
        self._feature_cache: Dict[str, Any] = {}
        self._max_feature_cache_mb = 1024  # 1GB for features
        
        self._ensure_cache_dir()
        self._load_cache_info()
    
    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_cache_info(self) -> None:
        """Load cache metadata from disk."""
        try:
            if os.path.exists(self.cache_info_file):
                with open(self.cache_info_file, 'r') as f:
                    cache_data = json.load(f)
                    for key, data in cache_data.items():
                        self._cache_info[key] = ModelCacheInfo(**data)
        except Exception as e:
            print(f"Warning: Could not load model cache info: {e}")
            self._cache_info = {}
    
    def _save_cache_info(self) -> None:
        """Save cache metadata to disk."""
        try:
            cache_data = {key: asdict(info) for key, info in self._cache_info.items()}
            with open(self.cache_info_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save model cache info: {e}")
    
    def _generate_model_key(self, model_size: str, device: str, compute_type: str, **kwargs) -> str:
        """Generate a unique key for model configuration."""
        config_str = f"{model_size}_{device}_{compute_type}"
        for key, value in sorted(kwargs.items()):
            config_str += f"_{key}_{value}"
        return hashlib.md5(config_str.encode()).hexdigest()[:12]
    
    def get_cached_model(self, model_size: str, device: str, compute_type: str, **kwargs):
        """Get a cached model instance or None if not cached."""
        model_key = self._generate_model_key(model_size, device, compute_type, **kwargs)
        
        with self._lock:
            # Check if model is in memory cache
            if model_key in self._model_cache:
                model = self._model_cache[model_key]
                if model is not None:
                    # Update access info
                    if model_key in self._cache_info:
                        self._cache_info[model_key].last_accessed = time.time()
                        self._cache_info[model_key].access_count += 1
                        self._save_cache_info()
                    return model
            
            # Check weak references
            if model_key in self._model_refs:
                model = self._model_refs[model_key]()
                if model is not None:
                    self._model_cache[model_key] = model
                    return model
                else:
                    # Clean up dead reference
                    del self._model_refs[model_key]
        
        return None
    
    def cache_model(self, model, model_size: str, device: str, compute_type: str, 
                   load_time: float = 0, **kwargs) -> str:
        """Cache a model instance."""
        model_key = self._generate_model_key(model_size, device, compute_type, **kwargs)
        current_time = time.time()
        
        with self._lock:
            # Store in memory cache
            self._model_cache[model_key] = model
            
            # Create weak reference for automatic cleanup
            def cleanup_callback(ref):
                with self._lock:
                    if model_key in self._model_refs and self._model_refs[model_key] is ref:
                        del self._model_refs[model_key]
            
            self._model_refs[model_key] = weakref.ref(model, cleanup_callback)
            
            # Estimate memory usage (rough approximation)
            memory_usage = 0
            if model_size == "tiny":
                memory_usage = 200
            elif model_size == "base":
                memory_usage = 400
            elif model_size == "small":
                memory_usage = 800
            elif model_size == "medium":
                memory_usage = 1500
            elif model_size in ["large", "large-v2", "large-v3"]:
                memory_usage = 3000
            
            # Create cache info
            cache_path = os.path.join(self.cache_dir, f"model_{model_key}.pkl")
            
            self._cache_info[model_key] = ModelCacheInfo(
                model_key=model_key,
                model_size=model_size,
                device=device,
                compute_type=compute_type,
                cache_path=cache_path,
                memory_usage_mb=memory_usage,
                load_time=load_time,
                cached_at=current_time,
                last_accessed=current_time,
                access_count=1
            )
            
            self._save_cache_info()
            
            # Cleanup if memory usage is too high
            self._manage_memory_usage()
        
        return model_key
    
    def _manage_memory_usage(self) -> None:
        """Manage memory usage by removing least recently used models."""
        total_usage = sum(info.memory_usage_mb for info in self._cache_info.values())
        
        if total_usage > self.max_memory_mb:
            # Sort by last accessed time (LRU)
            sorted_models = sorted(
                self._cache_info.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove oldest models until under memory limit
            for model_key, info in sorted_models:
                if total_usage <= self.max_memory_mb:
                    break
                
                self._remove_cached_model(model_key)
                total_usage -= info.memory_usage_mb
                print(f"🧹 Removed cached model {info.model_size} to free memory")
    
    def _remove_cached_model(self, model_key: str) -> None:
        """Remove a model from cache."""
        with self._lock:
            # Remove from memory cache
            if model_key in self._model_cache:
                del self._model_cache[model_key]
            
            if model_key in self._model_refs:
                del self._model_refs[model_key]
            
            # Remove cache info
            if model_key in self._cache_info:
                info = self._cache_info[model_key]
                # Try to remove cached file
                try:
                    if os.path.exists(info.cache_path):
                        os.remove(info.cache_path)
                except Exception:
                    pass
                del self._cache_info[model_key]
            
            self._save_cache_info()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self._lock:
            total_models = len(self._cache_info)
            total_memory_mb = sum(info.memory_usage_mb for info in self._cache_info.values())
            total_features = len(self._feature_cache)
            
            # Calculate hit rates
            total_accesses = sum(info.access_count for info in self._cache_info.values())
            avg_load_time = (
                sum(info.load_time for info in self._cache_info.values()) / total_models
                if total_models > 0 else 0
            )
            
            return {
                "models_cached": total_models,
                "memory_usage_mb": total_memory_mb,
                "memory_limit_mb": self.max_memory_mb,
                "features_cached": total_features,
                "total_accesses": total_accesses,
                "avg_load_time": avg_load_time,
                "cache_hit_ratio": total_accesses / max(1, total_models * 2),  # Rough estimate
                "cache_directory": self.cache_dir
            }
    
    def clear_cache(self, clear_disk: bool = True) -> None:
        """Clear all cached data."""
        with self._lock:
            self._model_cache.clear()
            self._model_refs.clear()
            self._feature_cache.clear()
            
            if clear_disk:
                try:
                    import shutil
                    if os.path.exists(self.cache_dir):
                        shutil.rmtree(self.cache_dir)
                        self._ensure_cache_dir()
                except Exception as e:
                    print(f"Warning: Could not clear disk cache: {e}")
            
            self._cache_info.clear()
            self._save_cache_info()
            
            print("🧹 Model cache cleared")


# Global cache instance
_global_model_cache = None

def get_model_cache() -> IntelligentModelCache:
    """Get the global model cache instance."""
    global _global_model_cache
    if _global_model_cache is None:
        _global_model_cache = IntelligentModelCache()
    return _global_model_cache