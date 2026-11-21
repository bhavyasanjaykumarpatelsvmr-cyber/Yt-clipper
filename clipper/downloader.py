from pathlib import Path
import re
import yt_dlp

MIN_DURATION_SEC = 10
MAX_DURATION_SEC = 5 * 3600  # 18,000 seconds (5 hours)


def _extract_video_id(url: str, info: dict) -> str:
    if info.get("id"):
        return re.sub(r"[^A-Za-z0-9_-]", "", str(info["id"])) or "video"
    match = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{6,})", url)
    return match.group(1) if match else "video"


def download_video(url: str, cache_dir: str = "cache") -> dict:
    """Download a YouTube video (10s to 5h) and return metadata + local file path."""
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)

    duration = info.get("duration")
    if duration is None:
        raise ValueError("Could not determine video duration.")
    duration = int(duration)
    if duration < MIN_DURATION_SEC or duration > MAX_DURATION_SEC:
        raise ValueError(
            f"Video duration ({duration}s) must be between {MIN_DURATION_SEC}s and {MAX_DURATION_SEC}s (5 hours)."
        )

    video_id = _extract_video_id(url, info)
    out_template = str(cache_path / f"{video_id}.%(ext)s")

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": out_template,
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        downloaded = ydl.extract_info(url, download=True)
        file_path = Path(ydl.prepare_filename(downloaded))
        if not file_path.exists():
            mp4_candidate = cache_path / f"{video_id}.mp4"
            if mp4_candidate.exists():
                file_path = mp4_candidate

    return {
        "id": video_id,
        "title": info.get("title") or f"YouTube Video {video_id}",
        "duration": duration,
        "path": str(file_path),
    }
