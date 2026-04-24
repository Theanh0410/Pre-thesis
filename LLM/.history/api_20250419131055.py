from fastapi import FastAPI, Request
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
import re

# Load model
model = SentenceTransformer('paraphrase-MiniLM-L12-v2')

# Danh sách các command smart home cơ bản
COMMANDS = [
    "Turn on light",
    "Turn on music",
    "Adjust thermostat",
    "Prepare drink"
]

# Encode trước command cho nhanh
command_embeddings = model.encode(COMMANDS, convert_to_tensor=True)

# FastAPI khởi tạo
app = FastAPI()

# Schema nhận input từ người dùng
class TextRequest(BaseModel):
    text: str

# Hàm xử lý chính
def match_commands_from_text(text: str, threshold=0.5):
    sentences = re.split(r'[.?!]\s+', text.strip())
    sentence_embeddings = model.encode(sentences, convert_to_tensor=True)

    matched_commands = set()
    for i, command in enumerate(COMMANDS):
        sims = util.cos_sim(command_embeddings[i], sentence_embeddings)
        if sims.max().item() >= threshold:
            matched_commands.add(command)
    return list(matched_commands)

# Route API
@app.post("/match-commands")
async def detect_smart_home_commands(req: TextRequest):
    matched = match_commands_from_text(req.text)
    return {"matched_commands": matched}
