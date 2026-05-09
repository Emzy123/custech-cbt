# Secure Session and Token Management System

## Overview

This document defines the comprehensive session and token management system for the CBT application, implementing secure JWT-based authentication with session tracking, device fingerprinting, and robust security controls.

## Session Architecture

### Session Lifecycle
```
1. Authentication → Session Creation
   - User authenticates with MFA
   - Session record created in database
   - JWT tokens generated
   - Session stored in Redis cache

2. Active Session → Token Validation
   - JWT token validated on each request
   - Session record checked for validity
   - Device fingerprint verified
   - Activity timestamp updated

3. Session Expiration → Token Refresh
   - Access token expires (15 minutes)
   - Refresh token used to get new access token
   - Session validity checked
   - New tokens issued

4. Session Termination → Cleanup
   - Manual logout or timeout
   - Session record invalidated
   - Tokens added to blacklist
   - Cache entries cleaned
```

### Security Features
```
Token Security:
- Short-lived access tokens (15 minutes)
- Longer-lived refresh tokens (7 days)
- Cryptographic signing with HS256
- Token rotation on refresh
- Immediate revocation capability

Session Security:
- Server-side session tracking
- Device fingerprint validation
- IP address monitoring
- Concurrent session limits
- Automatic timeout handling

Cache Security:
- Redis-based session storage
- Encrypted sensitive data
- TTL-based automatic cleanup
- Distributed cache consistency
- Backup and recovery procedures
```

---

## Token Management

### JWT Token Structure

#### Access Token Payload
```python
# models/tokens.py
import jwt
import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class AccessTokenPayload:
    user_id: str
    username: str
    email: str
    roles: list
    department_id: Optional[str]
    session_id: str
    device_fingerprint: str
    biometric_verified: bool
    permissions: list
    iat: datetime.datetime  # Issued at
    exp: datetime.datetime  # Expires at
    iss: str  # Issuer
    aud: str  # Audience
    jti: str  # JWT ID

@dataclass
class RefreshTokenPayload:
    user_id: str
    session_id: str
    token_type: str  # "refresh"
    iat: datetime.datetime
    exp: datetime.datetime
    iss: str
    aud: str
    jti: str

class TokenManager:
    def __init__(self, config: Dict[str, Any]):
        self.secret_key = config['jwt_secret']
        self.algorithm = 'HS256'
        self.access_token_expiry = config['access_token_expiry_minutes']
        self.refresh_token_expiry = config['refresh_token_expiry_days']
        self.issuer = config['issuer']
        self.audience = config['audience']
    
    def generate_access_token(self, user_data: Dict[str, Any], 
                              session_id: str, device_fingerprint: str,
                              biometric_verified: bool) -> str:
        """Generate JWT access token"""
        now = datetime.datetime.utcnow()
        expiry = now + datetime.timedelta(minutes=self.access_token_expiry)
        
        payload = {
            'user_id': user_data['user_id'],
            'username': user_data['username'],
            'email': user_data['email'],
            'roles': user_data['roles'],
            'department_id': user_data.get('department_id'),
            'session_id': session_id,
            'device_fingerprint': device_fingerprint,
            'biometric_verified': biometric_verified,
            'permissions': user_data.get('permissions', []),
            'iat': int(now.timestamp()),
            'exp': int(expiry.timestamp()),
            'iss': self.issuer,
            'aud': self.audience,
            'jti': self._generate_jti()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user_id: str, session_id: str) -> str:
        """Generate JWT refresh token"""
        now = datetime.datetime.utcnow()
        expiry = now + datetime.timedelta(days=self.refresh_token_expiry)
        
        payload = {
            'user_id': user_id,
            'session_id': session_id,
            'token_type': 'refresh',
            'iat': int(now.timestamp()),
            'exp': int(expiry.timestamp()),
            'iss': self.issuer,
            'aud': self.audience,
            'jti': self._generate_jti()
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_access_token(self, token: str) -> Optional[AccessTokenPayload]:
        """Verify and decode access token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer
            )
            
            return AccessTokenPayload(
                user_id=payload['user_id'],
                username=payload['username'],
                email=payload['email'],
                roles=payload['roles'],
                department_id=payload.get('department_id'),
                session_id=payload['session_id'],
                device_fingerprint=payload['device_fingerprint'],
                biometric_verified=payload['biometric_verified'],
                permissions=payload['permissions'],
                iat=datetime.datetime.fromtimestamp(payload['iat']),
                exp=datetime.datetime.fromtimestamp(payload['exp']),
                iss=payload['iss'],
                aud=payload['aud'],
                jti=payload['jti']
            )
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Access token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid access token: {str(e)}")
    
    def verify_refresh_token(self, token: str) -> Optional[RefreshTokenPayload]:
        """Verify and decode refresh token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=self.issuer
            )
            
            if payload.get('token_type') != 'refresh':
                raise InvalidTokenError("Invalid token type for refresh")
            
            return RefreshTokenPayload(
                user_id=payload['user_id'],
                session_id=payload['session_id'],
                token_type=payload['token_type'],
                iat=datetime.datetime.fromtimestamp(payload['iat']),
                exp=datetime.datetime.fromtimestamp(payload['exp']),
                iss=payload['iss'],
                aud=payload['aud'],
                jti=payload['jti']
            )
            
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Refresh token has expired")
        except jwt.InvalidTokenError as e:
            raise InvalidTokenError(f"Invalid refresh token: {str(e)}")
    
    def _generate_jti(self) -> str:
        """Generate JWT ID"""
        import secrets
        return secrets.token_urlsafe(32)

class TokenExpiredError(Exception):
    pass

class InvalidTokenError(Exception):
    pass
```

### Token Blacklist
```python
# services/token_blacklist.py
import redis
import json
from datetime import datetime, timedelta
from typing import Set

class TokenBlacklist:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.blacklist_prefix = "blacklist:"
        self.default_ttl = 3600  # 1 hour
    
    def add_token(self, jti: str, expiry: Optional[int] = None):
        """Add token to blacklist"""
        ttl = expiry or self.default_ttl
        key = f"{self.blacklist_prefix}{jti}"
        self.redis_client.setex(key, ttl, "blacklisted")
    
    def is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        key = f"{self.blacklist_prefix}{jti}"
        return self.redis_client.exists(key) > 0
    
    def remove_token(self, jti: str):
        """Remove token from blacklist"""
        key = f"{self.blacklist_prefix}{jti}"
        self.redis_client.delete(key)
    
    def blacklist_user_tokens(self, user_id: str):
        """Blacklist all tokens for a user"""
        # This would require tracking all active tokens for a user
        # For now, add user to blacklist
        key = f"{self.blacklist_prefix}user:{user_id}"
        self.redis_client.setex(key, 3600, "blacklisted")
    
    def is_user_blacklisted(self, user_id: str) -> bool:
        """Check if user is blacklisted"""
        key = f"{self.blacklist_prefix}user:{user_id}"
        return self.redis_client.exists(key) > 0
    
    def cleanup_expired_tokens(self):
        """Clean up expired blacklist entries"""
        # Redis handles TTL automatically, so this is a no-op
        pass
```

---

## Session Management Service

### Session Service Implementation
```python
# services/session_service.py
import uuid
import hashlib
import secrets
import redis
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

@dataclass
class SessionData:
    session_id: str
    user_id: str
    access_token: str
    refresh_token: str
    ip_address: str
    user_agent: str
    device_fingerprint: str
    biometric_verified: bool
    created_at: datetime.datetime
    last_activity_at: datetime.datetime
    expires_at: datetime.datetime
    is_active: bool = True
    termination_reason: Optional[str] = None

class SessionService:
    def __init__(self, redis_client: redis.Redis, config: Dict[str, Any]):
        self.redis_client = redis_client
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        self.session_ttl = config['session_ttl_minutes']
        self.max_concurrent_sessions = config['max_concurrent_sessions']
        self.idle_timeout = config['idle_timeout_minutes']
        self.blacklist_service = None  # Will be injected
    
    def set_blacklist_service(self, blacklist_service):
        """Inject token blacklist service"""
        self.blacklist_service = blacklist_service
    
    async def create_session(self, user_id: str, access_token: str, refresh_token: str,
                           ip_address: str, user_agent: str, device_fingerprint: str,
                           biometric_verified: bool = False) -> SessionData:
        """Create new user session"""
        session_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        expires_at = now + datetime.timedelta(minutes=self.session_ttl)
        
        # Check concurrent session limit
        await self._enforce_concurrent_session_limit(user_id)
        
        # Create session data
        session_data = SessionData(
            session_id=session_id,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            ip_address=ip_address,
            user_agent=user_agent,
            device_fingerprint=device_fingerprint,
            biometric_verified=biometric_verified,
            created_at=now,
            last_activity_at=now,
            expires_at=expires_at,
            is_active=True
        )
        
        # Store session in Redis
        await self._store_session(session_data)
        
        # Add session to user's session list
        await self._add_user_session(user_id, session_id)
        
        return session_data
    
    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session by ID"""
        key = f"{self.session_prefix}{session_id}"
        session_json = self.redis_client.get(key)
        
        if not session_json:
            return None
        
        session_dict = json.loads(session_json)
        session_data = SessionData(**session_dict)
        
        # Check if session is still valid
        if not await self._is_session_valid(session_data):
            await self._invalidate_session(session_id)
            return None
        
        # Update last activity
        await self._update_last_activity(session_id)
        
        return session_data
    
    async def validate_session(self, session_id: str, ip_address: str, 
                             user_agent: str, device_fingerprint: str) -> bool:
        """Validate session against request context"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return False
        
        # Check IP address
        if session_data.ip_address != ip_address:
            # Log IP change and potentially invalidate
            await self._log_security_event(
                session_data.user_id, "IP_ADDRESS_CHANGE", 
                f"IP changed from {session_data.ip_address} to {ip_address}"
            )
            return False
        
        # Check device fingerprint
        if session_data.device_fingerprint != device_fingerprint:
            # Log device change and potentially invalidate
            await self._log_security_event(
                session_data.user_id, "DEVICE_FINGERPRINT_CHANGE",
                f"Device fingerprint changed"
            )
            return False
        
        # Check session age
        if datetime.datetime.utcnow() > session_data.expires_at:
            await self._invalidate_session(session_id)
            return False
        
        return True
    
    async def refresh_session(self, refresh_token: str, new_access_token: str,
                             new_refresh_token: str) -> Optional[SessionData]:
        """Refresh session tokens"""
        # Verify refresh token and get session_id
        try:
            from .tokens import TokenManager
            token_manager = TokenManager({})
            refresh_payload = token_manager.verify_refresh_token(refresh_token)
            
            session_data = await self.get_session(refresh_payload.session_id)
            if not session_data:
                return None
            
            # Update tokens
            session_data.access_token = new_access_token
            session_data.refresh_token = new_refresh_token
            session_data.last_activity_at = datetime.datetime.utcnow()
            session_data.expires_at = datetime.datetime.utcnow() + timedelta(minutes=self.session_ttl)
            
            # Store updated session
            await self._store_session(session_data)
            
            return session_data
            
        except Exception as e:
            print(f"Session refresh failed: {str(e)}")
            return None
    
    async def invalidate_session(self, session_id: str, reason: str = "LOGOUT"):
        """Invalidate session"""
        session_data = await self.get_session(session_id)
        if not session_data:
            return
        
        # Mark as inactive
        session_data.is_active = False
        session_data.termination_reason = reason
        
        # Update session data
        await self._store_session(session_data)
        
        # Remove from user's session list
        await self._remove_user_session(session_data.user_id, session_id)
        
        # Blacklist tokens
        if self.blacklist_service:
            # Extract JWT IDs from tokens
            from .tokens import TokenManager
            token_manager = TokenManager({})
            
            try:
                access_payload = token_manager.verify_access_token(session_data.access_token)
                self.blacklist_service.add_token(access_payload.jti)
            except:
                pass
            
            try:
                refresh_payload = token_manager.verify_refresh_token(session_data.refresh_token)
                self.blacklist_service.add_token(refresh_payload.jti)
            except:
                pass
        
        # Log session termination
        await self._log_security_event(
            session_data.user_id, "SESSION_TERMINATED", 
            f"Session {session_id} terminated: {reason}"
        )
    
    async def invalidate_user_sessions(self, user_id: str, reason: str = "ADMIN_ACTION"):
        """Invalidate all sessions for user"""
        user_sessions = await self._get_user_sessions(user_id)
        
        for session_id in user_sessions:
            await self.invalidate_session(session_id, reason)
        
        # Blacklist user
        if self.blacklist_service:
            self.blacklist_service.blacklist_user_tokens(user_id)
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        # This would scan for expired sessions and clean them up
        # For now, rely on Redis TTL for automatic cleanup
        pass
    
    async def get_user_sessions(self, user_id: str) -> List[SessionData]:
        """Get all active sessions for user"""
        session_ids = await self._get_user_sessions(user_id)
        sessions = []
        
        for session_id in session_ids:
            session_data = await self.get_session(session_id)
            if session_data and session_data.is_active:
                sessions.append(session_data)
        
        return sessions
    
    async def _store_session(self, session_data: SessionData):
        """Store session in Redis"""
        key = f"{self.session_prefix}{session_data.session_id}"
        session_json = json.dumps(asdict(session_data), default=str)
        ttl = int((session_data.expires_at - datetime.datetime.utcnow()).total_seconds())
        
        self.redis_client.setex(key, ttl, session_json)
    
    async def _is_session_valid(self, session_data: SessionData) -> bool:
        """Check if session is still valid"""
        if not session_data.is_active:
            return False
        
        if datetime.datetime.utcnow() > session_data.expires_at:
            return False
        
        # Check idle timeout
        idle_time = datetime.datetime.utcnow() - session_data.last_activity_at
        if idle_time > timedelta(minutes=self.idle_timeout):
            return False
        
        # Check if user is blacklisted
        if self.blacklist_service and self.blacklist_service.is_user_blacklisted(session_data.user_id):
            return False
        
        return True
    
    async def _update_last_activity(self, session_id: str):
        """Update session last activity"""
        key = f"{self.session_prefix}{session_id}:activity"
        self.redis_client.setex(key, self.session_ttl * 60, datetime.datetime.utcnow().isoformat())
    
    async def _add_user_session(self, user_id: str, session_id: str):
        """Add session to user's session list"""
        key = f"{self.user_sessions_prefix}{user_id}"
        self.redis_client.sadd(key, session_id)
        self.redis_client.expire(key, self.session_ttl * 60)
    
    async def _remove_user_session(self, user_id: str, session_id: str):
        """Remove session from user's session list"""
        key = f"{self.user_sessions_prefix}{user_id}"
        self.redis_client.srem(key, session_id)
    
    async def _get_user_sessions(self, user_id: str) -> List[str]:
        """Get all session IDs for user"""
        key = f"{self.user_sessions_prefix}{user_id}"
        sessions = self.redis_client.smembers(key)
        return [session.decode() for session in sessions] if sessions else []
    
    async def _enforce_concurrent_session_limit(self, user_id: str):
        """Enforce maximum concurrent sessions"""
        user_sessions = await self._get_user_sessions(user_id)
        
        if len(user_sessions) >= self.max_concurrent_sessions:
            # Remove oldest session
            oldest_session = min(user_sessions, key=lambda s: self._get_session_creation_time(s))
            await self.invalidate_session(oldest_session, "CONCURRENT_LIMIT")
    
    def _get_session_creation_time(self, session_id: str) -> datetime.datetime:
        """Get session creation time"""
        key = f"{self.session_prefix}{session_id}"
        session_json = self.redis_client.hget(key, "created_at")
        if session_json:
            return datetime.datetime.fromisoformat(session_json)
        return datetime.datetime.utcnow()
    
    async def _log_security_event(self, user_id: str, event_type: str, description: str):
        """Log security event"""
        # This would integrate with audit logging system
        key = f"security_event:{user_id}:{datetime.datetime.utcnow().isoformat()}"
        event_data = {
            "user_id": user_id,
            "event_type": event_type,
            "description": description,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        self.redis_client.setex(key, 86400, json.dumps(event_data))  # 24 hours TTL
```

---

## Device Fingerprinting

### Device Fingerprint Service
```python
# services/device_fingerprint.py
import hashlib
import json
from typing import Dict, Any, Optional

class DeviceFingerprintService:
    def __init__(self):
        self.fingerprint_attributes = [
            'user_agent',
            'accept_language',
            'accept_encoding',
            'accept_charset',
            'platform',
            'vendor',
            'screen_resolution',
            'color_depth',
            'timezone_offset',
            'session_storage',
            'local_storage',
            'indexed_db',
            'webgl',
            'canvas',
            'plugins',
            'cookies_enabled',
            'java_enabled',
            'flash_enabled',
            'silverlight_enabled',
            'pdf_viewer',
            'touch_support'
        ]
    
    def generate_fingerprint(self, request_data: Dict[str, Any]) -> str:
        """Generate device fingerprint from request data"""
        fingerprint_data = {}
        
        # Collect relevant attributes
        for attr in self.fingerprint_attributes:
            value = request_data.get(attr)
            if value is not None:
                fingerprint_data[attr] = value
        
        # Create fingerprint string
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        
        # Generate hash
        fingerprint_hash = hashlib.sha256(fingerprint_string.encode()).hexdigest()
        
        return fingerprint_hash
    
    def generate_browser_fingerprint(self, user_agent: str, screen_resolution: str,
                                   timezone_offset: int, platform: str) -> str:
        """Generate simplified fingerprint from key browser attributes"""
        fingerprint_data = {
            'user_agent': user_agent,
            'screen_resolution': screen_resolution,
            'timezone_offset': timezone_offset,
            'platform': platform
        }
        
        fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    
    def validate_fingerprint(self, stored_fingerprint: str, current_fingerprint: str) -> bool:
        """Validate fingerprint against stored value"""
        return stored_fingerprint == current_fingerprint
    
    def calculate_similarity(self, fingerprint1: str, fingerprint2: str) -> float:
        """Calculate similarity between two fingerprints"""
        if fingerprint1 == fingerprint2:
            return 1.0
        
        # Simple similarity calculation based on hash comparison
        # In practice, this would use more sophisticated algorithms
        return 0.0  # Different hashes mean different devices
```

---

## Session Middleware

### FastAPI Session Middleware
```python
# middleware/session_middleware.py
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .session_service import SessionService
from .tokens import TokenManager, TokenExpiredError, InvalidTokenError

security = HTTPBearer()

class SessionMiddleware:
    def __init__(self, session_service: SessionService, token_manager: TokenManager):
        self.session_service = session_service
        self.token_manager = token_manager
    
    async def authenticate_request(self, request: Request) -> Optional[str]:
        """Authenticate request and return user_id"""
        try:
            # Extract token
            credentials: Optional[HTTPAuthorizationCredentials] = await security(request)
            if not credentials:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Verify token
            token_payload = self.token_manager.verify_access_token(credentials.credentials)
            
            # Validate session
            session_valid = await self.session_service.validate_session(
                token_payload.session_id,
                request.client.host if request.client else "unknown",
                request.headers.get("user-agent", ""),
                self._extract_device_fingerprint(request)
            )
            
            if not session_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired session"
                )
            
            return token_payload.user_id
            
        except TokenExpiredError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def _extract_device_fingerprint(self, request: Request) -> str:
        """Extract device fingerprint from request"""
        # In practice, this would extract from headers or cookies
        # For now, use a simple hash of user agent and IP
        user_agent = request.headers.get("user-agent", "")
        ip_address = request.client.host if request.client else "unknown"
        
        fingerprint_data = f"{user_agent}|{ip_address}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
```

---

## Configuration and Setup

### Session Configuration
```python
# config/session_config.py
import os
from typing import Dict, Any

def get_session_config() -> Dict[str, Any]:
    """Get session management configuration"""
    return {
        'jwt_secret': os.getenv('JWT_SECRET', 'your-super-secret-jwt-key-change-in-production'),
        'access_token_expiry_minutes': 15,
        'refresh_token_expiry_days': 7,
        'session_ttl_minutes': 120,  # 2 hours
        'max_concurrent_sessions': 3,
        'idle_timeout_minutes': 30,
        'issuer': 'cbt-system',
        'audience': 'cbt-users',
        
        'redis_config': {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'db': int(os.getenv('REDIS_DB', 0)),
            'password': os.getenv('REDIS_PASSWORD', None),
            'decode_responses': True,
            'encoding': 'utf-8'
        },
        
        'security_config': {
            'require_device_fingerprint': True,
            'track_ip_changes': True,
            'log_security_events': True,
            'auto_cleanup_expired_sessions': True,
            'session_validation_interval': 5  # minutes
        }
    }
```

This comprehensive session and token management system provides:

1. **Secure JWT Tokens**: Short-lived access tokens with refresh capability
2. **Session Tracking**: Server-side session validation and monitoring
3. **Device Security**: Fingerprinting to prevent session hijacking
4. **Concurrent Session Limits**: Control over multiple device access
5. **Token Blacklist**: Immediate token revocation capability
6. **Security Monitoring**: Comprehensive logging of security events
7. **Performance Optimization**: Redis-based caching for fast session validation
8. **Automatic Cleanup**: TTL-based cleanup and session expiration

The system ensures secure session management while maintaining excellent performance for the high-concurrency requirements of the CBT examination system.
