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


import spacy
from transformers import pipeline
import json

# Load spaCy model for NER
nlp = spacy.load("en_core_web_sm")

# Function to perform NER using spaCy
def perform_ner(text):
    # Process the text with spaCy model
    doc = nlp(text)
    entities = []
    
    # Extract entities from the text
    for ent in doc.ents:
        entities.append({
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char
        })
    return entities

# Function to simulate LLM response
def simulate_llm_response(prompt):
    # Here, simulate the response from LLM
    # In real-world, you would use LLM to generate a response based on the prompt
    return f"""
    To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. The room will now be well-lit and welcoming.
    Next, I'll put on some calming music to create a relaxing atmosphere. Please give me a moment while I select a soothing playlist...
    Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. Would you prefer it warmer or cooler?
    Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea or infused water? Would that be something you'd like me to fetch for you?
    """

# Sample user prompt
user_prompt = "I just go home and I feel tired, can you prepare the living room for me?"

# Simulate getting response from LLM
llm_response = simulate_llm_response(user_prompt)

# Perform NER on LLM response
entities = perform_ner(llm_response)

# Print the extracted entities
print(json.dumps(entities, indent=4))
