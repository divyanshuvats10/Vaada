import yt_dlp
import os
from datetime import datetime


def download_audio(youtube_url: str, politician_id: int, output_dir: str = "data/audio") -> dict:
    """
    Downloads audio from a YouTube video and returns metadata.
    """
    os.makedirs(output_dir, exist_ok=True)

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
        'extractor_args': {
            'youtube': {
                'js_runtimes': ['nodejs:C:\\Program Files\\nodejs\\node.exe']
            }
        },
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