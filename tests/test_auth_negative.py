import pytest
from fastapi import HTTPException

from src.auth.dependencies import get_current_user


class _FakeCredentials:
    def __init__(self, token: str):
        self.credentials = token


def test_get_current_user_rejects_malformed_token():
    """
    Regression coverage for the original vulnerability: previously any
    bearer token (even garbage) was accepted as a full-access user.
    get_current_user must now reject it with 401 via cloudforge_auth_core.
    """
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=_FakeCredentials("invalid.token.string"))
    assert exc_info.value.status_code == 401


def test_get_current_user_rejects_missing_credentials():
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(credentials=None)
    assert exc_info.value.status_code == 401
