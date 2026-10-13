"""Builds the thesis comparison table from results/*.json (one file per evaluated model).

  python make_table.py                    # every file in results/
  python make_table.py --detail           # also the per-class / per-category tables for each model
  python make_table.py results/a.json results/b.json

Tag convention: <RUN_NAME>-base and <RUN_NAME>-ft (e.g. llama32_3b-base, llama32_3b-ft). For a
"-ft" tag, run_<RUN_NAME>.json (written by the notebook; copy it from Google Drive into
results/ or pass --runs DIR) adds the training-minutes and peak-memory columns.
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bp_eval  # noqa: E402


def load_results(paths, runs_dir):
    results = []
    for p in paths:
        with open(p, encoding="utf-8") as f:
            r = json.load(f)
        tag = os.path.splitext(os.path.basename(p))[0]
        r["model"] = tag
        if tag.endswith("-ft"):
            run_path = os.path.join(runs_dir, f"run_{tag[:-3]}.json")
            if os.path.exists(run_path):
                with open(run_path, encoding="utf-8") as f:
                    r["run"] = json.load(f)
        results.append(r)
    return results


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--runs", default=os.path.join(HERE, "results"), help="folder with run_<name>.json files")
    ap.add_argument("--detail", action="store_true")
    args = ap.parse_args()
    paths = args.files or sorted(p for p in glob.glob(os.path.join(HERE, "results", "*.json"))
                                 if not os.path.basename(p).startswith("run_"))   # run logs are not results
    if not paths:
        raise SystemExit("no result files - run evaluate_ollama.py first")
    results = load_results(paths, args.runs)
    print(bp_eval.comparison_table(results))
    if args.detail:
        for r in results:
            print()
            print(bp_eval.format_result(r))
