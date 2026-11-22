import json
import os
import time
from functools import lru_cache

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes
from fastmcp.server.auth.providers.jwt import JWTVerifier


bearer = HTTPBearer(auto_error=False)


@lru_cache(maxsize=4)
def verifier(domain: str, audience: str) -> JWTVerifier:
    issuer = f"https://{domain}/"
    return JWTVerifier(
        jwks_uri=f"{issuer}.well-known/jwks.json",
        issuer=issuer,
        audience=audience,
        algorithm="RS256",
    )


async def require_owner(
    security_scopes: SecurityScopes,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> str:
    domain = os.environ.get("AUTH0_DOMAIN", "")
    audience = os.environ.get("AUTH0_AUDIENCE", "")
    if not domain or not audience or "/" in domain or ":" in domain:
        raise HTTPException(status_code=503, detail="Auth0 is not configured.")
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentication required.", headers={"WWW-Authenticate": "Bearer"})
    access = await verifier(domain, audience).verify_token(credentials.credentials)
    if access is None:
        raise HTTPException(status_code=401, detail="Invalid access token.", headers={"WWW-Authenticate": "Bearer"})
    claims = access.claims
    now = time.time()
    exp, issued, not_before = claims.get("exp"), claims.get("iat"), claims.get("nbf")
    subject = claims.get("sub")
    if (
        not isinstance(exp, (int, float)) or isinstance(exp, bool) or exp <= now
        or not isinstance(issued, (int, float)) or isinstance(issued, bool) or issued > now
        or (not_before is not None and (not isinstance(not_before, (int, float)) or isinstance(not_before, bool) or not_before > now))
        or not isinstance(subject, str) or not subject or subject.endswith("@clients")
        or claims.get("gty") == "client-credentials"
    ):
        raise HTTPException(status_code=401, detail="Invalid access token.", headers={"WWW-Authenticate": "Bearer"})
    if not set(security_scopes.scopes).issubset(access.scopes):
        raise HTTPException(status_code=403, detail="Insufficient permissions.")
    return json.dumps([claims["iss"], subject], separators=(",", ":"))
