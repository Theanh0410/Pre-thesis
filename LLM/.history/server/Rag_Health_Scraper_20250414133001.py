# --- HEALTHCARE MENTAL HEALTH RAG SYSTEM ---

import os
import requests
import time
import random
import json
import logging
import threading
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from datetime import datetime
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document as DocxDocument
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIG ---
DATA_DIR = "rag_health_data"
HTML_BACKUP_DIR = "html_backup"
CHROMA_DB_DIR = "chroma_db"
MODEL_NAME = "llama3"
JINA_API_URL = "https://r.jina.ai/"

# --- KEYWORDS FOR AUTO TAGGING ---
CATEGORY_KEYWORDS = {
    "stress": ["stress", "overwhelmed", "burnout", "pressure"],
    "anxiety": ["anxiety", "panic", "worry", "fear"],
    "depression": ["depression", "sadness", "hopeless", "low mood"],
    "self-care": ["self-care", "relaxation", "mindfulness", "meditation"],
    "sleep": ["insomnia", "sleep", "rest", "night"],
    "motivation": ["motivation", "productivity", "energy", "goal"]
}

def auto_tag(text):
    text_lower = text.lower()
    scores = {category: 0 for category in CATEGORY_KEYWORDS}
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[category] += 1
    max_score = max(scores.values())
    if max_score == 0:
        return ["general"]
    return [cat for cat, score in scores.items() if score == max_score]

# --- SCRAPER CLASS ---
class HealthScraper:
    def __init__(self, output_dir=DATA_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.html_backup_dir = Path(HTML_BACKUP_DIR)
        self.html_backup_dir.mkdir(exist_ok=True)
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

        self.headers = {'User-Agent': 'Mozilla/5.0'}
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

    def is_valid_article_link(self, link, source_url):
        parsed = urlparse(link)
        path = parsed.path.lower()
        return (
            self.is_same_domain(link, source_url) and
            not parsed.fragment and
            not link.lower().endswith(('.pdf', '.zip', '.jpg', '.jpeg', '.png', '.docx', '.svg', '.webp')) and
            all(skip not in path for skip in ['login', 'signup', 'account', 'privacy', 'terms', 'index']) and
            any(valid in path for valid in ['article', 'advice', 'guide', 'topics', 'mental', 'health', 'support'])
        )

    def extract_file_content(self, url):
        try:
            ext = url.split('.')[-1].lower()
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()

            if ext == 'pdf':
                with open("temp.pdf", 'wb') as f:
                    f.write(r.content)
                reader = PdfReader("temp.pdf")
                return "\n".join(p.extract_text() for p in reader.pages if p.extract_text())

            elif ext in ['doc', 'docx']:
                with open("temp.docx", 'wb') as f:
                    f.write(r.content)
                doc = DocxDocument("temp.docx")
                return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

            return None
        except Exception as e:
            logging.error(f"File extraction failed: {url} – {e}")
            return None

    def scrape_article(self, url, source_name):
        base_url = self.get_base_url(url)
        if base_url in self.visited_urls:
            return None

        try:
            if any(url.lower().endswith(ext) for ext in ['.pdf', '.doc', '.docx']):
                text = self.extract_file_content(url)
                if text and len(text) > 200:
                    self.visited_urls.add(base_url)
                    return text
                return None

            r = requests.get(base_url, headers=self.headers)
            r.raise_for_status()

            soup = BeautifulSoup(r.text, 'html.parser')

            # Remove irrelevant tags
            for tag in soup.find_all(['nav', 'footer', 'aside']):
                tag.decompose()
            for a in soup.find_all('a', href=True):
                a.decompose()

            text = soup.get_text(separator='\n', strip=True)
            if len(text) < 300:
                return None

            html_path = self.html_backup_dir / f"{source_name}_{hash(base_url)}.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(r.text)

            self.visited_urls.add(base_url)
            return text

        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return None

    def save_article(self, content, source_name, index):
        source_dir = self.output_dir / source_name
        source_dir.mkdir(exist_ok=True)
        path = source_dir / f"article_{index:04d}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def scrape_and_save_thread(self, link, source_name, index):
        content = self.scrape_article(link, source_name)
        if content:
            self.save_article(content, source_name, index)

    def scrape_source(self, name, url):
        try:
            r = requests.get(url, headers=self.headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
            links = list(dict.fromkeys(links))

            filtered = [link for link in links if self.is_valid_article_link(link, url)]
            logging.info(f"{name}: {len(filtered)} valid links")

            threads = []
            for i, link in enumerate(filtered):
                t = threading.Thread(target=self.scrape_and_save_thread, args=(link, name, i))
                t.start()
                threads.append(t)
                time.sleep(0.1)
            for t in threads:
                t.join()

        except Exception as e:
            logging.error(f"Failed to scrape source {name}: {e}")

    def run(self):
        for name, url in self.sources.items():
            logging.info(f"Start source: {name}")
            self.scrape_source(name, url)
        self.save_visited_urls()

# --- CHUNK + EMBED ---
def chunk_documents(data_dir):
    splitter = CharacterTextSplitter.from_tiktoken_encoder(separator="\n\n", chunk_size=512, chunk_overlap=50)
    documents = []

    for folder in Path(data_dir).iterdir():
        if not folder.is_dir():
            continue
        for file in folder.glob("*.md"):
            with open(file, 'r', encoding='utf-8') as f:
                text = f.read()
            chunks = splitter.create_documents([text])
            for chunk in chunks:
                tags = auto_tag(chunk.page_content)
                chunk.metadata = {"source": str(file), "tags": tags}
                documents.append(chunk)
    return documents

def embed_documents(docs):
    embedding = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma.from_documents(docs, embedding, persist_directory=CHROMA_DB_DIR)
    vectordb.persist()
    return vectordb

# --- FLASK APP ---
app = Flask(__name__)
CORS(app)

@app.route("/api/healthchat", methods=["POST"])
def health_chat():
    data = request.get_json()
    query = data.get("query")
    embedding = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embedding)
    docs = vectordb.similarity_search(query, k=4)

    context = "\n\n".join([doc.page_content for doc in docs])
    payload = {
        "model": MODEL_NAME,
        "prompt": f"You are a compassionate mental health advisor. Based on the following context, answer kindly:\n\n{context}\n\nQuestion: {query}\nAnswer:",
        "stream": False
    }
    r = requests.post("http://localhost:11434/api/generate", json=payload)
    return jsonify(r.json())

@app.route("/dashboard")
def dashboard():
    articles = []
    for folder in Path(DATA_DIR).iterdir():
        for file in folder.glob("*.md"):
            content = file.read_text(encoding='utf-8')
            articles.append({"filename": file.name, "path": str(file), "content": content[:500]})
    return jsonify(articles)

# --- MAIN ---
if __name__ == "__main__":
    print("Crawling mental health sources...")
    scraper = HealthScraper()
    scraper.run()

    print("✂Chunking documents...")
    docs = chunk_documents(DATA_DIR)
    print(f"✅ {len(docs)} chunks created.")

    print("Embedding into ChromaDB...")
    embed_documents(docs)
    print("✅ Embedding complete.")

    print("Launching API server...")
    app.run(debug=True)
