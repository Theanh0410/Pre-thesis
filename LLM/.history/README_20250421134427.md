# Project Setup Guide

## Prerequisites
- **Conda**: Make sure Conda is installed. If not, download it from [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download).

---

## 1. Create Conda Environment
To set up a Python 3.10.x environment (required for spaCy compatibility), run:

```bash
conda create -n llm python=3.10
conda activate llm

### NOTES
Use Python 3.10.x (needed for spaCy compatibility).

Always activate the Conda environment (llm) before running the project:
conda activate llm

## 2. Install Dependencies
Install all required packages from requirements.txt:

```bash
pip install -r requirements.txt


## 3. Download spaCy Language Model
Activate spaCy by downloading the English language model:

```bash
python -m spacy download en_core_web_sm

