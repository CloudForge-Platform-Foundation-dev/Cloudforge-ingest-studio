"""
Thin binding layer over cloudforge_auth_core — do NOT reimplement JWT
verification or scope-checking here. Reimplementing it per-Studio is
exactly how Ingest and Knowledge drifted (`scopes` list vs `scope`
string) before CloudForge Identity Contract v1. All verification and
scope logic lives in cloudforge_auth_core; this module only wires it to
Ingest's AuthConfig.
"""
from cloudforge_auth_core import Principal, build_auth_dependencies
from cloudforge_auth_core.jwks import JWKSCache

from src.auth.config import build_auth_config

_jwks_cache = JWKSCache(build_auth_config())
get_current_user, require_scope = build_auth_dependencies(
    build_auth_config(), jwks_cache=_jwks_cache
)

__all__ = ["get_current_user", "require_scope", "Principal", "_jwks_cache"]
