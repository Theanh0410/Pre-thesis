"""
Semantic intent matching: maps free-form natural language to configured
smart-home intents by embedding similarity, instead of hardcoded keyword
regexes. The embedding backend is injected (embed_fn) so this module has
no ML dependency of its own and can be tested with a fake embedder.
"""
from dataclasses import dataclass
from math import sqrt


@dataclass
class IntentMatch:
    intent: str
    actions: list
    score: float


def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sqrt(sum(x * x for x in a))
    norm_b = sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class IntentMatcher:
    """
    intents: {intent_name: {"examples": [str, ...], "actions": [dict, ...]}}
    embed_fn: list[str] -> list[vector], e.g. SentenceTransformer.encode
    """

    def __init__(self, intents, embed_fn):
        self.intents = intents
        self.embed_fn = embed_fn
        self._example_vectors = {
            intent_name: embed_fn(config["examples"]) if config["examples"] else []
            for intent_name, config in intents.items()
        }

    def match(self, text, threshold=0.6):
        [text_vector] = self.embed_fn([text])
        matches = []
        for intent_name, config in self.intents.items():
            example_vectors = self._example_vectors[intent_name]
            if not example_vectors:
                continue
            best_score = max(
                cosine_similarity(text_vector, ex_vec) for ex_vec in example_vectors
            )
            if best_score >= threshold:
                matches.append(IntentMatch(intent_name, config["actions"], best_score))
        matches.sort(key=lambda m: m.score, reverse=True)
        return matches
