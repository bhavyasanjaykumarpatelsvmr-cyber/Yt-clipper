from pathlib import Path


def upload_short(
    file_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    client_secrets_file: str = "client_secrets.json",
) -> str | None:
    """Optional YouTube uploader stub when OAuth client_secrets.json is present."""
    if not Path(client_secrets_file).exists():
        return None
    if not Path(file_path).exists():
        raise FileNotFoundError(f"Rendered clip not found: {file_path}")
    return None
