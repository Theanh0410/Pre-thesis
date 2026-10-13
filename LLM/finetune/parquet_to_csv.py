"""Converts the MedQuAD parquet file into CSVs you can open in Excel.

  pip install pandas pyarrow
  python parquet_to_csv.py                      # uses the parquet in dataset/
  python parquet_to_csv.py path/to/file.parquet

Writes next to the parquet file:
  medquad_bp.csv    only blood-pressure rows that have an answer (what the notebook trains on)
  medquad_full.csv  every row that has an answer (about 16,400 of the 47,441; the rest were
                    blanked by the dataset's publisher)
"""
import glob
import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

# Same selection as the notebook's MedQuAD cell.
KEYWORDS = ["high blood pressure", "hypertension", "blood pressure"]
EXCLUDE = ["pulmonary"]


def is_bp(row):
    text = f"{row['question'] or ''} {row['question_focus'] or ''}".lower()
    return any(k in text for k in KEYWORDS) and not any(e in text for e in EXCLUDE)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        found = glob.glob(os.path.join(HERE, "dataset", "*.parquet"))
        if not found:
            raise SystemExit("no .parquet file in dataset/ - pass the path as an argument")
        path = found[0]

    df = pd.read_parquet(path)
    print(f"{len(df)} rows, columns: {list(df.columns)}")
    has_answer = df[df["answer"].notna() & (df["answer"].str.strip() != "")]
    bp = has_answer[has_answer.apply(is_bp, axis=1)]

    out_dir = os.path.dirname(os.path.abspath(path))
    # utf-8-sig so Excel reads accents and symbols correctly
    has_answer.to_csv(os.path.join(out_dir, "medquad_full.csv"), index=False, encoding="utf-8-sig")
    bp.to_csv(os.path.join(out_dir, "medquad_bp.csv"), index=False, encoding="utf-8-sig")
    print(f"{len(has_answer)} rows with an answer -> medquad_full.csv")
    print(f"{len(bp)} blood-pressure rows with an answer -> medquad_bp.csv")
