import re

# Ví dụ với regex
patterns = [
    (r"(turn on|switch on|activate)\s(\w+)", "smart-home"),  # Nhận diện hành động bật
    (r"(play|put on)\s(some\s)?(\w+)\s(music|playlist)", "smart-home"),  # Nhận diện hành động phát nhạc
    (r"(prepare|get)\s(a\s)?(?P<drink>.+?)\s(for\s)?(?P<reason>.+?)(?=\s|$)", "task-allocation")  # Nhận diện hành động chuẩn bị đồ uống
]

text = """
I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting.
Next, I'll put on some calming music to create a relaxing atmosphere.
Now, let's get comfortable! I'll prepare a refreshing drink for you.
"""

for pattern, category in patterns:
    matches = re.finditer(pattern, text, re.IGNORECASE)
    for match in matches:
        print({
            "action": match.group(1),
            "object": match.group(2),
            "category": category
        })
