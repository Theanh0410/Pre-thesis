# Blood-pressure fine-tuning experiment

Fine-tune several small models for blood-pressure advice and compare them (thesis experiment).

## Workflow

1. **Generate the data** (already done once; rerun if you change `LLM/server/health_advice.py`):
   `python make_bp_dataset.py` -> `data/bp/train.jsonl`, `val.jsonl`, `test.jsonl` (+ `*_meta.jsonl`, used only by evaluation).
2. **Train in Colab**: upload `bp_finetune.ipynb` (File -> Upload notebook), choose a **T4 GPU**, upload the three `.jsonl`
   files, set `RUN_NAME` in the *Run config* cell, run the cells one at a time. The last cell copies the adapter, the GGUF and
   `run_<name>.json` (training time, memory, losses) to Google Drive. Repeat per model, **keeping every other setting identical**.
3. **Import into Ollama** (per fine-tuned model): download the GGUF + `Modelfile` from Drive, then
   `ollama create bp-llama32 -f Modelfile`.
4. **Evaluate** (base and fine-tuned models, same script):
   ```
   ollama pull llama3.2
   python evaluate_ollama.py --model llama3.2     --tag llama32_3b-base --format-hint
   python evaluate_ollama.py --model bp-llama32   --tag llama32_3b-finetuned
   ```
   `--format-hint` is for models *not* fine-tuned on the answer format. Results go to `results/<tag>.json`.
5. **Table**: copy each `run_<name>.json` from Drive into `results/`, then `python make_table.py` (add `--detail` for the
   per-class and per-category tables). **Name the tags `<RUN_NAME>-base` and `<RUN_NAME>-ft`** (e.g. `llama32_3b-base`,
   `llama32_3b-ft`): the `-ft` row picks up its training minutes and peak GPU memory from `run_<RUN_NAME>.json`.

Base-model names in Ollama (check ollama.com/library if a pull fails): `llama3.2`, `qwen2.5:3b`, `phi3.5`, `gemma2:2b`,
`smollm2:1.7b`. Import a fine-tuned GGUF with the `Modelfile` Unsloth writes next to it. If there is none, take the base
model's template: `ollama show llama3.2 --modelfile > Modelfile`, then change its `FROM` line to the GGUF path. After
`ollama create`, run it once and confirm the answer starts with `Blood pressure status:` and stops cleanly.

## What is measured

| Test set | What | Metrics |
|---|---|---|
| BPQA100 (`dataset/`) | 100 balanced Yes/No questions, evaluation only | accuracy (+95% bootstrap CI), precision / recall / F1 of "Yes", macro-F1, unparsed %, per category; also the `without_bp` control (reading hidden) |
| Generated test set | BP status from a reading, Yes/No questions, safety prompts | per-class P/R/F1 for Low/Normal/High, emergency P/R/F1, Yes/No P/R/F1, referral rate, dose-given rate |

Unparseable answers count as wrong. With only 100 BPQA100 questions, differences of a few points are noise - look at the CIs.

## Files

| File | Purpose |
|---|---|
| `make_bp_dataset.py`, `bp_common.py` | dataset generator and the wording shared with evaluation |
| `bp_finetune.ipynb` | the one Colab training notebook (has a check that stops the export if the model is not fine-tuned) |
| `export_from_adapter.ipynb` | recovery notebook: reload a saved `lora_<name>` adapter from Drive, verify it, export the GGUF |
| `evaluate_ollama.py`, `bp_eval.py`, `make_table.py` | evaluation (pure-Python scoring, thin Ollama client, table builder) |
| `test_make_bp_dataset.py`, `test_bp_eval.py` | unit tests (stdlib only) |
| `dataset/test_BPquestions100.csv` | BPQA100 (gated on Hugging Face - check terms before publishing) |
