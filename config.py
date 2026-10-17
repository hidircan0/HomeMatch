import os
from pathlib import Path


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://homematch:homematch_dev@db:5432/homematch"
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "local-only-change-this-secret")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "uploads"))
    upload_public_url: str = os.getenv("UPLOAD_PUBLIC_URL", "http://localhost:8000/uploads")


settings = Settings()
