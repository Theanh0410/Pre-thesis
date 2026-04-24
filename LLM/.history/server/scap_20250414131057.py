import os
import requests
import time
import random
import json
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from datetime import datetime
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIG ---
DATA_DIR = "rag_health_data"
CHROMA_DB_DIR = "chroma_db"
MODEL_NAME = "llama3"
JINA_API_URL = "https://r.jina.ai/"

# --- WEB SCRAPER CLASS ---
class HealthScraper:
    def __init__(self, output_dir=DATA_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.history_file = self.output_dir / "visited_urls.json"

        now = datetime.now()
        logging.basicConfig(
            filename=self.output_dir / f'scraping_{now.strftime("%Y_%m_%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

        self.sources = {
            "who_mental_health": "https://www.who.int/health-topics/mental-health",
            "mentalhealth_uk": "https://www.mentalhealth.org.uk/explore-mental-health",
            "psychology_today": "https://www.psychologytoday.com",
            "verywell_mind": "https://www.verywellmind.com/",
            "pubmed": "https://pubmed.ncbi.nlm.nih.gov",
            "mayo_clinic": "https://www.mayoclinic.org",
            "mind_charity": "https://www.mind.org.uk"
        }

        self.headers = {
            'User-Agent': 'Mozilla/5.0'
        }

        self.visited_urls = self.load_visited_urls()

    def load_visited_urls(self):
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return set(json.load(f))
        return set()

    def save_visited_urls(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.visited_urls), f, ensure_ascii=False, indent=2)

    def get_base_url(self, url):
        return urldefrag(url)[0]

    def is_same_domain(self, url1, url2):
        return urlparse(url1).netloc == urlparse(url2).netloc

    def scrape_article(self, url, source_name):
        base_url = self.get_base_url(url)
        if base_url in self.visited_urls:
            return None

        try:
            response = requests.get(JINA_API_URL + base_url, headers=self.headers)
            response.raise_for_status()
            text = response.text
            if len(text) < 300:
                return None
            self.visited_urls.add(base_url)
            logging.info(f"Scraped: {base_url}")
            return text
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return None

    def save_article(self, content, source_name, index):
        source_dir = self.output_dir / source_name
        source_dir.mkdir(exist_ok=True)
        file_path = source_dir / f"article_{index:04d}.md"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def scrape_source(self, name, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
            links = list(dict.fromkeys(links))  # remove duplicates

            count = 0
            for link in links:
                if not self.is_same_domain(link, url):
                    continue
                content = self.scrape_article(link, name)
                if content:
                    self.save_article(content, name, count)
                    count += 1
                time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            logging.error(f"Failed to scrape source {name}: {e}")

    def run(self):
        for name, url in self.sources.items():
            logging.info(f"Scraping source: {name}")
            self.scrape_source(name, url)
        self.save_visited_urls()

# --- STEP 1: Chunk Markdown files ---
def chunk_documents(data_dir):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    documents = []

    for source_dir in Path(data_dir).iterdir():
        if not source_dir.is_dir():
            continue
        for file in source_dir.glob("*.md"):
            with open(file, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            chunks = text_splitter.create_documents([raw_text])
            for chunk in chunks:
                chunk.metadata = {"source": str(file)}
                documents.append(chunk)

    return documents

# --- STEP 2: Embed documents into ChromaDB ---
def embed_documents(documents):
    embedding_function = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma.from_documents(documents, embedding_function, persist_directory=CHROMA_DB_DIR)
    vectordb.persist()
    return vectordb

# --- STEP 3: Flask API with Ollama + Retrieval ---
app = Flask(__name__)
CORS(app)

@app.route("/api/healthchat", methods=["POST"])
def health_chat():
    data = request.get_json()
    query = data.get("query")

    embedding_function = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embedding_function)

    docs = vectordb.similarity_search(query, k=4)
    context = "\n\n".join([doc.page_content for doc in docs])

    payload = {
        "model": MODEL_NAME,
        "prompt": f"You are a compassionate mental health advisor. Based on the following context, answer kindly:\n\n{context}\n\nQuestion: {query}\nAnswer:",
        "stream": False
    }

    response = requests.post("http://localhost:11434/api/generate", json=payload)
    return jsonify(response.json())

if __name__ == "__main__":
    print("🌐 Starting web scraping for mental health sources...")
    scraper = HealthScraper()
    scraper.run()

    print("⏳ Chunking documents...")
    docs = chunk_documents(DATA_DIR)
    print(f"✅ {len(docs)} chunks created.")

    print("🔗 Embedding to ChromaDB...")
    embed_documents(docs)
    print("✅ Embedding completed and saved to ChromaDB.")

    print("🚀 Starting Flask API on http://localhost:5000")
    app.run(debug=True)
