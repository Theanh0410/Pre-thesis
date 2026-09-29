"""
Automated unit tests for ContextualCommandProcessor's intent-based matching.
Uses a fake, deterministic embed_fn (no sentence-transformers needed). Run:
    python -m unittest test_contextual_command_processor -v
"""
import unittest

from ContextualCommandProcessor import ContextualCommandProcessor

ROOM_ACTIONS = {
    "living room": ["Turn on light", "Turn off light", "Turn on fan", "Turn off fan"],
    "bedroom": ["Turn on light", "Turn off light"],
    "kitchen": ["Turn on light", "Turn off light"],
}

GOING_TO_BED_INTENTS = {
    "going_to_bed": {
        "examples": ["i want to go to bed"],
        "actions": [
            {"device": "light", "action": "turn off", "room": "bedroom"},
            {"device": "light", "action": "turn off", "room": "living room"},
        ],
    }
}


def fake_embed_fn(vectors_by_text):
    def embed(texts):
        return [vectors_by_text[t] for t in texts]
    return embed


class ProcessContextualCommandTests(unittest.TestCase):
    def test_matched_intent_emits_one_command_per_configured_action(self):
        embed_fn = fake_embed_fn({
            "i want to go to bed": [1.0, 0.0],
            "i'm heading to sleep now": [1.0, 0.0],
        })
        processor = ContextualCommandProcessor(
            intents=GOING_TO_BED_INTENTS,
            embed_fn=embed_fn,
            room_actions=ROOM_ACTIONS,
        )

        commands = processor.process_contextual_command("i'm heading to sleep now")

        self.assertEqual(len(commands), 2)
        rooms = {c["room"] for c in commands}
        self.assertEqual(rooms, {"bedroom", "living room"})
        for c in commands:
            self.assertEqual(c["action"], "turn off")
            self.assertEqual(c["object"], "light")
            self.assertTrue(c["valid"])

    def test_explicit_room_in_text_overrides_a_single_shared_default_room(self):
        intents = {
            "hot": {
                "examples": ["i'm hot"],
                "actions": [{"device": "fan", "action": "turn on", "room": "living room"}],
            }
        }
        embed_fn = fake_embed_fn({
            "i'm hot": [1.0, 0.0],
            "i'm hot in the kitchen": [1.0, 0.0],
        })
        processor = ContextualCommandProcessor(
            intents=intents, embed_fn=embed_fn, room_actions=ROOM_ACTIONS,
        )

        commands = processor.process_contextual_command("i'm hot in the kitchen")

        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["room"], "kitchen")

    def test_action_invalid_for_room_is_flagged_not_valid(self):
        intents = {
            "going_to_bed": {
                "examples": ["i want to go to bed"],
                # bedroom fan control isn't in ROOM_ACTIONS for bedroom
                "actions": [{"device": "fan", "action": "turn off", "room": "bedroom"}],
            }
        }
        embed_fn = fake_embed_fn({
            "i want to go to bed": [1.0, 0.0],
        })
        processor = ContextualCommandProcessor(
            intents=intents, embed_fn=embed_fn, room_actions=ROOM_ACTIONS,
        )

        commands = processor.process_contextual_command("i want to go to bed")

        self.assertEqual(len(commands), 1)
        self.assertFalse(commands[0]["valid"])


if __name__ == "__main__":
    unittest.main()
