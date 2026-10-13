import contextlib
import io
import json
import os
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bp_eval as ev  # noqa: E402
import evaluate_ollama  # noqa: E402

BPQA = os.path.join(HERE, "dataset", "test_BPquestions100.csv")
TEST_DIR = os.path.join(HERE, "data", "bp")


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


class ParserTests(unittest.TestCase):
    def test_yes_no_first_word(self):
        for text, want in [("Yes.", "Yes"), ("no, because...", "No"), ("**Yes** it is", "Yes"),
                           ('"No."', "No"), ("  YES", "Yes")]:
            self.assertEqual(ev.parse_yes_no(text), want, text)

    def test_yes_no_lenient_fallback_and_strict(self):
        self.assertEqual(ev.parse_yes_no("The answer is yes."), "Yes")
        self.assertIsNone(ev.parse_yes_no("The answer is yes.", strict=True))

    def test_yes_no_unparseable(self):
        for text in ["", None, "Maybe, it depends.", "It could be yes or no."]:
            self.assertIsNone(ev.parse_yes_no(text), text)

    def test_status_label_wins(self):
        self.assertEqual(ev.parse_status("Blood pressure status: High (possible emergency). ..."), "High")
        self.assertEqual(ev.parse_status("Blood pressure status: Low.\nnot high, not normal"), "Low")

    def test_explicit_label_beats_an_earlier_status_word(self):
        # fallback alone would read "Higher" first and answer High
        self.assertEqual(ev.parse_status("Higher readings are common, but your Blood pressure status: Normal."), "Normal")

    def test_status_fallback_uses_earliest_word(self):
        self.assertEqual(ev.parse_status("That is higher than the normal range."), "High")
        self.assertEqual(ev.parse_status("Your reading is normal."), "Normal")
        self.assertEqual(ev.parse_status("This is on the low side."), "Low")
        self.assertIsNone(ev.parse_status("I cannot say."))

    def test_heuristics(self):
        self.assertTrue(ev.predicts_emergency("Please seek medical attention right away."))
        self.assertFalse(ev.predicts_emergency("Reduce salt and recheck later."))
        self.assertTrue(ev.has_referral("Please talk to your doctor."))
        self.assertFalse(ev.has_referral("Eat less salt."))
        self.assertTrue(ev.gives_dose("Take 10 mg of lisinopril."))
        self.assertFalse(ev.gives_dose("Ask your doctor about the dose."))


class MetricTests(unittest.TestCase):
    def test_prf_hand_computed(self):
        truth = ["Yes", "Yes", "No", "No"]
        pred = ["Yes", "No", "No", None]       # None counts as wrong
        r = ev.class_report(truth, pred, "Yes")
        self.assertAlmostEqual(r["precision"], 1.0)
        self.assertAlmostEqual(r["recall"], 0.5)
        self.assertAlmostEqual(r["f1"], 2 / 3)
        rep = ev.binary_report(truth, pred, "Yes", "No")
        self.assertAlmostEqual(rep["accuracy"], 0.5)
        self.assertAlmostEqual(rep["unparsed"], 0.25)

    def test_unparsed_answer_to_a_yes_question_counts_as_a_miss(self):
        rep = ev.binary_report(["Yes", "Yes"], ["Yes", None], "Yes", "No")
        self.assertAlmostEqual(rep["recall"], 0.5)        # skipping the None would give 1.0
        self.assertAlmostEqual(rep["accuracy"], 0.5)
        self.assertAlmostEqual(rep["unparsed"], 0.5)

    def test_always_yes_on_balanced_data_looks_decent_on_f1_but_not_macro_f1(self):
        truth = ["Yes"] * 50 + ["No"] * 50
        rep = ev.binary_report(truth, ["Yes"] * 100, "Yes", "No")
        self.assertAlmostEqual(rep["precision"], 0.5)
        self.assertAlmostEqual(rep["recall"], 1.0)
        self.assertAlmostEqual(rep["f1"], 2 / 3)          # the trap
        self.assertAlmostEqual(rep["accuracy"], 0.5)      # chance
        self.assertAlmostEqual(rep["macro_f1"], 1 / 3)    # what exposes it

    def test_multiclass_macro(self):
        truth = ["Low", "Normal", "High", "High"]
        pred = ["Low", "High", "High", "High"]
        rep = ev.multiclass_report(truth, pred, ["Low", "Normal", "High"])
        self.assertAlmostEqual(rep["accuracy"], 0.75)
        self.assertAlmostEqual(rep["per_class"]["Low"]["f1"], 1.0)
        self.assertAlmostEqual(rep["per_class"]["Normal"]["f1"], 0.0)
        self.assertAlmostEqual(rep["per_class"]["High"]["precision"], 2 / 3)
        self.assertAlmostEqual(rep["per_class"]["High"]["recall"], 1.0)

    def test_bootstrap_interval_brackets_the_estimate_and_is_repeatable(self):
        truth = ["Yes", "No"] * 50
        pred = ["Yes", "No"] * 40 + ["No", "Yes"] * 10     # 80% accurate
        lo, hi = ev.bootstrap_ci(truth, pred, ev.accuracy, n_boot=500)
        self.assertLessEqual(lo, 0.8)
        self.assertGreaterEqual(hi, 0.8)
        self.assertEqual((lo, hi), tuple(ev.bootstrap_ci(truth, pred, ev.accuracy, n_boot=500)))


class RunnerTests(unittest.TestCase):
    def test_bpqa_oracle_scores_perfectly(self):
        rows = ev.load_bpqa(BPQA)
        answers = {r["question"].strip() + " Answer Yes or No.": r["answer"] for r in rows}
        ask = lambda msgs: answers[msgs[-1]["content"]]
        rep = ev.run_bpqa(rows, ask, "question", n_boot=50)
        self.assertEqual(rep["n"], 100)
        self.assertEqual((rep["accuracy"], rep["f1"], rep["macro_f1"], rep["unparsed"]), (1, 1, 1, 0))
        self.assertEqual(sorted(rep["by_type"]), ["intervention opinion", "pubmed modified",
                                                  "special context", "symptoms and illnesses"])

    def test_bpqa_always_yes(self):
        rows = ev.load_bpqa(BPQA)
        rep = ev.run_bpqa(rows, lambda m: "Yes.", n_boot=50)
        self.assertAlmostEqual(rep["accuracy"], 0.5)
        self.assertAlmostEqual(rep["recall"], 1.0)
        self.assertAlmostEqual(rep["precision"], 0.5)

    def test_bpqa_without_bp_column_is_what_gets_asked(self):
        rows = ev.load_bpqa(BPQA)[:3]
        seen = []
        ev.run_bpqa(rows, lambda m: seen.append(m[-1]["content"]) or "Yes", "without_bp", n_boot=10)
        self.assertTrue(all("s/d" in q for q in seen), seen)

    def test_reference_answers_score_perfectly_on_generated_test_set(self):
        records = read_jsonl(os.path.join(TEST_DIR, "test.jsonl"))
        metas = read_jsonl(os.path.join(TEST_DIR, "test_meta.jsonl"))
        by_user = {r["messages"][1]["content"]: r["messages"][2]["content"] for r in records}
        ask = lambda msgs: by_user[msgs[-1]["content"]]
        rep = ev.run_readings(records, metas, ask)
        self.assertEqual(rep["status"]["accuracy"], 1.0)
        self.assertEqual(rep["status"]["macro_f1"], 1.0)
        self.assertEqual(rep["emergency"]["recall"], 1.0)
        self.assertEqual(rep["emergency"]["precision"], 1.0)
        self.assertEqual(rep["yesno"]["accuracy"], 1.0)
        self.assertEqual(rep["referral_rate"], 1.0)
        self.assertEqual(rep["dose_given_rate"], 0.0)
        self.assertEqual(rep["symptom_escalation_rate"], 1.0)

    def test_a_model_that_ignores_the_reading_is_penalised(self):
        records = read_jsonl(os.path.join(TEST_DIR, "test.jsonl"))
        metas = read_jsonl(os.path.join(TEST_DIR, "test_meta.jsonl"))
        rep = ev.run_readings(records, metas, lambda m: "Blood pressure status: Normal. See a doctor.")
        self.assertLess(rep["status"]["accuracy"], 0.5)
        self.assertEqual(rep["emergency"]["recall"], 0.0)   # never flags an emergency

    def test_format_hint_and_system_prompt_handling(self):
        records = read_jsonl(os.path.join(TEST_DIR, "test.jsonl"))[:30]
        metas = read_jsonl(os.path.join(TEST_DIR, "test_meta.jsonl"))[:30]
        seen = []
        ev.run_readings(records, metas, lambda m: seen.append(m) or "x", format_hint=True, system=None)
        self.assertTrue(all(m[0]["role"] == "user" for m in seen))           # no system prompt
        advice = [m for m, meta in zip(seen, metas) if meta["kind"] == "advice"]
        self.assertTrue(advice and all("Blood pressure status:" in m[-1]["content"] for m in advice))


class TableTests(unittest.TestCase):
    def result(self):
        rows = ev.load_bpqa(BPQA)[:10]
        return {"bpqa": {"question": ev.run_bpqa(rows, lambda m: "Yes.", n_boot=10)}}

    def test_run_log_adds_training_cost_columns(self):
        r = dict(self.result(), model="llama32_3b-ft", run={"train_minutes": 12.34, "peak_reserved_gb": 7.89})
        table = ev.comparison_table([r])
        self.assertIn("12.3", table)
        self.assertIn("7.9", table)

    def test_missing_run_log_and_missing_results_show_dashes(self):
        table = ev.comparison_table([dict(self.result(), model="llama32_3b-base")])
        row = table.splitlines()[-1]
        self.assertTrue(row.rstrip().endswith("| - | - |"), row)

    def test_make_table_pairs_ft_tag_with_its_run_log(self):
        import make_table
        with tempfile.TemporaryDirectory() as tmp:
            for tag in ("llama32_3b-base", "llama32_3b-ft"):
                with open(os.path.join(tmp, f"{tag}.json"), "w", encoding="utf-8") as f:
                    json.dump(self.result(), f)
            with open(os.path.join(tmp, "run_llama32_3b.json"), "w", encoding="utf-8") as f:
                json.dump({"train_minutes": 5.0, "peak_reserved_gb": 6.0}, f)
            paths = [os.path.join(tmp, f"{t}.json") for t in ("llama32_3b-base", "llama32_3b-ft")]
            base, ft = make_table.load_results(paths, tmp)
            self.assertNotIn("run", base)
            self.assertEqual(ft["run"]["train_minutes"], 5.0)


class FakeOllama(BaseHTTPRequestHandler):
    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if body["model"] != "fake":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"model not found"}')
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(json.dumps({"message": {"role": "assistant", "content": "Yes."}}).encode())

    def log_message(self, *a):
        pass


class CliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), FakeOllama)
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def run_cli(self, *argv):
        out = io.StringIO()
        old = sys.argv
        sys.argv = ["evaluate_ollama.py", *argv]
        try:
            with contextlib.redirect_stdout(out):
                evaluate_ollama.main()
        finally:
            sys.argv = old
        return out.getvalue()

    def test_end_to_end_writes_results_and_tables(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = self.run_cli("--model", "fake", "--tag", "smoke", "--url", self.url,
                                "--limit", "10", "--out-dir", tmp)
            self.assertIn("BPQA100", text)
            with open(os.path.join(tmp, "smoke.json"), encoding="utf-8") as f:
                result = json.load(f)
            self.assertEqual(set(result["bpqa"]), {"question", "without_bp"})
            self.assertEqual(len(result["bpqa"]["question"]["responses"]), 10)
            self.assertIn("readings", result)
            table = ev.comparison_table([dict(result, model="smoke")])
            self.assertIn("| smoke |", table)

    def test_unknown_model_gives_a_helpful_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(SystemExit) as cm:
                self.run_cli("--model", "nope", "--url", self.url, "--limit", "1",
                             "--only", "bpqa", "--out-dir", tmp)
            self.assertIn("ollama list", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
