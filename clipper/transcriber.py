import json
import os
from pathlib import Path
import subprocess
import tempfile

try:
    from google import genai
except Exception:
    genai = None


def _extract_audio_mp3(video_path: str, out_mp3: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-b:a",
        "64k",
        str(out_mp3),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def transcribe_video(video_path: str) -> list[dict]:
    """Transcribe video audio using Gemini API when GEMINI_API_KEY is set.

    Returns a list of segments: [{"start": float, "end": float, "text": str}, ...]
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key or genai is None:
        return []

    client = genai.Client(api_key=api_key)

    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = Path(tmpdir) / "audio.mp3"
        try:
            _extract_audio_mp3(video_path, audio_path)
            upload_target = audio_path
        except Exception:
            upload_target = Path(video_path)

        uploaded = client.files.upload(file=str(upload_target))
        prompt = (
            "Transcribe this media into chronological segments with approximate start and end times in seconds. "
            'Return ONLY valid JSON as a list of objects: [{"start": 0.0, "end": 12.5, "text": "..."}]'
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[uploaded, prompt],
        )
        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()

        try:
            data = json.loads(raw)
            if isinstance(data, list):
                cleaned = []
                for seg in data:
                    if isinstance(seg, dict) and "text" in seg:
                        cleaned.append({
                            "start": float(seg.get("start", 0.0)),
                            "end": float(seg.get("end", 0.0)),
                            "text": str(seg["text"]).strip(),
                        })
                return cleaned
        except Exception:
            pass

        return [{"start": 0.0, "end": 60.0, "text": raw}] if raw else []
