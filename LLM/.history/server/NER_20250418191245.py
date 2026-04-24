import re
from typing import List, Dict

def ner_after_llm(text: str) -> List[Dict]:
    """
    Extract entities from LLM output based on home automation (device control) and task allocation actions.
    Uses rule-based (regular expressions) approach.
    """
    entities = []

    # Device actions (smart-home control)
    # Detect actions like "turn on", "adjust", "play", "dim", etc.
    device_actions_pattern = r"(turn\s(on|off)|adjust|set|play|dim|switch\s(on|off))\s?(the\s)?(?P<object>[\w\s]+)(\s?(to\s?(?P<value>[\w\s]+))?)"
    
    # Task allocation (human tasks like fetching, moving, etc.)
    task_allocation_pattern = r"(carry|move|bring|get|pick\sup)\s?(a\s)?(?P<object>[\w\s]+)(\s?(to\s?(?P<location>[\w\s]+))?)"

    # Match device control actions
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

    # Match task allocation actions
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

    return entities

# Test NER after LLM
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
