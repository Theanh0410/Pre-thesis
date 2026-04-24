from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize
import spacy

class SmartHomeCommandExtractor:
    def __init__(self, actions, synonym_map=None, threshold=0.5):
        self.model = SentenceTransformer("paraphrase-MiniLM-L12-v2")
        self.actions = actions
        self.synonym_map = synonym_map or {}
        self.threshold = threshold
        self.action_embeddings = self.model.encode(actions, convert_to_tensor=True)
        self.nlp = spacy.load("en_core_web_sm")

    def extract(self, text):
        results = []
        sentences = sent_tokenize(text)
        sentence_embeddings = self.model.encode(sentences, convert_to_tensor=True)

        for i, sent in enumerate(sentences):
            sent_emb = sentence_embeddings[i]
            best_action, best_score = self._match_action(sent_emb)
            if best_score >= self.threshold:
                final_action = self.synonym_map.get(best_action, best_action)
                obj = self._extract_object(sent)
                results.append({
                    "sentence": sent,
                    "action": final_action,
                    "object": obj,
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
        objects = []
        for token in doc:
            if token.dep_ in ("dobj", "pobj", "attr", "dative") and token.pos_ in ("NOUN", "PROPN"):
                objects.append(token.text)
        return ", ".join(objects) if objects else None