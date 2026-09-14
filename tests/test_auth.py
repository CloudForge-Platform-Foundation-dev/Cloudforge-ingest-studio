import pytest
from fastapi import HTTPException
from src.auth.config import AuthSettings

def test_auth_settings_defaults():
    settings = AuthSettings()
    assert settings.jwt_issuer == "https://auth.cloudforge.internal"
    assert settings.jwt_audience == "cloudforge-ingest-studio"
    assert "RS256" in settings.jwt_algorithms
