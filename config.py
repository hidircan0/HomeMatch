import os


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://homematch:homematch_dev@db:5432/homematch"
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "local-only-change-this-secret")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    s3_endpoint_url: str = os.getenv("S3_ENDPOINT_URL", "http://minio:9000")
    s3_public_url: str = os.getenv("S3_PUBLIC_URL", "http://localhost:9000")
    s3_access_key: str = os.getenv("S3_ACCESS_KEY", "homematch")
    s3_secret_key: str = os.getenv("S3_SECRET_KEY", "homematch_local_secret")
    s3_bucket: str = os.getenv("S3_BUCKET", "homematch-images")


settings = Settings()
