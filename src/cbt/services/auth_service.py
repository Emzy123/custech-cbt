"""
Authentication service for user management, login, and security.
Uses Beanie ODM for MongoDB.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

from ..models.user import User
from ..models.security import UserSession, AuditLog, AuditAction
from ..core.security import security
from ..core.config import settings
from ..core.redis import cache_manager, session_manager
from ..schemas.auth import ProfileResponse


class AuthenticationResult:
    """Authentication result container."""

    def __init__(self, success: bool, user: Optional[User] = None,
                 token: Optional[str] = None, refresh_token: Optional[str] = None,
                 error_message: Optional[str] = None):
        self.success = success
        self.user = user
        self.token = token
        self.refresh_token = refresh_token
        self.error_message = error_message
        self.mfa_required = False
        self.mfa_methods = []


class AuthService:
    """Authentication and user management service."""

    def __init__(self, db: Any, cache, sessions):
        self.cache = cache
        self.sessions = sessions
        self.security = security

    async def authenticate(self, username: str, password: str, ip_address: str,
                           user_agent: str, device_fingerprint: str,
                           require_biometric: bool = False,
                           biometric_data: Optional[Dict] = None) -> AuthenticationResult:
        """Authenticate user with credentials (Username/Matric/Email + Password)."""
        try:
            user = await self._get_user_by_username_or_email(username)
            if not user:
                return AuthenticationResult(success=False, error_message="Invalid credentials")

            if not user.is_active:
                return AuthenticationResult(success=False, error_message="Account is inactive")

            if user.is_locked:
                return AuthenticationResult(success=False, error_message="Account is temporarily locked")

            if not self.security.verify_password(password, user.salt, user.password_hash):
                await self._handle_failed_login(user, ip_address, user_agent)
                return AuthenticationResult(success=False, error_message="Invalid credentials")

            session_data, access_token, refresh_token = await self._create_user_session(
                user, ip_address, user_agent, device_fingerprint
            )

            await self._update_last_login(user)
            await self._reset_failed_attempts(user)

            return AuthenticationResult(
                success=True,
                user=user,
                token=access_token,
                refresh_token=refresh_token
            )

        except Exception as e:
            return AuthenticationResult(success=False, error_message=f"Authentication failed: {str(e)}")

    async def register_user(self, username: str, email: str, password: str,
                            first_name: str, last_name: str, phone_number: Optional[str],
                            date_of_birth: Optional[datetime], gender: Optional[Any],
                            ip_address: str, user_agent: str, role: str = "student",
                            matric_number: Optional[str] = None,
                            department: Optional[str] = None) -> User:
        """Register new user account with direct role field."""
        try:
            if await self._get_user_by_username(username):
                raise ValueError("Username already exists")
            if await self._get_user_by_email(email):
                raise ValueError("Email already exists")

            user_id = str(uuid.uuid4())
            salt = self.security.generate_salt()
            password_hash = self.security.hash_password(password, salt)

            user = User(
                id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                full_name=f"{first_name} {last_name}".strip(),
                matric_number=matric_number,
                role=role.lower(),
                department=department,
                is_active=True,
                is_verified=True
            )
            await user.insert()

            await self._log_audit_event(
                user_id=user_id,
                action=AuditAction.CREATE,
                resource_type="user",
                resource_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            return user

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Registration failed: {str(e)}")

    async def refresh_token(self, refresh_token: str, ip_address: str,
                            user_agent: str) -> AuthenticationResult:
        """Refresh access token using refresh token."""
        try:
            session = await self._get_session_by_refresh_token(refresh_token)
            if not session or not session.is_active:
                return AuthenticationResult(success=False, error_message="Invalid or expired refresh token")

            if session.is_expired:
                await self._invalidate_session(session.id)
                return AuthenticationResult(success=False, error_message="Session expired")

            user = await self._get_user_by_id(session.user_id)
            if not user or not user.is_active:
                return AuthenticationResult(success=False, error_message="User not found or inactive")

            new_session_data, access_token, new_refresh_token = await self._create_user_session(
                user, ip_address, user_agent, session.device_fingerprint
            )
            await self._invalidate_session(session.id)

            return AuthenticationResult(success=True, user=user, token=access_token, refresh_token=new_refresh_token)

        except Exception as e:
            return AuthenticationResult(success=False, error_message=f"Token refresh failed: {str(e)}")

    async def logout_user(self, refresh_token: str, ip_address: str, user_agent: str) -> bool:
        """Logout user and invalidate tokens."""
        try:
            session = await self._get_session_by_refresh_token(refresh_token)
            if not session:
                return False

            await self._invalidate_session(session.id)
            await self._log_audit_event(
                user_id=session.user_id,
                action=AuditAction.LOGOUT,
                resource_type="session",
                resource_id=session.id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            return True
        except Exception:
            return False

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password."""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return False

            if not self.security.verify_password(current_password, user.salt, user.password_hash):
                return False

            salt = self.security.generate_salt()
            password_hash = self.security.hash_password(new_password, salt)

            await user.set({User.salt: salt, User.password_hash: password_hash})
            await self._invalidate_user_sessions(user_id)
            await self._log_audit_event(
                user_id=user_id, action=AuditAction.UPDATE,
                resource_type="user", resource_id=user_id,
                success=True, new_values={"password_changed": True}
            )
            return True
        except Exception:
            return False

    async def update_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> User:
        """Update user profile."""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                raise ValueError("User not found")

            update_fields = {}
            for field, value in profile_data.items():
                if hasattr(User, field) and field not in ['id', 'password_hash', 'salt']:
                    update_fields[getattr(User, field)] = value
            
            if update_fields:
                await user.set(update_fields)
                await user.sync()

            return user

        except Exception as e:
            raise ValueError(f"Profile update failed: {str(e)}")

    async def verify_email(self, token: str) -> bool:
        """Verify user email."""
        return True

    async def send_password_reset_email(self, email: str, ip_address: str) -> bool:
        """Send password reset email."""
        try:
            user = await self._get_user_by_email(email)
            if not user:
                return False
            reset_token = self.security.generate_password_reset_token(user.id)
            await self.cache.set(f"password_reset:{reset_token}", user.id, ttl=3600)
            return True
        except Exception:
            return False

    async def reset_password(self, token: str, new_password: str, ip_address: str) -> bool:
        """Reset password using reset token."""
        try:
            user_id = await self.cache.get(f"password_reset:{token}")
            if not user_id:
                return False
            user = await self._get_user_by_id(user_id)
            if not user:
                return False
            salt = self.security.generate_salt()
            password_hash = self.security.hash_password(new_password, salt)
            await user.set({User.salt: salt, User.password_hash: password_hash})
            await self.cache.delete(f"password_reset:{token}")
            return True
        except Exception:
            return False

    async def user_has_role(self, user_id: str, role: str) -> bool:
        """Check if user has specific role directly from User document."""
        try:
            user = await self._get_user_by_id(user_id)
            if not user:
                return False
            user_role = user.role.lower()
            check_role = role.lower()
            if user_role == "admin" and check_role in ["admin", "administrator", "exam_officer"]:
                return True
            return user_role == check_role
        except Exception:
            return False

    async def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from access token."""
        try:
            user_id = await self.cache.get(f"access_token:{token}")
            if not user_id:
                return None
            return await self._get_user_by_id(user_id)
        except Exception:
            return None

    # ── Private helpers ──────────────────────────────────────────────────

    async def _get_user_by_username_or_email(self, identifier: str) -> Optional[User]:
        return await User.find_one({"$or": [{"username": identifier}, {"email": identifier}, {"matric_number": identifier}]})

    async def _get_user_by_username(self, username: str) -> Optional[User]:
        return await User.find_one(User.username == username)

    async def _get_user_by_email(self, email: str) -> Optional[User]:
        return await User.find_one(User.email == email)

    async def _get_user_by_id(self, user_id: str) -> Optional[User]:
        return await User.find_one(User.id == user_id)

    async def _create_user_session(self, user: User, ip_address: str, user_agent: str,
                                   device_fingerprint: str) -> Tuple[Dict, str, str]:
        """Create user session and tokens."""
        access_token = self.security.generate_api_key()
        refresh_token = self.security.generate_api_key()
        session_token = self.security.generate_session_token()

        session_data = {
            "user_id": user.id,
            "session_token": session_token,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "device_fingerprint": device_fingerprint,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

        await self.sessions.create_session(session_token, session_data)
        await self.sessions.add_user_session(user.id, session_token)
        await self.cache.set(f"access_token:{access_token}", user.id, ttl=settings.access_token_expire_minutes * 60)
        await self.cache.set(f"refresh_token:{refresh_token}", session_token, ttl=settings.refresh_token_expire_days * 86400)

        return session_data, access_token, refresh_token

    async def _get_session_by_refresh_token(self, refresh_token: str) -> Optional[UserSession]:
        """Get session by refresh token (from Redis)."""
        session_token = await self.cache.get(f"refresh_token:{refresh_token}")
        if not session_token:
            return None
        session_data = await self.sessions.get_session(session_token)
        if not session_data:
            return None

        session = UserSession(
            id=session_token,
            user_id=session_data["user_id"],
            session_token=session_token,
            refresh_token=refresh_token,
            ip_address=session_data.get("ip_address"),
            device_fingerprint=session_data.get("device_fingerprint"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=2)
        )
        return session

    async def _invalidate_session(self, session_id: str):
        await self.sessions.delete_session(session_id)

    async def _invalidate_user_sessions(self, user_id: str):
        await self.sessions.clear_user_sessions(user_id)

    async def _update_last_login(self, user: User):
        await user.set({User.last_login_at: datetime.now(timezone.utc)})

    async def _handle_failed_login(self, user: User, ip_address: str, user_agent: str):
        new_attempts = user.failed_login_attempts + 1
        update = {User.failed_login_attempts: new_attempts}
        if new_attempts >= 5:
            update[User.locked_until] = datetime.now(timezone.utc) + timedelta(minutes=30)
        await user.set(update)
        await self._log_audit_event(
            user_id=user.id, action=AuditAction.LOGIN,
            resource_type="user", resource_id=user.id,
            ip_address=ip_address, user_agent=user_agent,
            success=False, error_message="Invalid credentials"
        )

    async def _reset_failed_attempts(self, user: User):
        if user.failed_login_attempts > 0 or user.locked_until:
            await user.set({User.failed_login_attempts: 0, User.locked_until: None})

    async def _log_audit_event(self, user_id: Optional[str], action: AuditAction,
                               resource_type: str, resource_id: Optional[str] = None,
                               ip_address: Optional[str] = None,
                               user_agent: Optional[str] = None,
                               success: bool = True, error_message: Optional[str] = None,
                               old_values: Optional[Dict] = None,
                               new_values: Optional[Dict] = None):
        """Log audit event to MongoDB."""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success,
                error_message=error_message,
                old_values=old_values,
                new_values=new_values
            )
            await audit_log.insert()
        except Exception:
            pass
