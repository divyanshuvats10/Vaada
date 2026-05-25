from database.db import get_statements_for_politician
from models.candidate_finder import find_contradiction_candidates
from models.classifier import classify_contradiction
from database.db import add_contradiction

statements = get_statements_for_politician(1)
print(f"Total statements: {len(statements)}")

# lower threshold to find more candidates
candidates = find_contradiction_candidates(
    statements,
    similarity_threshold=0.45,
    min_gap_days=180,
    max_candidates=20
)

print(f"Candidates found: {len(candidates)}")

for i, c in enumerate(candidates):
    print(f"\nCandidate {i+1} | Similarity: {c['similarity']} | Gap: {c['gap_days']} days")
    print(f"  A ({c['statement_a']['statement_date']}): {c['statement_a']['text'][:100]}...")
    print(f"  B ({c['statement_b']['statement_date']}): {c['statement_b']['text'][:100]}...")

    result = classify_contradiction(
        statement_a={
            'text': c['statement_a']['text'],
            'date': c['statement_a']['statement_date'],
            'video_title': 'Modi Speech',
        },
        statement_b={
            'text': c['statement_b']['text'],
            'date': c['statement_b']['statement_date'],
            'video_title': 'Modi Speech',
        }
    )

    if result:
        print(f"  ✓ {result['classification']} | {result['severity']} | {result['explanation']}")
        add_contradiction(
            statement_a_id=c['statement_a']['id'],
            statement_b_id=c['statement_b']['id'],
            classification=result['classification'],
            confidence=result['confidence'],
            explanation=result['explanation'],
            severity=result['severity']
        )
    else:
        print(f"  — No contradiction")