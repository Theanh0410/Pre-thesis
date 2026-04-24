def clean_text(text):
    # Loại bỏ các từ không cần thiết hoặc không có ý nghĩa trong ngữ cảnh trích xuất
    text = text.lower()
    text = re.sub(r"\b(the|some|a|an)\b", "", text)  # Loại bỏ các từ chung chung
    return text

text_cleaned = clean_text(text)
print(text_cleaned)  # Kiểm tra văn bản đã được làm sạch

# Sử dụng regex trên văn bản đã được làm sạch
for pattern, category in patterns:
    matches = re.finditer(pattern, text_cleaned, re.IGNORECASE)
    for match in matches:
        print({
            "action": match.group(1),
            "object": match.group(2),
            "category": category
        })
