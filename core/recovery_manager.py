"""Recovery manager for handling transcription loops and failures.

Implements 3 essential recovery strategies optimized for speed and effectiveness:
1. Conservative Settings - Reduce model aggressiveness 
2. Smaller Chunks - Break audio into manageable pieces
3. Tiny Model Fallback - Use lightweight model as last resort
"""

import os
import subprocess
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional, List, Callable

from .loop_detector import LightweightLoopDetector, QuickQualityValidator


class RecoveryStrategy(Enum):
    """Available recovery strategies."""
    CONSERVATIVE_SETTINGS = "conservative_settings"
    SMALLER_CHUNKS = "smaller_chunks"
    TINY_MODEL = "tiny_model"
    EMERGENCY_FALLBACK = "emergency_fallback"


@dataclass
class RecoveryResult:
    """Result of a recovery attempt."""
    success: bool
    text: str
    strategy_used: RecoveryStrategy
    attempts_made: int
    processing_time: float
    quality_score: float
    error_message: Optional[str] = None
    original_issue: Optional[str] = None


@dataclass
class RecoveryAttempt:
    """Individual recovery attempt record."""
    strategy: RecoveryStrategy
    success: bool
    processing_time: float
    result_text: str
    error: Optional[str] = None


class CoreRecoveryManager:
    """
    Essential recovery manager for transcription failures.
    
    Focuses on proven strategies with minimal overhead:
    - Conservative FastWhisper settings to reduce hallucination
    - Audio chunking to isolate problems
    - Model size fallback for difficult content
    
    Performance target: 15-30s additional processing for problematic chunks
    """
    
    def __init__(self, transcribe_function: Callable):
        """
        Initialize recovery manager.
        
        Args:
            transcribe_function: Function to call for transcription
                Should accept (audio_path, settings_dict) and return text
        """
        self.transcribe_function = transcribe_function
        self.loop_detector = LightweightLoopDetector()
        self.quality_validator = QuickQualityValidator()
        
        # Recovery statistics
        self.stats = {
            'total_recoveries': 0,
            'successful_recoveries': 0,
            'strategy_success_rate': {strategy: {'attempts': 0, 'successes': 0} 
                                   for strategy in RecoveryStrategy},
            'avg_recovery_time': 0.0
        }
        
        # Strategy definitions (ordered by speed/effectiveness)
        self.strategies = [
            self._strategy_conservative_settings,
            self._strategy_smaller_chunks, 
            self._strategy_tiny_model,
            self._strategy_emergency_fallback
        ]
    
    def recover_transcription(self, 
                            audio_path: str, 
                            problematic_text: str, 
                            original_settings: Dict[str, Any],
                            audio_duration: Optional[float] = None) -> RecoveryResult:
        """
        Main recovery orchestration method.
        
        Args:
            audio_path: Path to audio file that needs recovery
            problematic_text: The problematic transcription result
            original_settings: Original FastWhisper settings that failed
            audio_duration: Duration of audio for validation
            
        Returns:
            RecoveryResult with final outcome
        """
        start_time = time.time()
        self.stats['total_recoveries'] += 1
        
        recovery_log = []
        best_result = None
        best_quality = 0.0
        
        # Analyze the problem
        detection_result = self.loop_detector.detect(problematic_text, audio_duration)
        problem_type = detection_result.loop_type if detection_result.has_loop else "quality_issue"
        
        print(f"🔄 Starting recovery for {problem_type} (confidence: {detection_result.confidence:.2f})")
        
        # Try each strategy in order
        for i, strategy_func in enumerate(self.strategies):
            strategy_name = RecoveryStrategy(strategy_func.__name__.replace('_strategy_', ''))
            
            print(f"  Attempting strategy {i+1}/{len(self.strategies)}: {strategy_name.value}")
            
            attempt = self._execute_strategy(
                strategy_func, audio_path, problematic_text, 
                original_settings, audio_duration
            )
            recovery_log.append(attempt)
            
            # Update strategy statistics
            self._update_strategy_stats(strategy_name, attempt.success)
            
            if attempt.success:
                quality_score = self.quality_validator.validate(attempt.result_text, audio_duration)
                
                # Keep track of best result
                if quality_score > best_quality:
                    best_quality = quality_score
                    best_result = attempt
                
                # If quality is good enough, we can stop
                if self.quality_validator.is_acceptable_quality(attempt.result_text, audio_duration):
                    print(f"  ✅ Recovery successful with {strategy_name.value} (quality: {quality_score:.2f})")
                    break
            else:
                print(f"  ❌ Strategy failed: {attempt.error}")
        
        # Calculate final result
        total_time = time.time() - start_time
        
        if best_result:
            self.stats['successful_recoveries'] += 1
            result = RecoveryResult(
                success=True,
                text=best_result.result_text,
                strategy_used=RecoveryStrategy(best_result.strategy),
                attempts_made=len(recovery_log),
                processing_time=total_time,
                quality_score=best_quality,
                original_issue=problem_type
            )
        else:
            # All strategies failed - use emergency fallback
            result = RecoveryResult(
                success=False,
                text=self._generate_emergency_text(audio_path, audio_duration),
                strategy_used=RecoveryStrategy.EMERGENCY_FALLBACK,
                attempts_made=len(recovery_log),
                processing_time=total_time,
                quality_score=0.0,
                error_message="All recovery strategies failed",
                original_issue=problem_type
            )
        
        self._update_avg_recovery_time(total_time)
        return result
    
    def _execute_strategy(self, 
                         strategy_func: Callable, 
                         audio_path: str, 
                         problematic_text: str,
                         original_settings: Dict[str, Any],
                         audio_duration: Optional[float]) -> RecoveryAttempt:
        """Execute a single recovery strategy with error handling."""
        strategy_name = RecoveryStrategy(strategy_func.__name__.replace('_strategy_', ''))
        start_time = time.time()
        
        try:
            result_text = strategy_func(audio_path, problematic_text, original_settings)
            processing_time = time.time() - start_time
            
            # Validate result
            if result_text and len(result_text.strip()) > 0:
                # Check if we solved the loop problem
                loop_check = self.loop_detector.detect(result_text, audio_duration)
                if not loop_check.has_loop:
                    return RecoveryAttempt(
                        strategy=strategy_name,
                        success=True,
                        processing_time=processing_time,
                        result_text=result_text
                    )
                else:
                    return RecoveryAttempt(
                        strategy=strategy_name,
                        success=False,
                        processing_time=processing_time,
                        result_text=result_text,
                        error="Loop still detected in result"
                    )
            else:
                return RecoveryAttempt(
                    strategy=strategy_name,
                    success=False,
                    processing_time=processing_time,
                    result_text="",
                    error="Empty transcription result"
                )
                
        except Exception as e:
            processing_time = time.time() - start_time
            return RecoveryAttempt(
                strategy=strategy_name,
                success=False,
                processing_time=processing_time,
                result_text="",
                error=str(e)
            )
    
    def _strategy_conservative_settings(self, 
                                      audio_path: str, 
                                      problematic_text: str,
                                      original_settings: Dict[str, Any]) -> str:
        """
        Strategy 1: Use conservative FastWhisper settings.
        
        Reduces model aggressiveness to minimize hallucination:
        - beam_size=1 (greedy decoding)
        - temperature=0.1 (minimal randomness)
        - condition_on_previous_text=False (avoid context loops)
        """
        conservative_settings = original_settings.copy()
        conservative_settings.update({
            'beam_size': 1,
            'best_of': 1,
            'temperature': 0.1,  # Small amount to break determinism
            'condition_on_previous_text': False,
            'patience': 1.0,
            'no_speech_threshold': 0.6,  # Be more aggressive about silence
        })
        
        return self.transcribe_function(audio_path, conservative_settings)
    
    def _strategy_smaller_chunks(self, 
                                audio_path: str, 
                                problematic_text: str,
                                original_settings: Dict[str, Any]) -> str:
        """
        Strategy 2: Break audio into smaller chunks and transcribe separately.
        
        Divides the audio into 15-20 second chunks to isolate problems.
        """
        target_chunk_duration = 15  # seconds
        
        # Get audio duration first
        duration = self._get_audio_duration(audio_path)
        if duration <= target_chunk_duration:
            # Audio is already short, just retry with conservative settings
            return self._strategy_conservative_settings(audio_path, problematic_text, original_settings)
        
        # Split audio into chunks
        chunks = self._split_audio(audio_path, target_chunk_duration)
        
        try:
            # Transcribe each chunk with conservative settings
            conservative_settings = original_settings.copy()
            conservative_settings.update({
                'beam_size': 1,
                'temperature': 0.1,
                'condition_on_previous_text': False
            })
            
            transcription_parts = []
            for chunk_path in chunks:
                chunk_result = self.transcribe_function(chunk_path, conservative_settings)
                if chunk_result and chunk_result.strip():
                    transcription_parts.append(chunk_result.strip())
            
            return " ".join(transcription_parts)
            
        finally:
            # Clean up temporary chunk files
            for chunk_path in chunks:
                try:
                    os.unlink(chunk_path)
                except OSError:
                    pass
    
    def _strategy_tiny_model(self, 
                           audio_path: str, 
                           problematic_text: str,
                           original_settings: Dict[str, Any]) -> str:
        """
        Strategy 3: Use tiny model as fallback.
        
        The tiny model is less prone to hallucination but may be less accurate.
        """
        tiny_settings = original_settings.copy()
        tiny_settings.update({
            'model_size': 'tiny',
            'beam_size': 1,
            'temperature': 0.0,  # Fully deterministic
            'condition_on_previous_text': False
        })
        
        return self.transcribe_function(audio_path, tiny_settings)
    
    def _strategy_emergency_fallback(self, 
                                   audio_path: str, 
                                   problematic_text: str,
                                   original_settings: Dict[str, Any]) -> str:
        """
        Strategy 4: Emergency fallback - return descriptive text.
        
        Used when all other strategies fail.
        """
        duration = self._get_audio_duration(audio_path)
        return f"[Áudio de {duration:.1f}s - Transcrição não disponível devido a problemas técnicos]"
    
    def _split_audio(self, audio_path: str, chunk_duration: int) -> List[str]:
        """Split audio file into smaller chunks using FFmpeg."""
        duration = self._get_audio_duration(audio_path)
        chunks = []
        
        chunk_count = int(duration / chunk_duration) + (1 if duration % chunk_duration > 0 else 0)
        
        for i in range(chunk_count):
            start_time = i * chunk_duration
            
            # Create temporary file for chunk
            chunk_fd, chunk_path = tempfile.mkstemp(suffix='.wav', prefix=f'chunk_{i}_')
            os.close(chunk_fd)
            
            # Extract chunk using FFmpeg
            cmd = [
                'ffmpeg', '-y',
                '-i', audio_path,
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',
                '-ac', '1',
                chunk_path
            ]
            
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                chunks.append(chunk_path)
            except subprocess.CalledProcessError:
                # If chunk extraction fails, skip this chunk
                try:
                    os.unlink(chunk_path)
                except OSError:
                    pass
                continue
        
        return chunks
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using FFprobe."""
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'csv=p=0',
            audio_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except (subprocess.CalledProcessError, ValueError):
            # Fallback estimation based on file size (rough approximation)
            file_size = os.path.getsize(audio_path)
            # Assume ~32 kbps average for 16kHz mono WAV
            estimated_duration = file_size / (32000 / 8)  
            return max(estimated_duration, 10)  # Minimum 10 seconds
    
    def _generate_emergency_text(self, audio_path: str, audio_duration: Optional[float]) -> str:
        """Generate emergency fallback text when all strategies fail."""
        duration = audio_duration or self._get_audio_duration(audio_path)
        timestamp = time.strftime("%H:%M:%S", time.localtime())
        
        return (f"[ERRO DE TRANSCRIÇÃO - {timestamp}]\n"
                f"Áudio: {os.path.basename(audio_path)}\n" 
                f"Duração: {duration:.1f}s\n"
                f"Status: Todas as estratégias de recuperação falharam\n"
                f"Recomendação: Verificar qualidade do áudio ou tentar transcrição manual")
    
    def _update_strategy_stats(self, strategy: RecoveryStrategy, success: bool):
        """Update statistics for strategy performance."""
        self.stats['strategy_success_rate'][strategy]['attempts'] += 1
        if success:
            self.stats['strategy_success_rate'][strategy]['successes'] += 1
    
    def _update_avg_recovery_time(self, recovery_time: float):
        """Update running average of recovery time."""
        total = self.stats['total_recoveries']
        current_avg = self.stats['avg_recovery_time']
        new_avg = ((current_avg * (total - 1)) + recovery_time) / total
        self.stats['avg_recovery_time'] = new_avg
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get current recovery statistics."""
        stats = self.stats.copy()
        
        # Calculate success rates
        for strategy in RecoveryStrategy:
            attempts = stats['strategy_success_rate'][strategy]['attempts']
            successes = stats['strategy_success_rate'][strategy]['successes']
            stats['strategy_success_rate'][strategy]['success_rate'] = \
                successes / attempts if attempts > 0 else 0
        
        # Overall success rate
        stats['overall_success_rate'] = (
            self.stats['successful_recoveries'] / self.stats['total_recoveries']
            if self.stats['total_recoveries'] > 0 else 0
        )
        
        return stats
    
    def reset_statistics(self):
        """Reset all recovery statistics."""
        self.stats = {
            'total_recoveries': 0,
            'successful_recoveries': 0,
            'strategy_success_rate': {strategy: {'attempts': 0, 'successes': 0} 
                                   for strategy in RecoveryStrategy},
            'avg_recovery_time': 0.0
        }