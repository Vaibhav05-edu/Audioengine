"""
Screenplay parser for extracting scenes, dialogue, and voice-over from screenplay text
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SceneType(str, Enum):
    """Scene type enumeration"""
    INT = "INT"
    EXT = "EXT"
    INT_EXT = "INT/EXT"
    EXT_INT = "EXT/INT"


class ElementType(str, Enum):
    """Screenplay element type enumeration"""
    SCENE_HEADING = "scene_heading"
    ACTION = "action"
    CHARACTER = "character"
    DIALOGUE = "dialogue"
    PARENTHETICAL = "parenthetical"
    TRANSITION = "transition"
    VOICE_OVER = "voice_over"
    UNKNOWN = "unknown"


@dataclass
class SceneHeading:
    """Scene heading data structure"""
    scene_type: SceneType
    location: str
    time_of_day: Optional[str] = None
    raw_text: str = ""
    
    def __post_init__(self):
        if not self.raw_text:
            self.raw_text = f"{self.scene_type.value}. {self.location}"
            if self.time_of_day:
                self.raw_text += f" - {self.time_of_day}"


@dataclass
class ScreenplayElement:
    """Individual screenplay element"""
    element_type: ElementType
    text: str
    line_number: int
    character_name: Optional[str] = None
    is_voice_over: bool = False


@dataclass
class ParsedScene:
    """Parsed scene data structure"""
    scene_number: int
    heading: SceneHeading
    elements: List[ScreenplayElement]
    dialogue: List[Dict[str, Any]]
    voice_over: List[Dict[str, Any]]
    action_text: str
    raw_text: str
    
    @property
    def name(self) -> str:
        """Generate scene name from heading"""
        return f"Scene {self.scene_number}: {self.heading.location}"
    
    @property
    def description(self) -> str:
        """Generate scene description"""
        desc_parts = [f"{self.heading.scene_type.value}. {self.heading.location}"]
        if self.heading.time_of_day:
            desc_parts.append(f"Time: {self.heading.time_of_day}")
        
        if self.dialogue:
            desc_parts.append(f"Dialogue: {len(self.dialogue)} exchanges")
        
        if self.voice_over:
            desc_parts.append(f"Voice-over: {len(self.voice_over)} segments")
        
        return " | ".join(desc_parts)


class ScreenplayParser:
    """Main screenplay parser class"""
    
    def __init__(self):
        # Scene heading pattern: INT/EXT. LOCATION - TIME OF DAY
        self.scene_heading_pattern = re.compile(
            r'^(INT|EXT|INT/EXT|EXT/INT)\.\s*([^-]+?)(?:\s*-\s*(.+))?$',
            re.IGNORECASE | re.MULTILINE
        )
        
        # Character name pattern (all caps, centered-ish)
        self.character_pattern = re.compile(
            r'^[A-Z][A-Z\s\.\-\']+$',
            re.MULTILINE
        )
        
        # Voice-over pattern
        self.voice_over_pattern = re.compile(
            r'^(V\.O\.|VO|VOICE OVER|VOICE-OVER)',
            re.IGNORECASE
        )
        
        # Parenthetical pattern
        self.parenthetical_pattern = re.compile(
            r'^\([^)]+\)$',
            re.MULTILINE
        )
        
        # Transition pattern
        self.transition_pattern = re.compile(
            r'^(FADE IN|FADE OUT|CUT TO|DISSOLVE TO|SMASH CUT|MATCH CUT|WIPE TO|IRIS IN|IRIS OUT)',
            re.IGNORECASE
        )
    
    def parse(self, screenplay_text: str) -> List[ParsedScene]:
        """
        Parse screenplay text into scenes
        
        Args:
            screenplay_text: Raw screenplay text
            
        Returns:
            List of parsed scenes
        """
        lines = screenplay_text.split('\n')
        scenes = []
        current_scene = None
        scene_number = 1
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Check for scene heading
            scene_heading = self._parse_scene_heading(line)
            if scene_heading:
                # Save previous scene if exists
                if current_scene:
                    scenes.append(current_scene)
                
                # Start new scene
                current_scene = ParsedScene(
                    scene_number=scene_number,
                    heading=scene_heading,
                    elements=[],
                    dialogue=[],
                    voice_over=[],
                    action_text="",
                    raw_text=""
                )
                scene_number += 1
                current_scene.elements.append(ScreenplayElement(
                    element_type=ElementType.SCENE_HEADING,
                    text=line,
                    line_number=i + 1
                ))
                current_scene.raw_text += line + "\n"
            
            elif current_scene:
                # Parse element within current scene
                element = self._parse_element(line, i + 1)
                current_scene.elements.append(element)
                current_scene.raw_text += line + "\n"
                
                # Process element based on type
                if element.element_type == ElementType.CHARACTER:
                    # Look ahead for dialogue or parenthetical
                    dialogue_text = ""
                    parenthetical = None
                    
                    # Check next line for parenthetical
                    if i + 1 < len(lines) and self.parenthetical_pattern.match(lines[i + 1].strip()):
                        parenthetical = lines[i + 1].strip()
                        current_scene.elements.append(ScreenplayElement(
                            element_type=ElementType.PARENTHETICAL,
                            text=parenthetical,
                            line_number=i + 2
                        ))
                        current_scene.raw_text += parenthetical + "\n"
                        i += 1
                    
                    # Collect dialogue lines
                    j = i + 1
                    while j < len(lines):
                        dialogue_line = lines[j].strip()
                        if not dialogue_line or self._is_element_start(dialogue_line):
                            break
                        dialogue_text += dialogue_line + " "
                        current_scene.elements.append(ScreenplayElement(
                            element_type=ElementType.DIALOGUE,
                            text=dialogue_line,
                            line_number=j + 1
                        ))
                        current_scene.raw_text += dialogue_line + "\n"
                        j += 1
                    
                    # Store dialogue
                    if dialogue_text.strip():
                        is_vo = element.is_voice_over
                        dialogue_entry = {
                            "character": element.character_name,
                            "text": dialogue_text.strip(),
                            "parenthetical": parenthetical,
                            "is_voice_over": is_vo,
                            "line_number": element.line_number
                        }
                        
                        if is_vo:
                            current_scene.voice_over.append(dialogue_entry)
                        else:
                            current_scene.dialogue.append(dialogue_entry)
                    
                    i = j - 1
                
                elif element.element_type == ElementType.ACTION:
                    current_scene.action_text += line + " "
            
            i += 1
        
        # Add final scene
        if current_scene:
            scenes.append(current_scene)
        
        return scenes
    
    def _parse_scene_heading(self, line: str) -> Optional[SceneHeading]:
        """Parse scene heading from line"""
        match = self.scene_heading_pattern.match(line)
        if not match:
            return None
        
        scene_type_str = match.group(1).upper()
        location = match.group(2).strip()
        time_of_day = match.group(3).strip() if match.group(3) else None
        
        # Map scene type
        scene_type_map = {
            "INT": SceneType.INT,
            "EXT": SceneType.EXT,
            "INT/EXT": SceneType.INT_EXT,
            "EXT/INT": SceneType.EXT_INT
        }
        
        scene_type = scene_type_map.get(scene_type_str, SceneType.INT)
        
        return SceneHeading(
            scene_type=scene_type,
            location=location,
            time_of_day=time_of_day,
            raw_text=line
        )
    
    def _parse_element(self, line: str, line_number: int) -> ScreenplayElement:
        """Parse individual screenplay element"""
        # Check for character name
        if self.character_pattern.match(line) and not self._is_element_start(line):
            character_name = line.strip()
            is_vo = bool(self.voice_over_pattern.search(character_name))
            
            return ScreenplayElement(
                element_type=ElementType.CHARACTER,
                text=line,
                line_number=line_number,
                character_name=character_name,
                is_voice_over=is_vo
            )
        
        # Check for transition
        if self.transition_pattern.match(line):
            return ScreenplayElement(
                element_type=ElementType.TRANSITION,
                text=line,
                line_number=line_number
            )
        
        # Check for parenthetical
        if self.parenthetical_pattern.match(line):
            return ScreenplayElement(
                element_type=ElementType.PARENTHETICAL,
                text=line,
                line_number=line_number
            )
        
        # Default to action
        return ScreenplayElement(
            element_type=ElementType.ACTION,
            text=line,
            line_number=line_number
        )
    
    def _is_element_start(self, line: str) -> bool:
        """Check if line starts a new element type"""
        return (
            self.scene_heading_pattern.match(line) or
            self.character_pattern.match(line) or
            self.transition_pattern.match(line) or
            self.parenthetical_pattern.match(line)
        )


class ScenePersistenceManager:
    """Manager for persisting parsed scenes to database"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def persist_scenes(self, scenes: List[ParsedScene], project_id: int) -> List[Dict[str, Any]]:
        """
        Persist parsed scenes to database
        
        Args:
            scenes: List of parsed scenes
            project_id: Project ID to associate scenes with
            
        Returns:
            List of created scene data
        """
        from ..models import Scene
        
        created_scenes = []
        
        for parsed_scene in scenes:
            # Create timeline JSON from scene data
            timeline_json = self._create_timeline_json(parsed_scene)
            
            # Create scene object
            scene = Scene(
                name=parsed_scene.name,
                description=parsed_scene.description,
                scene_number=parsed_scene.scene_number,
                location=parsed_scene.heading.location,
                time_of_day=parsed_scene.heading.time_of_day,
                project_id=project_id,
                timeline_json=timeline_json
            )
            
            self.db.add(scene)
            self.db.commit()
            self.db.refresh(scene)
            
            created_scenes.append({
                "id": scene.id,
                "name": scene.name,
                "scene_number": scene.scene_number,
                "location": scene.location,
                "time_of_day": scene.time_of_day,
                "dialogue_count": len(parsed_scene.dialogue),
                "voice_over_count": len(parsed_scene.voice_over)
            })
        
        return created_scenes
    
    def _create_timeline_json(self, parsed_scene: ParsedScene) -> Dict[str, Any]:
        """Create timeline JSON from parsed scene data"""
        tracks = []
        
        # Create dialogue track
        if parsed_scene.dialogue:
            dialogue_assets = []
            for i, dialogue in enumerate(parsed_scene.dialogue):
                dialogue_assets.append({
                    "id": f"dialogue_{i}",
                    "name": f"{dialogue['character']} - Line {i+1}",
                    "character": dialogue['character'],
                    "text": dialogue['text'],
                    "parenthetical": dialogue.get('parenthetical'),
                    "start_time": 0.0,  # Will be calculated based on timing
                    "end_time": 0.0,
                    "line_number": dialogue['line_number']
                })
            
            tracks.append({
                "name": "Dialogue Track",
                "type": "dialogue",
                "assets": dialogue_assets,
                "volume": 1.0,
                "pan": 0.0,
                "mute": False,
                "solo": False
            })
        
        # Create voice-over track
        if parsed_scene.voice_over:
            vo_assets = []
            for i, vo in enumerate(parsed_scene.voice_over):
                vo_assets.append({
                    "id": f"vo_{i}",
                    "name": f"{vo['character']} V.O. - Line {i+1}",
                    "character": vo['character'],
                    "text": vo['text'],
                    "parenthetical": vo.get('parenthetical'),
                    "start_time": 0.0,
                    "end_time": 0.0,
                    "line_number": vo['line_number'],
                    "is_voice_over": True
                })
            
            tracks.append({
                "name": "Voice-Over Track",
                "type": "dialogue",  # VO is still dialogue type
                "assets": vo_assets,
                "volume": 0.8,  # Slightly lower volume for VO
                "pan": 0.0,
                "mute": False,
                "solo": False
            })
        
        return {
            "version": "1.0",
            "duration": 0.0,  # Will be calculated based on content
            "sample_rate": 44100,
            "tracks": tracks,
            "metadata": {
                "scene_type": parsed_scene.heading.scene_type.value,
                "location": parsed_scene.heading.location,
                "time_of_day": parsed_scene.heading.time_of_day,
                "total_dialogue": len(parsed_scene.dialogue),
                "total_voice_over": len(parsed_scene.voice_over),
                "raw_text": parsed_scene.raw_text.strip()
            }
        }
