"""
Tests for alignment service
"""

import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from datetime import datetime

from backend.services.alignment import (
    WhisperXAlignmentService, AlignmentCache, WordTimestamp, 
    SegmentTimestamp, AlignmentResult
)


class TestAlignmentCache:
    """Test cases for AlignmentCache"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache = AlignmentCache(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        cache_key = self.cache._generate_cache_key(1, 2, "/path/to/file.wav")
        assert cache_key.startswith("alignment_1_2_")
        assert cache_key.endswith(".json")
    
    def test_cache_set_and_get(self):
        """Test caching and retrieving alignment results"""
        # Create test alignment result
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
            WordTimestamp(word="world", start=0.5, end=1.0, confidence=0.8)
        ]
        segments = [
            SegmentTimestamp(
                text="Hello world",
                start=0.0,
                end=1.0,
                confidence=0.85,
                words=words
            )
        ]
        
        result = AlignmentResult(
            scene_id=1,
            asset_id=2,
            language="en",
            segments=segments,
            total_duration=1.0,
            processing_time=2.5,
            model_used="whisperx-large-v2",
            created_at=datetime.now(),
            cache_key="test_key"
        )
        
        # Test file path
        test_file = os.path.join(self.temp_dir, "test.wav")
        with open(test_file, "w") as f:
            f.write("test audio content")
        
        # Cache result
        self.cache.set(result, test_file)
        
        # Retrieve result
        cached_result = self.cache.get(1, 2, test_file)
        
        assert cached_result is not None
        assert cached_result.scene_id == 1
        assert cached_result.asset_id == 2
        assert cached_result.language == "en"
        assert len(cached_result.segments) == 1
        assert cached_result.segments[0].text == "Hello world"
        assert len(cached_result.segments[0].words) == 2
        assert cached_result.segments[0].words[0].word == "Hello"
        assert cached_result.segments[0].words[1].word == "world"
    
    def test_cache_miss(self):
        """Test cache miss scenario"""
        test_file = os.path.join(self.temp_dir, "nonexistent.wav")
        cached_result = self.cache.get(1, 2, test_file)
        assert cached_result is None
    
    def test_cache_clear(self):
        """Test cache clearing"""
        # Create test file
        test_file = os.path.join(self.temp_dir, "test.wav")
        with open(test_file, "w") as f:
            f.write("test audio content")
        
        # Create and cache result
        result = AlignmentResult(
            scene_id=1,
            asset_id=2,
            language="en",
            segments=[],
            total_duration=0.0,
            processing_time=0.0,
            model_used="test",
            created_at=datetime.now(),
            cache_key="test_key"
        )
        
        self.cache.set(result, test_file)
        
        # Verify cache file exists
        cache_files = list(Path(self.temp_dir).glob("alignment_1_2_*.json"))
        assert len(cache_files) == 1
        
        # Clear cache
        self.cache.clear(1, 2)
        
        # Verify cache file is gone
        cache_files = list(Path(self.temp_dir).glob("alignment_1_2_*.json"))
        assert len(cache_files) == 0


class TestWhisperXAlignmentService:
    """Test cases for WhisperXAlignmentService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.service = WhisperXAlignmentService(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('backend.services.alignment.whisperx.load_model')
    @patch('backend.services.alignment.whisperx.load_align_model')
    @patch('backend.services.alignment.whisperx.transcribe')
    @patch('backend.services.alignment.whisperx.align')
    @patch('backend.services.alignment.librosa.load')
    def test_align_audio_success(self, mock_librosa_load, mock_align, mock_transcribe, 
                                mock_load_align_model, mock_load_model):
        """Test successful audio alignment"""
        # Mock audio data
        mock_audio = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_librosa_load.return_value = (mock_audio, 16000)
        
        # Mock WhisperX models
        mock_whisper_model = Mock()
        mock_align_model = Mock()
        mock_align_metadata = Mock()
        mock_load_model.return_value = mock_whisper_model
        mock_load_align_model.return_value = (mock_align_model, mock_align_metadata)
        
        # Mock transcription result
        mock_transcribe.return_value = {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 1.0,
                    "score": 0.9
                }
            ],
            "language": "en"
        }
        
        # Mock alignment result
        mock_align.return_value = {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 1.0,
                    "score": 0.9,
                    "words": [
                        {
                            "word": "Hello",
                            "start": 0.0,
                            "end": 0.5,
                            "score": 0.9
                        },
                        {
                            "word": "world",
                            "start": 0.5,
                            "end": 1.0,
                            "score": 0.8
                        }
                    ]
                }
            ]
        }
        
        # Create test audio file
        test_file = os.path.join(self.temp_dir, "test.wav")
        with open(test_file, "w") as f:
            f.write("test audio content")
        
        # Test alignment
        result = self.service.align_audio(test_file, 1, 2, "en", False)
        
        # Verify result
        assert result.scene_id == 1
        assert result.asset_id == 2
        assert result.language == "en"
        assert len(result.segments) == 1
        assert result.segments[0].text == "Hello world"
        assert len(result.segments[0].words) == 2
        assert result.segments[0].words[0].word == "Hello"
        assert result.segments[0].words[1].word == "world"
        assert result.total_duration == 1.0
        assert result.model_used == "whisperx-large-v2"
        
        # Verify models were loaded
        mock_load_model.assert_called_once()
        mock_load_align_model.assert_called_once()
        
        # Verify transcription and alignment were called
        mock_transcribe.assert_called_once()
        mock_align.assert_called_once()
    
    @patch('backend.services.alignment.whisperx.load_model')
    @patch('backend.services.alignment.whisperx.load_align_model')
    @patch('backend.services.alignment.whisperx.transcribe')
    @patch('backend.services.alignment.librosa.load')
    def test_align_audio_with_caching(self, mock_librosa_load, mock_transcribe, 
                                    mock_load_align_model, mock_load_model):
        """Test audio alignment with caching"""
        # Mock audio data
        mock_audio = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_librosa_load.return_value = (mock_audio, 16000)
        
        # Mock WhisperX models
        mock_whisper_model = Mock()
        mock_align_model = Mock()
        mock_align_metadata = Mock()
        mock_load_model.return_value = mock_whisper_model
        mock_load_align_model.return_value = (mock_align_model, mock_align_metadata)
        
        # Mock transcription result
        mock_transcribe.return_value = {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 1.0,
                    "score": 0.9
                }
            ],
            "language": "en"
        }
        
        # Create test audio file
        test_file = os.path.join(self.temp_dir, "test.wav")
        with open(test_file, "w") as f:
            f.write("test audio content")
        
        # First alignment (should process)
        result1 = self.service.align_audio(test_file, 1, 2, "en", False)
        
        # Second alignment (should use cache)
        result2 = self.service.align_audio(test_file, 1, 2, "en", False)
        
        # Verify both results are the same
        assert result1.scene_id == result2.scene_id
        assert result1.asset_id == result2.asset_id
        assert result1.language == result2.language
        
        # Verify transcription was only called once (cached on second call)
        assert mock_transcribe.call_count == 1
    
    @patch('backend.services.alignment.librosa.load')
    def test_align_audio_file_not_found(self, mock_librosa_load):
        """Test alignment with non-existent file"""
        test_file = os.path.join(self.temp_dir, "nonexistent.wav")
        
        with pytest.raises(Exception):
            self.service.align_audio(test_file, 1, 2, "en", False)
    
    def test_get_alignment_summary(self):
        """Test alignment summary generation"""
        # Create test alignment result
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
            WordTimestamp(word="world", start=0.5, end=1.0, confidence=0.8)
        ]
        segments = [
            SegmentTimestamp(
                text="Hello world",
                start=0.0,
                end=1.0,
                confidence=0.85,
                words=words
            )
        ]
        
        result = AlignmentResult(
            scene_id=1,
            asset_id=2,
            language="en",
            segments=segments,
            total_duration=1.0,
            processing_time=2.5,
            model_used="whisperx-large-v2",
            created_at=datetime.now(),
            cache_key="test_key"
        )
        
        summary = self.service.get_alignment_summary(result)
        
        assert summary["scene_id"] == 1
        assert summary["asset_id"] == 2
        assert summary["language"] == "en"
        assert summary["total_segments"] == 1
        assert summary["total_words"] == 2
        assert summary["total_duration"] == 1.0
        assert summary["average_confidence"] == 0.85
        assert summary["processing_time"] == 2.5
        assert summary["model_used"] == "whisperx-large-v2"


class TestAlignmentDataStructures:
    """Test cases for alignment data structures"""
    
    def test_word_timestamp(self):
        """Test WordTimestamp dataclass"""
        word = WordTimestamp(
            word="Hello",
            start=0.0,
            end=0.5,
            confidence=0.9,
            speaker="John"
        )
        
        assert word.word == "Hello"
        assert word.start == 0.0
        assert word.end == 0.5
        assert word.confidence == 0.9
        assert word.speaker == "John"
    
    def test_segment_timestamp(self):
        """Test SegmentTimestamp dataclass"""
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
            WordTimestamp(word="world", start=0.5, end=1.0, confidence=0.8)
        ]
        
        segment = SegmentTimestamp(
            text="Hello world",
            start=0.0,
            end=1.0,
            confidence=0.85,
            words=words,
            speaker="John"
        )
        
        assert segment.text == "Hello world"
        assert segment.start == 0.0
        assert segment.end == 1.0
        assert segment.confidence == 0.85
        assert len(segment.words) == 2
        assert segment.speaker == "John"
    
    def test_alignment_result(self):
        """Test AlignmentResult dataclass"""
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.5, confidence=0.9),
            WordTimestamp(word="world", start=0.5, end=1.0, confidence=0.8)
        ]
        segments = [
            SegmentTimestamp(
                text="Hello world",
                start=0.0,
                end=1.0,
                confidence=0.85,
                words=words
            )
        ]
        
        result = AlignmentResult(
            scene_id=1,
            asset_id=2,
            language="en",
            segments=segments,
            total_duration=1.0,
            processing_time=2.5,
            model_used="whisperx-large-v2",
            created_at=datetime.now(),
            cache_key="test_key"
        )
        
        assert result.scene_id == 1
        assert result.asset_id == 2
        assert result.language == "en"
        assert len(result.segments) == 1
        assert result.total_duration == 1.0
        assert result.processing_time == 2.5
        assert result.model_used == "whisperx-large-v2"
        assert result.cache_key == "test_key"


class TestAlignmentServiceIntegration:
    """Integration tests for alignment service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.service = WhisperXAlignmentService(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('backend.services.alignment.whisperx.load_model')
    @patch('backend.services.alignment.whisperx.load_align_model')
    @patch('backend.services.alignment.whisperx.transcribe')
    @patch('backend.services.alignment.whisperx.align')
    @patch('backend.services.alignment.librosa.load')
    def test_align_scene_vo_mock(self, mock_librosa_load, mock_align, mock_transcribe, 
                                mock_load_align_model, mock_load_model):
        """Test aligning all VO assets in a scene (mocked)"""
        # Mock audio data
        mock_audio = [0.1, 0.2, 0.3, 0.4, 0.5]
        mock_librosa_load.return_value = (mock_audio, 16000)
        
        # Mock WhisperX models
        mock_whisper_model = Mock()
        mock_align_model = Mock()
        mock_align_metadata = Mock()
        mock_load_model.return_value = mock_whisper_model
        mock_load_align_model.return_value = (mock_align_model, mock_align_metadata)
        
        # Mock transcription result
        mock_transcribe.return_value = {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 1.0,
                    "score": 0.9
                }
            ],
            "language": "en"
        }
        
        # Mock alignment result
        mock_align.return_value = {
            "segments": [
                {
                    "text": "Hello world",
                    "start": 0.0,
                    "end": 1.0,
                    "score": 0.9,
                    "words": [
                        {
                            "word": "Hello",
                            "start": 0.0,
                            "end": 0.5,
                            "score": 0.9
                        },
                        {
                            "word": "world",
                            "start": 0.5,
                            "end": 1.0,
                            "score": 0.8
                        }
                    ]
                }
            ]
        }
        
        # Create mock database session and scene
        mock_db = Mock()
        mock_scene = Mock()
        mock_scene.id = 1
        mock_scene.name = "Test Scene"
        
        # Create mock VO assets
        mock_asset1 = Mock()
        mock_asset1.id = 1
        mock_asset1.name = "JOHN (V.O.)"
        mock_asset1.file_path = os.path.join(self.temp_dir, "vo1.wav")
        mock_asset1.metadata = {"is_voice_over": True}
        
        mock_asset2 = Mock()
        mock_asset2.id = 2
        mock_asset2.name = "MARY (VOICE OVER)"
        mock_asset2.file_path = os.path.join(self.temp_dir, "vo2.wav")
        mock_asset2.metadata = {"is_voice_over": True}
        
        # Create test audio files
        with open(mock_asset1.file_path, "w") as f:
            f.write("test audio content 1")
        with open(mock_asset2.file_path, "w") as f:
            f.write("test audio content 2")
        
        # Mock database query
        mock_db.query.return_value.filter.return_value.all.return_value = [mock_asset1, mock_asset2]
        mock_db.query.return_value.filter.return_value.first.return_value = mock_scene
        
        # Test scene VO alignment
        result = self.service.align_scene_vo(1, mock_db, "en", False)
        
        # Verify result
        assert result["scene_id"] == 1
        assert result["scene_name"] == "Test Scene"
        assert len(result["alignments"]) == 2
        assert result["total_assets"] == 2
        assert result["successful_alignments"] == 2
        assert result["failed_alignments"] == 0
        
        # Verify both assets were processed
        assert result["alignments"][0]["asset_id"] == 1
        assert result["alignments"][0]["success"] is True
        assert result["alignments"][1]["asset_id"] == 2
        assert result["alignments"][1]["success"] is True
