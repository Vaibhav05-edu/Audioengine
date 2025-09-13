"""
Audio effects tasks
"""

from typing import Dict, Any, List
from celery import current_task

from ..celery_app import celery_app


@celery_app.task(bind=True, name="apply_voice_enhancement")
def apply_voice_enhancement(
    self,
    audio_data: List[float],
    sample_rate: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply voice enhancement effects to audio data
    
    Args:
        audio_data: Audio data as list of floats
        sample_rate: Sample rate of the audio
        config: Enhancement configuration
    
    Returns:
        Dict with enhancement results
    """
    import numpy as np
    import librosa
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": 100, "status": "Starting voice enhancement..."}
    )
    
    # Convert to numpy array
    audio_array = np.array(audio_data)
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 20, "total": 100, "status": "Applying noise reduction..."}
    )
    
    # Noise reduction
    if config.get("noise_reduction", True):
        audio_array = _apply_noise_reduction(audio_array, sample_rate)
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 40, "total": 100, "status": "Applying EQ..."}
    )
    
    # EQ adjustment
    if config.get("eq_enabled", True):
        audio_array = _apply_eq(audio_array, sample_rate, config.get("eq_settings", {}))
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 60, "total": 100, "status": "Applying compression..."}
    )
    
    # Compression
    if config.get("compression_enabled", True):
        audio_array = _apply_compression(audio_array, config.get("compression_settings", {}))
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 80, "total": 100, "status": "Normalizing audio..."}
    )
    
    # Normalize
    if config.get("normalize", True):
        audio_array = librosa.util.normalize(audio_array)
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 100, "total": 100, "status": "Voice enhancement complete!"}
    )
    
    return {
        "status": "completed",
        "enhanced_audio": audio_array.tolist(),
        "sample_rate": sample_rate,
        "effects_applied": ["noise_reduction", "eq", "compression", "normalize"]
    }


def _apply_noise_reduction(audio_array, sample_rate):
    """Apply noise reduction"""
    import librosa
    
    # Simple noise reduction using spectral gating
    # This is a basic implementation - in production you'd use more sophisticated methods
    audio_array = librosa.effects.preemphasis(audio_array)
    
    return audio_array


def _apply_eq(audio_array, sample_rate, eq_settings):
    """Apply EQ adjustment"""
    import scipy.signal
    
    # Simple EQ using butterworth filters
    # Low shelf
    if eq_settings.get("low_gain", 0) != 0:
        b, a = scipy.signal.butter(2, 200, btype='low', fs=sample_rate)
        audio_array = scipy.signal.filtfilt(b, a, audio_array)
    
    # High shelf
    if eq_settings.get("high_gain", 0) != 0:
        b, a = scipy.signal.butter(2, 8000, btype='high', fs=sample_rate)
        audio_array = scipy.signal.filtfilt(b, a, audio_array)
    
    return audio_array


def _apply_compression(audio_array, compression_settings):
    """Apply audio compression"""
    import numpy as np
    
    # Simple compression implementation
    threshold = compression_settings.get("threshold", 0.5)
    ratio = compression_settings.get("ratio", 4.0)
    
    # Apply compression
    compressed = np.where(
        np.abs(audio_array) > threshold,
        np.sign(audio_array) * (threshold + (np.abs(audio_array) - threshold) / ratio),
        audio_array
    )
    
    return compressed


@celery_app.task(bind=True, name="mix_background_music")
def mix_background_music(
    self,
    voice_audio: List[float],
    music_audio: List[float],
    sample_rate: int,
    config: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Mix background music with voice audio
    
    Args:
        voice_audio: Voice audio data
        music_audio: Background music audio data
        sample_rate: Sample rate
        config: Mixing configuration
    
    Returns:
        Dict with mixing results
    """
    import numpy as np
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": 100, "status": "Starting music mixing..."}
    )
    
    # Convert to numpy arrays
    voice_array = np.array(voice_audio)
    music_array = np.array(music_audio)
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 30, "total": 100, "status": "Adjusting levels..."}
    )
    
    # Adjust music level
    music_level = config.get("music_level", 0.3)
    music_array = music_array * music_level
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 60, "total": 100, "status": "Mixing audio..."}
    )
    
    # Mix audio
    mixed_audio = voice_array + music_array
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 80, "total": 100, "status": "Normalizing mix..."}
    )
    
    # Normalize to prevent clipping
    max_val = np.max(np.abs(mixed_audio))
    if max_val > 1.0:
        mixed_audio = mixed_audio / max_val
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 100, "total": 100, "status": "Music mixing complete!"}
    )
    
    return {
        "status": "completed",
        "mixed_audio": mixed_audio.tolist(),
        "sample_rate": sample_rate,
        "music_level": music_level
    }


@celery_app.task(bind=True, name="add_sound_effects")
def add_sound_effects(
    self,
    audio_data: List[float],
    sample_rate: int,
    effects_config: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Add sound effects to audio
    
    Args:
        audio_data: Audio data
        sample_rate: Sample rate
        effects_config: List of sound effects to apply
    
    Returns:
        Dict with effects results
    """
    import numpy as np
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": 100, "status": "Starting sound effects..."}
    )
    
    audio_array = np.array(audio_data)
    effects_applied = []
    
    for i, effect_config in enumerate(effects_config):
        # Update progress
        progress = int((i / len(effects_config)) * 80)
        self.update_state(
            state="PROGRESS",
            meta={"current": progress, "total": 100, "status": f"Applying {effect_config['type']}..."}
        )
        
        # Apply effect based on type
        if effect_config["type"] == "reverb":
            audio_array = _apply_reverb(audio_array, sample_rate, effect_config)
            effects_applied.append("reverb")
        elif effect_config["type"] == "echo":
            audio_array = _apply_echo(audio_array, sample_rate, effect_config)
            effects_applied.append("echo")
        elif effect_config["type"] == "distortion":
            audio_array = _apply_distortion(audio_array, effect_config)
            effects_applied.append("distortion")
    
    # Update progress
    self.update_state(
        state="PROGRESS",
        meta={"current": 100, "total": 100, "status": "Sound effects complete!"}
    )
    
    return {
        "status": "completed",
        "processed_audio": audio_array.tolist(),
        "sample_rate": sample_rate,
        "effects_applied": effects_applied
    }


def _apply_reverb(audio_array, sample_rate, config):
    """Apply reverb effect"""
    import scipy.signal
    
    # Simple reverb using convolution
    # This is a basic implementation
    reverb_length = int(config.get("length", 0.5) * sample_rate)
    reverb = np.random.normal(0, 0.1, reverb_length)
    reverb[0] = 1.0
    
    return scipy.signal.convolve(audio_array, reverb, mode='same')


def _apply_echo(audio_array, sample_rate, config):
    """Apply echo effect"""
    delay = int(config.get("delay", 0.3) * sample_rate)
    decay = config.get("decay", 0.5)
    
    # Create echo
    echo = np.zeros_like(audio_array)
    echo[delay:] = audio_array[:-delay] * decay
    
    return audio_array + echo


def _apply_distortion(audio_array, config):
    """Apply distortion effect"""
    gain = config.get("gain", 2.0)
    threshold = config.get("threshold", 0.5)
    
    # Apply gain
    distorted = audio_array * gain
    
    # Soft clipping
    distorted = np.tanh(distorted)
    
    return distorted
