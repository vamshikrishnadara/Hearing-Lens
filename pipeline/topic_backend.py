"""Density clustering with local vectors and auditable outliers; no downloads."""
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer


def refine_assignments(vectors, labels, minimum_similarity=.45, minimum_margin=.03):
    """Refine density assignments in original embedding space, keeping noise explicit.

    No labels or metadata from the input dataset are used. Existing density
    outliers remain outliers. A move needs both minimum similarity and a margin;
    ambiguous rows keep the density assignment instead of forcing a new theme.
    """
    original = np.asarray(labels, dtype=int)
    current = original.copy()
    for _ in range(10):
        ids = sorted(set(current) - {-1})
        if len(ids) < 2: break
        centers = np.asarray([vectors[current == label].mean(axis=0) for label in ids])
        norms = np.linalg.norm(centers, axis=1, keepdims=True)
        if (norms < 1e-12).any(): break
        scores = vectors @ (centers / norms).T
        sorted_scores = np.sort(scores, axis=1)
        revised = current.copy()
        confident = ((original != -1) & (sorted_scores[:, -1] >= minimum_similarity)
                     & ((sorted_scores[:, -1] - sorted_scores[:, -2]) >= minimum_margin))
        revised[confident] = np.asarray(ids)[scores.argmax(axis=1)][confident]
        if np.array_equal(revised, current): break
        current = revised
    return current


def cluster_bertopic(texts, vectors, embedding_model, target_topics=6):
    from bertopic import BERTopic
    from umap import UMAP
    from hdbscan import HDBSCAN
    # Repeated identical vectors otherwise form disconnected UMAP islands. Fit
    # distinct vectors once, then restore every original row and its vote/count.
    _, unique_rows, inverse = np.unique(vectors, axis=0, return_index=True, return_inverse=True)
    unique_texts = [texts[i] for i in unique_rows]
    if len(unique_rows) < 5:
        return np.full(len(texts), -1), {'mode': 'density', 'selected_count': 0,
            'fallback_reason': 'Too little distinct text for density clustering; comments retained as outliers.',
            'skipped_counts': [], 'candidate_scores': []}
    model = BERTopic(
        embedding_model=embedding_model,
        umap_model=UMAP(n_neighbors=min(10, len(unique_rows)-1), n_components=min(5, len(unique_rows)-2),
                        min_dist=0., metric='cosine', random_state=42, init='random', n_jobs=1),
        hdbscan_model=HDBSCAN(min_cluster_size=max(3, min(20, len(unique_rows)//30)), min_samples=1,
                             metric='euclidean', prediction_data=False, core_dist_n_jobs=1),
        vectorizer_model=CountVectorizer(stop_words='english', ngram_range=(1, 3),
            token_pattern=r'(?u)\b(?![xX]{3,}\b)[^\W\d_]{3,}\b'),
        nr_topics=None, calculate_probabilities=False, verbose=False,
    )
    initial, _ = model.fit_transform(unique_texts, embeddings=vectors[unique_rows])
    initial_count = len(set(initial) - {-1})
    if initial_count > target_topics:
        # BERTopic's requested count includes its -1 bucket; our target does not.
        model.reduce_topics(unique_texts, nr_topics=target_topics + int(-1 in initial))
    labels = np.asarray(model.topics_, dtype=int)[inverse]
    before_refinement = labels.copy()
    labels = refine_assignments(vectors, labels)
    if labels.shape != (len(texts),) or (labels < -1).any():
        raise ValueError('Invalid clustering output')
    return labels, {'mode': 'density', 'selected_count': len(set(labels) - {-1}),
        'metric': None, 'candidate_scores': [], 'skipped_counts': [], 'fallback_reason': None,
        'distinct_vectors_fitted': len(unique_rows), 'initial_density_topics': initial_count,
        'refinement_reassigned': int(((labels != before_refinement) & (labels != -1)).sum()),
        'refinement_abstained': int(((labels == -1) & (before_refinement != -1)).sum()),
        'refinement_minimum_similarity': .45, 'refinement_minimum_margin': .03}


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
