"""
Contextual Command Processor - Converts comfort/emotional statements to device commands.
Example: "I'm hot" -> turn on fan in living room
"""

import re
from difflib import SequenceMatcher

class ContextualCommandProcessor:
    """
    Maps contextual statements (comfort, emotional) to smart home device commands.
    Integrates with SmartHomeCommandExtractor for comprehensive command understanding.
    """
    
    # Comfort state to device action mappings
    COMFORT_MAPPINGS = {
        # Temperature-related
        "hot": {
            "device": "fan",
            "action": "turn on",
            "room": "living room",  # default room
            "priority": 1
        },
        "cold": {
            "device": "fan",
            "action": "turn off",
            "room": "living room",
            "priority": 1
        },
        "warm": {
            "device": "fan",
            "action": "turn on",
            "room": "living room",
            "priority": 0.8
        },
        "freezing": {
            "device": "fan",
            "action": "turn off",
            "room": "living room",
            "priority": 1
        },
        # Darkness/lighting
        "dark": {
            "device": "light",
            "action": "turn on",
            "room": "living room",
            "priority": 0.9
        },
        # "bright": {
        #     "device": "light",
        #     "action": "turn off",
        #     "room": "living room",
        #     "priority": 0.7
        # },
        "too bright": {
            "device": "light",
            "action": "turn off",
            "room": "living room",
            "priority": 0.9
        },
        # Comfort/wellbeing
        "comfortable": {
            "device": "light",
            "action": "turn off",
            "room": "living room",
            "priority": 0.6
        },
        "uncomfortable": {
            "device": "fan",
            "action": "turn on",
            "room": "living room",
            "priority": 0.7
        },
        # Tiredness/sleep
        "sleepy": {
            "device": "light",
            "action": "turn off",
            "room": "bedroom",
            "priority": 0.8
        },
        "tired": {
            "device": "light",
            "action": "turn off",
            "room": "bedroom",
            "priority": 0.8
        },
        "awake": {
            "device": "light",
            "action": "turn on",
            "room": "bedroom",
            "priority": 0.7
        },
    }
    
    # Room detection from context
    ROOM_KEYWORDS = {
        "bedroom": ["bedroom", "bed", "sleep", "bedroom"],
        "living room": ["living room", "lounge", "living", "room"],
        "kitchen": ["kitchen", "cook"],
        "bathroom": ["bathroom", "bath", "shower"],
    }
    
    # Common speech recognition mishearings
    # Maps mishearing -> correct comfort word
    VOICE_MISHEARING_MAP = {
        "coat": "cold",
        "coal": "cold",
        "colon": "cold",
        "code": "cold",
        "colt": "cold",
        "colts": "cold",
        "gold": "cold",
        "colt": "cold",
        "hole": "cold",
        "halls": "cold",
        "hauled": "cold",
        "hole": "cold",
        "hott": "hot",
        "hottie": "hot",
        "heart": "hot",
        "hut": "hot",
        "hall": "cold",
        "hauled": "cold",
        "aud": "cold",
        "allowed": "cold",
        "aloud": "cold",
        "sleepy": "sleepy",
        "sleepie": "sleepy",
        "slip": "sleepy",
        "slippery": "sleepy",
        "darker": "dark",
        "dark": "dark",
        "darque": "dark",
        "darker": "dark",
    }
    
    def __init__(self, room_actions=None, object_room_map=None):
        """
        Initialize the contextual processor.
        
        Args:
            room_actions: Dict of valid actions per room
            object_room_map: Dict mapping devices to default rooms
        """
        self.room_actions = room_actions or {}
        self.object_room_map = object_room_map or {}
    
    def _fuzzy_match_word(self, text_word, target_word, threshold=0.75):
        """
        Check if a word matches another with fuzzy matching (handles typos/mishearings).
        
        Args:
            text_word: Word from user input
            target_word: Word to match against
            threshold: Similarity threshold (0-1)
            
        Returns:
            Similarity score (0-1)
        """
        matcher = SequenceMatcher(None, text_word.lower(), target_word.lower())
        return matcher.ratio()
    
    def _correct_voice_mishearing(self, text):
        """
        Correct common speech recognition mishearings.
        
        Args:
            text: User input text
            
        Returns:
            Corrected text
        """
        text_lower = text.lower()
        
        # First pass: Direct mishearing map
        for mishearing, correct_word in self.VOICE_MISHEARING_MAP.items():
            text_lower = re.sub(rf"\b{mishearing}\b", correct_word, text_lower)
        
        return text_lower
    
    def _find_closest_comfort_word(self, text, threshold=0.75):
        """
        Find comfort words even if slightly misspelled/misheard.
        
        Args:
            text: User input text (lowercased)
            threshold: Minimum similarity score
            
        Returns:
            List of (comfort_word, score) tuples
        """
        matches = []
        words_in_text = text.split()
        
        for word in words_in_text:
            for comfort_word in self.COMFORT_MAPPINGS.keys():
                similarity = self._fuzzy_match_word(word, comfort_word, threshold)
                
                if similarity >= threshold:
                    matches.append((comfort_word, similarity))
        
        # Remove duplicates, keep highest score for each comfort word
        unique_matches = {}
        for comfort_word, score in matches:
            if comfort_word not in unique_matches or score > unique_matches[comfort_word]:
                unique_matches[comfort_word] = score
        
        return unique_matches.items()
    
    def detect_comfort_state(self, text):
        """
        Detect comfort/emotional state from user input with flexible pattern matching.
        Handles variations like:
        - "i'm hot", "i am hot", "i'm feeling hot", "i feel hot", "it's hot", "it is hot"
        - "i'm too hot", "i'm feeling too hot"
        - Corrects common speech recognition mishearings like "coat" -> "cold"
        
        Args:
            text: User input text
            
        Returns:
            List of detected comfort states with scores
        """
        # Step 1: Correct common voice mishearings
        text_corrected = self._correct_voice_mishearing(text)
        
        detected = []
        
        # Step 2: Try pattern matching first (exact comfort words)
        for comfort_word, mapping in self.COMFORT_MAPPINGS.items():
            # Build flexible pattern that matches:
            # "i'm/i am/it's/it is [feeling/too] [very] {comfort_word}"
            
            # Check for multi-word phrases first (like "too bright")
            if " " in comfort_word:
                # Multi-word: match directly
                patterns = [
                    rf"\b{re.escape(comfort_word)}\b",  # Direct match: "too bright"
                    rf"\b(i'm|i am|it's|it is)\s+(?:feeling\s+)?{re.escape(comfort_word)}\b",  # "it's too bright"
                    rf"\b(i\s+(?:am\s+)?feeling|i'm\s+feeling)\s+{re.escape(comfort_word)}\b",  # "i'm feeling too bright"
                ]
            else:
                # Single-word: allow modifiers
                patterns = [
                    # Direct matches: "i'm hot", "it's hot"
                    rf"\b(i'm|i am|it's|it is)\s+(?:feeling\s+)?(?:very\s+)?(?:too\s+)?{comfort_word}\b",
                    # With "feeling": "i'm feeling hot", "i feel hot"
                    rf"\b(i\s+(?:am\s+)?feeling|i'm\s+feeling)\s+(?:very\s+)?(?:too\s+)?{comfort_word}\b",
                    # Standalone: just "{comfort_word}" or "so {comfort_word}"
                    rf"\b(?:so|very|too|really|extremely)?\s+{comfort_word}\b",
                ]
            
            # Check each pattern
            for pattern in patterns:
                if re.search(pattern, text_corrected):
                    detected.append({
                        "state": comfort_word,
                        "mapping": mapping,
                        "score": mapping.get("priority", 0.5),
                        "matched_by": "pattern"
                    })
                    break  # Found this comfort word, move to next
        
        # Step 3: If pattern matching found results, return them
        if detected:
            detected.sort(key=lambda x: x["score"], reverse=True)
            return detected
        
        # Step 4: If no exact matches, try fuzzy matching for mishearings
        fuzzy_matches = self._find_closest_comfort_word(text_corrected, threshold=0.75)
        
        for comfort_word, similarity in fuzzy_matches:
            mapping = self.COMFORT_MAPPINGS[comfort_word]
            # Adjust score based on fuzzy match similarity
            score = mapping.get("priority", 0.5) * similarity
            
            detected.append({
                "state": comfort_word,
                "mapping": mapping,
                "score": score,
                "matched_by": f"fuzzy_match ({similarity:.0%})"
            })
        
        # Sort by priority (highest first)
        detected.sort(key=lambda x: x["score"], reverse=True)
        return detected
    
    def extract_room_from_text(self, text):
        """
        Extract room information from text.
        
        Args:
            text: User input text
            
        Returns:
            Room name or None
        """
        text_lower = text.lower()
        for room, keywords in self.ROOM_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return room
        return None
    
    def process_contextual_command(self, text):
        """
        Convert contextual statement to device command.
        
        Args:
            text: User input text
            
        Returns:
            List of command dicts or empty list if no contextual match
        """
        detected_states = self.detect_comfort_state(text)
        
        if not detected_states:
            return []
        
        # Extract room from text, or use default from mapping
        room = self.extract_room_from_text(text)
        
        commands = []
        for detected in detected_states:
            mapping = detected["mapping"]
            device = mapping["device"]
            action = mapping["action"]
            default_room = mapping.get("room", "living room")
            
            # Use extracted room or fall back to default
            final_room = room or default_room
            
            # Create command structure compatible with SmartHomeCommandExtractor output
            command = {
                "sentence": text,
                "action": action,
                "object": device,
                "room": final_room,
                "valid": True,
                "score": detected["score"],
                "source": "contextual"  # Mark as contextual to distinguish from direct commands
            }
            
            # Validate if room_actions is available
            if self.room_actions:
                action_key = f"{action} {device}".lower()
                is_valid = action_key in [a.lower() for a in self.room_actions.get(final_room, [])]
                command["valid"] = is_valid
            
            commands.append(command)
        
        return commands
    
    def is_contextual_statement(self, text):
        """
        Check if text is a contextual statement (vs direct command).
        
        Args:
            text: User input text
            
        Returns:
            Boolean indicating if text is contextual
        """
        return len(self.detect_comfort_state(text)) > 0
    
    def merge_commands(self, contextual_commands, extracted_commands):
        """
        Merge contextual commands with extracted commands, prioritizing contextual matches.
        
        Args:
            contextual_commands: Commands from contextual processing
            extracted_commands: Commands from SmartHomeCommandExtractor
            
        Returns:
            Merged command list prioritized correctly
        """
        # If strong contextual match found, use it
        if contextual_commands and contextual_commands[0].get("score", 0) > 0.7:
            return contextual_commands
        
        # Combine both if no strong contextual match
        return contextual_commands + extracted_commands if contextual_commands else extracted_commands
