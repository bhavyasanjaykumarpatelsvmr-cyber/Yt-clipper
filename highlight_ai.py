import json
import os
import re
import urllib.error
import urllib.request

DEFAULT_API_KEY = ""


def _fallback_highlights(
    transcript: list[dict],
    video_title: str,
    duration_sec: int,
    num_clips: int = 3,
) -> list[dict]:
    """Free offline fallback so clipping and metadata generation can be tested without an API key."""
    if not transcript:
        start = 0.0
        end = min(float(duration_sec), 30.0)
        return [
            {
                "start": start,
                "end": max(end, 1.0),
                "title": f"{video_title[:75]} - Short Clip 1",
                "description": f"Highlight clip from {video_title}. #shorts #clips",
                "tags": ["shorts", "clips", "highlights", "trending", "viral"],
            }
        ][:num_clips]

    words = re.findall(r"[A-Za-z0-9]{3,}", " ".join(seg.get("text", "") for seg in transcript).lower())
    freq: dict[str, int] = {}
    stop = {"the", "and", "for", "that", "with", "this", "from", "have", "you", "your", "are", "was", "but", "not"}
    for w in words:
        if w not in stop:
            freq[w] = freq.get(w, 0) + 1
    top_tags = [k for k, _ in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:7]] or ["shorts", "clip", "highlights"]

    clips = []
    step = max(1, len(transcript) // max(1, num_clips))
    for idx in range(num_clips):
        seg_idx = min(idx * step, len(transcript) - 1)
        seg = transcript[seg_idx]
        start = max(0.0, round(float(seg.get("start", 0.0)), 2))
        end = min(float(duration_sec), round(max(start + 20.0, float(seg.get("end", start + 30.0))), 2))
        if end <= start:
            continue
        snippet = str(seg.get("text", "")).strip()
        hook = (snippet[:65] + "...") if len(snippet) > 65 else (snippet or f"{video_title} Clip {idx + 1}")
        clips.append(
            {
                "start": start,
                "end": end,
                "title": hook[:100],
                "description": f"{snippet} — From {video_title}. #shorts #viral",
                "tags": top_tags[:10],
            }
        )
    return clips


def generate_highlights(
    transcript: list[dict],
    video_title: str,
    duration_sec: int,
    num_clips: int = 3,
    model_name: str = "gemini-3.8-flash",
    api_key: str | None = None,
    allow_fallback: bool = True,
) -> list[dict]:
    resolved_key = (api_key or os.getenv("GEMINI_API_KEY") or DEFAULT_API_KEY).strip()

    formatted_lines = [
        f"[{seg['start']}s - {seg['end']}s] {seg['text']}" for seg in transcript
    ]
    transcript_block = "\n".join(formatted_lines)

    prompt = (
        f"You are a viral YouTube Shorts editor.\n"
        f"Source video title: {video_title}\n"
        f"Total duration: {duration_sec} seconds.\n"
        f"Select up to {num_clips} high-retention, engaging moments (each ideally 15 to 60 seconds long) "
        f"that start and end cleanly near sentence/segment boundaries.\n\n"
        f"For each clip, return:\n"
        f"- start: float (seconds >= 0)\n"
        f"- end: float (seconds <= {duration_sec}, greater than start)\n"
        f"- title: string (catchy YouTube Short title, <= 90 chars)\n"
        f"- description: string (engaging short description with relevant hashtags)\n"
        f"- tags: list of 5 to 10 short keyword strings (no '#' symbols)\n\n"
        f"Return ONLY a valid JSON list of objects.\n\n"
        f"Transcript:\n{transcript_block}"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent"
    )

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": resolved_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
        items = json.loads(raw_text)

        cleaned = []
        for item in items:
            start = max(0.0, round(float(item.get("start", 0.0)), 2))
            end = min(float(duration_sec), round(float(item.get("end", start + 30.0)), 2))
            if end <= start:
                end = min(float(duration_sec), round(start + 30.0, 2))
            if end <= start:
                continue

            tags = [
                str(t).lstrip("#").strip()
                for t in (item.get("tags") or [])
                if str(t).strip()
            ][:12]

            cleaned.append(
                {
                    "start": start,
                    "end": end,
                    "title": str(item.get("title", "Highlight Clip")).strip()[:100],
                    "description": str(item.get("description", "")).strip(),
                    "tags": tags,
                }
            )

        if cleaned:
            return cleaned[:num_clips]

    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError) as e:
        if not allow_fallback:
            raise RuntimeError(f"Gemini request failed: {e}") from e

    return _fallback_highlights(transcript, video_title, duration_sec, num_clips=num_clips)
