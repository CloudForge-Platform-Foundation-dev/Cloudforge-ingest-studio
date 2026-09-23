from pydantic_settings import BaseSettings, SettingsConfigDict

from cloudforge_auth_core import AuthConfig


class AuthSettings(BaseSettings):
    """
    Studio-local environment settings only. The shared shape/validation
    of these values (algorithm, claims, scope format) lives in
    cloudforge-auth-core per CloudForge Identity Contract v1 — this class
    must not re-implement any of that, only supply the per-Studio values.
    """

    model_config = SettingsConfigDict(env_prefix="CLOUDFORGE_", extra="ignore")

    jwt_issuer: str = "https://identity.cloudforge.internal"
    # Contract v1 §2: audience is platform-wide, not per-Studio.
    # NOTE: this changes the previous default ("cloudforge-ingest-studio").
    # The Identity Service must issue tokens with this audience before
    # deploying this change — see migration notes.
    jwt_audience: str = "cloudforge-platform"
    jwt_jwks_uri: str = "https://identity.cloudforge.internal/.well-known/jwks.json"
    jwt_jwks_cache_ttl_seconds: int = 3600


auth_settings = AuthSettings()


def build_auth_config() -> AuthConfig:
    """Translate Ingest's local settings into the shared AuthConfig."""
    return AuthConfig(
        issuer=auth_settings.jwt_issuer,
        audience=auth_settings.jwt_audience,
        jwks_url=auth_settings.jwt_jwks_uri,
        jwks_cache_ttl_seconds=auth_settings.jwt_jwks_cache_ttl_seconds,
    )
