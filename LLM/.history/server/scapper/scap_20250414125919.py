class HealthCareScraper(SmarthomeScraper):
    def __init__(self, output_dir="rag_health_data", jina_api_url="https://r.jina.ai/"):
        super().__init__(output_dir, jina_api_url)
        self.sources = {
            'who': 'https://www.who.int/health-topics/mental-health',
            'mentalhealth_uk': 'https://www.mentalhealth.org.uk/explore-mental-health',
            'psychology_today': 'https://www.psychologytoday.com',
            'verywellmind': 'https://www.verywellmind.com/',
            'pubmed': 'https://pubmed.ncbi.nlm.nih.gov',
            'mayoclinic': 'https://www.mayoclinic.org',
            'mind_uk': 'https://www.mind.org.uk'
        }
        
        # Tắt kiểm tra theo từ khoá cũ
        self.relevant_keywords = set()

    def is_relevant_content(self, text):
        """
        Phân loại nội dung theo nhóm thay vì từ khoá rời. Kiểm tra xem nội dung có chứa
        cụm từ liên quan đến chăm sóc sức khoẻ tinh thần, cảm xúc, tâm lý học, v.v.
        """
        mental_health_patterns = [
            r'mental health', r'anxiety', r'depression', r'mindfulness', r'self[- ]?care',
            r'therap(?:ist|y)', r'sleep (quality|disorders)?', r'stress',
            r'coping skills', r'emotional (support|regulation)',
            r'well[- ]?being', r'cbt', r'(psychological|emotional) support'
        ]
        
        text_lower = text.lower()
        matches = sum(bool(re.search(pat, text_lower)) for pat in mental_health_patterns)
        return matches >= 1  # Nếu có ít nhất 1 nhóm trùng là chấp nhận

    def is_vietnamese(self, text):
        """Override để chỉ lấy tiếng Anh"""
        try:
            return detect(text) == 'en'
        except:
            return False

if __name__ == "__main__":
    scraper = HealthCareScraper()
    scraper.run()
