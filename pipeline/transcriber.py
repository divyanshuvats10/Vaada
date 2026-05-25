import json
import os
os.environ["CT2_CUDA_ALLOCATOR"] = "cub_caching"
from dotenv import load_dotenv
load_dotenv()
import torch
from faster_whisper import WhisperModel

_model = None

def get_model():
    global _model
    if _model is None:
        model_size = os.getenv("WHISPER_MODEL", "small")
        print(f"Loading Whisper model '{model_size}' on GPU...")
        _model = WhisperModel(model_size, device="cuda", compute_type="float16")
        print("Whisper model loaded ✓")
    return _model


def transcribe_with_cache(audio_path: str) -> dict:
    """
    Transcribes audio file and caches result as JSON.
    On second call with same file, loads from cache instantly.
    """
    cache_path = audio_path.replace('data/audio', 'data/transcripts').replace('.mp3', '_transcript.json')
    os.makedirs('data/transcripts', exist_ok=True)

    if os.path.exists(cache_path):
        print(f"Loading transcript from cache: {cache_path}")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    print(f"Transcribing: {audio_path}")
    model = get_model()

    segments, info = model.transcribe(
        audio_path,
        language=None,        # auto-detect — handles Hinglish better
        task="transcribe",
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        word_timestamps=True,
        beam_size=5,          # better accuracy
    )

    result = {
        'language': info.language,
        'duration': info.duration,
        'segments': [
            {
                'text':  segment.text.strip(),
                'start': round(segment.start, 2),
                'end':   round(segment.end, 2),
            }
            for segment in segments
        ]
    }

    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Transcript saved to cache: {cache_path}")

    # free GPU memory after transcription
    del model
    global _model
    _model = None
    torch.cuda.empty_cache()

    return result