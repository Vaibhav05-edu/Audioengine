"""
WhisperX alignment service for voice-over word-level timestamps
"""

import os
import json
import hashlib
import tempfile
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

import torch
import whisperx
import librosa
import numpy as np
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Scene, Asset

logger = logging.getLogger(__name__)


@dataclass
class WordTimestamp:
    """Word-level timestamp data structure"""
    word: str
    start: float
    end: float
    confidence: float
    speaker: Optional[str] = None


@dataclass
class SegmentTimestamp:
    """Segment-level timestamp data structure"""
    text: str
    start: float
    end: float
    confidence: float
    words: List[WordTimestamp]
    speaker: Optional[str] = None


@dataclass
class AlignmentResult:
    """Complete alignment result"""
    scene_id: int
    asset_id: int
    language: str
    segments: List[SegmentTimestamp]
    total_duration: float
    processing_time: float
    model_used: str
    created_at: datetime
    cache_key: str


class AlignmentCache:
    """Cache manager for alignment results"""
    
    def __init__(self, cache_dir: str = None):
        self.cache_dir = Path(cache_dir or settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_cache_key(self, scene_id: int, asset_id: int, file_path: str) -> str:
        """Generate cache key based on scene, asset, and file content"""
        # Create hash based on file content and metadata
        file_stat = os.stat(file_path)
        content_hash = hashlib.md5(f"{scene_id}_{asset_id}_{file_stat.st_mtime}_{file_stat.st_size}".encode()).hexdigest()
        return f"alignment_{scene_id}_{asset_id}_{content_hash}.json"
    
    def get(self, scene_id: int, asset_id: int, file_path: str) -> Optional[AlignmentResult]:
        """Get cached alignment result"""
        cache_key = self._generate_cache_key(scene_id, asset_id, file_path)
        cache_file = self.cache_dir / cache_key
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Convert back to dataclass
            segments = []
            for seg_data in data['segments']:
                words = [WordTimestamp(**word_data) for word_data in seg_data['words']]
                segments.append(SegmentTimestamp(
                    text=seg_data['text'],
                    start=seg_data['start'],
                    end=seg_data['end'],
                    confidence=seg_data['confidence'],
                    words=words,
                    speaker=seg_data.get('speaker')
                ))
            
            return AlignmentResult(
                scene_id=data['scene_id'],
                asset_id=data['asset_id'],
                language=data['language'],
                segments=segments,
                total_duration=data['total_duration'],
                processing_time=data['processing_time'],
                model_used=data['model_used'],
                created_at=datetime.fromisoformat(data['created_at']),
                cache_key=data['cache_key']
            )
        except Exception as e:
            logger.warning(f"Failed to load cached alignment result: {e}")
            return None
    
    def set(self, result: AlignmentResult, file_path: str) -> None:
        """Cache alignment result"""
        cache_file = self.cache_dir / result.cache_key
        
        try:
            # Convert to serializable format
            data = {
                'scene_id': result.scene_id,
                'asset_id': result.asset_id,
                'language': result.language,
                'segments': [
                    {
                        'text': seg.text,
                        'start': seg.start,
                        'end': seg.end,
                        'confidence': seg.confidence,
                        'words': [asdict(word) for word in seg.words],
                        'speaker': seg.speaker
                    }
                    for seg in result.segments
                ],
                'total_duration': result.total_duration,
                'processing_time': result.processing_time,
                'model_used': result.model_used,
                'created_at': result.created_at.isoformat(),
                'cache_key': result.cache_key
            }
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Cached alignment result: {cache_file}")
        except Exception as e:
            logger.error(f"Failed to cache alignment result: {e}")
    
    def clear(self, scene_id: int, asset_id: int) -> None:
        """Clear cached alignment result"""
        pattern = f"alignment_{scene_id}_{asset_id}_*.json"
        for cache_file in self.cache_dir.glob(pattern):
            cache_file.unlink()
            logger.info(f"Cleared cached alignment: {cache_file}")


class WhisperXAlignmentService:
    """WhisperX-based alignment service"""
    
    def __init__(self, cache_dir: str = None):
        self.cache = AlignmentCache(cache_dir)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        # Load models
        self.whisper_model = None
        self.align_model = None
        self.align_metadata = None
        
        logger.info(f"WhisperX Alignment Service initialized on {self.device}")
    
    def _load_models(self, language: str = "en"):
        """Load WhisperX models"""
        if self.whisper_model is None:
            logger.info("Loading WhisperX models...")
            self.whisper_model = whisperx.load_model(
                "large-v2", 
                self.device, 
                compute_type=self.compute_type,
                language=language
            )
        
        if self.align_model is None:
            logger.info("Loading alignment models...")
            self.align_model, self.align_metadata = whisperx.load_align_model(
                language_code=language, 
                device=self.device
            )
    
    def _preprocess_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """Preprocess audio file for WhisperX"""
        try:
            # Load audio with librosa
            audio, sr = librosa.load(file_path, sr=16000, mono=True)
            
            # Ensure audio is in the right format
            if len(audio.shape) > 1:
                audio = librosa.to_mono(audio)
            
            # Normalize audio
            audio = librosa.util.normalize(audio)
            
            return audio, sr
        except Exception as e:
            logger.error(f"Failed to preprocess audio {file_path}: {e}")
            raise
    
    def _detect_language(self, audio: np.ndarray) -> str:
        """Detect language of audio"""
        try:
            # Use WhisperX to detect language
            result = whisperx.transcribe(
                self.whisper_model, 
                audio, 
                batch_size=16,
                language=None  # Auto-detect
            )
            return result.get("language", "en")
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return "en"  # Default to English
    
    def align_audio(self, file_path: str, scene_id: int, asset_id: int, 
                   language: str = None, force_reprocess: bool = False) -> AlignmentResult:
        """
        Align audio file and return word-level timestamps
        
        Args:
            file_path: Path to audio file
            scene_id: Scene ID
            asset_id: Asset ID
            language: Language code (auto-detect if None)
            force_reprocess: Force reprocessing even if cached
            
        Returns:
            AlignmentResult with word-level timestamps
        """
        start_time = datetime.now()
        
        # Check cache first
        if not force_reprocess:
            cached_result = self.cache.get(scene_id, asset_id, file_path)
            if cached_result:
                logger.info(f"Using cached alignment result for scene {scene_id}, asset {asset_id}")
                return cached_result
        
        try:
            # Preprocess audio
            audio, sr = self._preprocess_audio(file_path)
            
            # Detect language if not provided
            if language is None:
                language = self._detect_language(audio)
            
            # Load models
            self._load_models(language)
            
            # Transcribe audio
            logger.info(f"Transcribing audio for scene {scene_id}, asset {asset_id}")
            result = whisperx.transcribe(
                self.whisper_model, 
                audio, 
                batch_size=16,
                language=language
            )
            
            # Align transcript
            logger.info(f"Aligning transcript for scene {scene_id}, asset {asset_id}")
            result = whisperx.align(
                result["segments"], 
                self.align_model, 
                self.align_metadata, 
                audio, 
                self.device,
                return_char_alignments=False
            )
            
            # Convert to our data structures
            segments = []
            for seg in result["segments"]:
                words = []
                for word in seg.get("words", []):
                    words.append(WordTimestamp(
                        word=word["word"],
                        start=word["start"],
                        end=word["end"],
                        confidence=word.get("score", 0.0),
                        speaker=word.get("speaker")
                    ))
                
                segments.append(SegmentTimestamp(
                    text=seg["text"],
                    start=seg["start"],
                    end=seg["end"],
                    confidence=seg.get("score", 0.0),
                    words=words,
                    speaker=seg.get("speaker")
                ))
            
            # Create result
            processing_time = (datetime.now() - start_time).total_seconds()
            cache_key = self.cache._generate_cache_key(scene_id, asset_id, file_path)
            
            alignment_result = AlignmentResult(
                scene_id=scene_id,
                asset_id=asset_id,
                language=language,
                segments=segments,
                total_duration=segments[-1].end if segments else 0.0,
                processing_time=processing_time,
                model_used="whisperx-large-v2",
                created_at=datetime.now(),
                cache_key=cache_key
            )
            
            # Cache result
            self.cache.set(alignment_result, file_path)
            
            logger.info(f"Alignment completed for scene {scene_id}, asset {asset_id} in {processing_time:.2f}s")
            return alignment_result
            
        except Exception as e:
            logger.error(f"Alignment failed for scene {scene_id}, asset {asset_id}: {e}")
            raise
    
    def align_scene_vo(self, scene_id: int, db: Session, 
                      language: str = None, force_reprocess: bool = False) -> Dict[str, Any]:
        """
        Align all voice-over assets in a scene
        
        Args:
            scene_id: Scene ID
            db: Database session
            language: Language code (auto-detect if None)
            force_reprocess: Force reprocessing even if cached
            
        Returns:
            Dictionary with alignment results for all VO assets
        """
        # Get scene and VO assets
        scene = db.query(Scene).filter(Scene.id == scene_id).first()
        if not scene:
            raise ValueError(f"Scene {scene_id} not found")
        
        vo_assets = db.query(Asset).filter(
            Asset.scene_id == scene_id,
            Asset.asset_type == "dialogue"  # VO is stored as dialogue type
        ).all()
        
        if not vo_assets:
            logger.warning(f"No voice-over assets found for scene {scene_id}")
            return {"scene_id": scene_id, "alignments": [], "message": "No VO assets found"}
        
        results = []
        for asset in vo_assets:
            try:
                # Check if this is actually a VO asset (has VO in name or metadata)
                is_vo = (
                    "V.O." in asset.name.upper() or 
                    "VOICE OVER" in asset.name.upper() or
                    "VOICE-OVER" in asset.name.upper() or
                    (asset.metadata and asset.metadata.get("is_voice_over", False))
                )
                
                if not is_vo:
                    continue
                
                # Check if file exists
                if not os.path.exists(asset.file_path):
                    logger.warning(f"Audio file not found: {asset.file_path}")
                    continue
                
                # Align audio
                alignment_result = self.align_audio(
                    asset.file_path, 
                    scene_id, 
                    asset.id, 
                    language, 
                    force_reprocess
                )
                
                results.append({
                    "asset_id": asset.id,
                    "asset_name": asset.name,
                    "file_path": asset.file_path,
                    "alignment": alignment_result,
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"Failed to align asset {asset.id}: {e}")
                results.append({
                    "asset_id": asset.id,
                    "asset_name": asset.name,
                    "file_path": asset.file_path,
                    "error": str(e),
                    "success": False
                })
        
        return {
            "scene_id": scene_id,
            "scene_name": scene.name,
            "alignments": results,
            "total_assets": len(vo_assets),
            "successful_alignments": len([r for r in results if r["success"]]),
            "failed_alignments": len([r for r in results if not r["success"]])
        }
    
    def get_alignment_summary(self, alignment_result: AlignmentResult) -> Dict[str, Any]:
        """Get summary statistics for alignment result"""
        total_words = sum(len(seg.words) for seg in alignment_result.segments)
        avg_confidence = np.mean([word.confidence for seg in alignment_result.segments for word in seg.words])
        
        return {
            "scene_id": alignment_result.scene_id,
            "asset_id": alignment_result.asset_id,
            "language": alignment_result.language,
            "total_segments": len(alignment_result.segments),
            "total_words": total_words,
            "total_duration": alignment_result.total_duration,
            "average_confidence": float(avg_confidence),
            "processing_time": alignment_result.processing_time,
            "model_used": alignment_result.model_used,
            "created_at": alignment_result.created_at.isoformat()
        }
