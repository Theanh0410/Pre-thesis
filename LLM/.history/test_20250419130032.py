from sentence_transformers import SentenceTransformer, util
import re

# Load mô hình paraphrase mạnh mẽ hơn
model = SentenceTransformer('paraphrase-MiniLM-L12-v2')

# Danh sách các lệnh smarthome
commands = [
    "Turn on light",
    "Turn on music",
    "Adjust thermostat",
    "Prepare drink"
]

# Đoạn văn bản người dùng
text = '''
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. 
The room will now be well-lit and welcoming. Next, I'll put on some calming music to create a relaxing atmosphere. 
Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. 
Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea?
'''

# Cắt đoạn text thành từng câu
sentences = re.split(r'[.?!]\s+', text.strip())

# Encode
sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
command_embeddings = model.encode(commands, convert_to_tensor=True)

# So sánh
matched_commands = set()

for i, command in enumerate(commands):
    similarities = util.cos_sim(command_embeddings[i], sentence_embeddings)
    max_sim = similarities.max().item()
    if max_sim > 0.5:  # Ngưỡng tương đồng ngữ nghĩa
        matched_commands.add(command)

# Kết quả
print("Matched commands:")
for cmd in matched_commands:
    print("-", cmd)
