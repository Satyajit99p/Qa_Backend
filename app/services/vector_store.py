from typing import List, Tuple, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel


class SimpleTfidfStore:
    def __init__(self, chunks: List[str]):
        self.chunks = chunks or []
        self.vectorizer = None
        self.tfidf_matrix = None
        if self.chunks:
            self.vectorizer = TfidfVectorizer(stop_words="english", max_df=0.9)
            self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)

    def top_k(self, query: str, k: int = 5) -> List[dict]:
        if self.tfidf_matrix is None or self.tfidf_matrix.shape[0] == 0:
            return []
        qv = self.vectorizer.transform([query])
        sims = linear_kernel(qv, self.tfidf_matrix).flatten()
        idxs = sims.argsort()[::-1][:k]
        results = []
        for i in idxs:
            results.append({"chunk_id": int(i), "score": float(sims[i]), "text": self.chunks[i]})
        return results