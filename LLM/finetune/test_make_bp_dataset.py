import json
import os
import re
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import make_bp_dataset as mk  # noqa: E402
from health_advice import classify_blood_pressure  # noqa: E402


def reading_of(meta):
    return (meta["systolic"], meta["diastolic"])


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = mk.generate(seed=42)

    def rows(self, split, kind=None):
        return [r for r in self.data[split] if kind is None or r[2]["kind"] == kind]

    def test_no_reading_appears_in_two_splits(self):
        seen = {}
        for split in mk.SPLITS:
            for _, _, m in self.data[split]:
                if "systolic" in m:
                    seen.setdefault(reading_of(m), set()).add(split)
        leaked = {r: s for r, s in seen.items() if len(s) > 1}
        self.assertEqual(leaked, {})

    def test_no_prompt_appears_in_two_splits(self):
        where = {}
        for split in mk.SPLITS:
            for prompt, _, m in self.data[split]:
                if m["kind"] in ("safety", "knowledge"):
                    where.setdefault(prompt, set()).add(split)
        self.assertEqual({p for p, s in where.items() if len(s) > 1}, set())

    def test_labels_match_the_classifier(self):
        for split in mk.SPLITS:
            for _, _, m in self.rows(split):
                if "systolic" not in m:
                    continue
                c = classify_blood_pressure(m["systolic"], m["diastolic"])
                self.assertEqual(m["status"], c["status"])
                self.assertEqual(m["emergency"], c["is_emergency"])

    def test_advice_answers_state_the_computed_status(self):
        for split in mk.SPLITS:
            for _, answer, m in self.rows(split, "advice"):
                label = re.match(r"Blood pressure status: (Low|Normal|High)", answer).group(1)
                self.assertEqual(label, m["status"])
                if m["emergency"]:
                    self.assertIn("emergency", answer.lower())

    def test_yes_no_answers_are_correct_and_balanced(self):
        truth = {"high": lambda c: c["status"] == "High", "low": lambda c: c["status"] == "Low",
                 "normal": lambda c: c["status"] == "Normal", "emergency": lambda c: c["is_emergency"]}
        for split in mk.SPLITS:
            rows = self.rows(split, "yesno")
            for _, answer, m in rows:
                c = classify_blood_pressure(m["systolic"], m["diastolic"])
                expect = "Yes" if truth[m["target"]](c) else "No"
                self.assertEqual(m["expect"], expect)
                self.assertTrue(answer.startswith(expect + "."), answer)
            yes = sum(1 for _, _, m in rows if m["expect"] == "Yes")
            self.assertEqual(yes * 2, len(rows))

    def test_every_split_covers_every_group(self):
        for split in mk.SPLITS:
            groups = {mk.group_of(reading_of(m)) for _, _, m in self.rows(split, "advice")}
            self.assertEqual(groups, {"low", "normal", "high", "emergency"}, split)

    def test_every_split_has_threshold_readings(self):
        boundary = set(mk.BOUNDARY)
        for split in mk.SPLITS:
            got = {reading_of(m) for _, _, m in self.rows(split, "advice")} & boundary
            self.assertTrue(got, f"{split} has no boundary readings")

    def test_every_safety_intent_is_in_train_and_test(self):
        for split in ("train", "test"):
            intents = {m["intent"] for _, _, m in self.rows(split, "safety")}
            for intent in mk.SAFETY:
                self.assertIn(intent, intents, f"{intent} missing from {split}")

    def test_assistant_never_gives_a_dose(self):
        dose = re.compile(r"\b\d+\s*(mg|milligrams?|mcg|tablets?|pills?)\b", re.I)
        for split in mk.SPLITS:
            for _, answer, _ in self.data[split]:
                self.assertIsNone(dose.search(answer), answer)

    def test_same_seed_gives_identical_data(self):
        self.assertEqual(self.data, mk.generate(seed=42))
        self.assertNotEqual(self.data["train"], mk.generate(seed=7)["train"])

    def test_written_files_match_notebook_format(self):
        with tempfile.TemporaryDirectory() as out:
            mk.write(self.data, out)
            for split in mk.SPLITS:
                with open(os.path.join(out, f"{split}.jsonl"), encoding="utf-8") as f:
                    records = [json.loads(line) for line in f]
                with open(os.path.join(out, f"{split}_meta.jsonl"), encoding="utf-8") as f:
                    metas = [json.loads(line) for line in f]
                self.assertEqual(len(records), len(metas))
                self.assertEqual(len(records), len(self.data[split]))
                for rec in records:
                    self.assertEqual(list(rec), ["messages"])
                    self.assertEqual([m["role"] for m in rec["messages"]],
                                     ["system", "user", "assistant"])
                    self.assertTrue(all(m["content"].strip() for m in rec["messages"]))


if __name__ == "__main__":
    unittest.main()
