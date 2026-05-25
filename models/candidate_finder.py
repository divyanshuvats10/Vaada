import numpy as np
from datetime import datetime
from sentence_transformers import util
from models.embedder import bytes_to_embedding


def find_contradiction_candidates(
    statements: list,
    similarity_threshold: float = 0.65,
    min_gap_days: int = 180,
    max_candidates: int = 50
) -> list:
    """
    Given a list of statement dicts from the DB, finds pairs that are:
    1. Topically similar (high embedding similarity)
    2. Temporally far apart (at least 6 months)

    These are the candidates worth sending to the classifier.
    """

    if len(statements) < 2:
        print("Not enough statements to compare.")
        return []

    # load embeddings from bytes
    embeddings = np.array([
        bytes_to_embedding(s['embedding'])
        for s in statements
    ])

    # compute full similarity matrix
    import torch
    embeddings_tensor = torch.tensor(embeddings)
    similarity_matrix = util.cos_sim(embeddings_tensor, embeddings_tensor).numpy()

    candidates = []

    for i in range(len(statements)):
        for j in range(i + 1, len(statements)):

            similarity = float(similarity_matrix[i][j])
            if similarity < similarity_threshold:
                continue

            # parse dates
            try:
                date_a = datetime.strptime(statements[i]['statement_date'], '%Y-%m-%d')
                date_b = datetime.strptime(statements[j]['statement_date'], '%Y-%m-%d')
            except (ValueError, TypeError):
                continue

            gap_days = abs((date_a - date_b).days)
            if gap_days < min_gap_days:
                continue

            candidates.append({
                'statement_a': statements[i],
                'statement_b': statements[j],
                'similarity':  round(similarity, 3),
                'gap_days':    gap_days,
            })

    # sort by similarity — most similar first
    candidates.sort(key=lambda x: x['similarity'], reverse=True)

    # cap to avoid too many API calls
    return candidates[:max_candidates]