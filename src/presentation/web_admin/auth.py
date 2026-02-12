import structlog

from fastapi import Header, HTTPException, status

logger = structlog.get_logger()


def verify_admin_token(token: str) -> bool:
    return bool(token)


def get_current_admin(
    x_admin_token: str | None = Header(default=None, alias="x-admin-token"),
) -> str:
    if not x_admin_token or not verify_admin_token(x_admin_token):
        logger.warning("admin.auth.failed", has_token=bool(x_admin_token))
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")
    return x_admin_token

