"""FFmpeg CUDA acceleration utilities for VoxSynopsis."""

import subprocess
import logging
from typing import Dict, List, Optional, Set
from functools import lru_cache

logger = logging.getLogger(__name__)


class FFmpegCUDADetector:
    """Detects and manages FFmpeg CUDA acceleration capabilities."""
    
    def __init__(self):
        self._cuda_available = None
        self._supported_decoders = None
        self._supported_encoders = None
        self._hardware_accels = None
    
    @lru_cache(maxsize=1)
    def is_cuda_available(self) -> bool:
        """Check if CUDA acceleration is available for FFmpeg."""
        try:
            # Check if CUDA is in hardware accelerators
            result = subprocess.run(
                ["ffmpeg", "-hwaccels"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                hwaccels = result.stdout.lower()
                cuda_available = "cuda" in hwaccels
                logger.info(f"FFmpeg CUDA acceleration available: {cuda_available}")
                return cuda_available
            else:
                logger.warning("Failed to check FFmpeg hardware accelerators")
                return False
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Error checking FFmpeg CUDA availability: {e}")
            return False
    
    @lru_cache(maxsize=1)
    def get_supported_decoders(self) -> Set[str]:
        """Get list of supported CUDA decoders."""
        supported = set()
        
        if not self.is_cuda_available():
            return supported
        
        try:
            result = subprocess.run(
                ["ffmpeg", "-decoders"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'cuvid' in line.lower():
                        # Extract decoder name (format: " V..... h264_cuvid")
                        parts = line.split()
                        if len(parts) >= 2:
                            decoder_name = parts[1]
                            supported.add(decoder_name)
                            
                logger.info(f"FFmpeg CUDA decoders available: {supported}")
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Error getting FFmpeg CUDA decoders: {e}")
        
        return supported
    
    @lru_cache(maxsize=1)
    def get_supported_encoders(self) -> Set[str]:
        """Get list of supported CUDA encoders."""
        supported = set()
        
        if not self.is_cuda_available():
            return supported
        
        try:
            result = subprocess.run(
                ["ffmpeg", "-encoders"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'nvenc' in line.lower():
                        # Extract encoder name (format: " V....D h264_nvenc")
                        parts = line.split()
                        if len(parts) >= 2:
                            encoder_name = parts[1]
                            supported.add(encoder_name)
                            
                logger.info(f"FFmpeg CUDA encoders available: {supported}")
                
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Error getting FFmpeg CUDA encoders: {e}")
        
        return supported
    
    def get_optimal_decoder(self, codec: str) -> Optional[str]:
        """Get optimal CUDA decoder for a given codec."""
        if not self.is_cuda_available():
            return None
        
        supported_decoders = self.get_supported_decoders()
        
        # Mapping of common codecs to their CUDA decoders
        codec_mapping = {
            'h264': 'h264_cuvid',
            'hevc': 'hevc_cuvid', 
            'h265': 'hevc_cuvid',
            'av1': 'av1_cuvid',
            'vp8': 'vp8_cuvid',
            'vp9': 'vp9_cuvid',
            'mpeg2': 'mpeg2_cuvid',
            'mpeg4': 'mpeg4_cuvid',
            'vc1': 'vc1_cuvid',
            'mjpeg': 'mjpeg_cuvid'
        }
        
        cuda_decoder = codec_mapping.get(codec.lower())
        if cuda_decoder and cuda_decoder in supported_decoders:
            return cuda_decoder
        
        return None
    
    def get_optimal_encoder(self, codec: str) -> Optional[str]:
        """Get optimal CUDA encoder for a given codec."""
        if not self.is_cuda_available():
            return None
        
        supported_encoders = self.get_supported_encoders()
        
        # Mapping of common codecs to their CUDA encoders
        codec_mapping = {
            'h264': 'h264_nvenc',
            'hevc': 'hevc_nvenc',
            'h265': 'hevc_nvenc',
            'av1': 'av1_nvenc'
        }
        
        cuda_encoder = codec_mapping.get(codec.lower())
        if cuda_encoder and cuda_encoder in supported_encoders:
            return cuda_encoder
        
        return None
    
    def test_cuda_decode(self, test_input: str = None) -> bool:
        """Test if CUDA decoding actually works."""
        if not self.is_cuda_available():
            return False
        
        try:
            # Test with a simple input
            test_cmd = [
                "ffmpeg", "-f", "lavfi", "-i", "testsrc2=duration=1:size=320x240:rate=1",
                "-c:v", "h264_nvenc", "-f", "null", "-"
            ]
            
            result = subprocess.run(
                test_cmd, 
                capture_output=True, 
                text=True, 
                timeout=15
            )
            
            success = result.returncode == 0
            if success:
                logger.info("FFmpeg CUDA decode test successful")
            else:
                logger.warning(f"FFmpeg CUDA decode test failed: {result.stderr}")
            
            return success
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.error(f"Error testing FFmpeg CUDA decode: {e}")
            return False
    
    def get_cuda_status(self) -> Dict[str, any]:
        """Get comprehensive CUDA status information."""
        return {
            "cuda_available": self.is_cuda_available(),
            "supported_decoders": list(self.get_supported_decoders()),
            "supported_encoders": list(self.get_supported_encoders()),
            "decode_test_passed": self.test_cuda_decode() if self.is_cuda_available() else False
        }


class FFmpegCUDAOptimizer:
    """Optimizes FFmpeg commands with CUDA acceleration when available."""
    
    def __init__(self):
        self.detector = FFmpegCUDADetector()
        self.cuda_enabled = self.detector.is_cuda_available()
        
    def optimize_audio_extraction_cmd(self, input_file: str, output_file: str, 
                                    sample_rate: int = 16000, channels: int = 1) -> List[str]:
        """Optimize FFmpeg command for audio extraction with CUDA when available."""
        
        base_cmd = ["ffmpeg"]
        
        if self.cuda_enabled:
            # Try to detect input codec and use appropriate CUDA decoder
            try:
                # Get codec info
                probe_cmd = [
                    "ffprobe", "-v", "quiet", "-show_streams", 
                    "-select_streams", "v:0", "-of", "csv=p=0", 
                    "-show_entries", "stream=codec_name", input_file
                ]
                
                result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    codec = result.stdout.strip()
                    cuda_decoder = self.detector.get_optimal_decoder(codec)
                    
                    if cuda_decoder:
                        # Use CUDA acceleration with specific decoder
                        base_cmd.extend([
                            "-hwaccel", "cuda",
                            "-c:v", cuda_decoder,
                            "-hwaccel_output_format", "cuda"
                        ])
                        logger.info(f"Using CUDA decoder: {cuda_decoder} for codec: {codec}")
                    else:
                        # Fallback to generic CUDA acceleration
                        base_cmd.extend(["-hwaccel", "cuda"])
                        logger.info("Using generic CUDA acceleration")
                else:
                    # Fallback to auto acceleration
                    base_cmd.extend(["-hwaccel", "auto"])
                    logger.warning("Could not detect codec, using auto acceleration")
                    
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                logger.error(f"Error detecting codec: {e}, falling back to auto acceleration")
                base_cmd.extend(["-hwaccel", "auto"])
        else:
            # No CUDA available, use auto acceleration
            base_cmd.extend(["-hwaccel", "auto"])
            logger.info("CUDA not available, using auto acceleration")
        
        # Add remaining parameters
        base_cmd.extend([
            "-threads", "0",
            "-i", input_file,
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            output_file,
            "-y"
        ])
        
        return base_cmd
    
    def optimize_audio_tempo_cmd(self, input_file: str, output_file: str, 
                                tempo_factor: float) -> List[str]:
        """Optimize FFmpeg command for audio tempo changes with CUDA when available."""
        
        base_cmd = ["ffmpeg"]
        
        if self.cuda_enabled:
            # For audio-only processing, CUDA helps mainly with decoding
            base_cmd.extend(["-hwaccel", "cuda"])
            logger.info("Using CUDA acceleration for audio tempo processing")
        else:
            # No CUDA, use multi-threading
            logger.info("CUDA not available, using multi-threading for audio tempo")
        
        base_cmd.extend([
            "-threads", "0",
            "-i", input_file,
            "-filter:a", f"atempo={tempo_factor}",
            output_file,
            "-y"
        ])
        
        return base_cmd
    
    def optimize_audio_chunking_cmd(self, input_file: str, output_file: str, 
                                   start_time: float, duration: float, 
                                   sample_rate: int = 16000, channels: int = 1) -> List[str]:
        """Optimize FFmpeg command for audio chunking with CUDA when available."""
        
        base_cmd = ["ffmpeg"]
        
        if self.cuda_enabled:
            # Use CUDA acceleration for faster audio processing
            base_cmd.extend(["-hwaccel", "cuda"])
            logger.info("Using CUDA acceleration for audio chunking")
        else:
            # No CUDA, use multi-threading
            logger.info("CUDA not available, using multi-threading for audio chunking")
        
        base_cmd.extend([
            "-threads", "0",
            "-i", input_file,
            "-ss", str(start_time),
            "-t", str(duration),
            "-vn",  # No video
            "-acodec", "pcm_s16le",
            "-ar", str(sample_rate),
            "-ac", str(channels),
            output_file,
            "-y"
        ])
        
        return base_cmd
    
    def optimize_silence_detection_cmd(self, input_file: str, 
                                     threshold_db: float = -40.0, 
                                     min_duration: float = 0.5) -> List[str]:
        """Optimize FFmpeg command for silence detection with CUDA when available."""
        
        base_cmd = ["ffmpeg"]
        
        if self.cuda_enabled:
            # Use CUDA acceleration for faster audio analysis
            base_cmd.extend(["-hwaccel", "cuda"])
            logger.info("Using CUDA acceleration for silence detection")
        else:
            # No CUDA, use multi-threading
            logger.info("CUDA not available, using multi-threading for silence detection")
        
        base_cmd.extend([
            "-threads", "0",
            "-i", input_file,
            "-af", f"silencedetect=noise={threshold_db}dB:d={min_duration}",
            "-f", "null",
            "-"
        ])
        
        return base_cmd
    
    def optimize_audio_probe_cmd(self, input_file: str) -> List[str]:
        """Optimize FFprobe command for audio duration detection."""
        
        # FFprobe doesn't benefit much from CUDA, but we can optimize it
        base_cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_file
        ]
        
        return base_cmd

    def get_optimization_info(self) -> Dict[str, any]:
        """Get information about current optimization settings."""
        return {
            "cuda_enabled": self.cuda_enabled,
            "cuda_status": self.detector.get_cuda_status(),
            "optimization_active": self.cuda_enabled
        }


# Global instance for use throughout the application
ffmpeg_cuda_optimizer = FFmpegCUDAOptimizer()