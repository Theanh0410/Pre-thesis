"""
Automated unit tests for intent_matching.py.

Uses a fake, deterministic embed_fn instead of the real sentence-transformers
model, so these run anywhere without the ML dependencies. Run with:
    python -m unittest test_intent_matching -v
"""
import unittest

from intent_matching import IntentMatcher


def fake_embed_fn(vectors_by_text):
    """Build an embed_fn from an exact text->vector lookup (test helper)."""
    def embed(texts):
        return [vectors_by_text[t] for t in texts]
    return embed


class IntentMatcherMatchTests(unittest.TestCase):
    def test_matches_intent_whose_example_is_most_similar_to_input(self):
        intents = {
            "going_to_bed": {
                "examples": ["i want to go to bed"],
                "actions": [{"device": "light", "action": "turn off", "room": "bedroom"}],
            }
        }
        # "i'm heading to sleep" is the input; it's identical (vector-wise)
        # to the example, so similarity should be a perfect 1.0.
        embed_fn = fake_embed_fn({
            "i want to go to bed": [1.0, 0.0],
            "i'm heading to sleep": [1.0, 0.0],
        })

        matcher = IntentMatcher(intents, embed_fn)
        matches = matcher.match("i'm heading to sleep", threshold=0.6)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].intent, "going_to_bed")
        self.assertAlmostEqual(matches[0].score, 1.0)


if __name__ == "__main__":
    unittest.main()
