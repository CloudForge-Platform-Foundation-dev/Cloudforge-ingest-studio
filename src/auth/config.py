from pydantic_settings import BaseSettings, SettingsConfigDict

class AuthSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CLOUDFORGE_", extra="ignore")

    jwt_issuer: str = "https://auth.cloudforge.internal"
    jwt_audience: str = "cloudforge-ingest-studio"
    jwt_jwks_uri: str = "https://auth.cloudforge.internal/.well-known/jwks.json"
    jwt_algorithms: list[str] = ["RS256"]

auth_settings = AuthSettings()
