import stanza
from typing import List, Dict

# Initialize NLP pipeline
stanza.download('en')  # Only need to run once
nlp = stanza.Pipeline('en', processors='tokenize,pos,lemma,ner,depparse')

# Knowledge Bases
SMART_HOME_DEVICES = {
    'light', 'bulb', 'thermostat', 'music', 'player', 'speaker',
    'curtain', 'door', 'fan', 'purifier', 'heater', 'tv', 'plug',
    'machine', 'lamp', 'appliance', 'device'
}

ACTION_MAPPING = {
    'turn': 'turn on',
    'put': 'play',
    'adjust': 'set',
    'change': 'adjust',
    'prepare': 'get',
    'fetch': 'bring'
}

HEALTH_TIPS = {
    'light': "Consider using warm light in evenings to reduce eye strain",
    'music': "Listening to nature sounds can lower stress hormones by 30%",
    'thermostat': "Maintain 20-22°C for optimal cognitive performance",
    'drink': "Herbal tea improves digestion and relaxation",
    'temperature': "Sudden temperature changes may affect blood pressure"
}

EMOTION_KEYWORDS = {
    'calming': 'relaxed',
    'comfortable': 'content',
    'refreshing': 'energized',
    'welcoming': 'happy'
}

def extract_actions(text: str) -> List[Dict]:
    """Extract structured actions from text with health suggestions"""
    doc = nlp(text)
    actions = []
    detected_emotions = set()

    # First pass: Detect emotions
    for sent in doc.sentences:
        for word in sent.words:
            if word.text.lower() in EMOTION_KEYWORDS:
                detected_emotions.add(EMOTION_KEYWORDS[word.text.lower()])

    # Second pass: Extract actions
    for sent in doc.sentences:
        for word in sent.words:
            if word.upos == "VERB":
                # Extract object and negation
                obj_words = [
                    w.text for w in sent.words 
                    if w.head == word.id and 
                    w.deprel in ("obj", "obl", "nmod", "compound")
                ]
                negation = any(
                    w.deprel == "neg" and w.head == word.id 
                    for w in sent.words
                )

                # Build action dictionary
                action = {
                    "base_action": word.lemma,
                    "normalized_action": ACTION_MAPPING.get(word.lemma, word.lemma),
                    "object": " ".join(obj_words),
                    "is_negative": negation,
                    "category": "smart-home" if any(
                        device in " ".join(obj_words).lower() or 
                        device in word.text.lower()
                        for device in SMART_HOME_DEVICES
                    ) else "task-allocation",
                    "health_tip": "",
                    "emotion_context": list(detected_emotions)
                }

                # Add health tip if available
                first_obj = action["object"].split()[0].lower() if action["object"] else ""
                action["health_tip"] = HEALTH_TIPS.get(first_obj, "")

                # Only keep meaningful actions
                if action["object"] or action["category"] == "smart-home":
                    if negation:
                        action["normalized_action"] = "not " + action["normalized_action"]
                    actions.append(action)

    return actions

def generate_health_report(actions: List[Dict]) -> str:
    """Generate summary health suggestions"""
    tips = set()
    emotion_stats = {}
    
    for action in actions:
        if action["health_tip"]:
            tips.add(action["health_tip"])
        for emotion in action["emotion_context"]:
            emotion_stats[emotion] = emotion_stats.get(emotion, 0) + 1
    
    # Build report
    report = []
    if tips:
        report.append("💡 Health Suggestions:")
        report.extend(f"- {tip}" for tip in tips)
    
    if emotion_stats:
        primary_emotion = max(emotion_stats.items(), key=lambda x: x[1])[0]
        report.append(f"\n😊 Emotional Context: You seem {primary_emotion}")
        if primary_emotion == 'stressed':
            report.append("Try deep breathing: Inhale 4s → Hold 4s → Exhale 6s")
    
    return "\n".join(report) if report else "No health suggestions available"

# Example Usage
if __name__ == "__main__":
    sample_text = """
    To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. 
    The room will now be well-lit and welcoming. Next, I'll put on some calming music to create a relaxing atmosphere. 
    Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. 
    Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea?
    """

    print("=== Extracted Actions ===")
    actions = extract_actions(sample_text)
    for idx, action in enumerate(actions, 1):
        print(f"{idx}. {action['normalized_action']} {action['object']} "
              f"({action['category']}) {'[NEG]' if action['is_negative'] else ''}")
        if action['health_tip']:
            print(f"   → Health Tip: {action['health_tip']}")

    print("\n=== Health Report ===")
    print(generate_health_report(actions))