"""Density clustering with local vectors and auditable outliers; no downloads."""
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer


def cluster_bertopic(texts, vectors, embedding_model, target_topics=6):
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    # Explicit random initialization also handles tiny post-cleaning matrices.
    if len(texts) < 5 or len(np.unique(vectors, axis=0)) < 2:
        return np.full(len(texts), -1), {'mode': 'density', 'selected_count': 0,
            'fallback_reason': 'Too little distinct text for density clustering; comments retained as outliers.',
            'skipped_counts': [], 'candidate_scores': []}
    model = BERTopic(
        embedding_model=embedding_model,
        umap_model=UMAP(n_neighbors=min(15, len(texts)-1), n_components=min(5, len(texts)-2),
                        min_dist=0., metric='cosine', random_state=42, init='random', n_jobs=1),
        hdbscan_model=HDBSCAN(min_cluster_size=max(5, min(20, len(texts)//20)), min_samples=3,
                             metric='euclidean', prediction_data=False, core_dist_n_jobs=1),
        vectorizer_model=CountVectorizer(stop_words='english', ngram_range=(1, 3),
            token_pattern=r'(?u)\b(?![xX]{3,}\b)[^\W\d_]{3,}\b'),
        nr_topics=target_topics, calculate_probabilities=False, verbose=False,
    )
    labels, _ = model.fit_transform(texts, embeddings=vectors)
    labels = np.asarray(labels, dtype=int)
    if labels.shape != (len(texts),) or (labels < -1).any():
        raise ValueError('Invalid clustering output')
    return labels, {'mode': 'density', 'selected_count': len(set(labels) - {-1}),
        'metric': None, 'candidate_scores': [], 'skipped_counts': [], 'fallback_reason': None}


def keybert_keywords(texts, groups, vectors, embedding_model):
    from keybert import KeyBERT
    # Shared keyword embeddings; group centers avoid truncating concatenated documents.
    docs = [' '.join(texts[i] for i in members) for members in groups]
    if not docs:
        return []
    vectorizer = CountVectorizer(stop_words='english', ngram_range=(1, 3), max_features=5000,
        token_pattern=r'(?u)\b(?![xX]{3,}\b)[^\W\d_]{3,}\b')
    try:
        vectorizer.fit(texts)
        # Fix vocabulary to within-comment phrases; avoid labels spanning comments.
        vectorizer = CountVectorizer(vocabulary=vectorizer.vocabulary_, stop_words="english", ngram_range=(1, 3),
            token_pattern=r"(?u)\b(?![xX]{3,}\b)[^\W\d_]{3,}\b")
    except ValueError:
        return [[] for _ in groups]
    centers = np.asarray([vectors[members].mean(axis=0) for members in groups])
    words = embedding_model.encode(vectorizer.get_feature_names_out().tolist(), batch_size=32,
                                   show_progress_bar=False, convert_to_numpy=True)
    result = KeyBERT(model=embedding_model).extract_keywords(
        docs, vectorizer=vectorizer, doc_embeddings=centers, word_embeddings=words,
        use_mmr=True, diversity=.5, top_n=5)
    if len(docs) == 1:
        result = [result]
    return [[word for word, _ in row] for row in result]
