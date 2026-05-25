import re

FILLER_WORDS = [
    "umm", "uh", "aah", "matlab", "basically", "actually",
    "you know", "toh", "woh", "matlab ki", "yaani", "theek hai",
    "achha", "haan", "dekho", "suniye", "bhai"
]

def clean_text(text: str) -> str:
    """Remove fillers, fix repetition, normalize whitespace."""
    for filler in FILLER_WORDS:
        text = re.sub(rf'\b{filler}\b', '', text, flags=re.IGNORECASE)

    # remove repeated words (e.g. "aur aur aur")
    text = re.sub(r'\b(\w+)( \1){2,}\b', r'\1', text)

    # normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def chunk_by_time(segments: list, chunk_duration: int = 45) -> list:
    """
    Groups transcript segments into ~45 second chunks.
    45 seconds ≈ one complete political thought.
    Returns chunks with start/end timestamps and YouTube deep link offset.
    """
    chunks = []
    current_segments = []
    chunk_start = 0.0

    for seg in segments:
        current_segments.append(seg)
        duration = seg['end'] - chunk_start

        if duration >= chunk_duration:
            text = ' '.join(s['text'] for s in current_segments)
            text = clean_text(text)

            if len(text) > 50:  # skip chunks that are too short to be meaningful
                chunks.append({
                    'text':       text,
                    'start_time': round(chunk_start, 2),
                    'end_time':   round(seg['end'], 2),
                    'yt_offset':  int(chunk_start),  # integer seconds for YouTube URL
                })

            current_segments = []
            chunk_start = seg['end']

    # don't lose the final chunk
    if current_segments:
        text = ' '.join(s['text'] for s in current_segments)
        text = clean_text(text)
        if len(text) > 50:
            chunks.append({
                'text':       text,
                'start_time': round(chunk_start, 2),
                'end_time':   round(current_segments[-1]['end'], 2),
                'yt_offset':  int(chunk_start),
            })

    return chunks


def make_youtube_url(video_id: str, offset_seconds: int) -> str:
    """Creates a deep link to exact timestamp in a YouTube video."""
    return f"https://youtube.com/watch?v={video_id}&t={offset_seconds}s"