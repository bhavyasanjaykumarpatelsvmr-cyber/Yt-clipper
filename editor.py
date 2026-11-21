from pathlib import Path
import subprocess


def render_clip(
    video_path: str,
    start: float,
    end: float,
    output_path: str,
    mode: str = "crop",
    preset: str = "veryfast",
    crf: int = 23,
) -> Path:
    src = Path(video_path)
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    duration = max(1.0, round(float(end) - float(start), 2))

    if mode == "blur":
        filter_args = [
            "-filter_complex",
            (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,boxblur=20:2[bg];"
                "[0:v]scale=1080:-2[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1"
            ),
        ]
    else:
        filter_args = [
            "-vf",
            "crop=ih*9/16:ih,scale=1080:1920,setsar=1",
        ]

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start),
        "-i",
        str(src),
        "-t",
        str(duration),
        *filter_args,
        "-c:v",
        "libx264",
        "-preset",
        preset,
        "-crf",
        str(crf),
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        str(out),
    ]

    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return out


def render_all_clips(
    video_path: str,
    video_id: str,
    clips: list[dict],
    output_dir: str = "output",
    mode: str = "crop",
) -> list[dict]:
    rendered = []
    base_dir = Path(output_dir) / video_id
    base_dir.mkdir(parents=True, exist_ok=True)

    for idx, clip in enumerate(clips, start=1):
        out_file = base_dir / f"short_{idx:02d}.mp4"
        render_clip(
            video_path=video_path,
            start=clip["start"],
            end=clip["end"],
            output_path=str(out_file),
            mode=mode,
        )
        rendered.append({**clip, "file_path": str(out_file)})

    return rendered
