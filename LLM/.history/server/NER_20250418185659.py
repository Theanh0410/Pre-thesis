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


from transformers import pipeline

# Load the NER model from Hugging Face
ner_model = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

def perform_ner(text):
    # Get entities from text
    entities = ner_model(text)
    return entities

text = "I just go home and I feel tired, can you prepare the living room for me?"
entities = perform_ner(text)

print(entities)
