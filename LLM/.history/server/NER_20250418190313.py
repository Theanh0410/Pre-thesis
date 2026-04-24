# from transformers import pipeline

# # Đoạn code này sử dụng pipeline của HuggingFace để thực hiện NER
# ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

# # Sau khi LLM trả về phản hồi
# assistant_response = """
# To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. The room will now be well-lit and welcoming.
# Next, I'll put on some calming music to create a relaxing atmosphere. Please give me a moment while I select a soothing playlist...
# Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. Would you prefer it warmer or cooler?
# Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea or infused water? Would that be something you'd like me to fetch for you?
# """

# # Sử dụng NER để trích xuất các thông tin
# entities = ner_pipeline(assistant_response)

# # Xử lý các entity để lấy ra Action, Location, và Category
# actions = []
# for entity in entities:
#     if entity['label'] == 'B-Action':
#         actions.append(entity['word'])

# locations = []
# for entity in entities:
#     if entity['label'] == 'B-Location':
#         locations.append(entity['word'])

# # Trích xuất Category (ví dụ, hành động liên quan đến âm nhạc là "Calm music")
# categories = []
# for entity in entities:
#     if entity['label'] == 'B-Category':
#         categories.append(entity['word'])

# print(f"Actions: {actions}")
# print(f"Locations: {locations}")
# print(f"Categories: {categories}")


import re
from typing import List, Dict

def ner_after_llm(text: str) -> List[Dict]:
    """
    Trích xuất thực thể từ output LLM (phức tạp, có health context).
    Sử dụng chỉ rule-based (regular expressions).
    """
    entities = []

    # Correct the pattern to match actions and objects correctly

    # Rule for detecting drink actions (e.g., prepare, get, make)
    drink_pattern = r"(prepare|get|make)\s?(a\s)?(?P<drink>.+?)\s(for\s)?(?P<reason>.+?)(?=\s|$)"
    
    # Rule for detecting music actions (e.g., play, put on)
    music_pattern = r"(play|put on)\s?(some\s)?(?P<music>.+?)\s(music|song|playlist)"
    
    # Rule for detecting thermostat/temperature adjustments
    temperature_pattern = r"(adjust|set)\s?(the\s)?(temperature|thermostat)\s?(to\s)?(?P<value>\d+°?[CF])"
    
    # Match drink actions
    for pattern, category in [(drink_pattern, "drink"), (music_pattern, "music"), (temperature_pattern, "temperature")]:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            action = match.group(1)
            if category == "drink":
                entities.append({
                    "action": action,
                    "object": match.group("drink"),
                    "purpose": match.group("reason") if "reason" in match.groupdict() else None,
                    "category": category,
                    "source": "NER-after-LLM"
                })
            elif category == "music":
                entities.append({
                    "action": action,
                    "object": match.group("music"),
                    "category": category,
                    "source": "NER-after-LLM"
                })
            elif category == "temperature":
                entities.append({
                    "action": action,
                    "object": "thermostat",
                    "value": match.group("value"),
                    "category": category,
                    "source": "NER-after-LLM"
                })

    return entities


# Test NER after LLM
llm_output = """
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. The room will now be well-lit and welcoming.

Next, I'll put on some calming music to create a relaxing atmosphere. Please give me a moment while I select a soothing playlist... (Playing calming background music)

Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. Would you prefer it warmer or cooler?

Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea or infused water? Would that be something you'd like me to fetch for you?

How do you feel right now? Is there anything specific that's on your mind or would you like some company while we get settled in?
"""

# Call NER function on the predefined LLM response
entities = ner_after_llm(llm_output)
print("Extracted Entities:", entities)
