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


# BERT model
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize
import nltk

nltk.download('punkt')

model = SentenceTransformer("paraphrase-MiniLM-L12-v2")

# Các hành động định nghĩa sẵn
actions = [
    "Turn on", "Turn off", "Adjust", "Prepare", "Play", "Stop"
]

# Văn bản
text = '''
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting.
Next, I'll put on some calming music to create a relaxing atmosphere.
I'll adjust the thermostat to maintain a comfortable temperature.
Lastly, I'll prepare a refreshing drink - perhaps some herbal tea?
'''

# Tách từng câu
sentences = sent_tokenize(text)
sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
action_embeddings = model.encode(actions, convert_to_tensor=True)

# So sánh từng câu với từng hành động
results = []

for i, sent_emb in enumerate(sentence_embeddings):
    best_action = None
    best_score = 0
    for j, action_emb in enumerate(action_embeddings):
        score = util.cos_sim(sent_emb, action_emb).item()
        if score > best_score:
            best_score = score
            best_action = actions[j]
    if best_score > 0.5:  # ngưỡng
        results.append({"sentence": sentences[i], "action": best_action, "score": best_score})


import spacy
nlp = spacy.load("en_core_web_sm")

for item in results:
    doc = nlp(item["sentence"])
    objects = []
    for token in doc:
        if token.dep_ in ("dobj", "pobj", "attr", "dative") and token.pos_ == "NOUN":
            objects.append(token.text)
    item["object"] = ", ".join(objects)

# In kết quả
for r in results:
    print(f"- Action: {r['action']}, Object: {r.get('object')}, Sentence: {r['sentence']}")
