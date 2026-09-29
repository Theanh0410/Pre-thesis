"""
Manual smoke-test script for ContextualCommandProcessor's real semantic
matching (uses the actual sentence-transformers model, not a fake embed_fn -
see test_contextual_command_processor.py for the fast automated unit tests).

Requires the project's ML dependencies (sentence-transformers etc.), so run
this inside the `llm` conda env, not the sandbox: `python test_contextual.py`
"""

import json

from sentence_transformers import SentenceTransformer

from ContextualCommandProcessor import ContextualCommandProcessor

# Load config
with open("smarthome/intents.json") as f:
    intents = json.load(f)
with open("smarthome/room_actions.json") as f:
    room_actions = json.load(f)
with open("smarthome/object_room_map.json") as f:
    object_room_map = json.load(f)

model = SentenceTransformer("paraphrase-MiniLM-L12-v2")
embed_fn = lambda texts: model.encode(texts, convert_to_tensor=False).tolist()

# Initialize processor
processor = ContextualCommandProcessor(
    intents=intents,
    embed_fn=embed_fn,
    room_actions=room_actions,
    object_room_map=object_room_map
)

# Test cases - various phrasings for comfort/sleep states
test_inputs = [
    # "I'm hot" variations
    "I'm hot",
    "I am hot",
    "I'm feeling hot",
    "I feel hot",
    "I'm feeling too hot",
    "I'm too hot",
    "It's hot",
    "It is hot",

    # "I'm cold" variations
    "I'm cold",
    "I am cold",
    "I'm feeling cold",
    "I feel cold",
    "I'm feeling too cold",
    "It's cold",
    "I'm freezing",

    # VOICE MISHEARING TEST CASES
    # Vosk commonly mishears "cold" as:
    "I'm feeling coat",  # Mishearing of "cold"
    "I'm feeling code",  # Mishearing of "cold"
    "I'm feeling colon",  # Mishearing of "cold"
    "I'm feeling coal",  # Mishearing of "cold"
    "I'm feeling colt",  # Mishearing of "cold"
    "I'm feeling gold",  # Mishearing of "cold"
    "I'm feeling hole",  # Mishearing of "cold"
    "I'm feeling halls",  # Mishearing of "cold"

    # Other comfort states
    "I'm comfortable",
    "It's dark",
    "I'm uncomfortable",

    # "Going to bed" - the new natural-command intent, deliberately phrased
    # differently from the configured examples to check generalization.
    "I want to go to bed",
    "I'm going to sleep now",
    "I think I'll turn in for the night",
    "Let's hit the sack",
    "Goodnight, heading to bed",

    # "Waking up"
    "I just woke up",
    "Good morning, I'm up",

    # Edge cases - non-contextual
    "Turn on the light in the kitchen",
    "What's the weather like?",
]

print("=" * 60)
print("CONTEXTUAL COMMAND PROCESSOR TEST")
print("=" * 60)

for test_input in test_inputs:
    print(f"\n📝 Input: '{test_input}'")

    # Check if contextual
    is_contextual = processor.is_contextual_statement(test_input)
    print(f"   Is Contextual: {is_contextual}")

    # Process contextual command
    commands = processor.process_contextual_command(test_input)

    if commands:
        print(f"   ✅ Generated {len(commands)} command(s):")
        for cmd in commands:
            print(f"      → Intent: {cmd.get('intent')}")
            print(f"      → Action: {cmd['action']}")
            print(f"      → Device: {cmd['object']}")
            print(f"      → Room: {cmd['room']}")
            print(f"      → Confidence: {cmd['score']:.3f}")
            print(f"      → Valid: {cmd['valid']}")
    else:
        print(f"   ❌ No contextual commands detected")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
