import re
import json

# --- Improved Regex Patterns for Action and Object ---
patterns = [
    # For detecting smart-home actions related to devices
    (r"(turn on|switch on|activate|adjust|dim)\s+([\w\s]+)(?=\s*|$)", "smart-home"),  # Detect turn on actions for smart-home devices
    (r"(play|put on)\s+(some\s)?([\w\s]+)\s*(music|song|playlist)?", "smart-home"),  # Detect play or put on actions for music
    # For detecting task allocation (tasks human can perform)
    (r"(prepare|get|bring|fetch)\s+(a\s)?([\w\s]+)", "task-allocation")  # Detect actions like preparing or bringing items
]

# --- Clean the input text to remove unnecessary words ---
def clean_text(text):
    """ Clean the text to remove common unnecessary words (like articles). """
    text = text.lower()
    text = re.sub(r"\b(the|some|a|an|to|for|in|by)\b", "", text)  # Remove common filler words
    return text.strip()

# --- Entity Extraction Function ---
def extract_entities(text):
    """ Extract entities (action, object, category) from the input text using regex patterns. """
    entities = []
    # Clean the text before processing
    text_cleaned = clean_text(text)
    
    # Apply each regex pattern to the cleaned text
    for pattern, category in patterns:
        matches = re.finditer(pattern, text_cleaned, re.IGNORECASE)
        for match in matches:
            entity = {
                "action": match.group(1).strip() if len(match.groups()) > 0 else "",
                "object": match.group(3).strip() if len(match.groups()) > 2 else "",
                "category": category
            }
            # Ensure that action and object are not empty before adding to the list
            if entity["action"] and entity["object"]:
                # Further clean up the object (remove extra descriptions if any)
                entity["object"] = re.sub(r"\b(create|make|turn)\b.*", "", entity["object"]).strip()
                # Special case handling for "get comfortable" which doesn't fit as an object
                if "comfortable" in entity["object"]:
                    entity["object"] = "comfortable place"
                entities.append(entity)
    
    return entities

# --- Example Test Case ---
input_text = """
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting.
Next, I'll put on some calming music to create a relaxing atmosphere.
Now, let's get comfortable! I'll prepare a refreshing drink for you.
"""

# Extract entities from the input text
entities = extract_entities(input_text)

# Print the results
print("Extracted Entities:")
for entity in entities:
    print(entity)
