from __future__ import annotations

import anyio
from minio import Minio

from src.application.interfaces.file_storage import IFileStorage


class MinioStorage(IFileStorage):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool) -> None:
        self._client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)

    async def upload_file(self, bucket: str, name: str, data: bytes) -> None:
        await anyio.to_thread.run_sync(self._put_object, bucket, name, data)

    async def get_presigned_url(self, bucket: str, name: str) -> str:
        return await anyio.to_thread.run_sync(self._client.presigned_get_object, bucket, name)

    def _put_object(self, bucket: str, name: str, data: bytes) -> None:
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)
        self._client.put_object(bucket, name, data, length=len(data))

