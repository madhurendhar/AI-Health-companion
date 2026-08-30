"""Object storage: S3 if credentials exist, else local filesystem. Never stores patient history."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class ObjectStore:
    def put_bytes(self, key: str, data: bytes) -> None:
        raise NotImplementedError

    def get_bytes(self, key: str) -> bytes | None:
        raise NotImplementedError

    def backend_name(self) -> str:
        raise NotImplementedError


class LocalObjectStore(ObjectStore):
    def __init__(self, root: str | None = None):
        self.root = Path(root or os.getenv("LOCAL_S3_DIR", "data/local_s3"))
        self.root.mkdir(parents=True, exist_ok=True)

    def put_bytes(self, key: str, data: bytes) -> None:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def get_bytes(self, key: str) -> bytes | None:
        path = self.root / key
        if not path.exists():
            return None
        return path.read_bytes()

    def backend_name(self) -> str:
        return "local_filesystem_fallback"


class S3ObjectStore(ObjectStore):
    def __init__(self):
        import boto3

        self.bucket = os.environ["S3_BUCKET"]
        self.prefix = os.getenv("S3_PREFIX", "companion/")
        self.client = boto3.client(
            "s3",
            region_name=os.getenv("AWS_REGION") or None,
        )

    def put_bytes(self, key: str, data: bytes) -> None:
        self.client.put_object(Bucket=self.bucket, Key=self.prefix + key, Body=data)

    def get_bytes(self, key: str) -> bytes | None:
        try:
            obj = self.client.get_object(Bucket=self.bucket, Key=self.prefix + key)
            return obj["Body"].read()
        except Exception:
            return None

    def backend_name(self) -> str:
        return "s3"


def build_store() -> ObjectStore:
    if os.getenv("S3_BUCKET") and os.getenv("AWS_ACCESS_KEY_ID"):
        try:
            return S3ObjectStore()
        except Exception:
            return LocalObjectStore()
    return LocalObjectStore()
