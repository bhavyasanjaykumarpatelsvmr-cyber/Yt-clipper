# AI YouTube Shorts Clipper

Free, open-source Python tool that takes a YouTube link (10 seconds to 5 hours), extracts highlights, generates titles, descriptions, and tags, renders 9:16 vertical Shorts with FFmpeg, and optionally uploads them to YouTube.

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env
python main.py "[https://youtu.be/VIDEO_ID](https://youtu.be/VIDEO_ID)" --clips 3
python main.py "[https://youtu.be/VIDEO_ID](https://youtu.be/VIDEO_ID)" --clips 3 --upload --privacy private
git init
git add .
git status
git commit -m "Initial commit: automated AI YouTube Shorts clipper and uploader"
git branch -M main
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/ai-yt-clipper.git
git push -u origin main
cd ~/ai-yt-clipper

cat << 'EOF' > README.md
# AI YouTube Shorts Clipper

Free, open-source Python tool that takes a YouTube link (10 seconds to 5 hours), extracts highlights, generates titles, descriptions, and tags, renders 9:16 vertical Shorts with FFmpeg, and optionally uploads them to YouTube.

## Setup

Make sure `ffmpeg` is installed on your system `PATH`, then install Python dependencies:

    pip install -r requirements.txt
    cp .env.example .env

## Usage

Generate vertical Shorts and metadata locally:

    python main.py "[https://youtu.be/VIDEO_ID](https://youtu.be/VIDEO_ID)" --clips 3

To auto-upload as private Shorts, place `client_secrets.json` (YouTube Data API v3 Desktop OAuth) in the project root and pass `--upload`:

    python main.py "[https://youtu.be/VIDEO_ID](https://youtu.be/VIDEO_ID)" --clips 3 --upload --privacy private
