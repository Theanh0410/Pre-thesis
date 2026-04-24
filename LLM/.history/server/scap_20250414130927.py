import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import urljoin, urlparse, urldefrag
import logging
from pathlib import Path
from langdetect import detect
from datetime import datetime
import re
import json

class SmarthomeScraper:
    def __init__(self, output_dir="smarthome_data", jina_api_url="https://r.jina.ai/"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize history file path
        self.history_file = self.output_dir / 'visited_urls.json'

        now = datetime.now()
        logging.basicConfig(
            filename=self.output_dir / f'scraping_{now.strftime("%Y_%m_%d")}.log',
            level=logging.INFO,
            format='%(asctime)s - %(message)s'
        )

        self.jina_api_url = jina_api_url
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        }
        
        self.sources = {
            'smarthome_wiki': r'https://vi.wikipedia.org/wiki/V%C4%83n_h%C3%B3a_Vi%E1%BB%87t_Nam',
        }

        # Load visited URLs from file or initialize empty set
        self.visited_base_urls = self.load_visited_urls()

        self.relevant_keywords = {
            # General Conversation & Daily Life
            'family',
            'home',
            'living room',
            'kitchen',
            'bedroom',
            'furniture',
            'decoration',
            'lighting',
            'atmosphere',
            'comfort',

            # Culture & Traditions (Adapted for Home)
            'tradition',
            'heritage',
            'customs',
            'rituals',
            'beliefs',
            'storytelling',
            'folklore',
            'superstitions',
            'etiquette',
            'ceremonies',

            # Food & Cooking (Common Indoor Topics)
            'cuisine',
            'dining table',
            'meal',
            'recipe',
            'cooking',
            'ingredients',
            'flavor',
            'dish',
            'seasoning',
            'homemade',

            # Clothing & Fashion (Indoor Attire & Discussion)
            'clothing',
            'fabric',
            'embroidery',
            'fashion',
            'dressing style',
            'homewear',
            'casual outfit',
            'accessories',
            'texture',
            'traditional dress',

            # Entertainment & Arts (Home & Indoor Activities)
            'television',
            'music',
            'singing',
            'dancing',
            'theater',
            'painting',
            'sculpture',
            'handicrafts',
            'literature',
            'poetry',

            # Spirituality & Indoor Religious Practices
            'meditation',
            'prayer',
            'worship',
            'offering',
            'incense',
            'altar',
            'ceremony',
            'mindfulness',
            'blessing',
            'ancestor worship',

            # Home & Family Relationships
            'conversation',
            'hospitality',
            'gathering',
            'reunion',
            'parenting',
            'childhood',
            'grandparents',
            'storytelling',
            'affection',
            'bonding',

            # Home Decorations & Architecture
            'interior design',
            'wooden furniture',
            'lighting fixtures',
            'wall art',
            'ceramic decorations',
            'tapestry',
            'feng shui',
            'color scheme',
            'flower arrangement',
            'bookshelf',

            # Indoor Games & Activities
            'chess',
            'board games',
            'storytelling',
            'card games',
            'reading',
            'calligraphy',
            'poetry recital',
            'puzzle-solving',
            'knitting',
            'home theater',

            # Indoor Tourism & Family Gatherings
            'guest reception',
            'indoor photography',
            'virtual museum tour',
            'traditional storytelling night',
            'housewarming',
            'New Year’s Eve gathering',
            'tea ceremony',
            'candlelight dinner',
            'anniversary celebration',
            'family movie night'
        }

    def load_visited_urls(self):
        """Load visited URLs from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    visited_urls_data = json.load(f)
                logging.info(f"Loaded {len(visited_urls_data)} visited URLs from history")
                return set(visited_urls_data)
            return set()
        except Exception as e:
            logging.error(f"Error loading visited URLs: {str(e)}")
            return set()

    def save_visited_urls(self):
        """Save visited URLs to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.visited_base_urls), f, ensure_ascii=False, indent=2)
            logging.info(f"Saved {len(self.visited_base_urls)} visited URLs to history")
        except Exception as e:
            logging.error(f"Error saving visited URLs: {str(e)}")

    def get_base_url(self, url):
        """Get the base URL without fragments"""
        return urldefrag(url)[0]

    def is_vietnamese(self, text):
        """Check if text is in Vietnamese"""
        try:
            return detect(text) == 'vi'
        except:
            return False

    def is_same_domain(self, url1, url2):
        """Check if two URLs belong to the same domain"""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2

    def is_relevant_url(self, url, source_url):
        """Check if URL is relevant based on patterns and domain"""
        # Get base URL without fragments
        base_url = self.get_base_url(url)
        
        # Skip if we've already visited this base URL
        if base_url in self.visited_base_urls:
            return False

        # Skip external links unless they're to known good domains
        if not self.is_same_domain(url, source_url):
            allowed_domains = {urlparse(src).netloc for src in self.sources.values()}
            if urlparse(url).netloc not in allowed_domains:
                return False

        # Skip common irrelevant Wikipedia sections
        if 'wikipedia.org' in url.lower():
            skip_patterns = [
                'action=edit',
                'oldid=',
                'diff=',
                'printable=yes',
                'veaction=',
                'Special:',
                'Talk:',
                'User:',
                'User_talk:',
                'Wikipedia:',
                'Help:',
                'File:',
                'Portal:',
                'Template:',
                'Category:'
            ]
            return not any(pattern in base_url for pattern in skip_patterns)

        return True

    def is_relevant_content(self, text):
        """Check if the content is relevant to Vietnamese culture"""
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in self.relevant_keywords if keyword in text_lower)
        return keyword_count >= 2

    def save_article_files(self, article, source_name, index, sub=False):
        """Save individual article as Markdown file"""
        if not article:
            return
            
        source_dir = self.output_dir / source_name
        source_dir.mkdir(exist_ok=True)

        prefix = 'article_sub_' if sub else 'article_'
        md_path = source_dir / f'{prefix}{source_name}_{index:04d}.md'
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(article)

    def save_articles(self, articles, source_name):
        """Save scraped articles to Markdown format"""
        if not articles:
            return
            
        for i, article in enumerate(articles):
            self.save_article_files(article, source_name, i)
            
        logging.info(f"Saved {len(articles)} articles from {source_name}")

    def scrape_article(self, url, source_url):
        """Scrape article content from URL"""
        # Get base URL without fragments
        base_url = self.get_base_url(url)
        
        if base_url in self.visited_base_urls:
            logging.info(f"Skipping already visited base URL: {base_url}")
            return None

        if not self.is_relevant_url(url, source_url):
            logging.info(f"Skipping irrelevant URL: {url}")
            return None

        try:
            # Use base URL for content fetching to avoid duplicate content
            response = requests.get(self.jina_api_url + base_url, headers=self.headers)
            response.raise_for_status()

            if not self.is_vietnamese(response.text):
                logging.info(f"Skipping non-Vietnamese content: {base_url}")
                return None

            if not self.is_relevant_content(response.text):
                logging.info(f"Skipping content not related to Vietnamese culture: {base_url}")
                return None

            # Mark base URL as visited
            self.visited_base_urls.add(base_url)
            time.sleep(random.uniform(1, 3))
            return response.text

        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return None

    def scrape_source(self, source_name, url):
        """Scrape all articles from a source"""
        articles = []

        try:
            base_url = self.get_base_url(url)
            response = requests.get(base_url, headers=self.headers)
            response_md = requests.get(self.jina_api_url + base_url, headers=self.headers)
            response.raise_for_status()
            response_md.raise_for_status()

            if not self.is_vietnamese(response_md.text):
                return None

            if self.is_relevant_content(response_md.text):
                articles.append(response_md.text)
                self.visited_base_urls.add(base_url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            article_links = soup.find_all('a', href=True)
            article_links = [urljoin(url, link['href']) for link in article_links]
            article_links = list(dict.fromkeys(article_links))

            for i, link in enumerate(article_links):
                logging.info(f"Starting scrape {i + 1}/{len(article_links)} with url: {link}")
                sub_article = self.scrape_article(link, url)
                if sub_article:
                    self.save_article_files(sub_article, source_name, i, True)

            time.sleep(random.uniform(1, 3))
        except Exception as e:
            logging.error(f"Error scraping source {source_name}: {str(e)}")
        return articles

    def run(self):
        """Run the scraper on all sources"""
        try:
            for source_name, url in self.sources.items():
                logging.info(f"Starting scrape of {source_name}")
                articles = self.scrape_source(source_name, url)
                self.save_articles(articles, source_name)
                logging.info(f"Completed scrape of {source_name}")
        finally:
            # Always save visited URLs when finishing
            self.save_visited_urls()

if __name__ == "__main__":
    scraper = SmarthomeScraper()
    scraper.run()


