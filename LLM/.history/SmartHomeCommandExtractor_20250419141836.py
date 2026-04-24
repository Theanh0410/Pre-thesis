from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize
import spacy
import nltk

# Tải các gói cần thiết
nltk.download('punkt')
spacy.cli.download("en_core_web_sm")

# Danh sách từ khóa để nhận diện phòng
ROOM_KEYWORDS = {
    "living room": ["living room", "lounge", "main room"],
    "bedroom": ["bedroom", "my room", "sleeping area"],
    "kitchen": ["kitchen", "cooking area"],
    "bathroom": ["bathroom", "restroom", "toilet"],
    "office": ["office", "workspace", "study room"],
    "garage": ["garage"],
    "dining room": ["dining room", "dinner area"]
}

class SmartHomeCommandExtractor:
    def __init__(self, actions, synonym_map=None, threshold=0.3):
        self.model = SentenceTransformer("paraphrase-MiniLM-L12-v2")
        self.actions = actions
        self.threshold = threshold
        self.synonym_map = {k.lower(): v for k, v in (synonym_map or {}).items()}
        self.action_embeddings = self.model.encode(actions, convert_to_tensor=True)
        self.nlp = spacy.load("en_core_web_sm")

    def extract(self, text):
        results = []
        sentences = sent_tokenize(text)
        sentence_embeddings = self.model.encode(sentences, convert_to_tensor=True)

        last_known_room = None

        for i, sent in enumerate(sentences):
            sent_emb = sentence_embeddings[i]
            best_action, best_score = self._match_action(sent_emb)

            print(f"\n[DEBUG] Sentence: {sent}")
            print(f"        ➤ Best action match: {best_action} (score={round(best_score, 3)})")

            if best_score >= self.threshold:
                mapped_action = self.synonym_map.get(best_action.lower(), best_action)
                obj = self._extract_object(sent)
                room = self._detect_room(sent) or last_known_room
                if room:
                    last_known_room = room

                results.append({
                    "sentence": sent,
                    "action": mapped_action,
                    "object": obj,
                    "room": room,
                    "score": round(best_score, 3)
                })

        return results

    def _match_action(self, sentence_embedding):
        best_action = None
        best_score = 0
        for i, action_embedding in enumerate(self.action_embeddings):
            score = util.cos_sim(sentence_embedding, action_embedding).item()
            if score > best_score:
                best_score = score
                best_action = self.actions[i]
        return best_action, best_score

    def _extract_object(self, sentence):
        doc = self.nlp(sentence)
        priority_deps = ["dobj", "pobj", "attr", "dative"]
        blacklist = {"room", "setting", "atmosphere", "area", "place", "space", "environment"}

        for token in doc:
            if token.dep_ in priority_deps and token.pos_ in ("NOUN", "PROPN"):
                if token.lemma_.lower() not in blacklist:
                    return token.lemma_.lower()
        return None

    def _detect_room(self, sentence):
        sentence = sentence.lower()
        for room, keywords in ROOM_KEYWORDS.items():
            for kw in keywords:
                if kw in sentence:
                    return room
        return None
