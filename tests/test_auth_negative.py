import pytest
from fastapi import HTTPException
from src.auth.jwt import verify_jwt

def test_verify_jwt_malformed():
    with pytest.raises(HTTPException) as exc_info:
        verify_jwt("invalid.token.string")
    assert exc_info.value.status_code == 401
