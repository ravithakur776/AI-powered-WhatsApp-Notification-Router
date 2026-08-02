"""Vector similarity RAG index over message history to retrieve evidence and past user preferences."""

from typing import List
import numpy as np
from src.schemas.input_models import MessageHistory
from src.utils.logger import logger


class HistoryRAG:
    def __init__(self, message_histories: List[MessageHistory]):
        self.histories = message_histories
        self._model = None
        self._embeddings = None
        self._initialized = False

    def _lazy_init(self):
        if self._initialized:
            return
        if not self.histories:
            logger.warning("HistoryRAG initialized with empty history dataset.")
            self._initialized = True
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading sentence-transformer embedding model (all-MiniLM-L6-v2)...")
            self._model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            texts = [f"User {h.user_id} Peer {h.peer_id}: {h.message_content} (Action: {h.user_action_taken})" for h in self.histories]
            self._embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
            self._initialized = True
            logger.info(f"HistoryRAG index built for {len(self.histories)} records.")
        except Exception as e:
            logger.warning(f"SentenceTransformer RAG initialization failed: {e}. Fallback to keyword matching.")
            self._initialized = True

    def retrieve_similar_history(self, user_id: str, query_text: str, top_k: int = 3) -> List[MessageHistory]:
        """Retrieves top-K historically similar interaction logs for a user."""
        self._lazy_init()
        
        user_histories = [h for h in self.histories if h.user_id == user_id]
        if not user_histories:
            user_histories = self.histories  # Fallback to global dataset if user has no individual logs

        if not user_histories:
            return []

        if self._model is not None and self._embeddings is not None:
            try:
                query_emb = self._model.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)[0]
                
                # Filter embeddings corresponding to indices
                indices = [i for i, h in enumerate(self.histories) if h in user_histories]
                if not indices:
                    return user_histories[:top_k]

                sub_embs = self._embeddings[indices]
                similarities = np.dot(sub_embs, query_emb)
                top_indices = np.argsort(similarities)[::-1][:top_k]
                return [self.histories[indices[idx]] for idx in top_indices]
            except Exception as e:
                logger.warning(f"Vector search failed in retrieve_similar_history: {e}")

        # Fallback heuristic: word overlap matching
        query_words = set(query_text.lower().split())
        scored = []
        for h in user_histories:
            h_words = set(h.message_content.lower().split())
            overlap = len(query_words.intersection(h_words))
            scored.append((overlap, h))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]
