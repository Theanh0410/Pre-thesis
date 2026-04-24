# import re

# # --- Improved Regex Patterns for Action and Object ---
# patterns = [
#     # For detecting smart-home actions related to devices (e.g., turning on lights)
#     (r"(turn on|switch on|activate|adjust|dim)\s+([\w\s]+(?:bulbs?|lights?|thermostat|fan|TV|window|sound)*)", "smart-home"),  # Updated to handle common objects in smart-home
#     # For detecting music-related actions
#     (r"(play|put on|turn on)\s+(some\s)?([\w\s]+)\s*(music|song|playlist)?", "smart-home"),  # Detect play or put on actions for music
#     # For detecting drink-related actions
#     (r"(prepare|get|bring|make)\s+(a\s)?([\w\s]+)(?=\s*drink)", "task-allocation"),  # Detect actions related to drinks
#     # For detecting task allocation (tasks humans can perform)
#     (r"(bring|fetch|carry|take|move|get)\s+(a\s)?([\w\s]+)(?=\s*to)", "task-allocation")  # Detect task-related actions
# ]

# # --- Clean the input text to remove unnecessary words ---
# def clean_text(text):
#     """ Clean the text to remove common unnecessary words (like articles). """
#     text = text.lower()
#     text = re.sub(r"\b(the|some|a|an|to|for|in|by)\b", "", text)  # Remove common filler words
#     return text.strip()

# # --- Entity Extraction Function ---
# def extract_entities(text):
#     """ Extract entities (action, object, category) from the input text using regex patterns. """
#     entities = []
#     # Clean the text before processing
#     text_cleaned = clean_text(text)
    
#     # Apply each regex pattern to the cleaned text
#     for pattern, category in patterns:
#         matches = re.finditer(pattern, text_cleaned, re.IGNORECASE)
#         for match in matches:
#             # Ensure that the match contains the expected groups
#             if len(match.groups()) > 2:
#                 action = match.group(1).strip() if match.group(1) else ""
#                 object_ = match.group(3).strip() if match.group(3) else ""  # Adjusted to correctly get the object (group 3)
#                 if action and object_:
#                     # Further clean up the object (remove extra descriptions if any)
#                     object_ = re.sub(r"\b(create|make|turn)\b.*", "", object_).strip()
#                     entities.append({
#                         "action": action,
#                         "object": object_,
#                         "category": category
#                     })
    
#     return entities

# # --- Example Test Case ---
# input_text = """
# To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting.
# Next, I'll put on some calming music to create a relaxing atmosphere.
# Now, let's get comfortable! I'll prepare a refreshing drink for you.
# """

# # Extract entities from the input text
# entities = extract_entities(input_text)

# # Print the results
# print("Extracted Entities:")
# for entity in entities:
#     print(entity)

import re

# --- Improved Regex Patterns for Action and Object ---
patterns = [
    # For detecting smart-home actions related to devices (e.g., turning on lights)
    (r"(turn on|switch on|activate|adjust|dim)\s+([\w\s]+(?:bulbs?|lights?|thermostat|fan|TV|window|sound)*)", "smart-home"),  # Updated to handle common objects in smart-home
    # For detecting music-related actions
    (r"(play|put on|turn on)\s+(some\s)?([\w\s]+)\s*(music|song|playlist)?", "smart-home"),  # Detect play or put on actions for music
    # For detecting drink-related actions
    (r"(prepare|get|bring|make)\s+(a\s)?([\w\s]+)(?=\s*drink)", "task-allocation"),  # Detect actions related to drinks
    # For detecting task allocation (tasks humans can perform)
    (r"(bring|fetch|carry|take|move|get)\s+(a\s)?([\w\s]+)(?=\s*to)", "task-allocation")  # Detect task-related actions
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
            # Ensure that the match contains the expected groups
            if len(match.groups()) > 2:
                action = match.group(1).strip() if match.group(1) else ""
                object_ = match.group(3).strip() if match.group(3) else ""  # Adjusted to correctly get the object (group 3)
                if action and object_:
                    # Further clean up the object (remove extra descriptions if any)
                    object_ = re.sub(r"\b(create|make|turn)\b.*", "", object_).strip()
                    entities.append({
                        "action": action,
                        "object": object_,
                        "category": category
                    })
    
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
