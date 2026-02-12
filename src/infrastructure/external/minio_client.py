from __future__ import annotations

import io
import anyio
from minio import Minio


class MinioClient:
    """
    Async-обертка над minio.Minio.
    Если задан presigned_endpoint — создается отдельный клиент для генерации presigned URL
    с этим хостом (чтобы ссылки открывались в браузере). Внутренние операции используют endpoint.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool,
        presigned_endpoint: str | None = None,
    ) -> None:
        self._client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        # Для presigned URL нужен клиент с public_endpoint, чтобы подпись была правильной
        # Но этот endpoint должен быть доступен из контейнера (например host.docker.internal:9000)
        self._presigned_client = (
            Minio(
                presigned_endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
            )
            if presigned_endpoint
            else None
        )
        self._secure = secure

    async def ensure_bucket(self, bucket: str) -> None:
        await anyio.to_thread.run_sync(self._ensure_bucket_sync, bucket)

    async def upload_bytes(
        self,
        bucket: str,
        object_name: str,
        data: bytes,
        content_type: str | None = None,
    ) -> None:
        await anyio.to_thread.run_sync(
            self._put_object_sync,
            bucket,
            object_name,
            data,
            content_type,
        )

    async def download_bytes(self, bucket: str, object_name: str) -> bytes:
        return await anyio.to_thread.run_sync(self._get_object_sync, bucket, object_name)

    async def delete_object(self, bucket: str, object_name: str) -> None:
        await anyio.to_thread.run_sync(self._client.remove_object, bucket, object_name)

    async def presigned_get_url(self, bucket: str, object_name: str) -> str:
        # Используем presigned_client если задан (для правильной подписи с нужным хостом)
        # Иначе используем основной клиент
        client = self._presigned_client if self._presigned_client is not None else self._client
        return await anyio.to_thread.run_sync(client.presigned_get_object, bucket, object_name)

    def _ensure_bucket_sync(self, bucket: str) -> None:
        if not self._client.bucket_exists(bucket):
            self._client.make_bucket(bucket)

    def _put_object_sync(
        self,
        bucket: str,
        object_name: str,
        data: bytes,
        content_type: str | None,
    ) -> None:
        self._ensure_bucket_sync(bucket)
        stream = io.BytesIO(data)
        self._client.put_object(
            bucket,
            object_name,
            stream,
            length=len(data),
            content_type=content_type or "application/octet-stream",
        )

    def _get_object_sync(self, bucket: str, object_name: str) -> bytes:
        response = self._client.get_object(bucket, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

