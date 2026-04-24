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


import json
import SmartHomeCommandExtractor from SmartHomeCommandExtractor
# Load synonym map từ JSON
with open("synonyms.json", "r", encoding="utf-8") as f:
    synonym_map = json.load(f)

# Load action list từ JSON hoặc định nghĩa sẵn
actions = list(set(synonym_map.values()))

# Khởi tạo extractor
extractor = SmartHomeCommandExtractor(actions=actions, synonym_map=synonym_map, threshold=0.3)

# Văn bản mẫu
text = """
    I'll turn on the lights in the living room.
    Then, I'll adjust the thermostat in the bedroom.
    Let's play music in the kitchen while I prepare a drink.
    Before sleeping, I'll turn off the lights.
    """

results = extractor.extract(text)

# In kết quả
print("\n✅ FINAL RESULT:")
if not results:
    print("❌ No matched smart home commands.")
else:
    for r in results:
        print(f"→ Action: {r['action']:<10} | Object: {r['object']:<12} | Room: {r['room'] or 'unknown':<12} | Sentence: {r['sentence']}")
