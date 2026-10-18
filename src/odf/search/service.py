"""
Search Service
Hybrid search: semantic vector search + exact keyword boosting.
"""

# Fetch more candidates than requested so keyword boosts can re-rank them
CANDIDATE_MULTIPLIER = 3
# Score added when the query appears verbatim in the filename / chunk text
TITLE_BOOST = 0.25
CONTENT_BOOST = 0.15


class SearchService:
    def __init__(self, store, embedder):
        self.store = store
        self.embedder = embedder

    def search(self, query, top_k=10, filter_metadata=None):
        """
        Search for documents similar to the query.
        Implements Hybrid Search: Semantic Vector Search + Exact Keyword Boosting.
        """
        try:
            if self.store.count() == 0:
                return []

            query_embedding = self.embedder.embed_text(query)

            # Hybrid Search Strategy:
            # 1. Fetch more candidates (3x) from vector search to cast a wider net
            # 2. Check for exact keyword matches in these candidates
            # 3. Apply boosting for exact matches
            # 4. Re-rank and return top_k
            hits = self.store.query(
                query_embedding,
                n_results=top_k * CANDIDATE_MULTIPLIER,
                where=filter_metadata,
            )

            candidates = []
            query_lower = query.lower().strip()

            for hit in hits:
                # Base Semantic Score
                # Chroma's cosine distance is 1 - cosine similarity
                base_score = 1 - hit['distance']
                final_score = base_score

                content_text = hit['document']
                metadata = hit['metadata']
                filename = metadata.get('filename', '').lower()

                # --- HYBRID BOOSTING LOGIC ---
                boost_applied = False

                # 1. Title Match Boost (Very High)
                if query_lower in filename:
                    final_score += TITLE_BOOST
                    boost_applied = True

                # 2. Exact Content Match Boost (Moderate)
                if query_lower in content_text.lower():
                    final_score += CONTENT_BOOST
                    boost_applied = True

                # Ensure we don't exceed 1.0 (optional, but good for consistent UI%)
                final_score = min(1.0, final_score)

                candidates.append({
                    'id': hit['id'],
                    'similarity': max(0.0, float(final_score)),
                    'base_score': base_score,  # Debugging
                    'boosted': boost_applied,
                    'content': content_text,
                    'metadata': metadata,
                    'file_path': metadata.get('source'),
                    'filename': metadata.get('filename', 'Unknown'),
                })

            # Re-rank based on final_score
            candidates.sort(key=lambda x: x['similarity'], reverse=True)

            # Return top_k
            return candidates[:top_k]

        except Exception as e:
            print(f"Search error: {e}")
            return []
