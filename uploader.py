from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def get_youtube_service(
    client_secrets_file: str = "client_secrets.json",
    token_file: str = "token.json",
):
    secrets_path = Path(client_secrets_file)
    if not secrets_path.exists():
        raise FileNotFoundError(
            f"Missing '{client_secrets_file}'. Download your OAuth Desktop App JSON "
            "from Google Cloud Console (YouTube Data API v3) and save it in the repo root."
        )

    creds = None
    token_path = Path(token_file)
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
            creds = flow.run_local_server(port=0, open_browser=False)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy_status: str = "private",
    category_id: str = "22",
    client_secrets_file: str = "client_secrets.json",
    token_file: str = "token.json",
) -> dict:
    youtube = get_youtube_service(
        client_secrets_file=client_secrets_file,
        token_file=token_file,
    )

    clean_desc = description.strip()
    if "#shorts" not in clean_desc.lower():
        clean_desc = f"{clean_desc}\n\n#Shorts".strip()

    body = {
        "snippet": {
            "title": title[:100],
            "description": clean_desc[:5000],
            "tags": (tags or [])[:15],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(
        video_path,
        mimetype="video/mp4",
        chunksize=1024 * 1024 * 4,
        resumable=True,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    while response is None:
        _, response = request.next_chunk()

    video_id = response["id"]
    return {
        "video_id": video_id,
        "url": f"https://youtube.com/shorts/{video_id}",
        "privacy": privacy_status,
    }
