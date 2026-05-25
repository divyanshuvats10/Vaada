import os
os.environ["CT2_CUDA_ALLOCATOR"] = "cub_caching"
import json
import torch
from pipeline.downloader import download_audio
from pipeline.transcriber import transcribe_with_cache, get_model
from pipeline.chunker import chunk_by_time, make_youtube_url
from models.embedder import embed_chunks, embedding_to_bytes, free_embedder
from models.topic_tagger import tag_topics, tags_to_string, free_tagger
from models.candidate_finder import find_contradiction_candidates
from models.classifier import classify_contradiction
from database.db import (
    init_db, add_politician, add_video, add_statement,
    mark_video_processed, get_statements_for_politician,
    add_contradiction, get_all_politicians
)


def process_video(youtube_url: str, politician_id: int, politician_name: str):
    """
    Full pipeline for a single YouTube video:
    download → transcribe → chunk → embed → tag → store
    """
    print(f"\n{'='*60}")
    print(f"Processing: {youtube_url}")
    print(f"{'='*60}")

    # Step 1: Download
    print("\n[1/5] Downloading audio...")
    meta = download_audio(youtube_url, politician_id)

    # Step 2: Add video to DB
    video_id = add_video(
        politician_id=politician_id,
        youtube_id=meta['video_id'],
        title=meta['title'],
        upload_date=meta['upload_date'],
        duration=meta['duration']
    )
    print(f"Video saved to DB: {meta['title']}")

    # Step 3: Transcribe
    print("\n[2/5] Transcribing...")
    transcript = transcribe_with_cache(meta['audio_path'])
    print(f"Segments: {len(transcript['segments'])}")

    # free whisper from GPU before loading embedder
    import gc
    gc.collect()
    torch.cuda.empty_cache()
    print("GPU memory cleared ✓")

    # Step 4: Chunk
    print("\n[3/5] Chunking...")
    chunks = chunk_by_time(transcript['segments'], chunk_duration=45)
    print(f"Chunks: {len(chunks)}")

    # Step 5: Embed + Tag + Store
    print("\n[4/5] Embedding and tagging...")
    embeddings = embed_chunks(chunks)

    statements_stored = 0
    for i, chunk in enumerate(chunks):
        embedding_bytes = embedding_to_bytes(embeddings[i])
        tags = tag_topics(chunk['text'])
        tag_str = tags_to_string(tags)
        youtube_url_ts = make_youtube_url(meta['video_id'], chunk['yt_offset'])

        add_statement(
            politician_id=politician_id,
            video_id=video_id,
            text=chunk['text'],
            start_time=chunk['start_time'],
            end_time=chunk['end_time'],
            youtube_url=youtube_url_ts,
            topic_tags=tag_str,
            embedding=embedding_bytes,
            statement_date=meta['upload_date']
        )
        statements_stored += 1

    print(f"Statements stored: {statements_stored}")

    # free embedder from GPU
    free_embedder()
    free_tagger()

    # mark video as processed
    mark_video_processed(video_id)
    print("\n[5/5] Video processing complete ✓")

    return statements_stored


def run_contradiction_detection(politician_id: int, politician_name: str):
    """
    Finds and stores contradictions for a politician.
    Run this after processing multiple videos.
    """
    print(f"\n{'='*60}")
    print(f"Running contradiction detection for: {politician_name}")
    print(f"{'='*60}")

    # get all statements from DB
    statements = get_statements_for_politician(politician_id)
    print(f"Total statements: {len(statements)}")

    if len(statements) < 2:
        print("Not enough statements yet. Process more videos first.")
        return

    # find candidates
    print("\nFinding candidates...")
    candidates = find_contradiction_candidates(
        statements,
        similarity_threshold=0.65,
        min_gap_days=180,
        max_candidates=50
    )
    print(f"Candidates to check: {len(candidates)}")

    if not candidates:
        print("No candidates found. Try processing more videos.")
        return

    # classify each candidate
    contradictions_found = 0
    for i, candidate in enumerate(candidates):
        print(f"\nChecking candidate {i+1}/{len(candidates)}...")

        sa = candidate['statement_a']
        sb = candidate['statement_b']

        result = classify_contradiction(
            statement_a={
                'text':        sa['text'],
                'date':        sa['statement_date'],
                'video_title': sa.get('title', 'Speech'),
            },
            statement_b={
                'text':        sb['text'],
                'date':        sb['statement_date'],
                'video_title': sb.get('title', 'Speech'),
            }
        )

        if result:
            add_contradiction(
                statement_a_id=sa['id'],
                statement_b_id=sb['id'],
                classification=result['classification'],
                confidence=result['confidence'],
                explanation=result['explanation'],
                severity=result['severity']
            )
            contradictions_found += 1
            print(f"  ✓ {result['classification']} — {result['explanation'][:60]}...")
        else:
            print(f"  — No contradiction")

    print(f"\nContradictions found and stored: {contradictions_found}")


if __name__ == "__main__":
    # initialize DB
    init_db()

    # ── Add a politician ──────────────────────────────────────
    print("\nAdding politician...")
    politician_id = add_politician(
        name="Arvind Kejriwal",
        party="AAP",
        channel_url="https://www.youtube.com/@ArvindKejriwal"
    )
    print(f"Politician ID: {politician_id}")

    # ── Process videos ────────────────────────────────────────
    # Add real YouTube URLs here — speeches from different years
    videos = [
        "https://www.youtube.com/watch?v=ExvEIOWB-H0",  # replace with real speeches
    ]

    for url in videos:
        process_video(url, politician_id, "Arvind Kejriwal")

    # ── Run contradiction detection ───────────────────────────
    run_contradiction_detection(politician_id, "Arvind Kejriwal")