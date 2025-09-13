"""
Prompt generator for ambience and SFX from scene analysis
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import spacy
from collections import Counter

from ..config import settings

logger = logging.getLogger(__name__)


@dataclass
class SceneAnalysis:
    """Scene analysis results"""
    scene_heading: str
    location: str
    time_of_day: str
    mood: Optional[str]
    verbs: List[str]
    nouns: List[str]
    adjectives: List[str]
    action_words: List[str]
    sound_cues: List[str]
    environment_cues: List[str]


@dataclass
class GeneratedPrompt:
    """Generated prompt with metadata"""
    prompt: str
    prompt_type: str  # "ambience" or "sfx"
    confidence: float
    source_elements: List[str]
    template_used: str
    manual_override: bool = False
    override_reason: Optional[str] = None


@dataclass
class FXPlanPrompts:
    """FX Plan prompts structure"""
    scene_id: int
    scene_name: str
    generated_at: datetime
    ambience_prompts: List[GeneratedPrompt]
    sfx_prompts: List[GeneratedPrompt]
    manual_overrides: Dict[str, str]
    analysis_summary: SceneAnalysis


class PromptTemplates:
    """PRD starter templates for prompt generation"""
    
    # Ambience templates
    AMBIENCE_TEMPLATES = {
        "location": {
            "forest": [
                "Deep forest ambience with rustling leaves and distant bird calls",
                "Woodland atmosphere with gentle wind through trees",
                "Forest soundscape with natural wildlife sounds"
            ],
            "city": [
                "Urban city ambience with traffic and distant conversations",
                "City street atmosphere with cars and pedestrian sounds",
                "Metropolitan ambience with urban life sounds"
            ],
            "beach": [
                "Ocean waves gently lapping against the shore",
                "Beach ambience with seagulls and distant waves",
                "Coastal atmosphere with wind and water sounds"
            ],
            "mountain": [
                "Mountain air with gentle wind and distant echoes",
                "High altitude ambience with natural mountain sounds",
                "Mountainous terrain with wind and wildlife"
            ],
            "desert": [
                "Desert wind with sand and distant animal calls",
                "Arid landscape ambience with natural desert sounds",
                "Desert atmosphere with wind and sparse wildlife"
            ],
            "rain": [
                "Gentle rain falling on various surfaces",
                "Rainy day ambience with water droplets",
                "Precipitation soundscape with natural rain sounds"
            ],
            "snow": [
                "Snow falling with muffled winter sounds",
                "Winter landscape with snow and wind",
                "Cold weather ambience with snow and ice"
            ]
        },
        "time": {
            "morning": [
                "Early morning ambience with dawn sounds",
                "Morning atmosphere with gentle awakening sounds",
                "Dawn soundscape with natural morning elements"
            ],
            "afternoon": [
                "Afternoon ambience with warm daylight sounds",
                "Midday atmosphere with natural afternoon elements",
                "Daytime soundscape with warm ambient sounds"
            ],
            "evening": [
                "Evening ambience with sunset and twilight sounds",
                "Dusk atmosphere with gentle evening elements",
                "Twilight soundscape with natural evening sounds"
            ],
            "night": [
                "Night ambience with nocturnal sounds",
                "Dark atmosphere with nighttime elements",
                "Nighttime soundscape with natural night sounds"
            ]
        },
        "mood": {
            "tense": [
                "Tense atmospheric ambience with subtle unease",
                "Suspenseful background with underlying tension",
                "Dramatic atmosphere with building suspense"
            ],
            "peaceful": [
                "Peaceful and serene ambient soundscape",
                "Calm atmosphere with gentle natural sounds",
                "Tranquil background with soothing elements"
            ],
            "mysterious": [
                "Mysterious ambience with enigmatic sounds",
                "Enigmatic atmosphere with subtle mystery",
                "Mysterious soundscape with hidden elements"
            ],
            "dramatic": [
                "Dramatic atmospheric ambience with intensity",
                "Powerful background with dramatic elements",
                "Intense atmosphere with emotional depth"
            ]
        }
    }
    
    # SFX templates
    SFX_TEMPLATES = {
        "action": {
            "walking": [
                "Footsteps on {surface}",
                "Walking sounds on {surface}",
                "Footstep audio on {surface}"
            ],
            "running": [
                "Running footsteps on {surface}",
                "Fast footsteps on {surface}",
                "Running sounds on {surface}"
            ],
            "opening": [
                "Door opening sound",
                "Opening {object} sound",
                "{object} opening audio"
            ],
            "closing": [
                "Door closing sound",
                "Closing {object} sound",
                "{object} closing audio"
            ],
            "breaking": [
                "Breaking {object} sound",
                "{object} breaking audio",
                "Shattering {object} sound"
            ],
            "falling": [
                "Object falling sound",
                "Falling {object} audio",
                "Drop sound of {object}"
            ]
        },
        "environment": {
            "wind": [
                "Wind blowing through {location}",
                "Wind sound in {location}",
                "Breeze through {location}"
            ],
            "rain": [
                "Rain hitting {surface}",
                "Rainfall on {surface}",
                "Water droplets on {surface}"
            ],
            "fire": [
                "Fire crackling sound",
                "Burning {object} audio",
                "Flame sounds"
            ],
            "water": [
                "Water flowing sound",
                "Liquid pouring audio",
                "Water movement sound"
            ]
        },
        "objects": {
            "glass": [
                "Glass breaking sound",
                "Glass shattering audio",
                "Glass impact sound"
            ],
            "metal": [
                "Metal clanging sound",
                "Metal impact audio",
                "Metal scraping sound"
            ],
            "wood": [
                "Wood creaking sound",
                "Wooden {object} audio",
                "Wood impact sound"
            ],
            "paper": [
                "Paper rustling sound",
                "Paper crinkling audio",
                "Paper movement sound"
            ]
        }
    }
    
    # Surface mappings
    SURFACE_MAPPINGS = {
        "wood": ["wooden floor", "hardwood", "wooden surface"],
        "stone": ["stone floor", "marble", "concrete", "pavement"],
        "grass": ["grass", "lawn", "field"],
        "sand": ["sand", "beach", "desert"],
        "snow": ["snow", "ice", "frozen ground"],
        "water": ["water", "puddle", "wet surface"],
        "metal": ["metal", "steel", "iron"],
        "glass": ["glass", "tile", "smooth surface"]
    }
    
    # Object mappings
    OBJECT_MAPPINGS = {
        "door": ["door", "gate", "entrance"],
        "window": ["window", "glass", "pane"],
        "book": ["book", "paper", "document"],
        "cup": ["cup", "glass", "mug", "container"],
        "phone": ["phone", "telephone", "device"],
        "car": ["car", "vehicle", "automobile"],
        "tree": ["tree", "branch", "wood"],
        "rock": ["rock", "stone", "boulder"]
    }


class SceneAnalyzer:
    """Scene text analyzer for extracting sound cues"""
    
    def __init__(self):
        try:
            # Load spaCy model for NLP processing
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using basic text processing")
            self.nlp = None
    
    def analyze_scene_heading(self, scene_heading: str) -> Tuple[str, str, str]:
        """Extract location, time, and mood from scene heading"""
        # Parse scene heading format: INT/EXT. LOCATION - TIME
        location = "unknown"
        time_of_day = "unknown"
        mood = None
        
        # Extract INT/EXT
        if "INT." in scene_heading.upper():
            location_type = "interior"
        elif "EXT." in scene_heading.upper():
            location_type = "exterior"
        else:
            location_type = "unknown"
        
        # Extract location
        location_match = re.search(r'\.\s*([^-]+)', scene_heading)
        if location_match:
            location = location_match.group(1).strip().lower()
        
        # Extract time
        time_match = re.search(r'-\s*([^-]+)', scene_heading)
        if time_match:
            time_of_day = time_match.group(1).strip().lower()
        
        # Extract mood from time description
        mood_keywords = {
            "tense": ["tense", "dramatic", "suspenseful", "urgent"],
            "peaceful": ["peaceful", "calm", "serene", "quiet"],
            "mysterious": ["mysterious", "enigmatic", "strange", "eerie"],
            "dramatic": ["dramatic", "intense", "powerful", "emotional"]
        }
        
        for mood_type, keywords in mood_keywords.items():
            if any(keyword in time_of_day for keyword in keywords):
                mood = mood_type
                break
        
        return location, time_of_day, mood
    
    def extract_sound_cues(self, text: str) -> List[str]:
        """Extract sound-related cues from text"""
        sound_cues = []
        
        # Sound-related keywords
        sound_keywords = [
            "sound", "noise", "voice", "whisper", "shout", "scream", "laugh",
            "footstep", "footsteps", "walking", "running", "creaking",
            "banging", "slamming", "crashing", "breaking", "shattering",
            "wind", "rain", "thunder", "lightning", "fire", "water",
            "door", "window", "phone", "bell", "alarm", "music",
            "engine", "car", "tire", "brake", "horn", "siren",
            "bird", "dog", "cat", "animal", "wildlife", "nature"
        ]
        
        # Find sentences containing sound keywords
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in sound_keywords):
                sound_cues.append(sentence.strip())
        
        return sound_cues
    
    def extract_environment_cues(self, text: str) -> List[str]:
        """Extract environment-related cues from text"""
        environment_cues = []
        
        # Environment keywords
        environment_keywords = [
            "forest", "city", "beach", "mountain", "desert", "rain", "snow",
            "wind", "storm", "sunny", "cloudy", "foggy", "hot", "cold",
            "indoor", "outdoor", "inside", "outside", "room", "building",
            "street", "park", "garden", "kitchen", "bedroom", "office"
        ]
        
        # Find sentences containing environment keywords
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in environment_keywords):
                environment_cues.append(sentence.strip())
        
        return environment_cues
    
    def extract_linguistic_elements(self, text: str) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Extract verbs, nouns, adjectives, and action words from text"""
        verbs = []
        nouns = []
        adjectives = []
        action_words = []
        
        if self.nlp:
            # Use spaCy for advanced NLP
            doc = self.nlp(text)
            
            for token in doc:
                if token.pos_ == "VERB" and not token.is_stop:
                    verbs.append(token.lemma_.lower())
                elif token.pos_ == "NOUN" and not token.is_stop:
                    nouns.append(token.lemma_.lower())
                elif token.pos_ == "ADJ" and not token.is_stop:
                    adjectives.append(token.lemma_.lower())
            
            # Extract action words (verbs that imply sound or movement)
            action_verbs = [
                "walk", "run", "jump", "fall", "drop", "break", "crash",
                "slam", "bang", "knock", "open", "close", "shut", "lock",
                "unlock", "turn", "twist", "pull", "push", "throw", "catch",
                "hit", "strike", "punch", "kick", "step", "stomp", "tap"
            ]
            
            for token in doc:
                if token.lemma_.lower() in action_verbs:
                    action_words.append(token.lemma_.lower())
        else:
            # Basic text processing without spaCy
            words = re.findall(r'\b\w+\b', text.lower())
            
            # Simple word classification (basic approach)
            common_verbs = ["walk", "run", "jump", "fall", "break", "open", "close", "hit", "strike"]
            common_nouns = ["door", "window", "car", "phone", "book", "cup", "glass", "wood", "metal"]
            common_adjectives = ["loud", "quiet", "soft", "hard", "sharp", "dull", "bright", "dark"]
            
            for word in words:
                if word in common_verbs:
                    verbs.append(word)
                elif word in common_nouns:
                    nouns.append(word)
                elif word in common_adjectives:
                    adjectives.append(word)
        
        return verbs, nouns, adjectives, action_words
    
    def analyze_scene(self, scene_heading: str, scene_text: str) -> SceneAnalysis:
        """Perform complete scene analysis"""
        # Analyze scene heading
        location, time_of_day, mood = self.analyze_scene_heading(scene_heading)
        
        # Extract linguistic elements
        verbs, nouns, adjectives, action_words = self.extract_linguistic_elements(scene_text)
        
        # Extract sound and environment cues
        sound_cues = self.extract_sound_cues(scene_text)
        environment_cues = self.extract_environment_cues(scene_text)
        
        return SceneAnalysis(
            scene_heading=scene_heading,
            location=location,
            time_of_day=time_of_day,
            mood=mood,
            verbs=verbs,
            nouns=nouns,
            adjectives=adjectives,
            action_words=action_words,
            sound_cues=sound_cues,
            environment_cues=environment_cues
        )


class PromptGenerator:
    """Generate ambience and SFX prompts from scene analysis"""
    
    def __init__(self):
        self.analyzer = SceneAnalyzer()
        self.templates = PromptTemplates()
    
    def generate_ambience_prompts(self, analysis: SceneAnalysis) -> List[GeneratedPrompt]:
        """Generate ambience prompts from scene analysis"""
        prompts = []
        
        # Location-based prompts
        location_prompts = self._get_location_prompts(analysis.location)
        for prompt in location_prompts:
            prompts.append(GeneratedPrompt(
                prompt=prompt,
                prompt_type="ambience",
                confidence=0.8,
                source_elements=[analysis.location],
                template_used="location"
            ))
        
        # Time-based prompts
        time_prompts = self._get_time_prompts(analysis.time_of_day)
        for prompt in time_prompts:
            prompts.append(GeneratedPrompt(
                prompt=prompt,
                prompt_type="ambience",
                confidence=0.7,
                source_elements=[analysis.time_of_day],
                template_used="time"
            ))
        
        # Mood-based prompts
        if analysis.mood:
            mood_prompts = self._get_mood_prompts(analysis.mood)
            for prompt in mood_prompts:
                prompts.append(GeneratedPrompt(
                    prompt=prompt,
                    prompt_type="ambience",
                    confidence=0.9,
                    source_elements=[analysis.mood],
                    template_used="mood"
                ))
        
        # Environment cue-based prompts
        for cue in analysis.environment_cues:
            env_prompt = self._generate_environment_prompt(cue)
            if env_prompt:
                prompts.append(GeneratedPrompt(
                    prompt=env_prompt,
                    prompt_type="ambience",
                    confidence=0.6,
                    source_elements=[cue],
                    template_used="environment_cue"
                ))
        
        return prompts
    
    def generate_sfx_prompts(self, analysis: SceneAnalysis) -> List[GeneratedPrompt]:
        """Generate SFX prompts from scene analysis"""
        prompts = []
        
        # Action-based prompts
        for action in analysis.action_words:
            action_prompts = self._get_action_prompts(action, analysis.nouns)
            for prompt in action_prompts:
                prompts.append(GeneratedPrompt(
                    prompt=prompt,
                    prompt_type="sfx",
                    confidence=0.8,
                    source_elements=[action],
                    template_used="action"
                ))
        
        # Sound cue-based prompts
        for cue in analysis.sound_cues:
            sfx_prompt = self._generate_sfx_from_cue(cue)
            if sfx_prompt:
                prompts.append(GeneratedPrompt(
                    prompt=sfx_prompt,
                    prompt_type="sfx",
                    confidence=0.7,
                    source_elements=[cue],
                    template_used="sound_cue"
                ))
        
        # Object-based prompts
        for noun in analysis.nouns:
            object_prompts = self._get_object_prompts(noun)
            for prompt in object_prompts:
                prompts.append(GeneratedPrompt(
                    prompt=prompt,
                    prompt_type="sfx",
                    confidence=0.6,
                    source_elements=[noun],
                    template_used="object"
                ))
        
        return prompts
    
    def _get_location_prompts(self, location: str) -> List[str]:
        """Get location-based ambience prompts"""
        prompts = []
        
        # Check for specific location matches
        for template_location, template_prompts in self.templates.AMBIENCE_TEMPLATES["location"].items():
            if template_location in location.lower():
                prompts.extend(template_prompts)
        
        # If no specific match, use generic location prompt
        if not prompts:
            prompts.append(f"Ambient soundscape for {location}")
        
        return prompts
    
    def _get_time_prompts(self, time_of_day: str) -> List[str]:
        """Get time-based ambience prompts"""
        prompts = []
        
        # Check for specific time matches
        for template_time, template_prompts in self.templates.AMBIENCE_TEMPLATES["time"].items():
            if template_time in time_of_day.lower():
                prompts.extend(template_prompts)
        
        # If no specific match, use generic time prompt
        if not prompts:
            prompts.append(f"Ambient soundscape for {time_of_day}")
        
        return prompts
    
    def _get_mood_prompts(self, mood: str) -> List[str]:
        """Get mood-based ambience prompts"""
        return self.templates.AMBIENCE_TEMPLATES["mood"].get(mood, [])
    
    def _get_action_prompts(self, action: str, nouns: List[str]) -> List[str]:
        """Get action-based SFX prompts"""
        prompts = []
        
        # Check for specific action matches
        for template_action, template_prompts in self.templates.SFX_TEMPLATES["action"].items():
            if template_action in action.lower():
                # Try to find matching surface or object
                surface = self._find_matching_surface(nouns)
                object_name = self._find_matching_object(nouns)
                
                for template in template_prompts:
                    if "{surface}" in template and surface:
                        prompts.append(template.format(surface=surface))
                    elif "{object}" in template and object_name:
                        prompts.append(template.format(object=object_name))
                    else:
                        prompts.append(template)
        
        return prompts
    
    def _get_object_prompts(self, noun: str) -> List[str]:
        """Get object-based SFX prompts"""
        prompts = []
        
        # Check for specific object matches
        for template_object, template_prompts in self.templates.SFX_TEMPLATES["objects"].items():
            if template_object in noun.lower():
                prompts.extend(template_prompts)
        
        return prompts
    
    def _find_matching_surface(self, nouns: List[str]) -> Optional[str]:
        """Find matching surface from nouns"""
        for noun in nouns:
            for surface, variations in self.templates.SURFACE_MAPPINGS.items():
                if any(var in noun.lower() for var in variations):
                    return surface
        return None
    
    def _find_matching_object(self, nouns: List[str]) -> Optional[str]:
        """Find matching object from nouns"""
        for noun in nouns:
            for object_type, variations in self.templates.OBJECT_MAPPINGS.items():
                if any(var in noun.lower() for var in variations):
                    return object_type
        return None
    
    def _generate_environment_prompt(self, cue: str) -> Optional[str]:
        """Generate environment prompt from cue"""
        # Extract key environment words
        env_words = ["wind", "rain", "snow", "storm", "sunny", "cloudy", "foggy"]
        
        for word in env_words:
            if word in cue.lower():
                return f"Environmental {word} ambience"
        
        return None
    
    def _generate_sfx_from_cue(self, cue: str) -> Optional[str]:
        """Generate SFX prompt from sound cue"""
        # Extract key sound words
        sound_words = ["footstep", "door", "window", "phone", "bell", "alarm", "music"]
        
        for word in sound_words:
            if word in cue.lower():
                return f"{word.title()} sound effect"
        
        return None
    
    def generate_fx_plan_prompts(self, scene_heading: str, scene_text: str) -> FXPlanPrompts:
        """Generate complete FX plan prompts from scene"""
        # Analyze scene
        analysis = self.analyzer.analyze_scene(scene_heading, scene_text)
        
        # Generate prompts
        ambience_prompts = self.generate_ambience_prompts(analysis)
        sfx_prompts = self.generate_sfx_prompts(analysis)
        
        return FXPlanPrompts(
            scene_id=0,  # Will be set when saving
            scene_name=scene_heading,
            generated_at=datetime.now(),
            ambience_prompts=ambience_prompts,
            sfx_prompts=sfx_prompts,
            manual_overrides={},
            analysis_summary=analysis
        )
    
    def apply_manual_override(self, prompts: FXPlanPrompts, prompt_id: str, 
                            new_prompt: str, reason: str = None) -> FXPlanPrompts:
        """Apply manual override to a generated prompt"""
        # Find and update the prompt
        for prompt in prompts.ambience_prompts + prompts.sfx_prompts:
            if prompt.prompt == prompt_id:
                prompt.prompt = new_prompt
                prompt.manual_override = True
                prompt.override_reason = reason
                break
        
        # Store override in manual_overrides
        prompts.manual_overrides[prompt_id] = {
            "new_prompt": new_prompt,
            "reason": reason,
            "overridden_at": datetime.now().isoformat()
        }
        
        return prompts
