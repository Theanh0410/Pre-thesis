import stanza

# Tải mô hình tiếng Anh
nlp = stanza.Pipeline('en')

# Đoạn văn mẫu
text = """
To start, I'll turn on the lights in the living room by adjusting the smart bulbs to their brightest setting. The room will now be well-lit and welcoming.
Next, I'll put on some calming music to create a relaxing atmosphere. Please give me a moment while I select a soothing playlist... (Playing calming background music)
Now, let's get comfortable! I'll adjust the thermostat to maintain a comfortable temperature for you. Would you prefer it warmer or cooler?
Lastly, I'll prepare a refreshing drink for you - perhaps some herbal tea or infused water? Would that be something you'd like me to fetch for you?
"""

# Xử lý văn bản
doc = nlp(text)

# Kiểm tra nếu mô hình nhận diện thực thể
for ent in doc.ents:
    print(f"Entity: {ent.text}, Type: {ent.type}")
