import random
import string
from collections.abc import Collection
from datetime import timedelta
from typing import Any, Protocol

from fastapi_login import LoginManager


class TokenProvider(Protocol):
    bearer_format: str | None

    def create_access_token(
        self,
        *,
        data: dict[str, Any],
        expires: timedelta | None = None,
        scopes: Collection[str] | None = None,
    ) -> str: ...

    def get_payload(self, token: str) -> dict[str, Any]: ...

    def revoke(self, token: str) -> None: ...


class OpaqueTokenProvider:
    bearer_format: str | None = "Token"

    def __init__(self, not_authenticated_exception: Exception | type[Exception]) -> None:
        self.not_authenticated_exception = not_authenticated_exception
        self.active_tokens: dict[str, dict[str, Any]] = {}

    def create_access_token(
        self,
        *,
        data: dict[str, Any],
        expires: timedelta | None = None,
        scopes: Collection[str] | None = None,
    ) -> str:
        del expires
        payload = data.copy()
        if scopes is not None:
            payload["scopes"] = list(set(scopes))
        token = self._generate_token()
        self.active_tokens[token] = payload
        return token

    def get_payload(self, token: str) -> dict[str, Any]:
        payload = self.active_tokens.get(token)
        if payload is None:
            raise self.not_authenticated_exception
        return payload

    def revoke(self, token: str) -> None:
        if token not in self.active_tokens:
            raise self.not_authenticated_exception
        del self.active_tokens[token]

    def _generate_token(self) -> str:
        alphabet = string.ascii_letters + string.digits
        # Avoid collision-retry loops so seeded runs remain reproducible even when
        # app modules persist across AppWorld instances in the same process.
        return "".join(random.choice(alphabet) for _ in range(10))


class JwtTokenProvider:
    bearer_format: str | None = "JWT"

    def __init__(self, login_manager: LoginManager) -> None:
        self.login_manager = login_manager

    def create_access_token(
        self,
        *,
        data: dict[str, Any],
        expires: timedelta | None = None,
        scopes: Collection[str] | None = None,
    ) -> str:
        return LoginManager.create_access_token(
            self.login_manager,
            data=data,
            expires=expires,
            scopes=scopes,
        )

    def get_payload(self, token: str) -> dict[str, Any]:
        return LoginManager._get_payload(self.login_manager, token)

    def revoke(self, token: str) -> None:
        del token
        raise NotImplementedError("JWT token revocation is not supported by JwtTokenProvider.")
