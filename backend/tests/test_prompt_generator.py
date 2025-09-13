"""
Tests for prompt generation system
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from backend.services.prompt_generator import (
    PromptGenerator, SceneAnalyzer, PromptTemplates,
    SceneAnalysis, GeneratedPrompt, FXPlanPrompts
)


class TestPromptTemplates:
    """Test cases for PromptTemplates"""
    
    def test_ambience_templates_structure(self):
        """Test ambience templates structure"""
        templates = PromptTemplates()
        
        # Check location templates
        assert "location" in templates.AMBIENCE_TEMPLATES
        assert "forest" in templates.AMBIENCE_TEMPLATES["location"]
        assert "city" in templates.AMBIENCE_TEMPLATES["location"]
        assert "beach" in templates.AMBIENCE_TEMPLATES["location"]
        
        # Check time templates
        assert "time" in templates.AMBIENCE_TEMPLATES
        assert "morning" in templates.AMBIENCE_TEMPLATES["time"]
        assert "evening" in templates.AMBIENCE_TEMPLATES["time"]
        
        # Check mood templates
        assert "mood" in templates.AMBIENCE_TEMPLATES
        assert "tense" in templates.AMBIENCE_TEMPLATES["mood"]
        assert "peaceful" in templates.AMBIENCE_TEMPLATES["mood"]
    
    def test_sfx_templates_structure(self):
        """Test SFX templates structure"""
        templates = PromptTemplates()
        
        # Check action templates
        assert "action" in templates.SFX_TEMPLATES
        assert "walking" in templates.SFX_TEMPLATES["action"]
        assert "running" in templates.SFX_TEMPLATES["action"]
        assert "opening" in templates.SFX_TEMPLATES["action"]
        
        # Check environment templates
        assert "environment" in templates.SFX_TEMPLATES
        assert "wind" in templates.SFX_TEMPLATES["environment"]
        assert "rain" in templates.SFX_TEMPLATES["environment"]
        
        # Check object templates
        assert "objects" in templates.SFX_TEMPLATES
        assert "glass" in templates.SFX_TEMPLATES["objects"]
        assert "metal" in templates.SFX_TEMPLATES["objects"]
    
    def test_surface_mappings(self):
        """Test surface mappings"""
        templates = PromptTemplates()
        
        assert "wood" in templates.SURFACE_MAPPINGS
        assert "stone" in templates.SURFACE_MAPPINGS
        assert "grass" in templates.SURFACE_MAPPINGS
        
        # Check specific mappings
        assert "wooden floor" in templates.SURFACE_MAPPINGS["wood"]
        assert "concrete" in templates.SURFACE_MAPPINGS["stone"]
        assert "lawn" in templates.SURFACE_MAPPINGS["grass"]
    
    def test_object_mappings(self):
        """Test object mappings"""
        templates = PromptTemplates()
        
        assert "door" in templates.OBJECT_MAPPINGS
        assert "window" in templates.OBJECT_MAPPINGS
        assert "book" in templates.OBJECT_MAPPINGS
        
        # Check specific mappings
        assert "gate" in templates.OBJECT_MAPPINGS["door"]
        assert "glass" in templates.OBJECT_MAPPINGS["window"]
        assert "document" in templates.OBJECT_MAPPINGS["book"]


class TestSceneAnalyzer:
    """Test cases for SceneAnalyzer"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = SceneAnalyzer()
    
    def test_analyze_scene_heading_basic(self):
        """Test basic scene heading analysis"""
        scene_heading = "INT. LIVING ROOM - DAY"
        location, time_of_day, mood = self.analyzer.analyze_scene_heading(scene_heading)
        
        assert location == "living room"
        assert time_of_day == "day"
        assert mood is None
    
    def test_analyze_scene_heading_with_mood(self):
        """Test scene heading analysis with mood"""
        scene_heading = "EXT. FOREST - NIGHT (TENSE)"
        location, time_of_day, mood = self.analyzer.analyze_scene_heading(scene_heading)
        
        assert location == "forest"
        assert time_of_day == "night (tense)"
        assert mood == "tense"
    
    def test_analyze_scene_heading_exterior(self):
        """Test exterior scene heading analysis"""
        scene_heading = "EXT. BEACH - EVENING"
        location, time_of_day, mood = self.analyzer.analyze_scene_heading(scene_heading)
        
        assert location == "beach"
        assert time_of_day == "evening"
        assert mood is None
    
    def test_extract_sound_cues(self):
        """Test sound cue extraction"""
        text = "John walks across the wooden floor. The door creaks open. A phone rings in the distance."
        sound_cues = self.analyzer.extract_sound_cues(text)
        
        assert len(sound_cues) > 0
        assert any("door" in cue.lower() for cue in sound_cues)
        assert any("phone" in cue.lower() for cue in sound_cues)
    
    def test_extract_environment_cues(self):
        """Test environment cue extraction"""
        text = "The scene takes place in a forest. It's raining outside. The wind is blowing through the trees."
        environment_cues = self.analyzer.extract_environment_cues(text)
        
        assert len(environment_cues) > 0
        assert any("forest" in cue.lower() for cue in environment_cues)
        assert any("rain" in cue.lower() for cue in environment_cues)
    
    @patch('backend.services.prompt_generator.spacy.load')
    def test_extract_linguistic_elements_with_spacy(self, mock_spacy_load):
        """Test linguistic element extraction with spaCy"""
        # Mock spaCy model
        mock_nlp = Mock()
        mock_doc = Mock()
        
        # Mock tokens
        mock_token1 = Mock()
        mock_token1.pos_ = "VERB"
        mock_token1.lemma_ = "walk"
        mock_token1.is_stop = False
        
        mock_token2 = Mock()
        mock_token2.pos_ = "NOUN"
        mock_token2.lemma_ = "door"
        mock_token2.is_stop = False
        
        mock_token3 = Mock()
        mock_token3.pos_ = "ADJ"
        mock_token3.lemma_ = "loud"
        mock_token3.is_stop = False
        
        mock_doc.__iter__ = Mock(return_value=iter([mock_token1, mock_token2, mock_token3]))
        mock_nlp.return_value = mock_doc
        mock_spacy_load.return_value = mock_nlp
        
        # Create analyzer with mocked spaCy
        analyzer = SceneAnalyzer()
        analyzer.nlp = mock_nlp
        
        text = "John walks to the door. It's a loud sound."
        verbs, nouns, adjectives, action_words = analyzer.extract_linguistic_elements(text)
        
        assert "walk" in verbs
        assert "door" in nouns
        assert "loud" in adjectives
    
    def test_extract_linguistic_elements_without_spacy(self):
        """Test linguistic element extraction without spaCy"""
        # Create analyzer without spaCy
        analyzer = SceneAnalyzer()
        analyzer.nlp = None
        
        text = "John walks to the door. It's a loud sound."
        verbs, nouns, adjectives, action_words = analyzer.extract_linguistic_elements(text)
        
        # Should still extract some basic elements
        assert isinstance(verbs, list)
        assert isinstance(nouns, list)
        assert isinstance(adjectives, list)
        assert isinstance(action_words, list)
    
    def test_analyze_scene_complete(self):
        """Test complete scene analysis"""
        scene_heading = "INT. KITCHEN - MORNING"
        scene_text = "John walks across the wooden floor. The door creaks open. A phone rings in the distance."
        
        analysis = self.analyzer.analyze_scene(scene_heading, scene_text)
        
        assert analysis.scene_heading == scene_heading
        assert analysis.location == "kitchen"
        assert analysis.time_of_day == "morning"
        assert len(analysis.sound_cues) > 0
        assert len(analysis.environment_cues) >= 0


class TestPromptGenerator:
    """Test cases for PromptGenerator"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = PromptGenerator()
    
    def test_generate_ambience_prompts_location(self):
        """Test ambience prompt generation for location"""
        analysis = SceneAnalysis(
            scene_heading="INT. FOREST - DAY",
            location="forest",
            time_of_day="day",
            mood=None,
            verbs=[],
            nouns=[],
            adjectives=[],
            action_words=[],
            sound_cues=[],
            environment_cues=[]
        )
        
        prompts = self.generator.generate_ambience_prompts(analysis)
        
        assert len(prompts) > 0
        assert all(prompt.prompt_type == "ambience" for prompt in prompts)
        assert any("forest" in prompt.prompt.lower() for prompt in prompts)
    
    def test_generate_ambience_prompts_time(self):
        """Test ambience prompt generation for time"""
        analysis = SceneAnalysis(
            scene_heading="EXT. BEACH - EVENING",
            location="beach",
            time_of_day="evening",
            mood=None,
            verbs=[],
            nouns=[],
            adjectives=[],
            action_words=[],
            sound_cues=[],
            environment_cues=[]
        )
        
        prompts = self.generator.generate_ambience_prompts(analysis)
        
        assert len(prompts) > 0
        assert all(prompt.prompt_type == "ambience" for prompt in prompts)
        assert any("evening" in prompt.prompt.lower() for prompt in prompts)
    
    def test_generate_ambience_prompts_mood(self):
        """Test ambience prompt generation for mood"""
        analysis = SceneAnalysis(
            scene_heading="INT. ROOM - NIGHT (TENSE)",
            location="room",
            time_of_day="night (tense)",
            mood="tense",
            verbs=[],
            nouns=[],
            adjectives=[],
            action_words=[],
            sound_cues=[],
            environment_cues=[]
        )
        
        prompts = self.generator.generate_ambience_prompts(analysis)
        
        assert len(prompts) > 0
        assert all(prompt.prompt_type == "ambience" for prompt in prompts)
        assert any("tense" in prompt.prompt.lower() for prompt in prompts)
    
    def test_generate_sfx_prompts_action(self):
        """Test SFX prompt generation for actions"""
        analysis = SceneAnalysis(
            scene_heading="INT. ROOM - DAY",
            location="room",
            time_of_day="day",
            mood=None,
            verbs=["walk", "open"],
            nouns=["door", "floor"],
            adjectives=[],
            action_words=["walk", "open"],
            sound_cues=[],
            environment_cues=[]
        )
        
        prompts = self.generator.generate_sfx_prompts(analysis)
        
        assert len(prompts) > 0
        assert all(prompt.prompt_type == "sfx" for prompt in prompts)
        assert any("footstep" in prompt.prompt.lower() or "door" in prompt.prompt.lower() for prompt in prompts)
    
    def test_generate_sfx_prompts_objects(self):
        """Test SFX prompt generation for objects"""
        analysis = SceneAnalysis(
            scene_heading="INT. ROOM - DAY",
            location="room",
            time_of_day="day",
            mood=None,
            verbs=[],
            nouns=["glass", "metal"],
            adjectives=[],
            action_words=[],
            sound_cues=[],
            environment_cues=[]
        )
        
        prompts = self.generator.generate_sfx_prompts(analysis)
        
        assert len(prompts) > 0
        assert all(prompt.prompt_type == "sfx" for prompt in prompts)
        assert any("glass" in prompt.prompt.lower() or "metal" in prompt.prompt.lower() for prompt in prompts)
    
    def test_generate_fx_plan_prompts_complete(self):
        """Test complete FX plan prompt generation"""
        scene_heading = "INT. FOREST - EVENING (TENSE)"
        scene_text = "John walks through the forest. The wind blows through the trees. A door creaks in the distance."
        
        fx_plan_prompts = self.generator.generate_fx_plan_prompts(scene_heading, scene_text)
        
        assert fx_plan_prompts.scene_name == scene_heading
        assert len(fx_plan_prompts.ambience_prompts) > 0
        assert len(fx_plan_prompts.sfx_prompts) > 0
        assert fx_plan_prompts.analysis_summary.location == "forest"
        assert fx_plan_prompts.analysis_summary.time_of_day == "evening (tense)"
        assert fx_plan_prompts.analysis_summary.mood == "tense"
    
    def test_apply_manual_override(self):
        """Test manual override application"""
        # Create test prompts
        prompts = FXPlanPrompts(
            scene_id=1,
            scene_name="Test Scene",
            generated_at=datetime.now(),
            ambience_prompts=[
                GeneratedPrompt(
                    prompt="Forest ambience",
                    prompt_type="ambience",
                    confidence=0.8,
                    source_elements=["forest"],
                    template_used="location"
                )
            ],
            sfx_prompts=[],
            manual_overrides={},
            analysis_summary=SceneAnalysis(
                scene_heading="Test",
                location="forest",
                time_of_day="day",
                mood=None,
                verbs=[],
                nouns=[],
                adjectives=[],
                action_words=[],
                sound_cues=[],
                environment_cues=[]
            )
        )
        
        # Apply override
        updated_prompts = self.generator.apply_manual_override(
            prompts, 
            "Forest ambience", 
            "Custom forest ambience with birds", 
            "Added bird sounds"
        )
        
        # Check override was applied
        assert updated_prompts.ambience_prompts[0].prompt == "Custom forest ambience with birds"
        assert updated_prompts.ambience_prompts[0].manual_override is True
        assert updated_prompts.ambience_prompts[0].override_reason == "Added bird sounds"
        assert "Forest ambience" in updated_prompts.manual_overrides
    
    def test_get_location_prompts_known(self):
        """Test getting prompts for known location"""
        prompts = self.generator._get_location_prompts("forest")
        
        assert len(prompts) > 0
        assert any("forest" in prompt.lower() for prompt in prompts)
    
    def test_get_location_prompts_unknown(self):
        """Test getting prompts for unknown location"""
        prompts = self.generator._get_location_prompts("unknown_location")
        
        assert len(prompts) > 0
        assert "unknown_location" in prompts[0]
    
    def test_get_time_prompts_known(self):
        """Test getting prompts for known time"""
        prompts = self.generator._get_time_prompts("morning")
        
        assert len(prompts) > 0
        assert any("morning" in prompt.lower() for prompt in prompts)
    
    def test_get_time_prompts_unknown(self):
        """Test getting prompts for unknown time"""
        prompts = self.generator._get_time_prompts("unknown_time")
        
        assert len(prompts) > 0
        assert "unknown_time" in prompts[0]
    
    def test_get_mood_prompts_known(self):
        """Test getting prompts for known mood"""
        prompts = self.generator._get_mood_prompts("tense")
        
        assert len(prompts) > 0
        assert any("tense" in prompt.lower() for prompt in prompts)
    
    def test_get_mood_prompts_unknown(self):
        """Test getting prompts for unknown mood"""
        prompts = self.generator._get_mood_prompts("unknown_mood")
        
        assert len(prompts) == 0
    
    def test_get_action_prompts(self):
        """Test getting action-based prompts"""
        prompts = self.generator._get_action_prompts("walking", ["floor", "wood"])
        
        assert len(prompts) > 0
        assert any("footstep" in prompt.lower() for prompt in prompts)
    
    def test_get_object_prompts(self):
        """Test getting object-based prompts"""
        prompts = self.generator._get_object_prompts("glass")
        
        assert len(prompts) > 0
        assert any("glass" in prompt.lower() for prompt in prompts)
    
    def test_find_matching_surface(self):
        """Test finding matching surface"""
        surface = self.generator._find_matching_surface(["wooden", "floor"])
        
        assert surface == "wood"
    
    def test_find_matching_surface_no_match(self):
        """Test finding matching surface with no match"""
        surface = self.generator._find_matching_surface(["unknown", "surface"])
        
        assert surface is None
    
    def test_find_matching_object(self):
        """Test finding matching object"""
        object_type = self.generator._find_matching_object(["door", "handle"])
        
        assert object_type == "door"
    
    def test_find_matching_object_no_match(self):
        """Test finding matching object with no match"""
        object_type = self.generator._find_matching_object(["unknown", "object"])
        
        assert object_type is None
    
    def test_generate_environment_prompt(self):
        """Test generating environment prompt"""
        prompt = self.generator._generate_environment_prompt("The wind is blowing")
        
        assert prompt == "Environmental wind ambience"
    
    def test_generate_environment_prompt_no_match(self):
        """Test generating environment prompt with no match"""
        prompt = self.generator._generate_environment_prompt("No environment cues")
        
        assert prompt is None
    
    def test_generate_sfx_from_cue(self):
        """Test generating SFX from sound cue"""
        prompt = self.generator._generate_sfx_from_cue("The door creaks open")
        
        assert prompt == "Door sound effect"
    
    def test_generate_sfx_from_cue_no_match(self):
        """Test generating SFX from sound cue with no match"""
        prompt = self.generator._generate_sfx_from_cue("No sound cues")
        
        assert prompt is None


class TestDataStructures:
    """Test cases for data structures"""
    
    def test_scene_analysis_creation(self):
        """Test SceneAnalysis creation"""
        analysis = SceneAnalysis(
            scene_heading="INT. ROOM - DAY",
            location="room",
            time_of_day="day",
            mood="tense",
            verbs=["walk", "open"],
            nouns=["door", "floor"],
            adjectives=["loud", "quiet"],
            action_words=["walk", "open"],
            sound_cues=["door creaks"],
            environment_cues=["wind blowing"]
        )
        
        assert analysis.scene_heading == "INT. ROOM - DAY"
        assert analysis.location == "room"
        assert analysis.time_of_day == "day"
        assert analysis.mood == "tense"
        assert len(analysis.verbs) == 2
        assert len(analysis.nouns) == 2
        assert len(analysis.adjectives) == 2
        assert len(analysis.action_words) == 2
        assert len(analysis.sound_cues) == 1
        assert len(analysis.environment_cues) == 1
    
    def test_generated_prompt_creation(self):
        """Test GeneratedPrompt creation"""
        prompt = GeneratedPrompt(
            prompt="Forest ambience with birds",
            prompt_type="ambience",
            confidence=0.8,
            source_elements=["forest", "birds"],
            template_used="location",
            manual_override=False,
            override_reason=None
        )
        
        assert prompt.prompt == "Forest ambience with birds"
        assert prompt.prompt_type == "ambience"
        assert prompt.confidence == 0.8
        assert len(prompt.source_elements) == 2
        assert prompt.template_used == "location"
        assert prompt.manual_override is False
        assert prompt.override_reason is None
    
    def test_fx_plan_prompts_creation(self):
        """Test FXPlanPrompts creation"""
        analysis = SceneAnalysis(
            scene_heading="Test",
            location="room",
            time_of_day="day",
            mood=None,
            verbs=[],
            nouns=[],
            adjectives=[],
            action_words=[],
            sound_cues=[],
            environment_cues=[]
        )
        
        prompts = FXPlanPrompts(
            scene_id=1,
            scene_name="Test Scene",
            generated_at=datetime.now(),
            ambience_prompts=[],
            sfx_prompts=[],
            manual_overrides={},
            analysis_summary=analysis
        )
        
        assert prompts.scene_id == 1
        assert prompts.scene_name == "Test Scene"
        assert len(prompts.ambience_prompts) == 0
        assert len(prompts.sfx_prompts) == 0
        assert len(prompts.manual_overrides) == 0
        assert prompts.analysis_summary == analysis
