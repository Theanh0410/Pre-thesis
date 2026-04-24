# from sentence_transformers import SentenceTransformer, util
# from nltk.tokenize import sent_tokenize
# import nltk

# nltk.download('punkt')  # Tải tokenizer

# # Load mô hình BERT paraphrase
# model = SentenceTransformer('paraphrase-MiniLM-L12-v2')

# # Danh sách các lệnh smart home
# commands = [
#     "Turn on light",
#     "Turn on music",
#     "Adjust thermostat",
#     "Prepare drink"
# ]

# # Đoạn văn bản cần xử lý
# text = '''
# To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. 
# The room will now be well-lit and welcoming. Next, I'll put on some calming music to create a relaxing atmosphere. 
# Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. 
# Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea?
# '''

# # Tách câu bằng NLTK
# sentences = sent_tokenize(text)

# # Tính embedding
# sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
# command_embeddings = model.encode(commands, convert_to_tensor=True)

# # So khớp câu với lệnh
# matched_commands = set()
# for i, command in enumerate(commands):
#     similarity = util.cos_sim(command_embeddings[i], sentence_embeddings)
#     if similarity.max().item() > 0.5:
#         matched_commands.add(command)

# # Kết quả
# print("Matched commands:")
# for cmd in matched_commands:
#     print("-", cmd)

from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize
import spacy
from smart_home import SmartHomeCommandExtractor
actions = ["Turn on", "Turn off", "Adjust", "Prepare", "Play", "Stop"]

synonym_map = {
    "Put on": "Turn on",
    "Play": "Turn on"
}

text = '''
I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting.
Next, I'll put on some calming music to create a relaxing atmosphere.
I'll adjust the thermostat to maintain a comfortable temperature.
Lastly, I'll prepare a refreshing drink - perhaps some herbal tea?
'''

extractor = SmartHomeCommandExtractor(actions=actions, synonym_map=synonym_map)
results = extractor.extract(text)

for r in results:
    print(f"→ Action: {r['action']}, Object: {r['object']}, Sentence: {r['sentence']}")
