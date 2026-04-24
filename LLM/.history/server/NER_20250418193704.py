import re
from typing import List, Dict
from spacy import load

# Load SpaCy model for dependency parsing
nlp = load("en_core_web_sm")

def ner_after_llm(text: str) -> List[Dict]:
    """
    Extract entities from LLM output based on home automation (device control) and task allocation actions.
    Uses rule-based (regular expressions), Phrase Matching, and Dependency Parsing approach.
    """
    entities = []

    # --- 1. Device actions (smart-home control) ---
    # Flexible regex pattern to capture actions like turning on/off lights, adjusting thermostat, etc.
    device_actions_pattern = r"(turn\s(on|off)|adjust|set|play|dim|switch\s(on|off))\s?(the\s)?(?P<object>[\w\s]+(?:\s(?:to\s[\w\s]+))?)(\s?(to\s?(?P<value>[\w\s°F°C]+))?)"

    matches = re.finditer(device_actions_pattern, text, re.IGNORECASE)
    for match in matches:
        action = match.group(1)
        obj = match.group("object").strip()
        value = match.group("value") if match.group("value") else None
        entities.append({
            "action": action,
            "object": obj,
            "value": value,
            "category": "smart-home",
            "source": "NER-after-LLM"
        })

    # --- 2. Task allocation (human tasks like fetching, moving, etc.) ---
    # Matches actions like bringing, moving, getting items
    task_allocation_pattern = r"(carry|move|bring|get|pick\sup)\s?(a\s)?(?P<object>[\w\s]+)(\s?(to\s?(?P<location>[\w\s]+))?)"

    matches = re.finditer(task_allocation_pattern, text, re.IGNORECASE)
    for match in matches:
        action = match.group(1)
        obj = match.group("object").strip()
        location = match.group("location") if match.group("location") else None
        entities.append({
            "action": action,
            "object": obj,
            "value": location,
            "category": "task-allocation",
            "source": "NER-after-LLM"
        })

    # --- 3. Dependency Parsing for better object-action relationships ---
    doc = nlp(text)
    for token in doc:
        # Action words (verbs)
        if token.dep_ == "ROOT" and token.pos_ == "VERB":
            action = token.text
            # The object is usually the direct object (dobj) in a sentence
            object_tokens = [child.text for child in token.children if child.dep_ == "dobj"]
            if object_tokens:
                obj = " ".join(object_tokens)
                # The value is often an adverbial or prep phrase like "to 72" for the thermostat
                value_tokens = [child.text for child in token.children if child.dep_ == "prep"]
                value = " ".join(value_tokens) if value_tokens else None

                # Append action, object, and value to entities
                entities.append({
                    "action": action,
                    "object": obj,
                    "value": value,
                    "category": "smart-home",
                    "source": "SpaCy-NER"
                })

    # --- 4. Filtering out non-relevant content ---
    filtered_entities = []
    for entity in entities:
        # Ignore explanations or non-actionable content
        if not any(word in entity["object"].lower() for word in ["I'll", "I can", "please", "let me"]):
            filtered_entities.append(entity)

    return filtered_entities

# Example: Test NER function on LLM output
llm_output = """
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. The room will now be well-lit and welcoming.

Next, I'll bring the water to the kitchen counter, so you can easily reach it.

Now, let's get comfortable! I'll adjust the thermostat to 72°F to maintain a comfortable temperature for you. Would you prefer it warmer or cooler?

Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea or infused water? Would that be something you'd like me to fetch for you?

How do you feel right now? Is there anything specific that's on your mind or would you like some company while we get settled in?
"""

# Call NER function on the predefined LLM response
entities = ner_after_llm(llm_output)
print("Extracted Entities:", entities)
