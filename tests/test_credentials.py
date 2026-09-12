import pytest
from keyring.errors import NoKeyringError

from repoatlas.credentials import (
    ACCOUNT_NAME,
    API_KEY_ENVIRONMENT_VARIABLE,
    SERVICE_NAME,
    CredentialStoreError,
    clear_stored_api_key,
    resolve_api_key,
    set_stored_api_key,
)


def test_resolve_api_key_prefers_environment(monkeypatch):
    monkeypatch.setenv(API_KEY_ENVIRONMENT_VARIABLE, "  test-environment-key  ")
    monkeypatch.setattr(
        "repoatlas.credentials.keyring.get_password",
        lambda service, account: pytest.fail("keyring should not be read"),
    )

    credential = resolve_api_key()

    assert credential is not None
    assert credential.value == "test-environment-key"
    assert credential.source == "environment"


def test_resolve_api_key_uses_system_store(monkeypatch):
    monkeypatch.delenv(API_KEY_ENVIRONMENT_VARIABLE, raising=False)
    monkeypatch.setattr(
        "repoatlas.credentials.keyring.get_password",
        lambda service, account: "test-stored-key",
    )

    credential = resolve_api_key()

    assert credential is not None
    assert credential.value == "test-stored-key"
    assert credential.source == "system credential store"


def test_set_stored_api_key_uses_stable_identity(monkeypatch):
    recorded = []
    monkeypatch.setattr(
        "repoatlas.credentials.keyring.set_password",
        lambda service, account, value: recorded.append((service, account, value)),
    )

    set_stored_api_key("  test-key  ")

    assert recorded == [(SERVICE_NAME, ACCOUNT_NAME, "test-key")]


def test_set_stored_api_key_rejects_empty_value():
    with pytest.raises(ValueError, match="cannot be empty"):
        set_stored_api_key("   ")


def test_clear_stored_api_key_handles_present_and_missing_values(monkeypatch):
    deleted = []
    monkeypatch.setattr(
        "repoatlas.credentials.keyring.get_password",
        lambda service, account: "test-stored-key",
    )
    monkeypatch.setattr(
        "repoatlas.credentials.keyring.delete_password",
        lambda service, account: deleted.append((service, account)),
    )

    assert clear_stored_api_key() is True
    assert deleted == [(SERVICE_NAME, ACCOUNT_NAME)]

    monkeypatch.setattr(
        "repoatlas.credentials.keyring.get_password",
        lambda service, account: None,
    )
    assert clear_stored_api_key() is False


def test_keyring_backend_error_is_actionable_and_hides_backend_details(monkeypatch):
    monkeypatch.delenv(API_KEY_ENVIRONMENT_VARIABLE, raising=False)

    def fail(service, account):
        raise NoKeyringError("test backend diagnostic")

    monkeypatch.setattr("repoatlas.credentials.keyring.get_password", fail)

    with pytest.raises(CredentialStoreError, match="supported keyring backend") as error:
        resolve_api_key()

    assert "test backend diagnostic" not in str(error.value)
