from pydantic_settings import BaseSettings

class AuthSettings(BaseSettings):
    jwt_issuer: str = "https://auth.cloudforge.internal"
    jwt_audience: str = "cloudforge-ingest-studio"
    jwt_jwks_uri: str = "https://auth.cloudforge.internal/.well-known/jwks.json"
    jwt_algorithms: list[str] = ["RS256"]

    class Config:
        env_prefix = "CLOUDFORGE_"
        extra = "ignore"

auth_settings = AuthSettings()
