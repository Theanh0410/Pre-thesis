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
import torch
from transformers import BertForTokenClassification, BertTokenizer

# Load model and tokenizer
model_name = "dbmdz/bert-large-cased-finetuned-conll03-english"
model = BertForTokenClassification.from_pretrained(model_name)
tokenizer = BertTokenizer.from_pretrained(model_name)

# Sample text
text = "I just go home and I feel tired, can you prepare the living room for me?"

# Tokenize the input text
inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
outputs = model(**inputs)

# Get the logits (output) from the model
logits = outputs.logits

# Get predicted token class IDs
predictions = torch.argmax(logits, dim=-1)

# Convert token IDs to tokens
tokens = tokenizer.convert_ids_to_tokens(inputs["input_ids"].flatten())

# Map prediction IDs to NER labels
label_map = {
    0: 'O',  # Outside any entity
    1: 'B-PER',  # Beginning of a person's name
    2: 'I-PER',  # Inside a person's name
    3: 'B-LOC',  # Beginning of a location
    4: 'I-LOC',  # Inside a location
    5: 'B-ORG',  # Beginning of an organization
    6: 'I-ORG',  # Inside an organization
    7: 'B-MISC',  # Beginning of a miscellaneous entity
    8: 'I-MISC'   # Inside a miscellaneous entity
}

# Get the predicted labels
predicted_labels = [label_map[p.item()] for p in predictions[0]]

# Display the tokens with their corresponding predicted labels
for token, label in zip(tokens, predicted_labels):
    print(f"{token}: {label}")
