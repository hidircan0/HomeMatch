from pathlib import Path

from config import settings


def public_image_url(object_key: str) -> str:
    return f"{settings.upload_public_url.rstrip('/')}/{object_key}"


def save_image(object_key: str, data: bytes) -> Path:
    path = settings.upload_dir / object_key
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def delete_image(object_key: str) -> None:
    path = settings.upload_dir / object_key
    path.unlink(missing_ok=True)
    parent = path.parent
    if parent.exists() and not any(parent.iterdir()):
        parent.rmdir()
