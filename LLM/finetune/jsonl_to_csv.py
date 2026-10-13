"""Combines data/bp/{train,val,test}.jsonl and their *_meta.jsonl labels into ONE csv for Excel.

  python jsonl_to_csv.py            # writes data/bp_csv/bp_dataset.csv

One row per example. The (constant) system prompt is left out. Filter the `split` column in Excel to see
only train / val / test. This file is for reading only - training and evaluation use the .jsonl files.
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "data", "bp")
OUT_DIR = os.path.join(HERE, "data", "bp_csv")
SPLITS = ("train", "val", "test")
META_COLUMNS = ["kind", "systolic", "diastolic", "status", "emergency", "target", "expect", "intent", "topic"]


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def rows():
    for split in SPLITS:
        records = read_jsonl(os.path.join(SRC, f"{split}.jsonl"))
        metas = read_jsonl(os.path.join(SRC, f"{split}_meta.jsonl"))
        assert len(records) == len(metas), f"{split}: {len(records)} examples but {len(metas)} labels"
        for rec, meta in zip(records, metas):
            user, assistant = rec["messages"][1]["content"], rec["messages"][2]["content"]
            yield {"split": split, "user": user, "assistant": assistant, **{c: meta.get(c, "") for c in META_COLUMNS}}


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "bp_dataset.csv")
    n = 0
    # utf-8-sig so Excel reads symbols correctly; answers contain line breaks, which csv quotes properly
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["split", *META_COLUMNS, "user", "assistant"])
        w.writeheader()
        for row in rows():
            w.writerow(row)
            n += 1
    print(f"{n} examples -> {path}")
