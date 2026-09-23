import pytest

from src.auth.config import AuthSettings, build_auth_config


def test_auth_settings_defaults():
    settings = AuthSettings()
    assert settings.jwt_issuer == "https://identity.cloudforge.internal"
    # Contract v1 §2: platform-wide audience, not "cloudforge-ingest-studio"
    assert settings.jwt_audience == "cloudforge-platform"


def test_build_auth_config_matches_contract_v1():
    config = build_auth_config()
    # RS256-only is enforced by AuthConfig itself (raises otherwise),
    # so successfully constructing it here already proves compliance;
    # this assertion just documents the expectation.
    assert config.algorithms == ("RS256",)
    assert config.issuer == "https://identity.cloudforge.internal"
    assert config.audience == "cloudforge-platform"
