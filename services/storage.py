import boto3
from botocore.client import Config

from config import settings


def s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
        region_name="us-east-1",
    )


def public_image_url(object_key: str) -> str:
    return f"{settings.s3_public_url.rstrip('/')}/{settings.s3_bucket}/{object_key}"
