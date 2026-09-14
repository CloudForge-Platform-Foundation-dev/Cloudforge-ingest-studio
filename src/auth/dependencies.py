from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.jwt import verify_jwt

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    """
    Validate token และ enforce authentication แบบ fail-closed จริง

    เดิมฟังก์ชันนี้เช็คแค่ "มี credentials ส่งมาไหม" แล้วคืน full-access
    user เสมอ ไม่ว่า token จะถูกต้องหรือไม่ — เป็นช่องโหว่ร้ายแรง (bearer
    token อะไรก็ได้ = full access) ตอนนี้เรียก verify_jwt() จริง ซึ่งตรวจ
    ลายเซ็นกับ JWKS (RS256), issuer, audience, และวันหมดอายุ ก่อนเชื่อถือ
    scope ที่อยู่ใน token
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = verify_jwt(credentials.credentials)  # raise HTTPException(401) เองถ้า token ไม่ถูกต้อง
    return {"sub": payload.get("sub"), "scopes": payload.get("scopes", [])}


def require_scope(required_scope: str):
    """Dependency factory to enforce required scope"""

    def dependency(user: dict = Depends(get_current_user)) -> dict:
        user_scopes = user.get("scopes", [])
        if required_scope not in user_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required scope: {required_scope}",
            )
        return user

    return dependency
