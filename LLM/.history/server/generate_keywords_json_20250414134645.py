import json

CATEGORY_KEYWORDS = {
    "stress": ["stress", "overwhelmed", "burnout", "pressure"],
    "anxiety": ["anxiety", "panic", "worry", "fear"],
    "depression": ["depression", "sadness", "hopeless", "low mood"],
    "self-care": ["self-care", "relaxation", "mindfulness", "meditation"],
    "sleep": ["insomnia", "sleep", "rest", "night"],
    "motivation": ["motivation", "productivity", "energy", "goal"],

    "smart-home-action": [
        "turn on light", "turn off light", "dim light", "change light color", "adjust brightness",
        "play music", "stop music", "pause music", "resume music", "volume up", "volume down",
        "play ambient sound", "white noise", "nature sounds",
        "open curtain", "close curtain", "lock door", "unlock door",
        "adjust temperature", "increase temperature", "decrease temperature",
        "turn on fan", "turn off fan", "turn on air purifier", "turn off heater",
        "remind me", "set reminder", "send alert", "daily check-in",
        "greet user", "say welcome", "ask about mood", "read journal", "read daily affirmation",
        "suggest breathing exercise", "start morning routine", "start bedtime routine",
        "control smart plug", "turn on tv", "turn off tv", "start cleaning", "brew coffee",
        "start washing machine", "adjust humidity", "trigger scene", "execute command",
        "voice command", "gesture control", "robot nod", "robot dance", "robot encourage"
    ],

    "home-health": [
        "mental health", "emotional health", "stress relief", "wellbeing", "therapy session",
        "mood tracking", "guided meditation", "home workout", "indoor exercise", "yoga",
        "healthy eating", "balanced diet", "drink water", "hydration", "take vitamins",
        "improve sleep", "sleep tracker", "air quality", "purify air", "ventilation", "humidity",
        "heart rate", "blood pressure", "check temperature", "pain level", "fatigue", "fever",
        "wash hands", "sanitize", "clean environment", "daily routine", "stay healthy"
    ]
}

with open("health_keywords.json", "w", encoding="utf-8") as f:
    json.dump(CATEGORY_KEYWORDS, f, ensure_ascii=False, indent=2)

print("✅ Created health_keywords.json")
