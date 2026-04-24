from sentence_transformers import SentenceTransformer, util

# Khởi tạo mô hình BERT để lấy embedding
model = SentenceTransformer('all-MiniLM-L6-v2')  # nhẹ và nhanh, accuracy cao

# Danh sách các lệnh smarthome
commands = [
    "Turn on light",
    "Turn on music",
    "Adjust thermostat",
    "Prepare drink"
]

# Đoạn text cần phân tích
text = '''
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. 
The room will now be well-lit and welcoming. Next, I'll put on some calming music to create a relaxing atmosphere. 
Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. 
Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea?
'''

# Tách câu (có thể dùng tokenizer tốt hơn nếu muốn độ chính xác cao hơn)
import re
sentences = re.split(r'[.?!]\s+', text.strip())

# Tính embedding cho các câu và lệnh
sentence_embeddings = model.encode(sentences, convert_to_tensor=True)
command_embeddings = model.encode(commands, convert_to_tensor=True)

# So sánh từng lệnh với từng câu
matched_commands = set()

for i, command in enumerate(commands):
    sims = util.cos_sim(command_embeddings[i], sentence_embeddings)
    max_sim = sims.max().item()
    if max_sim > 0.5:  # ngưỡng tùy chỉnh, có thể tăng/giảm
        matched_commands.add(command)

# In ra kết quả
print("Matched commands:")
for cmd in matched_commands:
    print("-", cmd)
