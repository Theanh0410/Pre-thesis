"""Scores a model served by Ollama on BPQA100 and on the generated blood-pressure test set.

Examples
  python evaluate_ollama.py --model llama3.2 --tag llama32_3b-base --format-hint
  python evaluate_ollama.py --model bp-llama32 --tag llama32_3b-finetuned
  python evaluate_ollama.py --model llama3.2 --tag smoke --limit 5     # quick check

Each run writes results/<tag>.json (scores + every raw answer, so you can re-score without
re-running the model) and prints Markdown tables. Combine runs with make_table.py.

Fairness notes
  * Both base and fine-tuned models get the SAME system prompt unless you pass --no-system.
  * --format-hint tells a model that was NOT fine-tuned on our answer format to begin with
    'Blood pressure status:'; leave it off for fine-tuned models.
  * temperature is 0 so a run is repeatable.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bp_eval  # noqa: E402
from bp_common import SYSTEM  # noqa: E402


def make_ask(model, url, temperature, num_predict, timeout):
    def ask(messages):
        body = json.dumps({
            "model": model, "messages": messages, "stream": False,
            "options": {"temperature": temperature, "num_predict": num_predict},
        }).encode("utf-8")
        req = urllib.request.Request(f"{url}/api/chat", data=body,
                                     headers={"Content-Type": "application/json"})
        last = None
        for _ in range(3):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.load(resp)["message"]["content"]
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}"
                if e.code == 404:
                    break          # unknown model name: retrying will not help
            except Exception as e:  # connection refused, timeout, ...
                last = repr(e)
        raise SystemExit(f"Ollama request failed ({last}).\n"
                         f"Is `ollama serve` running at {url}, and does `ollama list` show '{model}'?")
    return ask


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="Ollama model name (see `ollama list`)")
    ap.add_argument("--tag", help="name for the results file (default: the model name)")
    ap.add_argument("--bpqa", default=os.path.join(HERE, "dataset", "test_BPquestions100.csv"))
    ap.add_argument("--test-dir", default=os.path.join(HERE, "data", "bp"))
    ap.add_argument("--out-dir", default=os.path.join(HERE, "results"))
    ap.add_argument("--url", default="http://localhost:11434")
    ap.add_argument("--only", choices=["bpqa", "readings"], help="run just one of the two test sets")
    ap.add_argument("--no-system", action="store_true", help="do not send the system prompt")
    ap.add_argument("--format-hint", action="store_true", help="ask for the 'Blood pressure status:' format")
    ap.add_argument("--strict", action="store_true", help="Yes/No must be the first word of the answer")
    ap.add_argument("--limit", type=int, help="only the first N items of each set (smoke test)")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--num-predict", type=int, default=300, help="max tokens per answer")
    ap.add_argument("--timeout", type=int, default=180)
    args = ap.parse_args()

    system = None if args.no_system else SYSTEM
    ask = make_ask(args.model, args.url, args.temperature, args.num_predict, args.timeout)
    result = {"model": args.model, "settings": {k: v for k, v in vars(args).items()
                                                if k in ("no_system", "format_hint", "strict", "limit",
                                                         "temperature", "num_predict")}}

    if args.only != "readings":
        rows = bp_eval.load_bpqa(args.bpqa)
        result["bpqa"] = {}
        for column in ("question", "without_bp"):
            print(f"BPQA100 [{column}] ...", flush=True)
            result["bpqa"][column] = bp_eval.run_bpqa(rows, ask, column, system, args.strict, args.limit)
    if args.only != "bpqa":
        records = read_jsonl(os.path.join(args.test_dir, "test.jsonl"))
        metas = read_jsonl(os.path.join(args.test_dir, "test_meta.jsonl"))
        print(f"Generated test set ({len(records)} items) ...", flush=True)
        result["readings"] = bp_eval.run_readings(records, metas, ask, system, args.format_hint,
                                                  args.strict, args.limit)

    os.makedirs(args.out_dir, exist_ok=True)
    tag = (args.tag or args.model).replace(":", "_").replace("/", "_")
    path = os.path.join(args.out_dir, f"{tag}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=1, ensure_ascii=False)
    print()
    print(bp_eval.format_result(result))
    print("saved", path)


if __name__ == "__main__":
    main()
