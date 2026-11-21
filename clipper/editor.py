import json
from pathlib import Path
import subprocess


def _render_single_clip(
    input_video: str,
    out_file: Path,
    start: float,
    end: float,
    mode: str = "crop",
) -> None:
    duration = max(1.0, float(end) - float(start))

    if mode == "blur":
        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:5[bg];"
            "[0:v]scale=1080:-2:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            input_video,
            "-filter_complex",
            vf,
            "-map",
            "[v]",
            "-map",
            "0:a?",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(out_file),
        ]
    else:
        vf = (
            "scale=-2:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,format=yuv420p"
        )
        cmd = [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-t",
            str(duration),
            "-i",
            input_video,
            "-vf",
            vf,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(out_file),
        ]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def render_all_clips(
    video_path: str,
    video_id: str,
    clips: list[dict],
    output_dir: str = "output",
    mode: str = "crop",
) -> list[dict]:
    """Render 9:16 vertical clips using FFmpeg and save metadata.json."""
    chosen_mode = mode if mode in ("crop", "blur") else "crop"
    target_dir = Path(output_dir) / video_id
    target_dir.mkdir(parents=True, exist_ok=True)

    rendered = []
    for idx, clip in enumerate(clips, start=1):
        out_path = target_dir / f"short_{idx:02d}.mp4"
        _render_single_clip(
            input_video=video_path,
            out_file=out_path,
            start=float(clip["start"]),
            end=float(clip["end"]),
            mode=chosen_mode,
        )
        record = {
            **clip,
            "file_path": str(out_path),
        }
        rendered.append(record)

    meta_path = target_dir / "metadata.json"
    meta_path.write_text(json.dumps(rendered, indent=2), encoding="utf-8")
    return rendered
