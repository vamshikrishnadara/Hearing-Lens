"""Optional, conservative small-group consolidation on existing comment vectors."""
import numpy as np

MIN_THEME_SIZE = 3
MIN_MERGE_SIMILARITY = 0.75  # Experimental policy, not a calibrated topic threshold.


def merge_small_groups(vectors, groups):
    """Merge the most similar eligible pair; never drop or duplicate a member.

    At least one current group must have fewer than three members. All cross-pair
    original centroid similarities must meet the threshold, preventing a chain
    of individually similar neighbors from bridging dissimilar original groups.
    Input group order defines stable initial IDs for tie breaking and audit.
    """
    centers = []
    for members in groups:
        center = vectors[members].mean(axis=0)
        norm = np.linalg.norm(center)
        centers.append(center / norm if norm > 1e-12 else None)
    similarities = {}
    for left in range(len(groups)):
        for right in range(left + 1, len(groups)):
            a, b = centers[left], centers[right]
            similarities[left, right] = (
                float(np.clip(a @ b, -1, 1)) if a is not None and b is not None else -1.0
            )
    active = [(list(members), [i]) for i, members in enumerate(groups)]
    history = []
    while True:
        best = None
        for left, (left_members, left_ids) in enumerate(active):
            for right in range(left + 1, len(active)):
                right_members, right_ids = active[right]
                if min(len(left_members), len(right_members)) >= MIN_THEME_SIZE:
                    continue
                score = min(similarities[min(a, b), max(a, b)] for a in left_ids for b in right_ids)
                if score < MIN_MERGE_SIMILARITY:
                    continue
                # Active groups stay ordered by their smallest original ID.
                if best is None or score > best[0]:
                    best = (score, left, right)
        if best is None:
            break
        score, left, right = best
        left_members, left_ids = active[left]
        right_members, right_ids = active[right]
        history.append({
            'left_initial_theme_ids': [i + 1 for i in left_ids],
            'right_initial_theme_ids': [i + 1 for i in right_ids],
            'minimum_similarity': score,
            'merged_count': len(left_members) + len(right_members),
        })
        active[left] = (sorted(left_members + right_members), sorted(left_ids + right_ids))
        del active[right]
    return [members for members, _ in active], {
        'minimum_theme_size': MIN_THEME_SIZE,
        'minimum_similarity': MIN_MERGE_SIMILARITY,
        'initial_count': len(groups), 'final_count': len(active),
        'history': history,
        'initial_theme_ids_by_group': [[i + 1 for i in ids] for _, ids in active],
    }
