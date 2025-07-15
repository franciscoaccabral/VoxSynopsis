"""Performance optimization module for FastWhisper.

This module configures optimal environment variables and settings
for maximum FastWhisper performance on CPU-based systems.
"""

import os
import platform
from typing import Any, Dict

import psutil


def setup_fastwhisper_environment(conservative_mode: bool = False) -> None:
    """Configure environment variables for FastWhisper performance.

    Args:
        conservative_mode: If True, uses only safe, well-tested optimizations

    Sets up CTranslate2 optimizations based on hardware detection:
    - OMP_NUM_THREADS: Use physical CPU cores for optimal threading
    - CT2_INTER_THREADS: Number of parallel translations
    - CT2_INTRA_THREADS: OpenMP threads per translation
    - CT2_USE_EXPERIMENTAL_PACKED_GEMM: Enable for Intel CPUs (if not conservative)
    - CT2_FORCE_CPU_ISA: Force AVX2 instruction set (if not conservative)
    - CT2_USE_MKL: Enable Intel MKL backend when available
    """
    # Get optimal thread count (physical cores)
    physical_cores = psutil.cpu_count(logical=False) or 1

    # Core threading configuration (always safe)
    os.environ["OMP_NUM_THREADS"] = str(physical_cores)

    # Advanced CTranslate2 threading configuration
    os.environ["CT2_INTER_THREADS"] = "1"  # Number of parallel translations
    os.environ["CT2_INTRA_THREADS"] = str(
        physical_cores
    )  # OpenMP threads per translation
    os.environ["CT2_MAX_QUEUED_BATCHES"] = "0"  # Auto-configuration

    if not conservative_mode:
        # Detect CPU architecture for specific optimizations
        cpu_info = platform.processor().lower()

        # Intel-specific optimizations (only in non-conservative mode)
        if "intel" in cpu_info or "genuine intel" in cpu_info:
            os.environ["CT2_USE_EXPERIMENTAL_PACKED_GEMM"] = "1"
            os.environ["CT2_USE_MKL"] = "1"
            print("🚀 Intel CPU detected: Enabled MKL and PACKED_GEMM optimizations")

        # Force AVX2 instruction set (only in non-conservative mode)
        os.environ["CT2_FORCE_CPU_ISA"] = "AVX2"

        # Additional aggressive optimizations for CPU performance
        os.environ["CT2_BEAM_SIZE"] = "1"  # Force beam size for faster decoding
        os.environ["CT2_DISABLE_FALLBACK"] = "1"  # Disable fallback optimizations
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "0"  # Disable MPS fallback

        print(
            f"⚡ FastWhisper optimized for {physical_cores} CPU cores (aggressive mode)"
        )
        print("🔥 Additional CPU optimizations enabled: AVX2, beam_size=1, no fallback")
    else:
        print(
            f"🛡️ FastWhisper optimized for {physical_cores} CPU cores (conservative mode)"
        )

    # Enable verbose logging for debugging (can be disabled in production)
    os.environ["CT2_VERBOSE"] = "0"  # Set to "1" for debugging

    # Log threading configuration
    logical_cores = psutil.cpu_count(logical=True) or 1
    print(
        f"📊 Threading: {physical_cores} physical cores, {logical_cores} logical cores"
    )
    print(f"🔧 CT2_INTER_THREADS: {os.environ.get('CT2_INTER_THREADS')}")
    print(f"🔧 CT2_INTRA_THREADS: {os.environ.get('CT2_INTRA_THREADS')}")


def get_optimal_threading_config() -> Dict[str, Any]:
    """Get optimal threading configuration for the current hardware.

    Returns:
        Dict with optimal threading parameters for WhisperModel
    """
    physical_cores = psutil.cpu_count(logical=False) or 1

    return {
        "cpu_threads": physical_cores,  # Use physical cores for stability
        "num_workers": 1,  # Single worker for CPU stability
        "inter_threads": 1,  # Single translation at a time
        "intra_threads": physical_cores,  # Threads per translation
        "max_queued_batches": 0,  # Auto-configuration
    }


def get_hardware_info() -> Dict[str, Any]:
    """Get detailed hardware information for optimization decisions.

    Returns:
        Dict with hardware specifications
    """
    memory_gb = psutil.virtual_memory().total / (1024**3)

    return {
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "memory_gb": round(memory_gb, 1),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "architecture": platform.architecture()[0],
    }


def validate_environment() -> bool:
    """Validate that performance optimizations are properly configured.

    Returns:
        True if environment is optimized, False otherwise
    """
    required_vars = ["OMP_NUM_THREADS", "CT2_FORCE_CPU_ISA"]

    missing_vars = [var for var in required_vars if var not in os.environ]

    if missing_vars:
        print(f"⚠️  Missing environment variables: {missing_vars}")
        return False

    print("✅ Performance environment validated")
    return True


def clear_problematic_environment_vars() -> None:
    """Clear potentially problematic environment variables that may cause model loading issues."""
    problematic_vars = [
        "CT2_USE_EXPERIMENTAL_PACKED_GEMM",
        "CT2_FORCE_CPU_ISA",
        "CT2_USE_MKL",
    ]

    cleared_vars = []
    for var in problematic_vars:
        if var in os.environ:
            del os.environ[var]
            cleared_vars.append(var)

    if cleared_vars:
        print(f"🧹 Cleared problematic environment variables: {cleared_vars}")


def diagnose_fastwhisper_issues() -> Dict[str, Any]:
    """Diagnose potential FastWhisper configuration issues."""
    issues = []
    recommendations = []

    # Check for known problematic environment variables
    problematic_vars = ["CT2_USE_EXPERIMENTAL_PACKED_GEMM", "CT2_FORCE_CPU_ISA"]
    active_problematic = [var for var in problematic_vars if var in os.environ]

    if active_problematic:
        issues.append(f"Experimental CT2 variables active: {active_problematic}")
        recommendations.append(
            "Try clearing experimental variables with clear_problematic_environment_vars()"
        )

    # Check thread configuration
    physical_cores = psutil.cpu_count(logical=False) or 1
    omp_threads = os.environ.get("OMP_NUM_THREADS")

    if omp_threads and int(omp_threads) > physical_cores:
        issues.append(
            f"OMP_NUM_THREADS ({omp_threads}) exceeds physical cores ({physical_cores})"
        )
        recommendations.append(f"Set OMP_NUM_THREADS to {physical_cores} or lower")

    return {
        "issues": issues,
        "recommendations": recommendations,
        "problematic_env_vars": active_problematic,
    }


def apply_optimal_config() -> Dict[str, Any]:
    """Apply optimal configuration based on current hardware.

    Returns:
        Dictionary with optimal configuration settings
    """
    hw_info = get_hardware_info()
    physical_cores = hw_info["physical_cores"]
    memory_gb = hw_info["memory_gb"]

    # Optimal configuration based on hardware
    optimal_config = {
        "model_size": "medium"
        if memory_gb >= 16
        else "base"
        if memory_gb >= 8
        else "tiny",
        "device": "cpu",
        "compute_type": "int8",
        "cpu_threads": physical_cores,
        "num_workers": 1,  # Single worker for CPU stability
        "beam_size": 1,
        "best_of": 1,
        "condition_on_previous_text": False,
        "temperature": 0.0,
        "vad_filter": True,
        "vad_threshold": 0.6,
        "vad_min_silence_duration_ms": 500,
        "use_batch_processing": True,
        "batch_threshold": 2,
        "batch_size": min(16, physical_cores * 2)
        if memory_gb >= 16
        else min(8, physical_cores),
        "enable_audio_preprocessing": True,
        "enable_model_caching": True,
        "target_sample_rate": 16000,
        "enable_noise_reduction": True,
        "conservative_mode": False,
    }

    print(
        f"🎯 Optimal configuration applied for {physical_cores} cores, {memory_gb}GB RAM"
    )
    print(f"   📊 Model: {optimal_config['model_size']}")
    print(f"   🚀 Batch size: {optimal_config['batch_size']}")
    print(f"   ⚡ Target sample rate: {optimal_config['target_sample_rate']}Hz")

    return optimal_config


def print_optimization_status() -> None:
    """Print current optimization status and recommendations."""
    hw_info = get_hardware_info()
    thread_config = get_optimal_threading_config()

    print("\n🔧 FastWhisper Performance Configuration:")
    print(
        f"   💻 Hardware: {hw_info['physical_cores']} cores, {hw_info['memory_gb']}GB RAM"
    )
    print(f"   🧵 Threading: {thread_config['cpu_threads']} CPU threads")
    print(
        f"   ⚙️  Environment: {len([k for k in os.environ if k.startswith('CT2_')])} CT2 variables set"
    )

    # Check for issues
    diagnosis = diagnose_fastwhisper_issues()
    if diagnosis["issues"]:
        print(f"   ⚠️  Issues detected: {len(diagnosis['issues'])}")
        for issue in diagnosis["issues"]:
            print(f"      - {issue}")

    # Performance recommendations
    if hw_info["memory_gb"] >= 16:
        print("   📊 Recommendation: Consider 'medium' model for better quality")
    elif hw_info["memory_gb"] >= 8:
        print("   📊 Recommendation: 'base' model optimal for your hardware")
    else:
        print("   📊 Recommendation: Use 'tiny' or 'base' model for memory constraints")

    print("   🚀 Ready for optimized transcription!\n")
