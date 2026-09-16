import jwt
from jwt import PyJWKClient
from fastapi import HTTPException, status
from src.auth.config import auth_settings

jwks_client = PyJWKClient(auth_settings.jwt_jwks_uri)

def verify_jwt(token: str) -> dict:
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=auth_settings.jwt_algorithms,
            audience=auth_settings.jwt_audience,
            issuer=auth_settings.jwt_issuer,
            options={"verify_signature": True, "verify_exp": True, "verify_iss": True, "verify_aud": True}
        )
        return payload
    except Exception as e:
        # Log detailed error server-side only; never leak JWT/JWKS details to client
        import logging
        logging.getLogger(__name__).warning(
            "JWT validation failed: %s", e, exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
