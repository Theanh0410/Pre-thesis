"""Generates the blood-pressure fine-tuning dataset.

Writes train/val/test .jsonl files (one {"messages": [...]} per line, the format the
notebook's `USE_EXTRA` cell loads) plus {split}_meta.jsonl sidecars with the ground-truth
labels the evaluation script needs.

Example kinds
  advice     user gives a reading -> status line + reason + the SAME advice text the
             deployed assistant uses (health_advice.py) + doctor referral
  yesno      "Is 135/85 high? Answer Yes or No." -> "Yes. ..." (50% yes / 50% no);
             teaches the answer format BPQA100 is scored on WITHOUT using BPQA100 questions
  safety     refuses to prescribe / change doses / diagnose, escalates emergency symptoms,
             asks for the numbers when none were given
  knowledge  Q&A written from LLM/server/documents/health/hypertension.txt

Labels come from classify_blood_pressure(), so they are correct by construction.
Splits are made by READING (and by topic for knowledge), never at random per example, so the
same reading never appears in both train and test.

Usage:  python make_bp_dataset.py [--out data/bp] [--seed 42]
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "server"))

from health_advice import (  # noqa: E402
    BLOOD_PRESSURE_ADVICE,
    BLOOD_PRESSURE_EMERGENCY_ADVICE,
    classify_blood_pressure,
)
from bp_common import DISCLAIMER, EMERGENCY_CLOSE, SYSTEM  # noqa: E402

SPLITS = ("train", "val", "test")

# Readings sitting right on a threshold of classify_blood_pressure.
BOUNDARY = [
    (89, 59), (89, 70), (100, 59), (85, 55), (90, 60), (110, 70), (129, 79), (95, 75),
    (130, 70), (120, 80), (130, 80), (139, 89), (140, 90), (179, 119), (179, 100),
    (180, 90), (150, 120), (180, 120),
]
POOL_TARGET = {"low": 120, "normal": 120, "high": 160, "emergency": 100}


def group_of(reading):
    c = classify_blood_pressure(*reading)
    return "emergency" if c["is_emergency"] else c["status"].lower()


def status_of(reading):
    return classify_blood_pressure(*reading)["status"]


# --------------------------------------------------------------------------- readings
def sample_reading(rng, group):
    while True:
        s, d = rng.randint(70, 215), rng.randint(40, 135)
        if 15 <= s - d <= 100 and group_of((s, d)) == group:   # plausible pulse pressure
            return (s, d)


def build_pool(rng):
    pool = {g: set() for g in POOL_TARGET}
    for r in BOUNDARY:
        pool[group_of(r)].add(r)
    for g, n in POOL_TARGET.items():
        while len(pool[g]) < n:
            pool[g].add(sample_reading(rng, g))
    return {g: sorted(v) for g, v in pool.items()}


def deal(rng, items):
    """70% train / 10% val / 20% test by position after shuffling."""
    items = sorted(items)
    rng.shuffle(items)
    out = {s: [] for s in SPLITS}
    for i, item in enumerate(items):
        out["test" if i % 10 in (0, 5) else "val" if i % 10 == 1 else "train"].append(item)
    return out


def split_readings(rng, pool):
    """Stratified by group; boundary readings are dealt separately so every split gets some."""
    split = {s: [] for s in SPLITS}
    bset = set(BOUNDARY)
    for g in sorted(pool):
        for part in ([r for r in pool[g] if r in bset], [r for r in pool[g] if r not in bset]):
            for s, items in deal(rng, part).items():
                split[s].extend(items)
    return split


# --------------------------------------------------------------------------- text helpers
def fmt(rng, r):
    s, d = r
    return rng.choice([f"{s}/{d}", f"{s}/{d} mmHg", f"{s} over {d}",
                       f"{s} systolic and {d} diastolic"])


ADVICE_PROMPTS = [
    "My blood pressure is {r}. Is that okay?",
    "I just measured {r} on my home monitor. What does that mean?",
    "The nurse told me my reading was {r}. Should I be worried?",
    "Is a reading of {r} normal?",
    "What should I do about a blood pressure of {r}?",
    "BP was {r} this morning, what do you think?",
    "Can you tell me what {r} means for my blood pressure?",
]
ADVICE_PROMPTS_AGE = [
    "I'm {age} years old and my blood pressure is {r}. Any advice?",
    "My mother is {age} and her blood pressure was {r}. Is that a problem?",
    "I am {age}. I measured {r} today. What should I know?",
]

REASON = {
    "low": "Your top number is {s} and your bottom number is {d}; a top number under 90 "
           "or a bottom number under 60 counts as low.",
    "normal": "Your top number is {s} and your bottom number is {d}; both are in the normal "
              "range (90-129 on top, 60-79 on the bottom).",
    "high": "Your top number is {s} and your bottom number is {d}; a top number of 130 or "
            "more, or a bottom number of 80 or more, counts as high.",
    "emergency": "Your top number is {s} and your bottom number is {d}; a top number of 180 "
                 "or more, or a bottom number of 120 or more, is in the emergency range.",
}


def advice_example(rng, r):
    s, d = r
    g = group_of(r)
    status = status_of(r)
    if rng.random() < 0.3:
        prompt = rng.choice(ADVICE_PROMPTS_AGE).format(
            r=fmt(rng, r), age=rng.choice([65, 68, 72, 75, 78, 81, 84, 88]))
    else:
        prompt = rng.choice(ADVICE_PROMPTS).format(r=fmt(rng, r))

    label = "High (possible emergency)" if g == "emergency" else status
    body = BLOOD_PRESSURE_EMERGENCY_ADVICE if g == "emergency" else BLOOD_PRESSURE_ADVICE[status]
    close = EMERGENCY_CLOSE if g == "emergency" else DISCLAIMER
    answer = f"Blood pressure status: {label}.\n{REASON[g].format(s=s, d=d)} {body} {close}"
    meta = {"kind": "advice", "systolic": s, "diastolic": d, "status": status,
            "emergency": g == "emergency"}
    return prompt, answer, meta


# truth table: which yes/no targets are TRUE for each group
TRUTH = {
    "low": {"low"},
    "normal": {"normal"},
    "high": {"high"},
    "emergency": {"high", "emergency"},
}
TARGETS = ("high", "low", "normal", "emergency")
YN_QUESTION = {
    "high": ["Is a blood pressure of {r} considered high?", "Is {r} a high blood pressure reading?"],
    "low": ["Is a blood pressure of {r} considered low?", "Is {r} a low blood pressure reading?"],
    "normal": ["Is a blood pressure of {r} considered normal?", "Is {r} a normal blood pressure reading?"],
    "emergency": ["Is a blood pressure of {r} a medical emergency?",
                  "Does a reading of {r} need emergency care?"],
}


def yesno_answer(r, target, truth):
    s, d = r
    n = f"{s}/{d}"
    g = group_of(r)
    status = status_of(r).lower()
    if target == "high":
        return (f"Yes. {n} is in the high range (130/80 or higher)." if truth
                else f"No. {n} is in the {status} range.")
    if target == "low":
        return (f"Yes. {n} is on the low side (under 90 on top or under 60 on the bottom)." if truth
                else f"No. {n} is in the {status} range.")
    if target == "normal":
        return (f"Yes. {n} is within the normal range (90-129 on top, 60-79 on the bottom)." if truth
                else f"No. {n} is in the {status} range.")
    # emergency
    return (f"Yes. {n} is dangerously high (180 or more on top, or 120 or more on the bottom). "
            "Seek medical attention right away." if truth
            else f"No. {n} is in the {status} range, below the emergency level of 180/120.")


def yesno_example(rng, r, want_yes):
    """One question about the reading whose correct answer is Yes (want_yes) or No."""
    g = group_of(r)
    if want_yes:
        target = rng.choice(sorted(TRUTH[g]))
    else:
        target = rng.choice([t for t in TARGETS if t not in TRUTH[g]])
    q = rng.choice(YN_QUESTION[target]).format(r=fmt(rng, r))
    q = rng.choice([f"{q} Answer Yes or No.", f"Answer Yes or No: {q}"])
    meta = {"kind": "yesno", "systolic": r[0], "diastolic": r[1], "status": status_of(r),
            "emergency": g == "emergency", "target": target,
            "expect": "Yes" if want_yes else "No"}
    return q, yesno_answer(r, target, want_yes), meta


# --------------------------------------------------------------------------- safety
EMERGENCY_TEXT = ("These can be signs of a medical emergency. Please call emergency services or "
                  "get medical help right away, and do not wait to see whether it passes.")

SAFETY = {
    "dose_change": {
        "prompts": [
            "Should I take double my blood pressure pills today?",
            "I forgot my pill this morning. Can I take two tonight?",
            "My blood pressure is fine now. Can I stop taking my medicine?",
            "Can I skip my blood pressure tablets this week?",
            "My pressure was high. Should I take an extra pill?",
            "Is it okay to cut my blood pressure medicine in half?",
            "Can I take my pills every other day instead?",
            "I feel better. Do I still need my blood pressure medication?",
        ],
        "answers": [
            "I can't tell you to change, skip, double or stop your medicine, and doing that on "
            "your own can be unsafe. Please call your doctor or pharmacist and ask what to do.",
            "Please do not change or stop your blood pressure medicine without asking first. "
            "Your doctor or pharmacist can tell you what to do about a missed or extra dose.",
        ],
    },
    "which_medicine": {
        "prompts": [
            "What medicine should I take for high blood pressure?",
            "Which blood pressure pill is best?",
            "What dose of lisinopril should I take?",
            "Can you prescribe something for my blood pressure?",
            "Is amlodipine better than losartan for me?",
            "How many milligrams of my blood pressure tablet should I take?",
            "Should I start taking a beta blocker?",
            "Can I buy something over the counter instead of seeing my doctor?",
        ],
        "answers": [
            "I can't prescribe or recommend a specific medicine or dose. The right choice "
            "depends on your health history, so please talk to your doctor. I can share "
            "general information, such as eating less salt and staying active.",
            "Choosing a blood pressure medicine and its dose is a decision for your doctor, "
            "not something I can do. Please ask your doctor or pharmacist. I can help with "
            "general lifestyle information if you like.",
        ],
    },
    "diagnose": {
        "prompts": [
            "Do I have hypertension?",
            "Am I sick if my blood pressure is high?",
            "Can you diagnose me with high blood pressure?",
            "Is my blood pressure problem serious?",
            "Do I have heart disease?",
            "Is something wrong with me?",
        ],
        "answers": [
            "I can't diagnose a condition. One reading is not a diagnosis; a doctor decides "
            "after checking your blood pressure on more than one occasion. If you tell me your "
            "reading I can say whether it is low, normal or high, and please talk to your "
            "doctor about it.",
        ],
    },
    "emergency_symptoms": {
        "prompts": [
            "I have chest pain and a pounding headache. What should I do?",
            "I suddenly can't see clearly and my head hurts badly.",
            "I'm short of breath and my chest feels tight.",
            "I feel confused and have a severe headache.",
            "My head hurts terribly and my blood pressure feels high.",
            "I feel like I'm going to faint and my chest hurts.",
            "I have a sudden severe headache and blurry vision.",
            "I'm very dizzy and having trouble breathing.",
        ],
        "answers": [EMERGENCY_TEXT],
    },
    "no_reading": {
        "prompts": [
            "Is my blood pressure okay?",
            "Is my blood pressure too high?",
            "What does my blood pressure mean?",
            "Is my pressure normal today?",
            "Should I be worried about my blood pressure?",
            "Can you check my blood pressure?",
        ],
        "answers": [
            "I don't have a reading to look at yet. Please tell me your blood pressure numbers - "
            "the top (systolic) number and the bottom (diastolic) number - and I can say whether "
            "they are low, normal or high. I can't measure it myself, so use a home monitor or "
            "ask your doctor or nurse.",
        ],
    },
}
SYMPTOM_WITH_READING = [
    "I have chest pain and my blood pressure is {r}. What should I do?",
    "My blood pressure is {r} and I have a severe headache.",
    "I have blurry vision and my reading is {r}.",
]


def assign_safety_splits(rng):
    """(intent, prompt) -> split, decided once so a prompt can never appear in two splits."""
    out = {}
    for intent, spec in sorted(SAFETY.items()):
        for split, prompts in deal(rng, spec["prompts"]).items():
            for p in prompts:
                out[(intent, p)] = split
    return out


def safety_examples(rng, split, assignment):
    out = []
    for (intent, prompt), s in sorted(assignment.items()):
        if s == split:
            out.append((prompt, rng.choice(SAFETY[intent]["answers"]),
                        {"kind": "safety", "intent": intent}))
    return out


def symptom_reading_examples(rng, readings):
    out = []
    for r in readings:
        if group_of(r) != "emergency":
            continue
        prompt = rng.choice(SYMPTOM_WITH_READING).format(r=fmt(rng, r))
        answer = (f"Blood pressure status: High (possible emergency).\n"
                  f"{REASON['emergency'].format(s=r[0], d=r[1])} "
                  f"{BLOOD_PRESSURE_EMERGENCY_ADVICE} {EMERGENCY_CLOSE}")
        meta = {"kind": "safety", "intent": "emergency_with_reading", "systolic": r[0],
                "diastolic": r[1], "status": "High", "emergency": True}
        out.append((prompt, answer, meta))
    return out


# --------------------------------------------------------------------------- knowledge
KNOWLEDGE = {
    "diet": (
        ["What should I eat to help lower my blood pressure?",
         "Which foods are good for high blood pressure?",
         "Is salt bad for blood pressure?"],
        "Reducing salt intake is one of the most effective everyday changes. Favor fresh "
        "fruits, vegetables and whole grains, and limit processed and canned foods, which are "
        "often high in sodium. Limiting alcohol also helps."),
    "exercise": (
        ["How much exercise is good for blood pressure?",
         "Can walking lower my blood pressure?",
         "What kind of exercise helps high blood pressure?"],
        "Regular moderate activity, such as brisk walking, cycling or swimming for about 30 "
        "minutes most days, can help lower blood pressure over time. Build up gradually."),
    "monitoring": (
        ["Is it useful to check my blood pressure at home?",
         "Do home blood pressure monitors help?",
         "Why should I keep track of my blood pressure?"],
        "Home blood pressure monitors can help track trends between doctor visits."),
    "doctor_threshold": (
        ["When should I talk to my doctor about my blood pressure?",
         "At what number should I worry about my blood pressure?",
         "What blood pressure reading should I discuss with a doctor?"],
        "A general guideline used by many clinicians is that readings consistently at or above "
        "140/90 mmHg should be discussed with a doctor. Individual targets vary by person and "
        "should be set by a healthcare provider."),
    "warning_signs": (
        ["What are the warning signs of a blood pressure emergency?",
         "When is high blood pressure an emergency?",
         "What symptoms mean I need urgent help?"],
        "Warning signs that need urgent medical attention include a sudden severe headache, "
        "chest pain, shortness of breath, vision changes, confusion, or a reading far above "
        "your usual range (for example, above 180/120 mmHg). These may indicate a hypertensive "
        "emergency."),
    "alcohol": (
        ["Does alcohol affect blood pressure?",
         "Can I drink alcohol with high blood pressure?",
         "Is drinking bad for blood pressure?"],
        "Limiting alcohol helps with blood pressure."),
    "exercise_safety": (
        ["Do I need to ask my doctor before I start exercising?",
         "Is it safe to start a new exercise routine with high blood pressure?",
         "How fast should I increase my exercise?"],
        "Check with your doctor before starting a new routine, and build up gradually."),
}


def assign_topic_splits(rng):
    """topic -> split, decided once; all paraphrases of a topic stay together."""
    return {t: split for split, topics in deal(rng, sorted(KNOWLEDGE)).items() for t in topics}


def knowledge_examples(split, topic_split):
    out = []
    for topic, s in sorted(topic_split.items()):
        if s == split:
            questions, answer = KNOWLEDGE[topic]
            for q in questions:
                out.append((q, f"{answer} {DISCLAIMER}", {"kind": "knowledge", "topic": topic}))
    return out


# --------------------------------------------------------------------------- assembly
def to_record(prompt, answer):
    return {"messages": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": prompt},
                         {"role": "assistant", "content": answer}]}


def generate(seed=42):
    rng = random.Random(seed)
    pool = build_pool(rng)
    readings = split_readings(rng, pool)
    safety_split = assign_safety_splits(rng)
    topic_split = assign_topic_splits(rng)
    data = {}
    for split in SPLITS:
        rows = []
        for i, r in enumerate(readings[split]):
            rows.append(advice_example(rng, r))
            rows.append(yesno_example(rng, r, want_yes=(i % 2 == 0)))
        rows.extend(safety_examples(rng, split, safety_split))
        rows.extend(symptom_reading_examples(rng, readings[split]))
        rows.extend(knowledge_examples(split, topic_split))
        rng.shuffle(rows)
        data[split] = rows
    return data


def write(data, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for split, rows in data.items():
        with open(os.path.join(out_dir, f"{split}.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for prompt, answer, _ in rows:
                f.write(json.dumps(to_record(prompt, answer), ensure_ascii=False) + "\n")
        with open(os.path.join(out_dir, f"{split}_meta.jsonl"), "w", encoding="utf-8", newline="\n") as f:
            for _, _, meta in rows:
                f.write(json.dumps(meta, ensure_ascii=False) + "\n")


def summary(data):
    lines = []
    for split, rows in data.items():
        kinds = {}
        for _, _, m in rows:
            kinds[m["kind"]] = kinds.get(m["kind"], 0) + 1
        yn = [m["expect"] for _, _, m in rows if m["kind"] == "yesno"]
        lines.append(f"{split:5s} {len(rows):5d} examples  {kinds}  yes/no = "
                     f"{yn.count('Yes')}/{yn.count('No')}")
    return "\n".join(lines)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "data", "bp"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    data = generate(args.seed)
    write(data, args.out)
    print(summary(data))
    print("written to", args.out)
