"""Resolve and manage RepoAtlas's single user-level API credential."""

from __future__ import annotations

from dataclasses import dataclass
import os

import keyring
from keyring.errors import KeyringError


SERVICE_NAME = "repoatlas"
ACCOUNT_NAME = "default"
API_KEY_ENVIRONMENT_VARIABLE = "REPOATLAS_API_KEY"


class CredentialStoreError(RuntimeError):
    """Raised when the operating-system credential backend is unavailable."""


@dataclass(frozen=True)
class ResolvedAPIKey:
    """Hold an API key and its non-secret source label."""

    value: str
    source: str


def _store_error(action: str, error: Exception) -> CredentialStoreError:
    """把 keyring 后端错误转换成不泄露凭据的用户错误。"""
    return CredentialStoreError(
        f"Could not {action} the system credential store. "
        "Ensure a supported keyring backend is available."
    )


def get_stored_api_key() -> str | None:
    """读取 RepoAtlas 的单一默认系统凭据。"""
    try:
        value = keyring.get_password(SERVICE_NAME, ACCOUNT_NAME)
    except KeyringError as error:
        raise _store_error("access", error) from error
    return value.strip() if value and value.strip() else None


def set_stored_api_key(api_key: str) -> None:
    """把非空 API key 保存到操作系统凭据存储。"""
    value = api_key.strip()
    if not value:
        raise ValueError("API key cannot be empty.")
    try:
        keyring.set_password(SERVICE_NAME, ACCOUNT_NAME, value)
    except KeyringError as error:
        raise _store_error("write to", error) from error


def clear_stored_api_key() -> bool:
    """仅删除 RepoAtlas 默认凭据；不存在时返回 False。"""
    if get_stored_api_key() is None:
        return False
    try:
        keyring.delete_password(SERVICE_NAME, ACCOUNT_NAME)
    except KeyringError as error:
        raise _store_error("update", error) from error
    return True


def resolve_api_key() -> ResolvedAPIKey | None:
    """按环境变量、系统凭据的顺序解析运行时 API key。"""
    environment_value = os.getenv(API_KEY_ENVIRONMENT_VARIABLE)
    if environment_value and environment_value.strip():
        return ResolvedAPIKey(environment_value.strip(), "environment")

    stored_value = get_stored_api_key()
    if stored_value:
        return ResolvedAPIKey(stored_value, "system credential store")
    return None
