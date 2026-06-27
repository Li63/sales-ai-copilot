import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPayload:
    user_id: int
    exp: int


class AuthService:
    def __init__(self, secret: str):
        self.secret = secret or "change-this-secret"

    def hash_password(self, password: str, salt: str | None = None) -> str:
        salt = salt or base64.urlsafe_b64encode(os.urandom(16)).decode("ascii")
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
        return f"pbkdf2_sha256${salt}${base64.urlsafe_b64encode(digest).decode('ascii')}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, salt, expected = password_hash.split("$", 2)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        actual = self.hash_password(password, salt)
        return hmac.compare_digest(actual, password_hash)

    def create_token(self, user_id: int, ttl_seconds: int = 60 * 60 * 24 * 14) -> str:
        payload = {"user_id": user_id, "exp": int(time.time()) + ttl_seconds}
        body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signature = self._sign(body)
        return f"{body}.{signature}"

    def parse_token(self, token: str) -> TokenPayload | None:
        try:
            body, signature = token.split(".", 1)
            if not hmac.compare_digest(self._sign(body), signature):
                return None
            payload = json.loads(_unb64(body))
            exp = int(payload["exp"])
            if exp < int(time.time()):
                return None
            return TokenPayload(user_id=int(payload["user_id"]), exp=exp)
        except Exception:
            return None

    def _sign(self, body: str) -> str:
        digest = hmac.new(self.secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).digest()
        return _b64(digest)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)
