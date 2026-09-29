"""
Schema/regression checks for smarthome/intents.json - the data file the
intent-matching feature depends on. Not TDD'd (it's config, not logic), but
guards against someone breaking its shape or dropping the going_to_bed
intent this feature was built for. Run:
    python -m unittest test_smarthome_intents_config -v
"""
import json
import os
import unittest

INTENTS_PATH = os.path.join(os.path.dirname(__file__), "smarthome", "intents.json")


class IntentsConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(INTENTS_PATH) as f:
            cls.intents = json.load(f)

    def test_every_intent_has_nonempty_examples_and_well_formed_actions(self):
        for name, config in self.intents.items():
            with self.subTest(intent=name):
                self.assertTrue(config.get("examples"), f"{name} has no examples")
                self.assertTrue(config.get("actions"), f"{name} has no actions")
                for action in config["actions"]:
                    self.assertIn("device", action)
                    self.assertIn("action", action)
                    self.assertIn("room", action)

    def test_going_to_bed_intent_turns_off_bedroom_light(self):
        self.assertIn("going_to_bed", self.intents)
        actions = self.intents["going_to_bed"]["actions"]
        self.assertTrue(
            any(a["device"] == "light" and a["action"] == "turn off" and a["room"] == "bedroom"
                for a in actions),
            "going_to_bed should turn off the bedroom light",
        )


if __name__ == "__main__":
    unittest.main()
