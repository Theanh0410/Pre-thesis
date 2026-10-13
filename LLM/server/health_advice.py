# Deterministic blood-pressure classification. Kept as plain code rather
# than left to the LLM to infer, since asking the model to compare numbers
# against a threshold it read in a document is unreliable and unverifiable -
# this way the status is computed the same way every time and can be tested
# directly. Thresholds are a simplified 3-tier reading of the standard AHA
# categories (Normal / Elevated+Stage 1+2 collapsed to "High" / Hypotension).
BLOOD_PRESSURE_ADVICE = {
    "Low": (
        "Your reading is on the low side. Sit or lie down if you feel dizzy "
        "or lightheaded, stay hydrated, and stand up slowly from sitting or "
        "lying down. If you feel faint, have chest pain, or this is a big "
        "change from your usual reading, contact your doctor."
    ),
    "Normal": (
        "Your reading is within a normal range. Keep up healthy habits: a "
        "balanced low-salt diet, regular light exercise, and routine "
        "monitoring."
    ),
    "High": (
        "Your reading is elevated. Reduce salt intake, avoid caffeine and "
        "alcohol for now, try to relax, and recheck it after resting. If "
        "readings stay high across multiple checks, contact your doctor."
    ),
}

BLOOD_PRESSURE_EMERGENCY_ADVICE = (
    "This reading is dangerously high and may be a hypertensive emergency. "
    "Please seek medical attention right away or call emergency services, "
    "especially if you also have a severe headache, chest pain, shortness "
    "of breath, or vision changes."
)


def classify_blood_pressure(systolic, diastolic):
    """Returns {"status": "Low"|"Normal"|"High", "is_emergency": bool}, or
    None if either reading is missing."""
    if systolic is None or diastolic is None:
        return None

    is_emergency = systolic >= 180 or diastolic >= 120

    if systolic < 90 or diastolic < 60:
        status = "Low"
    elif systolic >= 130 or diastolic >= 80:
        status = "High"
    else:
        status = "Normal"

    return {"status": status, "is_emergency": is_emergency}
