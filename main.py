import argparse
import json
from pathlib import Path

from clipper.downloader import download_video
from clipper.transcriber import transcribe_video
from clipper.highlight_ai import generate_highlights
from clipper.editor import render_all_clips


def main():
    parser = argparse.ArgumentParser(
        description="Automated AI YouTube Shorts Clipper & Uploader (10s min - 5h max)"
    )
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--clips", type=int, default=3, help="Number of Shorts to generate (default: 3)")
    parser.add_argument("--mode", choices=["crop", "blur"], default="crop", help="9:16 framing mode")
    parser.add_argument("--upload", action="store_true", help="Automatically upload clips to YouTube")
    parser.add_argument(
        "--privacy",
        choices=["private", "unlisted", "public"],
        default="private",
        help="YouTube upload privacy status (default: private)",
    )
    args = parser.parse_args()

    print("[1/5] Downloading video (validating 10s - 5h duration)...")
    video = download_video(args.url)
    print(f"      Downloaded: {video['title']} ({video['duration']}s)")

    print("[2/5] Generating timestamped transcript...")
    try:
        transcript = transcribe_video(video["path"])
    except Exception as e:
        print(f"      Transcription API skipped ({e}); using fallback segmentation.")
        transcript = []

    print(f"[3/5] Selecting up to {args.clips} highlight clips & generating metadata...")
    clips = generate_highlights(
        transcript=transcript,
        video_title=video["title"],
        duration_sec=video["duration"],
        num_clips=args.clips,
    )

    print("[4/5] Rendering vertical 9:16 Shorts with FFmpeg...")
    rendered = render_all_clips(
        video_path=video["path"],
        video_id=video["id"],
        clips=clips,
        mode=args.mode,
    )

    meta_file = Path("output") / video["id"] / "metadata.json"
    meta_file.write_text(json.dumps(rendered, indent=2), encoding="utf-8")
    print(f"      Saved clips & metadata to {meta_file.parent}")

    if args.upload:
        from clipper.uploader import upload_short

        print(f"[5/5] Uploading {len(rendered)} clip(s) to YouTube ({args.privacy})...")
        for idx, item in enumerate(rendered, start=1):
            res = upload_short(
                video_path=item["file_path"],
                title=item["title"],
                description=item["description"],
                tags=item["tags"],
                privacy_status=args.privacy,
            )
            print(f"      Clip {idx} uploaded: {res['url']}")
    else:
        print("[5/5] Skipping upload (pass --upload to publish to YouTube).")


if __name__ == "__main__":
    main()
