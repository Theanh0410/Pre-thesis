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
from langchain_ollama import OllamaEmbeddings
from flask import Flask, request, jsonify
from flask_cors import CORS

# --- CONFIG ---
DATA_DIR = "rag_health_data"
HTML_BACKUP_DIR = "html_backup"
CHROMA_DB_DIR = "chroma_db"
MODEL_NAME = "llama3.2"
JINA_API_URL = "https://r.jina.ai/"

# Load CATEGORY_KEYWORDS externally

def load_category_keywords(file_path="./health_keywords.json"):
    path = Path(file_path)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"{file_path} does not exist.")

# Load crawler config
def load_crawler_config(path="crawler_config.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def auto_tag(text, category_keywords):
    text_lower = text.lower()
    scores = {cat: sum(kw in text_lower for kw in kws) for cat, kws in category_keywords.items()}
    max_score = max(scores.values())
    return [k for k, v in scores.items() if v == max_score] if max_score > 0 else ["general"]

class HealthScraper:
    def __init__(self):
        self.output_dir = Path(DATA_DIR)
        self.output_dir.mkdir(exist_ok=True)
        self.html_backup_dir = Path(HTML_BACKUP_DIR)
        self.html_backup_dir.mkdir(exist_ok=True)
        self.history_file = self.output_dir / "visited_urls.json"
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.visited_urls = self.load_visited_urls()
        self.config = load_crawler_config()

        self.sources = {
            "who_mental_health": "https://www.who.int/health-topics/mental-health",
            "mentalhealth_uk": "https://www.mentalhealth.org.uk/explore-mental-health",
            "psychology_today": "https://www.psychologytoday.com",
            "verywell_mind": "https://www.verywellmind.com/",
            "pubmed": "https://pubmed.ncbi.nlm.nih.gov",
            "mayo_clinic": "https://www.mayoclinic.org",
            "mind_charity": "https://www.mind.org.uk"
        }

        logging.basicConfig(filename=self.output_dir / f"log_{datetime.now().date()}.log",
                            level=logging.INFO, format="%(asctime)s - %(message)s")

    def load_visited_urls(self):
        if self.history_file.exists():
            return set(json.load(open(self.history_file, 'r', encoding='utf-8')))
        return set()

    def save_visited_urls(self):
        json.dump(list(self.visited_urls), open(self.history_file, 'w', encoding='utf-8'), indent=2)

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
            all(skip not in path for skip in self.config["skip_keywords"]) and
            any(valid in path for valid in self.config["valid_path_keywords"])
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
        except Exception as e:
            logging.error(f"Error parsing file: {url} — {e}")
        return None

    def scrape_article(self, url, source_name, depth=0):
        base_url = self.get_base_url(url)
        if base_url in self.visited_urls:
            return None

        try:
            if any(url.lower().endswith(ext) for ext in self.config["skip_extensions"]):
                text = self.extract_file_content(url)
                if text and len(text) > 200:
                    self.visited_urls.add(base_url)
                    return text
                return None

            r = requests.get(base_url, headers=self.headers)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')

            for tag in soup.find_all(['nav', 'footer', 'aside']):
                tag.decompose()
            for a in soup.find_all('a', href=True):
                a.decompose()

            text = soup.get_text(separator='\n', strip=True)
            if len(text) < 300:
                return None

            with open(self.html_backup_dir / f"{source_name}_{hash(base_url)}.html", "w", encoding="utf-8") as f:
                f.write(r.text)

            self.visited_urls.add(base_url)

            # Crawl deeper if depth allows
            if depth < self.config["max_depth"]:
                inner_links = [urljoin(base_url, a['href']) for a in soup.find_all('a', href=True)]
                filtered = [l for l in inner_links if self.is_valid_article_link(l, base_url)]
                for idx, link in enumerate(filtered):
                    if self.get_base_url(link) not in self.visited_urls:
                        content = self.scrape_article(link, source_name, depth + 1)
                        if content:
                            self.save_article(content, source_name, hash(link) % 100000)

            return text
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return None

    def save_article(self, content, source_name, index):
        folder = self.output_dir / source_name
        folder.mkdir(exist_ok=True)
        with open(folder / f"article_{index:04d}.md", "w", encoding="utf-8") as f:
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
            links = list({urljoin(url, a['href']) for a in soup.find_all('a', href=True)})
            valid = [l for l in links if self.is_valid_article_link(l, url)]

            threads = []
            for i, link in enumerate(valid):
                t = threading.Thread(target=self.scrape_and_save_thread, args=(link, name, i))
                t.start()
                threads.append(t)
                time.sleep(0.1)
            for t in threads:
                t.join()

        except Exception as e:
            logging.error(f"Source scrape failed: {name} — {e}")

    def run(self):
        for name, url in self.sources.items():
            logging.info(f"Start scraping source: {name}")
            self.scrape_source(name, url)
        self.save_visited_urls()

# --- CHUNK & EMBED ---
def chunk_documents(data_dir):
    splitter = CharacterTextSplitter.from_tiktoken_encoder(separator="\n\n", chunk_size=512, chunk_overlap=50)
    category_keywords = load_category_keywords()
    docs = []

    for folder in Path(data_dir).iterdir():
        if not folder.is_dir():
            continue
        for file in folder.glob("*.md"):
            with open(file, 'r', encoding='utf-8') as f:
                raw = f.read()
            chunks = splitter.create_documents([raw])
            for c in chunks:
                tags = auto_tag(c.page_content, category_keywords)
                c.metadata = {
                    "source": str(file),
                    "tags": tags,
                    "type": "health_advice" if "home-health" in tags else "general"
                }
                docs.append(c)
    return docs


def embed_documents(docs):
    embed_fn = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma.from_documents(docs, embed_fn, persist_directory=CHROMA_DB_DIR)
    vectordb.persist()
    return vectordb

# --- FLASK APP ---
app = Flask(__name__)
CORS(app)

@app.route("/api/healthchat", methods=["POST"])
def health_chat():
    query = request.json.get("query")
    embed_fn = OllamaEmbeddings(model=MODEL_NAME)
    vectordb = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embed_fn)
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
    results = []
    for folder in Path(DATA_DIR).iterdir():
        for file in folder.glob("*.md"):
            preview = file.read_text(encoding="utf-8")[:500]
            results.append({"file": file.name, "content": preview})
    return jsonify(results)

# --- RUN SYSTEM ---
if __name__ == "__main__":
    print("🌐 Crawling mental health sources...")
    HealthScraper().run()

    print("📄 Chunking documents...")
    docs = chunk_documents(DATA_DIR)
    print(f"✅ {len(docs)} chunks generated.")

    print("💾 Embedding into ChromaDB...")
    embed_documents(docs)
    print("✅ Done embedding.")

    print("🚀 Starting Flask server...")
    app.run(debug=True)
