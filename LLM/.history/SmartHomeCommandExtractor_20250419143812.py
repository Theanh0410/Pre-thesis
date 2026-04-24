import json
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize import sent_tokenize
import spacy
import nltk

nltk.download("punkt")
spacy.cli.download("en_core_web_sm")

class SmartHomeCommandExtractor:
    def __init__(self, actions, synonym_map, room_actions, object_room_map, threshold=0.3):
        self.model = SentenceTransformer("paraphrase-MiniLM-L12-v2")
        self.actions = actions
        self.synonym_map = {k.lower(): v for k, v in synonym_map.items()}
        self.room_actions = room_actions
        self.object_room_map = object_room_map
        self.threshold = threshold
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
            print(f"        ➤ Best matched action: {best_action} (score={round(best_score, 3)})")

            if best_score >= self.threshold:
                mapped_action = self.synonym_map.get(best_action.lower(), best_action)
                obj = self._extract_object(sent)

                # Room detection: từ câu / object / context trước
                room = self._detect_room_from_text(sent) or self.object_room_map.get(obj) or last_known_room
                if room:
                    last_known_room = room

                action_key = mapped_action.lower()  # giữ nguyên full câu lệnh action

                # Check validity: full action phải có trong room_actions
                is_valid = action_key in [a.lower() for a in self.room_actions.get(room, [])]

                results.append({
                    "sentence": sent,
                    "action": mapped_action,
                    "object": obj,
                    "room": room,
                    "valid": is_valid,
                    "score": round(best_score, 3)
                })

        return results

    def _match_action(self, sentence_embedding):
        best_action, best_score = None, 0
        for i, action_emb in enumerate(self.action_embeddings):
            score = util.cos_sim(sentence_embedding, action_emb).item()
            if score > best_score:
                best_score = score
                best_action = self.actions[i]
        return best_action, best_score

    def _extract_object(self, sentence):
        doc = self.nlp(sentence)
        priority_deps = ["dobj", "pobj", "attr", "dative"]
        blacklist = {"room", "setting", "area", "place", "environment"}

        for token in doc:
            if token.dep_ in priority_deps and token.pos_ in ("NOUN", "PROPN"):
                if token.lemma_.lower() not in blacklist:
                    return token.lemma_.lower()
        return None

    def _detect_room_from_text(self, sentence):
        sentence = sentence.lower()
        for room in self.room_actions:
            if room in sentence:
                return room
        return None
