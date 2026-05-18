"""Unit tests for the current AuthService contract."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.cbt.services.auth_service import AuthService


@pytest.fixture
def auth_service() -> AuthService:
    """Create AuthService with mocked cache/session managers."""
    cache = AsyncMock()
    sessions = AsyncMock()
    return AuthService(db=None, cache=cache, sessions=sessions)


@pytest.mark.asyncio
async def test_authenticate_returns_error_for_missing_user(auth_service: AuthService):
    """Authentication fails when no matching user exists."""
    auth_service._get_user_by_username_or_email = AsyncMock(return_value=None)

    result = await auth_service.authenticate(
        username="ghost",
        password="nope",
        ip_address="127.0.0.1",
        user_agent="pytest",
        device_fingerprint="fp-1",
    )

    assert result.success is False
    assert result.error_message == "Invalid credentials"


@pytest.mark.asyncio
async def test_authenticate_returns_error_for_inactive_user(auth_service: AuthService):
    """Authentication fails for inactive accounts."""
    user = SimpleNamespace(is_active=False, is_locked=False)
    auth_service._get_user_by_username_or_email = AsyncMock(return_value=user)

    result = await auth_service.authenticate(
        username="inactive.user",
        password="secret",
        ip_address="127.0.0.1",
        user_agent="pytest",
        device_fingerprint="fp-2",
    )

    assert result.success is False
    assert result.error_message == "Account is inactive"


@pytest.mark.asyncio
async def test_authenticate_success_returns_tokens_and_user(auth_service: AuthService):
    """Authentication succeeds with valid credentials and active user."""
    user = SimpleNamespace(
        id="user-1",
        username="student1",
        email="student1@custech.edu.ng",
        is_active=True,
        is_locked=False,
        salt="salt",
        password_hash="hash",
    )

    auth_service._get_user_by_username_or_email = AsyncMock(return_value=user)
    auth_service._create_user_session = AsyncMock(
        return_value=({"session_token": "session-1"}, "access-1", "refresh-1")
    )
    auth_service._update_last_login = AsyncMock()
    auth_service._reset_failed_attempts = AsyncMock()

    with patch.object(auth_service.security, "verify_password", return_value=True):
        result = await auth_service.authenticate(
            username="student1",
            password="correct-password",
            ip_address="127.0.0.1",
            user_agent="pytest",
            device_fingerprint="fp-3",
        )

    assert result.success is True
    assert result.user == user
    assert result.token == "access-1"
    assert result.refresh_token == "refresh-1"
    auth_service._create_user_session.assert_awaited_once()
    auth_service._update_last_login.assert_awaited_once_with(user)
    auth_service._reset_failed_attempts.assert_awaited_once_with(user)


@pytest.mark.asyncio
async def test_refresh_token_fails_for_unknown_session(auth_service: AuthService):
    """Refresh token flow fails when no active session is found."""
    auth_service._get_session_by_refresh_token = AsyncMock(return_value=None)

    result = await auth_service.refresh_token(
        refresh_token="missing-refresh",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert result.success is False
    assert result.error_message == "Invalid or expired refresh token"


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_username(auth_service: AuthService):
    """Registration fails when username already exists."""
    auth_service._get_user_by_username = AsyncMock(return_value=object())
    auth_service._get_user_by_email = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="Username already exists"):
        await auth_service.register_user(
            username="taken",
            email="new@custech.edu.ng",
            password="StrongPassword123!",
            first_name="New",
            last_name="User",
            phone_number=None,
            date_of_birth=None,
            gender=None,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )


@pytest.mark.asyncio
async def test_register_user_rejects_duplicate_email(auth_service: AuthService):
    """Registration fails when email already exists."""
    auth_service._get_user_by_username = AsyncMock(return_value=None)
    auth_service._get_user_by_email = AsyncMock(return_value=object())

    with pytest.raises(ValueError, match="Email already exists"):
        await auth_service.register_user(
            username="newuser",
            email="taken@custech.edu.ng",
            password="StrongPassword123!",
            first_name="New",
            last_name="User",
            phone_number=None,
            date_of_birth=None,
            gender=None,
            ip_address="127.0.0.1",
            user_agent="pytest",
        )


@pytest.mark.asyncio
async def test_refresh_token_fails_for_inactive_user(auth_service: AuthService):
    """Refresh flow fails when session user is inactive."""
    session = SimpleNamespace(
        id="sess-1",
        user_id="user-1",
        is_active=True,
        is_expired=False,
        device_fingerprint="fp-9",
    )
    auth_service._get_session_by_refresh_token = AsyncMock(return_value=session)
    auth_service._get_user_by_id = AsyncMock(return_value=SimpleNamespace(is_active=False))

    result = await auth_service.refresh_token(
        refresh_token="refresh-1",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert result.success is False
    assert result.error_message == "User not found or inactive"


@pytest.mark.asyncio
async def test_logout_user_returns_false_for_missing_session(auth_service: AuthService):
    """Logout returns False when refresh token has no session."""
    auth_service._get_session_by_refresh_token = AsyncMock(return_value=None)

    ok = await auth_service.logout_user(
        refresh_token="unknown",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert ok is False


@pytest.mark.asyncio
async def test_logout_user_invalidates_existing_session(auth_service: AuthService):
    """Logout invalidates a known active session."""
    session = SimpleNamespace(id="sess-2", user_id="user-2")
    auth_service._get_session_by_refresh_token = AsyncMock(return_value=session)
    auth_service._invalidate_session = AsyncMock()
    auth_service._log_audit_event = AsyncMock()

    ok = await auth_service.logout_user(
        refresh_token="refresh-2",
        ip_address="127.0.0.1",
        user_agent="pytest",
    )

    assert ok is True
    auth_service._invalidate_session.assert_awaited_once_with("sess-2")
    auth_service._log_audit_event.assert_awaited_once()


@pytest.mark.asyncio
async def test_change_password_returns_false_for_unknown_user(auth_service: AuthService):
    """Password change returns False when user does not exist."""
    auth_service._get_user_by_id = AsyncMock(return_value=None)

    ok = await auth_service.change_password(
        user_id="missing",
        current_password="old",
        new_password="new",
    )

    assert ok is False


@pytest.mark.asyncio
async def test_change_password_rejects_bad_current_password(auth_service: AuthService):
    """Password change returns False for incorrect current password."""
    user = SimpleNamespace(salt="salt", password_hash="hash")
    auth_service._get_user_by_id = AsyncMock(return_value=user)

    with patch.object(auth_service.security, "verify_password", return_value=False):
        ok = await auth_service.change_password(
            user_id="user-3",
            current_password="wrong",
            new_password="new",
        )

    assert ok is False


@pytest.mark.asyncio
async def test_get_user_from_token_returns_none_without_user_claim(auth_service: AuthService):
    """When cache has no mapping for the access token, return None."""
    auth_service.cache.get = AsyncMock(return_value=None)

    user = await auth_service.get_user_from_token("token-without-cache-entry")

    assert user is None
    auth_service.cache.get.assert_awaited_once_with("access_token:token-without-cache-entry")


@pytest.mark.asyncio
async def test_get_user_from_token_returns_user_with_valid_claim(auth_service: AuthService):
    """When cache maps token to user id, return the resolved user."""
    resolved = SimpleNamespace(id="user-42")
    auth_service.cache.get = AsyncMock(return_value="user-42")
    auth_service._get_user_by_id = AsyncMock(return_value=resolved)

    user = await auth_service.get_user_from_token("good-token")

    assert user == resolved
    auth_service.cache.get.assert_awaited_once_with("access_token:good-token")
    auth_service._get_user_by_id.assert_awaited_once_with("user-42")
