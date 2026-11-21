from pathlib import Path
import yt_dlp

MIN_DURATION_SEC = 10
MAX_DURATION_SEC = 5 * 3600  # 18,000 seconds (5 hours)


class VideoDurationError(ValueError):
    """Raised when a video is shorter than MIN_DURATION_SEC or longer than MAX_DURATION_SEC."""


def validate_duration(duration: int | float | None) -> int:
    if duration is None:
        raise VideoDurationError("Could not determine video duration.")
    sec = int(duration)
    if sec < MIN_DURATION_SEC:
        raise VideoDurationError(
            f"Video is too short ({sec}s). Minimum allowed length is {MIN_DURATION_SEC}s."
        )
    if sec > MAX_DURATION_SEC:
        raise VideoDurationError(
            f"Video is too long ({sec}s). Maximum allowed length is {MAX_DURATION_SEC}s (5 hours)."
        )
    return sec


def download_video(
    url: str,
    cache_dir: str = "cache",
    min_duration: int = MIN_DURATION_SEC,
    max_duration: int = MAX_DURATION_SEC,
) -> dict:
    out_dir = Path(cache_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # First fetch metadata without downloading so we enforce duration limits early
    probe_opts = {
        "noplaylist": True,
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(probe_opts) as ydl:
        probe_info = ydl.extract_info(url, download=False)
        duration = int(probe_info.get("duration") or 0)
        if duration < min_duration:
            raise VideoDurationError(
                f"Video is too short ({duration}s). Minimum allowed length is {min_duration}s."
            )
        if duration > max_duration:
            raise VideoDurationError(
                f"Video is too long ({duration}s). Maximum allowed length is {max_duration}s (5 hours)."
            )

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(out_dir / "%(id)s.%(ext)s"),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        video_id = info["id"]
        file_path = out_dir / f"{video_id}.mp4"

        return {
            "id": video_id,
            "title": info.get("title", ""),
            "duration": int(info.get("duration") or duration),
            "path": str(file_path),
        }
