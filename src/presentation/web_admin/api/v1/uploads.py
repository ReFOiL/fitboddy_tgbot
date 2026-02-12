"""API v1: загрузка и просмотр видео для упражнений."""
from __future__ import annotations

import structlog

from fastapi import APIRouter, Depends, File, Header, HTTPException, Query, Response, UploadFile, status
from dependency_injector.wiring import Provide, inject
from pydantic import BaseModel

from src.infrastructure.external.file_storage import VideoFileStorage, VideoValidationError
from src.presentation.web_admin.auth import get_current_admin, verify_admin_token
from src.shared.di.containers import Container

logger = structlog.get_logger()

router = APIRouter()


class VideoUploadOut(BaseModel):
    object_key: str


@router.post("/uploads/video", response_model=VideoUploadOut)
@inject
async def upload_video(
    file: UploadFile = File(...),
    _admin: str = Depends(get_current_admin),
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
    x_admin_token: str | None = Header(default=None, alias="x-admin-token"),
    token: str | None = Query(default=None, description="Admin token (for video src requests)"),
    video_storage: VideoFileStorage = Depends(Provide[Container.video_file_storage]),
) -> Response:
    """
    Прокси для просмотра видео из MinIO.
    Вместо presigned URL отдаем ссылку на наш бэкенд, который проксирует запрос.
    Токен можно передать через заголовок x-admin-token или query параметр token.
    """
    # Проверяем токен из заголовка или query параметра
    admin_token = x_admin_token or token
    if not admin_token or not verify_admin_token(admin_token):
        logger.warning("admin.video.auth_failed", has_header_token=bool(x_admin_token), has_query_token=bool(token))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")
    
    if not object_key.startswith("videos/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid object key")
    try:
        data = await video_storage.client.download_bytes(bucket=video_storage.bucket, object_name=object_key)
        # Определяем content-type по расширению
        content_type = "video/mp4" if object_key.endswith(".mp4") else "video/quicktime"
        logger.info("admin.video.proxied", object_key=object_key, size_bytes=len(data))
        return Response(content=data, media_type=content_type)
    except Exception as e:
        logger.error("admin.video.proxy_failed", object_key=object_key, error=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Video not found")
