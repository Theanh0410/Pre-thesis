# bm25.py
import os
from rank_bm25 import BM25Okapi
import nltk

nltk.download("punkt")

class BM25Retriever:
    def __init__(self, docs_folder="documents"):
        self.docs_folder = docs_folder
        self.filenames = []
        self.documents = []
        self.bm25 = None

        self._load_documents()

    def _load_documents(self):
        for filename in os.listdir(self.docs_folder):
            if filename.endswith(".txt"):
                path = os.path.join(self.docs_folder, filename)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                    self.documents.append(content)
                    self.filenames.append(filename)
        tokenized_corpus = [doc.lower().split() for doc in self.documents]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def get_top_k_docs(self, query, k=5):
        if not self.bm25:
            return []
        tokenized_query = query.lower().split()
        return self.bm25.get_top_n(tokenized_query, self.documents, n=k)

    def get_top_k_filenames(self, query, k=5):
        if not self.bm25:
            return []
        tokenized_query = query.lower().split()
        top_scores = self.bm25.get_scores(tokenized_query)
        ranked = sorted(enumerate(top_scores), key=lambda x: x[1], reverse=True)
        top_indices = [idx for idx, _ in ranked[:k]]
        return [(self.filenames[idx], self.documents[idx]) for idx in top_indices]
