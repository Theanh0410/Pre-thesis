"""
Contextual Command Processor - Converts natural-language statements
("I'm hot", "I want to go to bed") into device commands.

Matching is delegated to IntentMatcher (semantic embedding similarity against
example phrases configured per intent, e.g. smarthome/intents.json) rather
than hardcoded keyword regexes, so new phrasings for an existing intent
generally don't need code changes - just more examples in the config.
"""

import re

from intent_matching import IntentMatcher

# Room detection from context
ROOM_KEYWORDS = {
    "bedroom": ["bedroom", "bed", "sleep", "bedroom"],
    "living room": ["living room", "lounge", "living", "room"],
    "kitchen": ["kitchen", "cook"],
    "bathroom": ["bathroom", "bath", "shower"],
}

# Common speech recognition mishearings.
# Maps mishearing -> correct word, applied before matching so embeddings see
# normalized text.
VOICE_MISHEARING_MAP = {
    "coat": "cold",
    "coal": "cold",
    "colon": "cold",
    "code": "cold",
    "colt": "cold",
    "colts": "cold",
    "gold": "cold",
    "hole": "cold",
    "halls": "cold",
    "hauled": "cold",
    "hott": "hot",
    "hottie": "hot",
    "heart": "hot",
    "hut": "hot",
    "hall": "cold",
    "aud": "cold",
    "allowed": "cold",
    "aloud": "cold",
    "sleepie": "sleepy",
    "slip": "sleepy",
    "slippery": "sleepy",
    "darker": "dark",
    "darque": "dark",
}


def correct_voice_mishearing(text):
    """Correct common speech recognition mishearings before matching."""
    text_lower = text.lower()
    for mishearing, correct_word in VOICE_MISHEARING_MAP.items():
        text_lower = re.sub(rf"\b{mishearing}\b", correct_word, text_lower)
    return text_lower


class ContextualCommandProcessor:
    """
    Maps contextual/natural-language statements to smart home device
    commands. Integrates with SmartHomeCommandExtractor for comprehensive
    command understanding (this handles indirect phrasing; the extractor
    handles direct commands).
    """

    def __init__(self, intents, embed_fn, room_actions=None, object_room_map=None, threshold=0.6):
        """
        Args:
            intents: {intent_name: {"examples": [str, ...], "actions": [{"device", "action", "room"}, ...]}}
            embed_fn: list[str] -> list[vector], e.g. a SentenceTransformer's .encode
            room_actions: dict of valid actions per room (for validity checks)
            object_room_map: dict mapping devices to default rooms (reserved for future use)
            threshold: minimum cosine similarity to accept an intent match
        """
        self.matcher = IntentMatcher(intents, embed_fn)
        self.room_actions = room_actions or {}
        self.object_room_map = object_room_map or {}
        self.threshold = threshold

    def _correct_voice_mishearing(self, text):
        return correct_voice_mishearing(text)

    def extract_room_from_text(self, text):
        """Extract an explicit room mention from text, if any."""
        text_lower = text.lower()
        for room, keywords in ROOM_KEYWORDS.items():
            for keyword in keywords:
                if re.search(rf"\b{re.escape(keyword)}\b", text_lower):
                    return room
        return None

    def process_contextual_command(self, text):
        """
        Convert a natural-language statement into device command(s).

        Returns a list of command dicts (possibly empty), in the same shape
        SmartHomeCommandExtractor produces: sentence/action/object/room/valid/score.
        An intent with multiple configured actions produces one command dict
        per action. If the text mentions a room explicitly, that room
        overrides each action's configured default room.
        """
        corrected_text = self._correct_voice_mishearing(text)
        matches = self.matcher.match(corrected_text, threshold=self.threshold)

        if not matches:
            return []

        extracted_room = self.extract_room_from_text(text)

        commands = []
        for match in matches:
            # Only let an extracted room override the configured room(s) when
            # this intent's actions all share one ambiguous default room
            # (e.g. "hot" -> living room fan, unless another room is named).
            # An intent whose actions deliberately target different rooms
            # (e.g. "going_to_bed" -> bedroom light + living room light)
            # keeps its explicit per-action rooms regardless of stray room
            # keywords in the sentence.
            action_rooms = {a.get("room", "living room") for a in match.actions}
            override_room = extracted_room if extracted_room and len(action_rooms) == 1 else None

            for action in match.actions:
                device = action["device"]
                act = action["action"]
                room = override_room or action.get("room", "living room")

                command = {
                    "sentence": text,
                    "action": act,
                    "object": device,
                    "room": room,
                    "valid": True,
                    "score": match.score,
                    "source": "contextual",
                    "intent": match.intent,
                }

                if self.room_actions:
                    action_key = f"{act} {device}".lower()
                    command["valid"] = action_key in [a.lower() for a in self.room_actions.get(room, [])]

                commands.append(command)

        return commands

    def is_contextual_statement(self, text):
        """Check if text matches any configured intent (vs. a direct command)."""
        corrected_text = self._correct_voice_mishearing(text)
        return len(self.matcher.match(corrected_text, threshold=self.threshold)) > 0
