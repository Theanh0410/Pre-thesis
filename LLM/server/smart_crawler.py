
import os
import json
import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("data")
HTML_BACKUP_DIR = Path("html_backup")
HTML_BACKUP_DIR.mkdir(exist_ok=True)
HEADERS = {'User-Agent': 'Mozilla/5.0'}

def load_sources():
    with open("smart_crawler_sources.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_base_url(url):
    return urldefrag(url)[0]

def is_same_domain(url1, url2):
    return urlparse(url1).netloc == urlparse(url2).netloc

def is_valid_link(link):
    parsed = urlparse(link)
    return not parsed.fragment and parsed.scheme.startswith("http")

def scrape_url(url, save_path):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator="\n", strip=True)
        if len(text) < 300:
            return None
        file_path = save_path / f"{hash(url)}.md"
        file_path.write_text(text, encoding="utf-8")
        html_path = HTML_BACKUP_DIR / f"{hash(url)}.html"
        html_path.write_text(res.text, encoding="utf-8")
        return True
    except Exception as e:
        logging.warning(f"Failed to scrape {url}: {e}")
        return False

def crawl():
    sources = load_sources()
    for category, urls in sources.items():
        for name, base_url in urls.items():
            print(f"🌐 Crawling {name} [{category}]")
            try:
                res = requests.get(base_url, headers=HEADERS, timeout=10)
                res.raise_for_status()
                soup = BeautifulSoup(res.text, "html.parser")
                links = {urljoin(base_url, a["href"]) for a in soup.find_all("a", href=True)}
                valid_links = [l for l in links if is_same_domain(l, base_url) and is_valid_link(l)]

                save_path = OUTPUT_DIR / category
                save_path.mkdir(parents=True, exist_ok=True)
                for link in valid_links:
                    scrape_url(link, save_path)
            except Exception as e:
                logging.error(f"Error fetching {base_url}: {e}")

if __name__ == "__main__":
    crawl()
