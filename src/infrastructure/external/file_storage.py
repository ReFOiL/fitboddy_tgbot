from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from src.infrastructure.external.minio_client import MinioClient


class VideoValidationError(ValueError):
    pass


@dataclass(slots=True)
class VideoFileStorage:
    """
    Сервис для хранения видео упражнений в MinIO.

    Хранит видео как объект (key) в bucket, наружу отдает presigned URL.
    """

    client: MinioClient
    bucket: str
    prefix: str = "videos/"
    max_size_bytes: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: frozenset[str] = frozenset({".mp4", ".mov"})

    async def upload_video(self, filename: str, data: bytes) -> str:
        """
        Загружает видео и возвращает object_name (ключ).
        """
        ext = self._validate(filename, data)
        object_name = f"{self.prefix}{uuid4().hex}{ext}"
        await self.client.upload_bytes(
            bucket=self.bucket,
            object_name=object_name,
            data=data,
            content_type=self._content_type(ext),
        )
        return object_name

    async def get_video_url(self, object_name: str) -> str:
        return await self.client.presigned_get_url(bucket=self.bucket, object_name=object_name)

    async def delete_video(self, object_name: str) -> None:
        await self.client.delete_object(bucket=self.bucket, object_name=object_name)

    def _validate(self, filename: str, data: bytes) -> str:
        if len(data) > self.max_size_bytes:
            raise VideoValidationError("Видео слишком большое (макс 50MB).")
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise VideoValidationError("Неверный формат видео (разрешены .mp4, .mov).")
        return ext

    def _content_type(self, ext: str) -> str:
        return "video/mp4" if ext == ".mp4" else "video/quicktime"

