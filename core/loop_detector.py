"""Lightweight loop detection system for VoxSynopsis transcription.

This module provides fast detection of repetitive patterns in transcribed text
with minimal performance overhead (< 1%).
"""

import re
import time
from dataclasses import dataclass
from typing import Optional, Dict, List


@dataclass
class LoopDetectionResult:
    """Result of loop detection analysis."""
    has_loop: bool
    loop_type: str
    confidence: float
    pattern: Optional[str] = None
    word_diversity: float = 0.0
    detection_time_ms: float = 0.0


class LightweightLoopDetector:
    """
    Fast loop detector optimized for real-time transcription.
    
    Designed to detect common repetitive patterns with minimal overhead:
    - Word/phrase repetitions: "o que é o que é o que é..."
    - Single word loops: "é é é é é é..."
    - N-gram repetitions: patterns of 2-4 words repeated
    
    Performance target: < 1ms detection time for typical transcription chunks
    """
    
    def __init__(self, 
                 max_repetition_ratio: float = 0.7,
                 min_word_diversity: float = 0.3,
                 min_text_length: int = 20):
        """
        Initialize loop detector with configurable thresholds.
        
        Args:
            max_repetition_ratio: Maximum allowed repetition before flagging as loop
            min_word_diversity: Minimum word diversity (unique words / total words)
            min_text_length: Minimum text length to analyze (skip very short texts)
        """
        self.max_repetition_ratio = max_repetition_ratio
        self.min_word_diversity = min_word_diversity
        self.min_text_length = min_text_length
        
        # Pre-compiled regex patterns for performance
        self._compile_patterns()
        
        # Statistics for monitoring
        self.stats = {
            'total_checks': 0,
            'loops_detected': 0,
            'avg_detection_time_ms': 0.0,
            'pattern_hits': {}
        }
    
    def _compile_patterns(self):
        """Pre-compile regex patterns for better performance."""
        self.patterns = {
            # Phrase repetition: 1-3 words repeated 3+ times
            'phrase_loop': re.compile(
                r'\b(\w+(?:\s+\w+){0,2})\s+(?:\1\s*){3,}', 
                re.IGNORECASE
            ),
            
            # Specific known problematic pattern
            'o_que_e_loop': re.compile(
                r'\bo\s+que\s+é(?:\s+o\s+que\s+é){2,}', 
                re.IGNORECASE
            ),
            
            # Single word repeated many times
            'word_loop': re.compile(
                r'\b(\w+)(?:\s+\1){4,}', 
                re.IGNORECASE
            ),
            
            # Generic excessive repetition
            'excessive_repetition': re.compile(
                r'\b(\w{2,})\s*(?:\1\s*){6,}', 
                re.IGNORECASE
            )
        }
    
    def detect(self, text: str, audio_duration: Optional[float] = None) -> LoopDetectionResult:
        """
        Main detection method - fast analysis of transcribed text.
        
        Args:
            text: Transcribed text to analyze
            audio_duration: Duration of original audio (for length validation)
            
        Returns:
            LoopDetectionResult with detection outcome and metadata
        """
        start_time = time.perf_counter()
        self.stats['total_checks'] += 1
        
        # Quick length check
        if not text or len(text.strip()) < self.min_text_length:
            return LoopDetectionResult(
                has_loop=False,
                loop_type="too_short",
                confidence=0.0,
                detection_time_ms=self._get_elapsed_ms(start_time)
            )
        
        # Clean text for analysis
        cleaned_text = self._clean_text(text)
        
        # Pattern-based detection (fastest)
        pattern_result = self._detect_patterns(cleaned_text)
        if pattern_result.has_loop:
            pattern_result.detection_time_ms = self._get_elapsed_ms(start_time)
            self._update_stats(pattern_result)
            return pattern_result
        
        # Statistical analysis (word diversity)
        diversity_result = self._detect_low_diversity(cleaned_text)
        if diversity_result.has_loop:
            diversity_result.detection_time_ms = self._get_elapsed_ms(start_time)
            self._update_stats(diversity_result)
            return diversity_result
        
        # Length validation (if audio duration provided)
        length_result = self._validate_length_ratio(cleaned_text, audio_duration)
        if length_result.has_loop:
            length_result.detection_time_ms = self._get_elapsed_ms(start_time)
            self._update_stats(length_result)
            return length_result
        
        # No loop detected
        result = LoopDetectionResult(
            has_loop=False,
            loop_type="clean",
            confidence=0.0,
            word_diversity=self._calculate_word_diversity(cleaned_text),
            detection_time_ms=self._get_elapsed_ms(start_time)
        )
        self._update_stats(result)
        return result
    
    def _clean_text(self, text: str) -> str:
        """Basic text cleaning for analysis."""
        # Remove extra whitespace and normalize
        cleaned = ' '.join(text.split())
        # Remove common punctuation for pattern matching
        cleaned = re.sub(r'[.!?,:;]', ' ', cleaned)
        return cleaned.strip()
    
    def _detect_patterns(self, text: str) -> LoopDetectionResult:
        """Fast regex-based pattern detection."""
        for pattern_name, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                confidence = self._calculate_pattern_confidence(match, text)
                return LoopDetectionResult(
                    has_loop=True,
                    loop_type=f"pattern_{pattern_name}",
                    confidence=confidence,
                    pattern=match.group(0)[:50] + "..." if len(match.group(0)) > 50 else match.group(0)
                )
        
        return LoopDetectionResult(has_loop=False, loop_type="no_pattern", confidence=0.0)
    
    def _detect_low_diversity(self, text: str) -> LoopDetectionResult:
        """Detect loops based on word diversity statistics."""
        diversity = self._calculate_word_diversity(text)
        
        if diversity < self.min_word_diversity:
            # Additional check: ensure it's not just short text with valid repetition
            words = text.split()
            if len(words) >= 10:  # Only flag longer texts with low diversity
                confidence = 1.0 - diversity  # Lower diversity = higher confidence of loop
                return LoopDetectionResult(
                    has_loop=True,
                    loop_type="low_diversity",
                    confidence=confidence,
                    word_diversity=diversity
                )
        
        return LoopDetectionResult(
            has_loop=False, 
            loop_type="good_diversity", 
            confidence=0.0,
            word_diversity=diversity
        )
    
    def _validate_length_ratio(self, text: str, audio_duration: Optional[float]) -> LoopDetectionResult:
        """Validate text length against audio duration."""
        if not audio_duration or audio_duration <= 0:
            return LoopDetectionResult(has_loop=False, loop_type="no_duration", confidence=0.0)
        
        # Rough estimation: normal speech ~150-200 words per minute
        words = len(text.split())
        expected_words_min = (audio_duration / 60.0) * 100  # Conservative estimate
        expected_words_max = (audio_duration / 60.0) * 250  # Liberal estimate
        
        # Flag if text is extremely long (possible repetition) or extremely short
        if words > expected_words_max * 2:
            return LoopDetectionResult(
                has_loop=True,
                loop_type="excessive_length",
                confidence=0.7
            )
        elif words < expected_words_min * 0.3 and audio_duration > 5:
            return LoopDetectionResult(
                has_loop=True,
                loop_type="insufficient_length",
                confidence=0.6
            )
        
        return LoopDetectionResult(has_loop=False, loop_type="appropriate_length", confidence=0.0)
    
    def _calculate_word_diversity(self, text: str) -> float:
        """Calculate word diversity ratio (unique words / total words)."""
        words = text.split()
        if not words:
            return 1.0
        
        unique_words = set(word.lower() for word in words)
        return len(unique_words) / len(words)
    
    def _calculate_pattern_confidence(self, match: re.Match, text: str) -> float:
        """Calculate confidence level for pattern matches."""
        matched_text = match.group(0)
        match_ratio = len(matched_text) / len(text)
        
        # Higher ratio = higher confidence of problematic loop
        return min(match_ratio * 2, 1.0)
    
    def _get_elapsed_ms(self, start_time: float) -> float:
        """Get elapsed time in milliseconds."""
        return (time.perf_counter() - start_time) * 1000
    
    def _update_stats(self, result: LoopDetectionResult):
        """Update detection statistics."""
        if result.has_loop:
            self.stats['loops_detected'] += 1
            self.stats['pattern_hits'][result.loop_type] = \
                self.stats['pattern_hits'].get(result.loop_type, 0) + 1
        
        # Update rolling average of detection time
        current_avg = self.stats['avg_detection_time_ms']
        count = self.stats['total_checks']
        new_avg = ((current_avg * (count - 1)) + result.detection_time_ms) / count
        self.stats['avg_detection_time_ms'] = new_avg
    
    def get_statistics(self) -> Dict:
        """Get current detection statistics."""
        total = self.stats['total_checks']
        detected = self.stats['loops_detected']
        
        return {
            'total_checks': total,
            'loops_detected': detected,
            'detection_rate': detected / total if total > 0 else 0,
            'avg_detection_time_ms': round(self.stats['avg_detection_time_ms'], 3),
            'pattern_distribution': self.stats['pattern_hits'].copy()
        }
    
    def reset_statistics(self):
        """Reset detection statistics."""
        self.stats = {
            'total_checks': 0,
            'loops_detected': 0,
            'avg_detection_time_ms': 0.0,
            'pattern_hits': {}
        }


class QuickQualityValidator:
    """
    Lightweight quality validator for transcription results.
    
    Performs basic quality checks without heavy language model analysis
    to maintain the 25-180x performance gains.
    """
    
    def __init__(self):
        self.min_quality_threshold = 0.6
    
    def validate(self, text: str, audio_duration: Optional[float] = None) -> float:
        """
        Calculate a basic quality score for transcribed text.
        
        Args:
            text: Transcribed text
            audio_duration: Original audio duration
            
        Returns:
            Quality score 0.0-1.0 (higher is better)
        """
        if not text or len(text.strip()) < 5:
            return 0.0
        
        scores = {
            'diversity': self._score_word_diversity(text),
            'structure': self._score_basic_structure(text),
            'length': self._score_length_appropriateness(text, audio_duration),
            'repetition': self._score_repetition_penalty(text)
        }
        
        # Weighted average
        weights = {
            'diversity': 0.3,
            'structure': 0.2, 
            'length': 0.2,
            'repetition': 0.3  # Higher weight for repetition detection
        }
        
        weighted_score = sum(scores[key] * weights[key] for key in scores)
        return min(max(weighted_score, 0.0), 1.0)
    
    def is_acceptable_quality(self, text: str, audio_duration: Optional[float] = None) -> bool:
        """Check if transcription meets minimum quality threshold."""
        quality_score = self.validate(text, audio_duration)
        return quality_score >= self.min_quality_threshold
    
    def _score_word_diversity(self, text: str) -> float:
        """Score based on vocabulary diversity."""
        words = text.split()
        if len(words) < 3:
            return 0.8  # Neutral score for very short text
        
        unique_ratio = len(set(word.lower() for word in words)) / len(words)
        return min(unique_ratio * 2, 1.0)  # Scale to make meaningful
    
    def _score_basic_structure(self, text: str) -> float:
        """Score based on basic text structure."""
        # Check for basic punctuation and capitalization
        has_punctuation = bool(re.search(r'[.!?]', text))
        has_capital = bool(re.search(r'[A-Z]', text))
        
        structure_score = 0.5  # Base score
        if has_punctuation:
            structure_score += 0.25
        if has_capital:
            structure_score += 0.25
        
        return structure_score
    
    def _score_length_appropriateness(self, text: str, audio_duration: Optional[float]) -> float:
        """Score based on text length vs audio duration."""
        if not audio_duration or audio_duration <= 0:
            return 0.7  # Neutral score when duration unknown
        
        words_per_minute = len(text.split()) / (audio_duration / 60.0)
        
        # Normal range: 120-200 WPM
        if 120 <= words_per_minute <= 200:
            return 1.0
        elif 80 <= words_per_minute <= 300:
            return 0.8
        elif 50 <= words_per_minute <= 400:
            return 0.6
        else:
            return 0.3
    
    def _score_repetition_penalty(self, text: str) -> float:
        """Penalty score for excessive repetition."""
        detector = LightweightLoopDetector()
        result = detector.detect(text)
        
        if result.has_loop:
            return max(1.0 - result.confidence, 0.0)
        else:
            return 1.0