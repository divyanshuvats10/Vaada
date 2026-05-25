import torch
from sentence_transformers import SentenceTransformer, util

_model = None
_topic_embeddings = None

TOPICS = [
    "economy and inflation, mehngai, petrol diesel prices, rupee",
    "unemployment and jobs, naukri, rozgaar, employment",
    "agriculture and farmers, kisan, fasal, MSP, farm laws",
    "national security and military, army, Pakistan, border, terrorism",
    "religion and communalism, mandir, masjid, Hindu, Muslim",
    "education policy, school, university, students",
    "healthcare and hospitals, doctor, medicine, health",
    "corruption and governance, bhrashtachar, scam, bribery",
    "infrastructure and development, roads, highways, smart city",
    "foreign policy and international relations, China, America, trade",
    "environment and climate change, pollution, forest",
    "women and social issues, mahila, gender, safety",
    "reservation and caste, OBC, SC ST, dalit, quota",
    "tax and GST, income tax, business, vyapaar",
    "poverty and welfare schemes, garib, BPL, ration",
    "elections and democracy, vote, chunav, rally",
    "media and freedom of speech, press, journalist",
    "judiciary and law, court, Supreme Court, justice",
]


def get_model_and_topics():
    global _model, _topic_embeddings
    if _model is None:
        print("Loading topic tagger...")
        _model = SentenceTransformer(
            'paraphrase-multilingual-MiniLM-L12-v2',
            device="cuda"
        )
        _topic_embeddings = _model.encode(
            TOPICS,
            convert_to_tensor=True,
            device="cuda"
        )
        print("Topic tagger loaded ✓")
    return _model, _topic_embeddings


def tag_topics(text: str, top_k: int = 2, threshold: float = 0.20) -> list:
    """
    Returns top_k most relevant topics for a chunk of text.
    Only returns topics above the threshold score.
    """
    model, topic_embeddings = get_model_and_topics()

    text_embedding = model.encode(text, convert_to_tensor=True, device="cuda")
    scores = util.cos_sim(text_embedding, topic_embeddings)[0]

    top_results = []
    for idx in scores.argsort(descending=True)[:top_k]:
        score = scores[idx].item()
        if score >= threshold:
            top_results.append({
                'topic': TOPICS[idx],
                'score': round(score, 3)
            })

    return top_results


def tags_to_string(tags: list) -> str:
    """Convert tag list to JSON string for SQLite storage."""
    import json
    # extract clean topic name (before the first comma)
    clean_tags = [t['topic'].split(',')[0].strip() for t in tags]
    return json.dumps(clean_tags)


def free_tagger():
    global _model, _topic_embeddings
    _model = None
    _topic_embeddings = None
    torch.cuda.empty_cache()