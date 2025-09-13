"""
Tests for ElevenLabs SFX client
"""

import pytest
import tempfile
import os
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path
from datetime import datetime

from backend.services.elevenlabs_sfx import (
    ElevenLabsSFXClient, SFXGenerationRequest, SFXGenerationResult,
    WordTimestamp, SegmentTimestamp, AlignmentResult
)


class TestSFXGenerationRequest:
    """Test cases for SFXGenerationRequest"""
    
    def test_sfx_generation_request_creation(self):
        """Test SFX generation request creation"""
        request = SFXGenerationRequest(
            prompt="Rain falling on leaves",
            duration=30.0,
            seed=12345,
            loopable=True,
            crossfade_duration=1.0
        )
        
        assert request.prompt == "Rain falling on leaves"
        assert request.duration == 30.0
        assert request.seed == 12345
        assert request.loopable is True
        assert request.crossfade_duration == 1.0
        assert request.output_format == "wav"
        assert request.sample_rate == 48000
        assert request.bit_depth == 24


class TestElevenLabsSFXClient:
    """Test cases for ElevenLabsSFXClient"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.client = ElevenLabsSFXClient(api_key="test-key", cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_client_initialization(self):
        """Test client initialization"""
        assert self.client.api_key == "test-key"
        assert self.client.base_url == "https://api.elevenlabs.io/v1"
        assert self.client.max_duration_per_request == 22.0
        assert self.client.target_sample_rate == 48000
        assert self.client.target_bit_depth == 24
    
    def test_client_initialization_no_api_key(self):
        """Test client initialization without API key"""
        with patch('backend.services.elevenlabs_sfx.settings') as mock_settings:
            mock_settings.elevenlabs_api_key = None
            with pytest.raises(ValueError, match="ElevenLabs API key is required"):
                ElevenLabsSFXClient()
    
    def test_generate_cache_key(self):
        """Test cache key generation"""
        request = SFXGenerationRequest(
            prompt="Test prompt",
            duration=10.0,
            seed=12345,
            loopable=True
        )
        
        cache_key = self.client._generate_cache_key(request)
        assert cache_key.startswith("sfx_")
        assert cache_key.endswith(".wav")
        
        # Test deterministic cache keys
        cache_key2 = self.client._generate_cache_key(request)
        assert cache_key == cache_key2
    
    def test_cache_set_and_get(self):
        """Test caching and retrieving SFX results"""
        # Create test result
        result = SFXGenerationResult(
            success=True,
            audio_data=b"fake audio data",
            duration=10.0,
            sample_rate=48000,
            bit_depth=24,
            tiles_generated=1,
            seed_used=12345
        )
        
        # Create test request
        request = SFXGenerationRequest(
            prompt="Test prompt",
            duration=10.0,
            seed=12345
        )
        
        cache_key = self.client._generate_cache_key(request)
        
        # Cache result
        self.client._cache_result(result, cache_key)
        
        # Retrieve result
        cached_result = self.client._get_cached_result(cache_key)
        
        assert cached_result is not None
        assert cached_result.success is True
        assert cached_result.audio_data == b"fake audio data"
        assert cached_result.duration == 10.0
        assert cached_result.sample_rate == 48000
        assert cached_result.bit_depth == 24
        assert cached_result.tiles_generated == 1
        assert cached_result.seed_used == 12345
    
    def test_cache_miss(self):
        """Test cache miss scenario"""
        cache_key = "nonexistent_cache_key.wav"
        cached_result = self.client._get_cached_result(cache_key)
        assert cached_result is None
    
    @patch('backend.services.elevenlabs_sfx.aiohttp.ClientSession')
    async def test_generate_sfx_tile_success(self, mock_session):
        """Test successful SFX tile generation"""
        # Mock response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"fake audio data")
        
        # Mock session
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        # Test tile generation
        result = await self.client._generate_sfx_tile("Test prompt", 10.0, 12345)
        
        assert result == b"fake audio data"
        mock_session_instance.post.assert_called_once()
    
    @patch('backend.services.elevenlabs_sfx.aiohttp.ClientSession')
    async def test_generate_sfx_tile_api_error(self, mock_session):
        """Test SFX tile generation with API error"""
        # Mock error response
        mock_response = AsyncMock()
        mock_response.status = 400
        mock_response.text = AsyncMock(return_value="API Error")
        
        # Mock session
        mock_session_instance = AsyncMock()
        mock_session_instance.post.return_value.__aenter__.return_value = mock_response
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        # Test tile generation
        with pytest.raises(Exception, match="ElevenLabs API error 400"):
            await self.client._generate_sfx_tile("Test prompt", 10.0, 12345)
    
    @patch('backend.services.elevenlabs_sfx.librosa.load')
    def test_process_audio_tile(self, mock_librosa_load):
        """Test audio tile processing"""
        # Mock librosa load
        mock_audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_librosa_load.return_value = (mock_audio, 16000)
        
        # Test processing
        result = self.client._process_audio_tile(b"fake audio data", 48000)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
        mock_librosa_load.assert_called_once()
    
    def test_create_crossfade(self):
        """Test crossfade creation between audio segments"""
        # Create test audio segments
        audio1 = np.array([1.0, 1.0, 1.0, 1.0, 1.0])
        audio2 = np.array([0.5, 0.5, 0.5, 0.5, 0.5])
        
        # Test crossfade
        result = self.client._create_crossfade(audio1, audio2, 0.1, 48000)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > len(audio1) + len(audio2)  # Should be longer due to crossfade
    
    def test_create_crossfade_short_segments(self):
        """Test crossfade with segments too short for crossfade"""
        # Create short audio segments
        audio1 = np.array([1.0, 1.0])
        audio2 = np.array([0.5, 0.5])
        
        # Test crossfade
        result = self.client._create_crossfade(audio1, audio2, 1.0, 48000)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == len(audio1) + len(audio2)  # Should just concatenate
    
    def test_stitch_tiles(self):
        """Test stitching multiple audio tiles"""
        # Create test tiles
        tiles = [
            np.array([1.0, 1.0, 1.0]),
            np.array([0.5, 0.5, 0.5]),
            np.array([0.2, 0.2, 0.2])
        ]
        
        # Test stitching
        result = self.client._stitch_tiles(tiles, 0.1, 48000, False)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > sum(len(tile) for tile in tiles)  # Should be longer due to crossfades
    
    def test_stitch_tiles_loopable(self):
        """Test stitching tiles with loopable option"""
        # Create test tiles
        tiles = [
            np.array([1.0, 1.0, 1.0]),
            np.array([0.5, 0.5, 0.5])
        ]
        
        # Test stitching with loopable
        result = self.client._stitch_tiles(tiles, 0.1, 48000, True)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > sum(len(tile) for tile in tiles)
    
    def test_stitch_tiles_single(self):
        """Test stitching single tile"""
        tiles = [np.array([1.0, 1.0, 1.0])]
        
        result = self.client._stitch_tiles(tiles, 0.1, 48000, False)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == len(tiles[0])
    
    def test_stitch_tiles_empty(self):
        """Test stitching empty tile list"""
        tiles = []
        
        result = self.client._stitch_tiles(tiles, 0.1, 48000, False)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 0
    
    def test_make_loopable(self):
        """Test making audio loopable"""
        # Create test audio
        audio = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0])
        
        # Test making loopable
        result = self.client._make_loopable(audio, 0.1, 48000)
        
        assert isinstance(result, np.ndarray)
        assert len(result) > 0
    
    def test_make_loopable_short_audio(self):
        """Test making short audio loopable"""
        # Create short audio
        audio = np.array([1.0, 1.0])
        
        # Test making loopable
        result = self.client._make_loopable(audio, 1.0, 48000)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == len(audio)  # Should return unchanged
    
    @patch('backend.services.elevenlabs_sfx.sf.write')
    def test_save_audio(self, mock_sf_write):
        """Test saving audio to file"""
        # Create test audio
        audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        # Test saving
        self.client._save_audio(audio, "test.wav", 48000, 24)
        
        mock_sf_write.assert_called_once()
    
    @patch('backend.services.elevenlabs_sfx.sf.write')
    def test_save_audio_16bit(self, mock_sf_write):
        """Test saving audio in 16-bit format"""
        # Create test audio
        audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        # Test saving 16-bit
        self.client._save_audio(audio, "test.wav", 48000, 16)
        
        mock_sf_write.assert_called_once()
    
    @patch('backend.services.elevenlabs_sfx.sf.write')
    def test_save_audio_32bit(self, mock_sf_write):
        """Test saving audio in 32-bit format"""
        # Create test audio
        audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        
        # Test saving 32-bit
        self.client._save_audio(audio, "test.wav", 48000, 32)
        
        mock_sf_write.assert_called_once()
    
    @patch('backend.services.elevenlabs_sfx.ElevenLabsSFXClient._generate_sfx_tile')
    @patch('backend.services.elevenlabs_sfx.ElevenLabsSFXClient._process_audio_tile')
    @patch('backend.services.elevenlabs_sfx.ElevenLabsSFXClient._stitch_tiles')
    @patch('backend.services.elevenlabs_sfx.ElevenLabsSFXClient._save_audio')
    async def test_generate_sfx_success(self, mock_save, mock_stitch, mock_process, mock_generate):
        """Test successful SFX generation"""
        # Mock tile generation
        mock_generate.return_value = b"fake audio data"
        
        # Mock audio processing
        mock_audio = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
        mock_process.return_value = mock_audio
        
        # Mock stitching
        mock_stitch.return_value = mock_audio
        
        # Mock file operations
        with patch('tempfile.NamedTemporaryFile') as mock_temp:
            mock_temp.return_value.__enter__.return_value.name = "test.wav"
            with patch('builtins.open', mock_open()) as mock_file:
                mock_file.return_value.read.return_value = b"fake audio data"
                
                # Create request
                request = SFXGenerationRequest(
                    prompt="Test prompt",
                    duration=10.0,
                    seed=12345
                )
                
                # Test generation
                result = await self.client.generate_sfx(request, use_cache=False)
                
                assert result.success is True
                assert result.duration == 10.0
                assert result.seed_used == 12345
                assert result.tiles_generated == 1
    
    async def test_generate_sfx_duration_too_short(self):
        """Test SFX generation with duration too short"""
        request = SFXGenerationRequest(
            prompt="Test prompt",
            duration=0.5  # Too short
        )
        
        result = await self.client.generate_sfx(request, use_cache=False)
        
        assert result.success is False
        assert "Duration must be at least" in result.error_message
    
    async def test_generate_sfx_duration_too_long(self):
        """Test SFX generation with duration too long"""
        request = SFXGenerationRequest(
            prompt="Test prompt",
            duration=400.0  # Too long
        )
        
        result = await self.client.generate_sfx(request, use_cache=False)
        
        assert result.success is False
        assert "Duration cannot exceed" in result.error_message
    
    def test_clear_cache(self):
        """Test cache clearing"""
        # Create some test cache files
        cache_file1 = self.client.cache_dir / "sfx_test1.wav"
        cache_file2 = self.client.cache_dir / "sfx_test2.wav"
        cache_file1.write_bytes(b"fake data")
        cache_file2.write_bytes(b"fake data")
        
        # Test clearing cache
        cleared_count = self.client.clear_cache("test*")
        
        assert cleared_count == 2
        assert not cache_file1.exists()
        assert not cache_file2.exists()
    
    def test_get_cache_info(self):
        """Test getting cache information"""
        # Create some test cache files
        cache_file1 = self.client.cache_dir / "sfx_test1.wav"
        cache_file2 = self.client.cache_dir / "sfx_test2.wav"
        cache_file1.write_bytes(b"fake data 1")
        cache_file2.write_bytes(b"fake data 2")
        
        # Test getting cache info
        info = self.client.get_cache_info()
        
        assert info["total_files"] == 2
        assert info["total_size_bytes"] == len(b"fake data 1") + len(b"fake data 2")
        assert info["total_size_mb"] > 0


class TestSFXGenerationResult:
    """Test cases for SFXGenerationResult"""
    
    def test_sfx_generation_result_creation(self):
        """Test SFX generation result creation"""
        result = SFXGenerationResult(
            success=True,
            audio_data=b"fake audio data",
            duration=10.0,
            sample_rate=48000,
            bit_depth=24,
            tiles_generated=1,
            seed_used=12345
        )
        
        assert result.success is True
        assert result.audio_data == b"fake audio data"
        assert result.duration == 10.0
        assert result.sample_rate == 48000
        assert result.bit_depth == 24
        assert result.tiles_generated == 1
        assert result.seed_used == 12345
    
    def test_sfx_generation_result_failure(self):
        """Test SFX generation result for failure"""
        result = SFXGenerationResult(
            success=False,
            error_message="Generation failed"
        )
        
        assert result.success is False
        assert result.error_message == "Generation failed"
        assert result.audio_data is None


# Mock open function for testing
def mock_open(*args, **kwargs):
    """Mock open function for testing"""
    mock_file = MagicMock()
    mock_file.read.return_value = b"fake audio data"
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None
    return mock_file
