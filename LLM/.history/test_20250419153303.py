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
from SmartHomeCommandExtractor import SmartHomeCommandExtractor
import os
import pandas as pd

# Văn bản mẫu
# text = """
#     I'll turn on the lights in the living room.
#     Then, I'll adjust the thermostat in the bedroom.
#     Let's play music in the kitchen while I prepare a drink.
#     Before sleeping, I'll turn off the lights.
#     """

text = """
    Can you open the curtains in the bedroom?
    Please make a cup of coffee in the kitchen.
    Also, turn off the lights in the living room.
    Finally, set the thermostat to a comfortable temperature in the bathroom.
    """

# Load data từ file
with open("actions.json") as f:
    actions = json.load(f)
with open("synonyms.json") as f:
    synonym_map = json.load(f)
with open("room_actions.json") as f:
    room_actions = json.load(f)
with open("object_room_map.json") as f:
    object_room_map = json.load(f)

extractor = SmartHomeCommandExtractor(
    actions=actions,
    synonym_map=synonym_map,
    room_actions=room_actions,
    object_room_map=object_room_map,
    threshold=0.3
)

# Văn bản đầu vào
# text = "Hey, turn on the lights and make some coffee."

results = extractor.extract(text)

for r in results:
    print(f"→ Action: {r['action']} | Object: {r['object']} | Room: {r['room']} | ✅ Valid: {r['valid']} | Sentence: {r['sentence']}")

# Mapping room name → RoomNumber
ROOM_ID_MAP = {
    "living room": 201,
    "kitchen": 1,
    "bedroom": 301,
    "bathroom": 401
}

# Đọc file task.csv để biết ID hiện tại
csv_path = "task.csv"
try:

    if not os.path.exists(csv_path) or os.stat(csv_path).st_size == 0:
        df_existing = pd.DataFrame()
        current_id = 1
    else:
        df_existing = pd.read_csv(csv_path)
        if "ID" not in df_existing.columns or df_existing["ID"].dropna().empty:
            current_id = 1
        else:
            current_id = int(df_existing["ID"].max()) + 1

except FileNotFoundError:
    df_existing = pd.DataFrame()
    current_id = 1

# Tạo các dòng mới
new_rows = []
for r in results:
    room_number = ROOM_ID_MAP.get(r["room"], "")
    new_row = {
        "ID": current_id,
        "user_prompt": r["sentence"].strip(),
        "RoomNumber": room_number,
        "Object": r["object"] or "",
        "Action": r["action"].lower(),
        "Status": "not done",
        "Agent_id": ""
    }
    new_rows.append(new_row)
    current_id += 1

df_new = pd.DataFrame(new_rows)

# Ghi vào file CSV
if df_existing.empty:
    df_new.to_csv(csv_path, index=False)
else:
    df_combined = pd.concat([df_existing, df_new], ignore_index=True)
    df_combined.to_csv(csv_path, index=False)

print(f"✅ Đã ghi {len(df_new)} task vào {csv_path}")
