"""
Tests for screenplay parser
"""

import pytest
from backend.parsers.screenplay import (
    ScreenplayParser, ScenePersistenceManager, SceneType, ElementType,
    SceneHeading, ScreenplayElement, ParsedScene
)


class TestScreenplayParser:
    """Test cases for ScreenplayParser"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = ScreenplayParser()
    
    def test_parse_simple_scene(self):
        """Test parsing a simple scene with dialogue"""
        screenplay = """
INT. LIVING ROOM - DAY

John sits on the couch, reading a newspaper.

JOHN
Hello there.

MARY
Hi John, how are you?

JOHN
I'm doing well, thank you.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 1
        scene = scenes[0]
        
        # Test scene heading
        assert scene.scene_number == 1
        assert scene.heading.scene_type == SceneType.INT
        assert scene.heading.location == "LIVING ROOM"
        assert scene.heading.time_of_day == "DAY"
        
        # Test dialogue
        assert len(scene.dialogue) == 3
        assert scene.dialogue[0]["character"] == "JOHN"
        assert scene.dialogue[0]["text"] == "Hello there."
        assert scene.dialogue[1]["character"] == "MARY"
        assert scene.dialogue[1]["text"] == "Hi John, how are you?"
        assert scene.dialogue[2]["character"] == "JOHN"
        assert scene.dialogue[2]["text"] == "I'm doing well, thank you."
        
        # Test voice-over
        assert len(scene.voice_over) == 0
    
    def test_parse_multiple_scenes(self):
        """Test parsing multiple scenes"""
        screenplay = """
INT. LIVING ROOM - DAY

John sits on the couch.

JOHN
Hello there.

EXT. GARDEN - EVENING

Mary walks through the garden.

MARY
What a beautiful evening.

INT. KITCHEN - NIGHT

John prepares dinner.

JOHN
Time to cook.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 3
        
        # Test first scene
        assert scenes[0].heading.scene_type == SceneType.INT
        assert scenes[0].heading.location == "LIVING ROOM"
        assert scenes[0].heading.time_of_day == "DAY"
        assert len(scenes[0].dialogue) == 1
        
        # Test second scene
        assert scenes[1].heading.scene_type == SceneType.EXT
        assert scenes[1].heading.location == "GARDEN"
        assert scenes[1].heading.time_of_day == "EVENING"
        assert len(scenes[1].dialogue) == 1
        
        # Test third scene
        assert scenes[2].heading.scene_type == SceneType.INT
        assert scenes[2].heading.location == "KITCHEN"
        assert scenes[2].heading.time_of_day == "NIGHT"
        assert len(scenes[2].dialogue) == 1
    
    def test_parse_voice_over(self):
        """Test parsing voice-over elements"""
        screenplay = """
INT. LIVING ROOM - DAY

John sits on the couch.

JOHN (V.O.)
This is what I was thinking at the time.

MARY
What are you thinking about?

JOHN
Nothing important.

NARRATOR (VOICE OVER)
The story continues as John reflects on his past.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 1
        scene = scenes[0]
        
        # Test dialogue (non-VO)
        assert len(scene.dialogue) == 2
        assert scene.dialogue[0]["character"] == "MARY"
        assert scene.dialogue[1]["character"] == "JOHN"
        
        # Test voice-over
        assert len(scene.voice_over) == 2
        assert scene.voice_over[0]["character"] == "JOHN (V.O.)"
        assert scene.voice_over[0]["text"] == "This is what I was thinking at the time."
        assert scene.voice_over[1]["character"] == "NARRATOR (VOICE OVER)"
        assert scene.voice_over[1]["text"] == "The story continues as John reflects on his past."
    
    def test_parse_parentheticals(self):
        """Test parsing parentheticals"""
        screenplay = """
INT. LIVING ROOM - DAY

JOHN
(smiling)
Hello there.

MARY
(confused)
What did you say?

JOHN
(laughing)
I said hello!
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 1
        scene = scenes[0]
        
        assert len(scene.dialogue) == 3
        assert scene.dialogue[0]["parenthetical"] == "(smiling)"
        assert scene.dialogue[1]["parenthetical"] == "(confused)"
        assert scene.dialogue[2]["parenthetical"] == "(laughing)"
    
    def test_parse_complex_scene(self):
        """Test parsing a complex scene with various elements"""
        screenplay = """
INT. COFFEE SHOP - MORNING

The coffee shop is bustling with morning commuters. 
Sarah sits at a corner table, typing on her laptop.

SARAH
(to herself)
I need to finish this report.

WAITER
Good morning! What can I get you?

SARAH
A large coffee, please.

WAITER
Coming right up.

SARAH (V.O.)
I remember this day clearly. It was the beginning of everything.

FADE TO:

EXT. STREET - CONTINUOUS

Sarah walks down the busy street, coffee in hand.

SARAH
(whispering)
Today is the day.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 2
        
        # Test first scene
        scene1 = scenes[0]
        assert scene1.heading.location == "COFFEE SHOP"
        assert scene1.heading.time_of_day == "MORNING"
        assert len(scene1.dialogue) == 3
        assert len(scene1.voice_over) == 1
        assert scene1.dialogue[0]["parenthetical"] == "(to herself)"
        assert scene1.voice_over[0]["character"] == "SARAH (V.O.)"
        
        # Test second scene
        scene2 = scenes[1]
        assert scene2.heading.location == "STREET"
        assert scene2.heading.time_of_day == "CONTINUOUS"
        assert len(scene2.dialogue) == 1
        assert scene2.dialogue[0]["parenthetical"] == "(whispering)"
    
    def test_parse_scene_without_time(self):
        """Test parsing scene heading without time of day"""
        screenplay = """
INT. LIVING ROOM

John sits on the couch.

JOHN
Hello there.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 1
        scene = scenes[0]
        assert scene.heading.scene_type == SceneType.INT
        assert scene.heading.location == "LIVING ROOM"
        assert scene.heading.time_of_day is None
    
    def test_parse_int_ext_scene(self):
        """Test parsing INT/EXT scene type"""
        screenplay = """
INT/EXT. CAR - DAY

John drives through the city.

JOHN
What a beautiful day.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 1
        scene = scenes[0]
        assert scene.heading.scene_type == SceneType.INT_EXT
        assert scene.heading.location == "CAR"
        assert scene.heading.time_of_day == "DAY"
    
    def test_parse_multiline_dialogue(self):
        """Test parsing multiline dialogue"""
        screenplay = """
INT. LIVING ROOM - DAY

JOHN
This is a long speech that goes on for multiple lines.
It continues here with more dialogue.
And even more dialogue on this line.

MARY
A shorter response.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 1
        scene = scenes[0]
        
        assert len(scene.dialogue) == 2
        assert "This is a long speech that goes on for multiple lines." in scene.dialogue[0]["text"]
        assert "It continues here with more dialogue." in scene.dialogue[0]["text"]
        assert "And even more dialogue on this line." in scene.dialogue[0]["text"]
        assert scene.dialogue[1]["text"] == "A shorter response."
    
    def test_parse_empty_screenplay(self):
        """Test parsing empty screenplay"""
        scenes = self.parser.parse("")
        assert len(scenes) == 0
    
    def test_parse_screenplay_with_only_action(self):
        """Test parsing screenplay with only action lines"""
        screenplay = """
INT. LIVING ROOM - DAY

John sits on the couch.
He reads a newspaper.
The room is quiet.
"""
        
        scenes = self.parser.parse(screenplay)
        
        assert len(scenes) == 1
        scene = scenes[0]
        assert len(scene.dialogue) == 0
        assert len(scene.voice_over) == 0
        assert "John sits on the couch." in scene.action_text
        assert "He reads a newspaper." in scene.action_text
        assert "The room is quiet." in scene.action_text


class TestSceneHeading:
    """Test cases for SceneHeading"""
    
    def test_scene_heading_creation(self):
        """Test scene heading creation"""
        heading = SceneHeading(
            scene_type=SceneType.INT,
            location="LIVING ROOM",
            time_of_day="DAY"
        )
        
        assert heading.scene_type == SceneType.INT
        assert heading.location == "LIVING ROOM"
        assert heading.time_of_day == "DAY"
        assert heading.raw_text == "INT. LIVING ROOM - DAY"
    
    def test_scene_heading_without_time(self):
        """Test scene heading without time of day"""
        heading = SceneHeading(
            scene_type=SceneType.EXT,
            location="GARDEN"
        )
        
        assert heading.scene_type == SceneType.EXT
        assert heading.location == "GARDEN"
        assert heading.time_of_day is None
        assert heading.raw_text == "EXT. GARDEN"


class TestParsedScene:
    """Test cases for ParsedScene"""
    
    def test_parsed_scene_properties(self):
        """Test parsed scene properties"""
        heading = SceneHeading(
            scene_type=SceneType.INT,
            location="LIVING ROOM",
            time_of_day="DAY"
        )
        
        scene = ParsedScene(
            scene_number=1,
            heading=heading,
            elements=[],
            dialogue=[{"character": "JOHN", "text": "Hello"}],
            voice_over=[{"character": "NARRATOR (V.O.)", "text": "The story begins"}],
            action_text="John sits on the couch.",
            raw_text="INT. LIVING ROOM - DAY\nJohn sits on the couch.\nJOHN\nHello"
        )
        
        assert scene.name == "Scene 1: LIVING ROOM"
        assert "INT. LIVING ROOM" in scene.description
        assert "Time: DAY" in scene.description
        assert "Dialogue: 1 exchanges" in scene.description
        assert "Voice-over: 1 segments" in scene.description


class TestScenePersistenceManager:
    """Test cases for ScenePersistenceManager"""
    
    def test_create_timeline_json(self, db_session):
        """Test timeline JSON creation"""
        manager = ScenePersistenceManager(db_session)
        
        heading = SceneHeading(
            scene_type=SceneType.INT,
            location="LIVING ROOM",
            time_of_day="DAY"
        )
        
        scene = ParsedScene(
            scene_number=1,
            heading=heading,
            elements=[],
            dialogue=[
                {
                    "character": "JOHN",
                    "text": "Hello there.",
                    "parenthetical": "(smiling)",
                    "line_number": 5
                }
            ],
            voice_over=[
                {
                    "character": "NARRATOR (V.O.)",
                    "text": "The story begins.",
                    "line_number": 8
                }
            ],
            action_text="John sits on the couch.",
            raw_text="INT. LIVING ROOM - DAY\nJohn sits on the couch.\nJOHN\n(smiling)\nHello there."
        )
        
        timeline_json = manager._create_timeline_json(scene)
        
        assert timeline_json["version"] == "1.0"
        assert timeline_json["sample_rate"] == 44100
        assert len(timeline_json["tracks"]) == 2
        
        # Test dialogue track
        dialogue_track = timeline_json["tracks"][0]
        assert dialogue_track["name"] == "Dialogue Track"
        assert dialogue_track["type"] == "dialogue"
        assert len(dialogue_track["assets"]) == 1
        assert dialogue_track["assets"][0]["character"] == "JOHN"
        assert dialogue_track["assets"][0]["text"] == "Hello there."
        assert dialogue_track["assets"][0]["parenthetical"] == "(smiling)"
        
        # Test voice-over track
        vo_track = timeline_json["tracks"][1]
        assert vo_track["name"] == "Voice-Over Track"
        assert vo_track["type"] == "dialogue"
        assert len(vo_track["assets"]) == 1
        assert vo_track["assets"][0]["character"] == "NARRATOR (V.O.)"
        assert vo_track["assets"][0]["text"] == "The story begins."
        assert vo_track["assets"][0]["is_voice_over"] is True
        
        # Test metadata
        metadata = timeline_json["metadata"]
        assert metadata["scene_type"] == "INT"
        assert metadata["location"] == "LIVING ROOM"
        assert metadata["time_of_day"] == "DAY"
        assert metadata["total_dialogue"] == 1
        assert metadata["total_voice_over"] == 1


# Sample screenplay texts for testing
SAMPLE_SCREENPLAY_1 = """
FADE IN:

INT. LIVING ROOM - DAY

John sits on the couch, reading a newspaper. The room is quiet except for the ticking of a clock.

JOHN
(to himself)
I need to call Mary.

MARY (V.O.)
I was thinking about him at that exact moment.

EXT. GARDEN - EVENING

Mary walks through the garden, admiring the flowers.

MARY
What a beautiful evening.

NARRATOR (VOICE OVER)
The story of two people who were meant to be together.

FADE TO:

INT. KITCHEN - NIGHT

John prepares dinner, humming to himself.

JOHN
Time to cook something special.

FADE OUT.
"""

SAMPLE_SCREENPLAY_2 = """
INT. COFFEE SHOP - MORNING

The coffee shop is bustling with morning commuters. Sarah sits at a corner table, typing on her laptop.

SARAH
(to herself)
I need to finish this report.

WAITER
Good morning! What can I get you?

SARAH
A large coffee, please.

WAITER
Coming right up.

SARAH (V.O.)
I remember this day clearly. It was the beginning of everything.

CUT TO:

EXT. STREET - CONTINUOUS

Sarah walks down the busy street, coffee in hand.

SARAH
(whispering)
Today is the day.

DISSOLVE TO:

INT. OFFICE - LATER

Sarah sits at her desk, staring at her computer screen.

SARAH
I can't believe this is happening.

BOSS (O.S.)
Sarah, can you come to my office?

SARAH
Of course, Mr. Johnson.
"""

SAMPLE_SCREENPLAY_3 = """
INT. BEDROOM - NIGHT

A young woman, LISA, sits on her bed, holding a letter.

LISA
(reading aloud)
Dear Lisa, I hope this letter finds you well...

LISA (V.O.)
I remember the first time I read this letter. It changed everything.

FLASHBACK:

INT. CLASSROOM - DAY (FLASHBACK)

Young Lisa sits at her desk, writing in a notebook.

TEACHER
Lisa, can you answer question three?

LISA
(hesitant)
I'm not sure, Mrs. Smith.

TEACHER
That's okay. Take your time.

BACK TO PRESENT:

INT. BEDROOM - NIGHT

Lisa folds the letter and places it in a drawer.

LISA
Some things are meant to be.

FADE OUT.
"""


class TestSampleScreenplays:
    """Test cases using sample screenplay texts"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.parser = ScreenplayParser()
    
    def test_sample_screenplay_1(self):
        """Test parsing sample screenplay 1"""
        scenes = self.parser.parse(SAMPLE_SCREENPLAY_1)
        
        assert len(scenes) == 3
        
        # Test first scene
        scene1 = scenes[0]
        assert scene1.heading.location == "LIVING ROOM"
        assert scene1.heading.time_of_day == "DAY"
        assert len(scene1.dialogue) == 1
        assert len(scene1.voice_over) == 1
        assert scene1.dialogue[0]["character"] == "JOHN"
        assert scene1.voice_over[0]["character"] == "MARY (V.O.)"
        
        # Test second scene
        scene2 = scenes[1]
        assert scene2.heading.location == "GARDEN"
        assert scene2.heading.time_of_day == "EVENING"
        assert len(scene2.dialogue) == 1
        assert len(scene2.voice_over) == 1
        assert scene2.dialogue[0]["character"] == "MARY"
        assert scene2.voice_over[0]["character"] == "NARRATOR (VOICE OVER)"
        
        # Test third scene
        scene3 = scenes[2]
        assert scene3.heading.location == "KITCHEN"
        assert scene3.heading.time_of_day == "NIGHT"
        assert len(scene3.dialogue) == 1
        assert len(scene3.voice_over) == 0
        assert scene3.dialogue[0]["character"] == "JOHN"
    
    def test_sample_screenplay_2(self):
        """Test parsing sample screenplay 2"""
        scenes = self.parser.parse(SAMPLE_SCREENPLAY_2)
        
        assert len(scenes) == 3
        
        # Test first scene
        scene1 = scenes[0]
        assert scene1.heading.location == "COFFEE SHOP"
        assert scene1.heading.time_of_day == "MORNING"
        assert len(scene1.dialogue) == 3
        assert len(scene1.voice_over) == 1
        assert scene1.dialogue[0]["parenthetical"] == "(to herself)"
        assert scene1.voice_over[0]["character"] == "SARAH (V.O.)"
        
        # Test second scene
        scene2 = scenes[1]
        assert scene2.heading.location == "STREET"
        assert scene2.heading.time_of_day == "CONTINUOUS"
        assert len(scene2.dialogue) == 1
        assert scene2.dialogue[0]["parenthetical"] == "(whispering)"
        
        # Test third scene
        scene3 = scenes[2]
        assert scene3.heading.location == "OFFICE"
        assert scene3.heading.time_of_day == "LATER"
        assert len(scene3.dialogue) == 2
        assert scene3.dialogue[1]["character"] == "SARAH"
    
    def test_sample_screenplay_3(self):
        """Test parsing sample screenplay 3 with flashback"""
        scenes = self.parser.parse(SAMPLE_SCREENPLAY_3)
        
        assert len(scenes) == 3
        
        # Test first scene
        scene1 = scenes[0]
        assert scene1.heading.location == "BEDROOM"
        assert scene1.heading.time_of_day == "NIGHT"
        assert len(scene1.dialogue) == 1
        assert len(scene1.voice_over) == 1
        assert scene1.dialogue[0]["parenthetical"] == "(reading aloud)"
        assert scene1.voice_over[0]["character"] == "LISA (V.O.)"
        
        # Test flashback scene
        scene2 = scenes[1]
        assert scene2.heading.location == "CLASSROOM"
        assert scene2.heading.time_of_day == "DAY (FLASHBACK)"
        assert len(scene2.dialogue) == 2
        assert scene2.dialogue[0]["character"] == "TEACHER"
        assert scene2.dialogue[1]["character"] == "LISA"
        
        # Test back to present scene
        scene3 = scenes[2]
        assert scene3.heading.location == "BEDROOM"
        assert scene3.heading.time_of_day == "NIGHT"
        assert len(scene3.dialogue) == 1
        assert scene3.dialogue[0]["character"] == "LISA"
