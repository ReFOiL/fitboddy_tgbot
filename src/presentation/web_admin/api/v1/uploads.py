"""API v1: загрузка и просмотр видео для упражнений."""
from __future__ import annotations

import structlog

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Response, UploadFile, status
from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from src.infrastructure.external.file_storage import VideoFileStorage, VideoValidationError
from src.presentation.web_admin.auth import AdminPrincipal, decode_bearer_token, get_current_admin
from src.shared.di.containers import Container

logger = structlog.get_logger()

router = APIRouter()


class VideoUploadOut(BaseModel):
    object_key: str


@router.post("/uploads/video", response_model=VideoUploadOut)
@inject
async def upload_video(
    file: UploadFile = File(...),
    _admin: AdminPrincipal = Depends(get_current_admin),
    video_storage: VideoFileStorage = Depends(Provide[Container.video_file_storage]),
) -> VideoUploadOut:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )
    try:
        data = await file.read()
    except Exception as e:
        logger.error("admin.video.upload_read_failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to read file: {e!s}",
        )
    try:
        object_key = await video_storage.upload_video(file.filename, data)
        logger.info(
            "admin.video.uploaded",
            filename=file.filename,
            object_key=object_key,
            size_bytes=len(data),
        )
    except VideoValidationError as e:
        logger.warning("admin.video.upload_validation_failed", filename=file.filename, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return VideoUploadOut(object_key=object_key)


@router.get("/videos/{object_key:path}")
@inject
async def get_video(
    object_key: str,
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None, alias="x-admin-token"),
    token: str | None = Query(default=None, description="JWT access token (for <video src>)"),
    video_storage: VideoFileStorage = Depends(Provide[Container.video_file_storage]),
) -> Response:
    """
    Прокси для просмотра видео из MinIO.
    JWT: заголовок Authorization: Bearer …, либо x-admin-token / query token (сырой JWT).
    """
    raw: str | None = None
    if authorization and authorization.lower().startswith("bearer "):
        raw = authorization[7:].strip()
    raw = raw or x_admin_token or token
    if not raw:
        logger.warning("admin.video.auth_failed", reason="missing_token")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Missing token")
    try:
        decode_bearer_token(raw)
    except HTTPException:
        raise

    if not object_key.startswith("videos/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid object key")
    try:
        data = await video_storage.client.download_bytes(bucket=video_storage.bucket, object_name=object_key)
        content_type = "video/mp4" if object_key.endswith(".mp4") else "video/quicktime"
        logger.info("admin.video.proxied", object_key=object_key, size_bytes=len(data))
        return Response(content=data, media_type=content_type)
    except Exception as e:
        logger.error("admin.video.proxy_failed", object_key=object_key, error=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
