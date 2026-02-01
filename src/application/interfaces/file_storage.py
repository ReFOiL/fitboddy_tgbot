from __future__ import annotations

from typing import Protocol


class IFileStorage(Protocol):
    async def upload_file(self, bucket: str, name: str, data: bytes) -> None: ...
    async def get_presigned_url(self, bucket: str, name: str) -> str: ...

