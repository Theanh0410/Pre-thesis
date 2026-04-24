
import os
from pathlib import Path
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings

MODEL_NAME = "llama3"
EMBED_DIR = {
    "emotional": "chroma_emotional",
    "smarthome": "chroma_smarthome",
    "healthcare": "chroma_healthcare"
}

def auto_tag(category):
    return {
        "emotional": "intent: emotional",
        "smarthome": "intent: smart_action",
        "healthcare": "intent: health_advice"
    }[category]

def embed_documents(category):
    splitter = CharacterTextSplitter.from_tiktoken_encoder(
        separator="\n\n", chunk_size=512, chunk_overlap=50
    )
    docs = []
    folder = Path("data") / category
    for file in folder.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        chunks = splitter.create_documents([content])
        for c in chunks:
            c.metadata = {
                "source": str(file),
                "intent": auto_tag(category)
            }
            docs.append(c)
    emb_fn = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma.from_documents(docs, emb_fn, persist_directory=EMBED_DIR[category])
    vectordb.persist()
    print(f"✅ Embedded {len(docs)} chunks into {EMBED_DIR[category]}")

if __name__ == "__main__":
    for category in ["emotional", "smarthome", "healthcare"]:
        embed_documents(category)
