import base64
import json
import os
from pathlib import Path
import subprocess
import urllib.request


def extract_audio(video_path: str, audio_dir: str = "cache/audio") -> Path:
    src = Path(video_path)
    out_dir = Path(audio_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_path = out_dir / f"{src.stem}.mp3"

    if not audio_path.exists():
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(src),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-b:a",
            "48k",
            str(audio_path),
        ]
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    return audio_path


def transcribe_video(video_path: str, model_name: str = "gemini-3.8-flash") -> list[dict]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.startswith("paste-your-real"):
        raise RuntimeError(
            "Set a real GEMINI_API_KEY first: export GEMINI_API_KEY='your_real_key'"
        )

    audio_path = extract_audio(video_path)
    audio_b64 = base64.b64encode(audio_path.read_bytes()).decode("ascii")

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={api_key}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": "audio/mpeg",
                            "data": audio_b64,
                        }
                    },
                    {
                        "text": (
                            "Transcribe this audio accurately with timestamps in seconds. "
                            "Return ONLY a valid JSON list of objects with keys: "
                            "'start' (float), 'end' (float), and 'text' (string)."
                        )
                    },
                ]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
    data = json.loads(raw_text)

    transcript = []
    for item in data:
        text = str(item.get("text", "")).strip()
        if text:
            transcript.append(
                {
                    "start": round(float(item.get("start", 0.0)), 2),
                    "end": round(float(item.get("end", 0.0)), 2),
                    "text": text,
                }
            )
    return transcript
