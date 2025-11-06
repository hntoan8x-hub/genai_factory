# domain_models/genai_assistant/monitoring/drift_monitor.py

from collections import deque
from typing import Dict, Any, Deque
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DriftMonitor:
    """
    Detects changes in the distribution of user queries (query drift).
    
    This can signal changes in user behavior, new trends, or a failure
    in the LLM to handle new types of inputs.
    """
    
    def __init__(self, window_size: int = 100):
        """
        Initializes the drift monitor.
        
        Args:
            window_size (int): The number of recent queries to keep for analysis.
        """
        self.query_history: Deque[str] = deque(maxlen=window_size)
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.baseline_vector = None
        
    def add_query(self, query: str):
        """Adds a new query to the history and updates the baseline."""
        self.query_history.append(query)
        self._update_baseline()
        
    def _update_baseline(self):
        """Recalculates the baseline vector from the current history."""
        if len(self.query_history) > 10: # Ensure enough data for a stable baseline
            corpus = list(self.query_history)
            tfidf_matrix = self.vectorizer.fit_transform(corpus)
            self.baseline_vector = np.mean(tfidf_matrix.toarray(), axis=0)

    def check_drift(self, new_query: str) -> Dict[str, Any]:
        """
        Checks for drift between a new query and the historical baseline.
        
        Returns a cosine similarity score. A lower score indicates greater drift.
        """
        if self.baseline_vector is None or len(self.query_history) < 10:
            return {"drift_detected": False, "reason": "Insufficient history for baseline."}
        
        new_query_vector = self.vectorizer.transform([new_query]).toarray()
        if new_query_vector.shape[1] != self.baseline_vector.shape[0]:
            # This can happen if the new query has new words not in the baseline vocabulary.
            # A more robust solution would retrain the vectorizer, but for a simple monitor, this is sufficient.
            return {"drift_detected": True, "reason": "Query contains new vocabulary."}

        similarity = cosine_similarity(new_query_vector, self.baseline_vector.reshape(1, -1))[0][0]
        
        # A simple drift detection threshold
        threshold = 0.5 
        
        return {
            "drift_detected": similarity < threshold,
            "similarity_score": float(similarity),
            "reason": "Similarity score is below the threshold." if similarity < threshold else "No significant drift detected."
        }
