import yt_dlp
import os
from datetime import datetime


def download_audio(youtube_url: str, politician_id: int, output_dir: str = "data/audio") -> dict:
    """
    Downloads audio from a YouTube video and returns metadata.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Pre-check if audio already exists to skip download
    ydl_opts_meta = {
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': {'js_runtimes': ['nodejs']}},
    }
    with yt_dlp.YoutubeDL(ydl_opts_meta) as ydl:
        info = ydl.extract_info(youtube_url, download=False)
        video_id = info['id']
        expected_audio_path = f"{output_dir}/{politician_id}_{video_id}.mp3"
        
        if os.path.exists(expected_audio_path):
            print(f"Audio file already exists, skipping download: {expected_audio_path}")
            raw_date = info.get('upload_date', '19700101')
            upload_date = datetime.strptime(raw_date, '%Y%m%d').strftime('%Y-%m-%d')
            return {
                'video_id':    video_id,
                'title':       info['title'],
                'upload_date': upload_date,
                'duration':    info.get('duration', 0),
                'audio_path':  expected_audio_path,
                'url':         youtube_url,
            }

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_dir}/{politician_id}_%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '128',
        }],
        'quiet': False,
        'no_warnings': False,
        'extractor_args': {'youtube': {'js_runtimes': ['nodejs']}},
        'socket_timeout': 30,      # timeout after 30 seconds
        'retries': 2,              # retry twice then give up
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=True)

        # parse upload date from YYYYMMDD string to proper date
        raw_date = info.get('upload_date', '19700101')
        upload_date = datetime.strptime(raw_date, '%Y%m%d').strftime('%Y-%m-%d')

        return {
            'video_id':    info['id'],
            'title':       info['title'],
            'upload_date': upload_date,
            'duration':    info.get('duration', 0),
            'audio_path':  f"{output_dir}/{politician_id}_{info['id']}.mp3",
            'url':         youtube_url,
        }



def get_channel_videos(channel_url: str, max_videos: int = 20) -> list:
    """
    Returns a list of video metadata from a politician's YouTube channel.
    Does NOT download — just fetches the list.
    """
    ydl_opts = {
        'extract_flat': True,
        'playlistend':  max_videos,
        'quiet':        True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)

        return [
            {
                'url':   f"https://youtube.com/watch?v={entry['id']}",
                'title': entry.get('title', 'Unknown'),
                'id':    entry['id'],
            }
            for entry in info.get('entries', [])
            if entry and entry.get('id')
        ]