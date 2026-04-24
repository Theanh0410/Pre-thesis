import re
import json

# --- Cải thiện Regex Patterns cho Hành Động và Đối Tượng ---
patterns = [
    # Nhận diện hành động bật các thiết bị smarthome
    (r"(turn on|switch on|activate)\s+([\w\s]+)", "smart-home"),  # Nhận diện hành động bật đèn
    (r"(play|put on)\s+(some\s)?([\w\s]+)\s*(music|song|playlist)?", "smart-home"),  # Nhận diện hành động phát nhạc
    # Nhận diện hành động chuẩn bị đồ uống
    (r"(prepare|get)\s+(a\s)?([\w\s]+)", "task-allocation")  # Nhận diện hành động chuẩn bị đồ uống
]

# --- Hàm làm sạch văn bản ---
def clean_text(text):
    """ Làm sạch văn bản bằng cách loại bỏ từ ngữ không cần thiết (như "the", "some",...) """
    text = text.lower()
    text = re.sub(r"\b(the|some|a|an)\b", "", text)  # Loại bỏ các từ chung chung
    return text

# --- Trích xuất thực thể ---
def extract_entities(text):
    """ Trích xuất hành động, đối tượng và giá trị từ văn bản nhập vào sử dụng regex """
    entities = []
    # Làm sạch văn bản trước khi xử lý
    text_cleaned = clean_text(text)
    
    # Duyệt qua các pattern regex
    for pattern, category in patterns:
        matches = re.finditer(pattern, text_cleaned, re.IGNORECASE)
        for match in matches:
            entities.append({
                "action": match.group(1),  # Nhận diện hành động
                "object": match.group(3).strip(),  # Nhận diện đối tượng, loại bỏ khoảng trắng thừa
                "category": category
            })
    
    return entities

# --- Trích xuất thông tin liên quan đến thiết bị smarthome ---
def extract_smart_home_entities(text):
    """ Trích xuất các hành động, thiết bị liên quan đến smarthome từ văn bản """
    entities = []
    smart_home_patterns = [
        r"(turn on|switch on|activate)\s+([\w\s]+)",  # Bật thiết bị
        r"(play|put on)\s+(some\s)?([\w\s]+)\s*(music|song|playlist)?"  # Phát nhạc
    ]
    
    # Áp dụng mỗi pattern một lần
    for pattern in smart_home_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append({
                "action": match.group(1),
                "object": match.group(2).strip(),
                "category": "smart-home"
            })
    
    return entities

# --- Trích xuất thông tin liên quan đến hành động con người ---
def extract_task_allocation_entities(text):
    """ Trích xuất hành động của con người trong ngữ cảnh smarthome (task allocation) """
    task_patterns = [
        r"(bring|move|fetch|get)\s+(a\s)?([\w\s]+)",  # Mang đồ
        r"(set)\s+(a\s)?([\w\s]+)"  # Cài đặt các thiết bị
    ]
    
    entities = []
    
    # Áp dụng mỗi pattern một lần
    for pattern in task_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            entities.append({
                "action": match.group(1),
                "object": match.group(3).strip(),
                "category": "task-allocation"
            })
    
    return entities

# --- Hợp nhất các hàm nhận diện thực thể ---
def extract_all_entities(text):
    """ Kết hợp các hàm trích xuất cho smart-home và task-allocation vào một hàm duy nhất """
    smart_home_entities = extract_smart_home_entities(text)
    task_allocation_entities = extract_task_allocation_entities(text)
    
    # Gộp tất cả các entities lại
    all_entities = smart_home_entities + task_allocation_entities
    return all_entities

# --- Ví dụ kiểm tra ---
input_text = """
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting.
Next, I'll put on some calming music to create a relaxing atmosphere.
Now, let's get comfortable! I'll prepare a refreshing drink for you.
"""

# Trích xuất thực thể
entities = extract_all_entities(input_text)

# In kết quả
print("Extracted Entities:")
for entity in entities:
    print(entity)
