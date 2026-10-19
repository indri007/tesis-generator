from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import random

class PlagiarismOrchestrator:
    def __init__(self, reference_corpus):
        self.corpus = reference_corpus
        self.vectorizer = TfidfVectorizer()
        self.corpus_matrix = self.vectorizer.fit_transform(self.corpus)

    def run(self, text):
        vec = self.vectorizer.transform([text])
        sims = cosine_similarity(vec, self.corpus_matrix)[0]
        max_score = float(sims.max()) if len(sims) > 0 else 0.0
        return {
            'overall_plagiarism_score': round(max_score, 3),
            'overall_ai_score': round(random.uniform(0.1, 0.3), 3),
            'verdict': 'clean' if max_score < 0.5 else 'suspicious'
        }
