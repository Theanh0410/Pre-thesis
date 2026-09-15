"""
Test script to demonstrate contextual command processing.
Run this to test if "I'm hot" properly triggers "turn on fan in living room"
"""

from ContextualCommandProcessor import ContextualCommandProcessor
import json

# Load config
with open("smarthome/actions.json") as f:
    actions = json.load(f)
with open("smarthome/synonyms.json") as f:
    synonym_map = json.load(f)
with open("smarthome/room_actions.json") as f:
    room_actions = json.load(f)
with open("smarthome/object_room_map.json") as f:
    object_room_map = json.load(f)

# Initialize processor
processor = ContextualCommandProcessor(
    room_actions=room_actions,
    object_room_map=object_room_map
)

# Test cases - various phrasings for comfort states
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
    "I'm sleepy",
    "I'm tired",
    "I'm uncomfortable",
    
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
            print(f"      → Action: {cmd['action']}")
            print(f"      → Device: {cmd['object']}")
            print(f"      → Room: {cmd['room']}")
            print(f"      → Confidence: {cmd['score']}")
            print(f"      → Valid: {cmd['valid']}")
            print(f"      → Detected by: {cmd.get('matched_by', 'pattern')}")
    else:
        print(f"   ❌ No contextual commands detected")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
