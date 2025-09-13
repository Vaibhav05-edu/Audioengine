"""
ElevenLabs SFX client for text-to-sound generation
"""

import os
import io
import json
import hashlib
import tempfile
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio
import aiohttp
import numpy as np
import librosa
import soundfile as sf
from scipy import signal

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class SFXGenerationRequest:
    """SFX generation request parameters"""
    prompt: str
    duration: float  # Duration in seconds
    seed: Optional[int] = None
    loopable: bool = False
    crossfade_duration: float = 0.5  # Crossfade duration in seconds
    output_format: str = "wav"
    sample_rate: int = 48000
    bit_depth: int = 24


@dataclass
class SFXGenerationResult:
    """SFX generation result"""
    success: bool
    audio_data: Optional[bytes] = None
    file_path: Optional[str] = None
    duration: float = 0.0
    sample_rate: int = 48000
    bit_depth: int = 24
    format: str = "wav"
    generation_time: float = 0.0
    tiles_generated: int = 0
    seed_used: Optional[int] = None
    error_message: Optional[str] = None


class ElevenLabsSFXClient:
    """ElevenLabs SFX generation client"""
    
    def __init__(self, api_key: str = None, cache_dir: str = None):
        self.api_key = api_key or settings.elevenlabs_api_key
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.cache_dir = Path(cache_dir or settings.cache_dir) / "sfx"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ElevenLabs SFX API limits
        self.max_duration_per_request = 22.0  # ~22 seconds
        self.min_duration = 1.0
        self.max_duration = 300.0  # 5 minutes max
        
        # Audio processing settings
        self.target_sample_rate = 48000
        self.target_bit_depth = 24
        self.crossfade_duration = 0.5
        
        logger.info("ElevenLabs SFX Client initialized")
    
    def _generate_cache_key(self, request: SFXGenerationRequest) -> str:
        """Generate cache key for request"""
        # Create deterministic hash from request parameters
        cache_data = {
            "prompt": request.prompt,
            "duration": request.duration,
            "seed": request.seed,
            "loopable": request.loopable,
            "crossfade_duration": request.crossfade_duration,
            "sample_rate": request.sample_rate,
            "bit_depth": request.bit_depth
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        return f"sfx_{cache_hash}.{request.output_format}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[SFXGenerationResult]:
        """Get cached generation result"""
        cache_file = self.cache_dir / cache_key
        
        if not cache_file.exists():
            return None
        
        try:
            # Read cached audio data
            with open(cache_file, 'rb') as f:
                audio_data = f.read()
            
            # Read metadata
            metadata_file = cache_file.with_suffix('.json')
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = {}
            
            return SFXGenerationResult(
                success=True,
                audio_data=audio_data,
                file_path=str(cache_file),
                duration=metadata.get('duration', 0.0),
                sample_rate=metadata.get('sample_rate', self.target_sample_rate),
                bit_depth=metadata.get('bit_depth', self.target_bit_depth),
                format=request.output_format,
                generation_time=metadata.get('generation_time', 0.0),
                tiles_generated=metadata.get('tiles_generated', 0),
                seed_used=metadata.get('seed_used')
            )
        except Exception as e:
            logger.warning(f"Failed to load cached result: {e}")
            return None
    
    def _cache_result(self, result: SFXGenerationResult, cache_key: str) -> None:
        """Cache generation result"""
        try:
            cache_file = self.cache_dir / cache_key
            
            # Write audio data
            with open(cache_file, 'wb') as f:
                f.write(result.audio_data)
            
            # Write metadata
            metadata = {
                'duration': result.duration,
                'sample_rate': result.sample_rate,
                'bit_depth': result.bit_depth,
                'generation_time': result.generation_time,
                'tiles_generated': result.tiles_generated,
                'seed_used': result.seed_used,
                'cached_at': datetime.now().isoformat()
            }
            
            metadata_file = cache_file.with_suffix('.json')
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Cached SFX result: {cache_file}")
        except Exception as e:
            logger.error(f"Failed to cache result: {e}")
    
    async def _generate_sfx_tile(self, prompt: str, duration: float, seed: Optional[int] = None) -> bytes:
        """Generate a single SFX tile using ElevenLabs API"""
        headers = {
            "Accept": "audio/wav",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Prepare request payload
        payload = {
            "text": prompt,
            "duration": min(duration, self.max_duration_per_request),
            "model_id": "eleven_multilingual_v2"  # Use SFX-capable model
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/text-to-speech/sfx",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info(f"Generated SFX tile: {len(audio_data)} bytes")
                        return audio_data
                    else:
                        error_text = await response.text()
                        raise Exception(f"ElevenLabs API error {response.status}: {error_text}")
            except Exception as e:
                logger.error(f"Failed to generate SFX tile: {e}")
                raise
    
    def _process_audio_tile(self, audio_data: bytes, target_sample_rate: int = 48000) -> np.ndarray:
        """Process audio tile to target format"""
        try:
            # Load audio from bytes
            audio, sr = librosa.load(io.BytesIO(audio_data), sr=None, mono=True)
            
            # Resample if necessary
            if sr != target_sample_rate:
                audio = librosa.resample(audio, orig_sr=sr, target_sr=target_sample_rate)
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            return audio
        except Exception as e:
            logger.error(f"Failed to process audio tile: {e}")
            raise
    
    def _create_crossfade(self, audio1: np.ndarray, audio2: np.ndarray, 
                         crossfade_duration: float, sample_rate: int) -> np.ndarray:
        """Create crossfade between two audio segments"""
        crossfade_samples = int(crossfade_duration * sample_rate)
        
        if len(audio1) < crossfade_samples or len(audio2) < crossfade_samples:
            # If segments are too short, just concatenate
            return np.concatenate([audio1, audio2])
        
        # Create fade curves
        fade_out = np.linspace(1.0, 0.0, crossfade_samples)
        fade_in = np.linspace(0.0, 1.0, crossfade_samples)
        
        # Apply crossfade
        audio1_faded = audio1[-crossfade_samples:] * fade_out
        audio2_faded = audio2[:crossfade_samples] * fade_in
        
        # Combine segments
        crossfaded = audio1_faded + audio2_faded
        
        # Concatenate: audio1 (without fade) + crossfaded + audio2 (without fade)
        result = np.concatenate([
            audio1[:-crossfade_samples],
            crossfaded,
            audio2[crossfade_samples:]
        ])
        
        return result
    
    def _stitch_tiles(self, tiles: List[np.ndarray], crossfade_duration: float, 
                     sample_rate: int, loopable: bool = False) -> np.ndarray:
        """Stitch audio tiles together with crossfades"""
        if not tiles:
            return np.array([])
        
        if len(tiles) == 1:
            return tiles[0]
        
        # Start with first tile
        result = tiles[0]
        
        # Stitch remaining tiles with crossfades
        for i, tile in enumerate(tiles[1:], 1):
            if loopable and i == len(tiles) - 1:
                # For loopable content, create seamless loop with first tile
                result = self._create_crossfade(result, tiles[0], crossfade_duration, sample_rate)
            else:
                # Regular crossfade between consecutive tiles
                result = self._create_crossfade(result, tile, crossfade_duration, sample_rate)
        
        return result
    
    def _make_loopable(self, audio: np.ndarray, crossfade_duration: float, 
                      sample_rate: int) -> np.ndarray:
        """Make audio loopable by creating seamless start/end transition"""
        crossfade_samples = int(crossfade_duration * sample_rate)
        
        if len(audio) < crossfade_samples * 2:
            # If audio is too short, just return as is
            return audio
        
        # Create fade curves
        fade_out = np.linspace(1.0, 0.0, crossfade_samples)
        fade_in = np.linspace(0.0, 1.0, crossfade_samples)
        
        # Apply crossfade to beginning and end
        audio_start = audio[:crossfade_samples] * fade_in
        audio_end = audio[-crossfade_samples:] * fade_out
        
        # Create seamless loop
        looped_audio = np.concatenate([
            audio_start + audio_end,  # Crossfaded start/end
            audio[crossfade_samples:-crossfade_samples]  # Middle section
        ])
        
        return looped_audio
    
    def _save_audio(self, audio: np.ndarray, file_path: str, sample_rate: int, 
                   bit_depth: int) -> None:
        """Save audio to file in specified format"""
        try:
            # Convert bit depth
            if bit_depth == 16:
                audio_int16 = (audio * 32767).astype(np.int16)
                sf.write(file_path, audio_int16, sample_rate, subtype='PCM_16')
            elif bit_depth == 24:
                audio_int24 = (audio * 8388607).astype(np.int32)
                sf.write(file_path, audio_int24, sample_rate, subtype='PCM_24')
            else:  # 32-bit float
                sf.write(file_path, audio, sample_rate, subtype='FLOAT')
            
            logger.info(f"Saved audio: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save audio: {e}")
            raise
    
    async def generate_sfx(self, request: SFXGenerationRequest, 
                          use_cache: bool = True) -> SFXGenerationResult:
        """
        Generate SFX audio from text prompt
        
        Args:
            request: SFX generation request parameters
            use_cache: Whether to use cached results
            
        Returns:
            SFX generation result with audio data
        """
        start_time = datetime.now()
        
        # Validate request
        if request.duration < self.min_duration:
            return SFXGenerationResult(
                success=False,
                error_message=f"Duration must be at least {self.min_duration} seconds"
            )
        
        if request.duration > self.max_duration:
            return SFXGenerationResult(
                success=False,
                error_message=f"Duration cannot exceed {self.max_duration} seconds"
            )
        
        # Check cache
        if use_cache:
            cache_key = self._generate_cache_key(request)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                logger.info(f"Using cached SFX result: {cache_key}")
                return cached_result
        
        try:
            # Calculate number of tiles needed
            tiles_needed = int(np.ceil(request.duration / self.max_duration_per_request))
            tile_duration = request.duration / tiles_needed
            
            logger.info(f"Generating {tiles_needed} tiles of {tile_duration:.2f}s each")
            
            # Generate tiles
            tiles = []
            for i in range(tiles_needed):
                # Use seed for deterministic generation
                tile_seed = request.seed + i if request.seed is not None else None
                
                # Generate tile
                tile_data = await self._generate_sfx_tile(
                    request.prompt, 
                    tile_duration, 
                    tile_seed
                )
                
                # Process tile
                tile_audio = self._process_audio_tile(tile_data, request.sample_rate)
                tiles.append(tile_audio)
                
                logger.info(f"Generated tile {i+1}/{tiles_needed}")
            
            # Stitch tiles together
            if request.loopable:
                # Make each tile loopable first
                loopable_tiles = []
                for tile in tiles:
                    loopable_tile = self._make_loopable(tile, request.crossfade_duration, request.sample_rate)
                    loopable_tiles.append(loopable_tile)
                tiles = loopable_tiles
            
            # Stitch tiles with crossfades
            final_audio = self._stitch_tiles(
                tiles, 
                request.crossfade_duration, 
                request.sample_rate, 
                request.loopable
            )
            
            # Ensure exact duration
            target_samples = int(request.duration * request.sample_rate)
            if len(final_audio) > target_samples:
                final_audio = final_audio[:target_samples]
            elif len(final_audio) < target_samples:
                # Pad with silence if needed
                padding = np.zeros(target_samples - len(final_audio))
                final_audio = np.concatenate([final_audio, padding])
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(
                suffix=f".{request.output_format}", 
                delete=False
            )
            temp_file.close()
            
            self._save_audio(final_audio, temp_file.name, request.sample_rate, request.bit_depth)
            
            # Read audio data
            with open(temp_file.name, 'rb') as f:
                audio_data = f.read()
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Create result
            result = SFXGenerationResult(
                success=True,
                audio_data=audio_data,
                file_path=temp_file.name,
                duration=request.duration,
                sample_rate=request.sample_rate,
                bit_depth=request.bit_depth,
                format=request.output_format,
                generation_time=generation_time,
                tiles_generated=tiles_needed,
                seed_used=request.seed
            )
            
            # Cache result
            if use_cache:
                self._cache_result(result, cache_key)
            
            logger.info(f"SFX generation completed: {generation_time:.2f}s, {tiles_needed} tiles")
            return result
            
        except Exception as e:
            logger.error(f"SFX generation failed: {e}")
            return SFXGenerationResult(
                success=False,
                error_message=str(e)
            )
    
    def clear_cache(self, pattern: str = "*") -> int:
        """Clear cached SFX results"""
        cleared_count = 0
        for cache_file in self.cache_dir.glob(f"sfx_{pattern}.wav"):
            try:
                cache_file.unlink()
                metadata_file = cache_file.with_suffix('.json')
                if metadata_file.exists():
                    metadata_file.unlink()
                cleared_count += 1
            except Exception as e:
                logger.warning(f"Failed to clear cache file {cache_file}: {e}")
        
        logger.info(f"Cleared {cleared_count} cached SFX results")
        return cleared_count
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache information"""
        cache_files = list(self.cache_dir.glob("sfx_*.wav"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "cache_dir": str(self.cache_dir),
            "total_files": len(cache_files),
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024)
        }
