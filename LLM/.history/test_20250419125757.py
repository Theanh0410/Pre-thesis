def extract_smart_home_commands(text, commands):
    text_lower = text.lower()  # Chuyển text về chữ thường để so sánh không phân biệt hoa thường
    matched_commands = []
    
    for cmd in commands:
        # Kiểm tra từng lệnh có xuất hiện trong text không
        if cmd in text_lower:
            matched_commands.append(cmd.capitalize())  # Viết hoa chữ cái đầu cho đẹp
    
    return matched_commands

smart_home_commands = [
    "turn on light",       # Bật đèn
    "turn on music",       # Bật nhạc
    "adjust thermostat",   # Điều chỉnh nhiệt
    "prepare drink"        # Chuẩn bị đồ uống
]

text = '''To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. 
    The room will now be well-lit and welcoming. Next, I'll put on some calming music to create a relaxing atmosphere. 
    Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. 
    Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea? '''

matched_commands = extract_smart_home_commands(text, smart_home_commands)
print("Các lệnh trùng khớp:")
for cmd in matched_commands:
    print(f"- {cmd}")



