import json
import os

try:
    from google import genai
except Exception:
    genai = None


def _fallback_highlights(video_title: str, duration_sec: int, num_clips: int) -> list[dict]:
    """Deterministic fallback when Gemini API key is unavailable or returns non-JSON."""
    safe_duration = max(10, int(duration_sec))
    clip_len = min(55, max(15, safe_duration // max(1, num_clips)))
    clip_len = min(clip_len, safe_duration)

    if safe_duration <= clip_len:
        step = 0
    else:
        step = max(1, (safe_duration - clip_len) // max(1, num_clips - 1)) if num_clips > 1 else 0

    clips = []
    for i in range(num_clips):
        start = min(i * step, max(0, safe_duration - clip_len))
        end = min(safe_duration, start + clip_len)
        if end <= start:
            end = safe_duration
        clips.append({
            "start": float(start),
            "end": float(end),
            "title": f"{video_title[:65]} - Part {i + 1}",
            "description": f"Highlight clip #{i + 1} from {video_title}. #Shorts",
            "tags": ["shorts", "highlights", "clips"],
        })
    return clips


def generate_highlights(
    transcript: list[dict],
    video_title: str,
    duration_sec: int,
    num_clips: int = 3,
) -> list[dict]:
    """Select high-retention Short segments (15s-60s) with titles, descriptions, and tags."""
    num_clips = max(1, min(10, int(num_clips)))
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or genai is None:
        return _fallback_highlights(video_title, duration_sec, num_clips)

    transcript_text = "\n".join(
        f"[{seg.get('start', 0):.1f}s - {seg.get('end', 0):.1f}s] {seg.get('text', '')}"
        for seg in transcript[:250]
    ) or "(No transcript available; pick evenly spaced engaging moments.)"

    prompt = (
        f"You are creating {num_clips} engaging YouTube Shorts (each 15 to 60 seconds long, within 0s to {duration_sec}s) "
        f"from the video titled '{video_title}'.\n"
        f"Transcript:\n{transcript_text}\n\n"
        "Return ONLY a JSON array of objects with keys: "
        '"start" (number in seconds), "end" (number in seconds), "title" (string <= 90 chars), '
        '"description" (string with #Shorts), "tags" (list of 3-6 short strings).'
    )

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw = (response.text or "").strip()
        if raw.startswith("```"):
            raw = raw.strip("`")
            if raw.startswith("json"):
                raw = raw[4:].strip()
        parsed = json.loads(raw)
        if not isinstance(parsed, list) or not parsed:
            return _fallback_highlights(video_title, duration_sec, num_clips)

        results = []
        for idx, item in enumerate(parsed[:num_clips], start=1):
            start = max(0.0, min(float(item.get("start", 0.0)), float(max(0, duration_sec - 1))))
            end = max(start + 5.0, min(float(item.get("end", start + 30.0)), float(duration_sec)))
            if end <= start:
                end = min(float(duration_sec), start + 15.0)
            results.append({
                "start": round(start, 2),
                "end": round(end, 2),
                "title": str(item.get("title") or f"{video_title[:65]} - Clip {idx}")[:95],
                "description": str(item.get("description") or f"{video_title} #Shorts"),
                "tags": [str(t) for t in (item.get("tags") or ["shorts", "clip"])][:8],
            })
        return results
    except Exception:
        return _fallback_highlights(video_title, duration_sec, num_clips)
