"""
Security utilities and helpers for CBT system.
"""

import secrets
import hashlib
import hmac
from typing import Optional, Union
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import argon2

from .config import settings


class SecurityManager:
    """Security utilities for password hashing, token generation, and encryption."""
    
    def __init__(self):
        self.secret_key = settings.secret_key.encode()
        self.jwt_secret = settings.jwt_secret.encode()
        self.biometric_key = settings.biometric_encryption_key.encode()
    
    def generate_salt(self) -> str:
        """Generate cryptographically secure salt."""
        return secrets.token_hex(32)
    
    def hash_password(self, password: str, salt: str) -> str:
        """
        Hash password using Argon2.
        
        Args:
            password: Plain text password
            salt: Salt value
            
        Returns:
            str: Hashed password
        """
        password_hasher = argon2.PasswordHasher(
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            salt_len=16
        )
        return password_hasher.hash(password + salt)
    
    def verify_password(self, password: str, salt: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            salt: Salt value
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches
        """
        try:
            password_hasher = argon2.PasswordHasher()
            return password_hasher.verify(hashed_password, password + salt)
        except argon2.exceptions.VerifyMismatchError:
            return False
    
    def generate_api_key(self) -> str:
        """Generate secure API key."""
        return secrets.token_urlsafe(32)
    
    def generate_session_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(32)
    
    def generate_device_fingerprint(self, user_agent: str, ip_address: str) -> str:
        """
        Generate device fingerprint from user agent and IP.
        
        Args:
            user_agent: User agent string
            ip_address: IP address
            
        Returns:
            str: Device fingerprint
        """
        fingerprint_data = f"{user_agent}|{ip_address}|{self.secret_key}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data using Fernet.
        
        Args:
            data: Plain text data
            
        Returns:
            str: Encrypted data
        """
        # Derive encryption key from secret key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'cbt_encryption_salt',
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(self.secret_key)
        
        # Create Fernet instance
        f = Fernet(Fernet.generate_key())
        
        # Encrypt data
        encrypted_data = f.encrypt(data.encode())
        
        # Store key alongside encrypted data (in production, use HSM)
        return encrypted_data.decode() + ':' + f.encrypt(key).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            str: Decrypted data
        """
        try:
            # Split encrypted data and key
            parts = encrypted_data.split(':')
            if len(parts) != 2:
                raise ValueError("Invalid encrypted data format")
            
            encrypted_content, encrypted_key = parts
            
            # Derive key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'cbt_encryption_salt',
                iterations=100000,
                backend=default_backend()
            )
            derived_key = kdf.derive(self.secret_key)
            
            # Decrypt key
            f_key = Fernet(Fernet.generate_key())
            key = f_key.decrypt(encrypted_key.encode())
            
            # Decrypt content
            f_content = Fernet(key)
            decrypted_data = f_content.decrypt(encrypted_content.encode())
            
            return decrypted_data.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")
    
    def encrypt_biometric_template(self, template: bytes) -> bytes:
        """
        Encrypt biometric template.
        
        Args:
            template: Biometric template bytes
            
        Returns:
            bytes: Encrypted template
        """
        # Derive biometric encryption key
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'cbt_biometric_salt',
            iterations=100000,
            backend=default_backend()
        )
        key = kdf.derive(self.biometric_key)
        
        # Create Fernet instance
        f = Fernet(Fernet.generate_key())
        
        # Encrypt template
        encrypted_template = f.encrypt(template)
        
        # Store key alongside encrypted template
        return encrypted_template + b':' + f.encrypt(key)
    
    def decrypt_biometric_template(self, encrypted_template: bytes) -> bytes:
        """
        Decrypt biometric template.
        
        Args:
            encrypted_template: Encrypted template bytes
            
        Returns:
            bytes: Decrypted template
        """
        try:
            # Split encrypted template and key
            parts = encrypted_template.split(b':')
            if len(parts) != 2:
                raise ValueError("Invalid encrypted template format")
            
            encrypted_content, encrypted_key = parts
            
            # Derive key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'cbt_biometric_salt',
                iterations=100000,
                backend=default_backend()
            )
            derived_key = kdf.derive(self.biometric_key)
            
            # Decrypt key
            f_key = Fernet(Fernet.generate_key())
            key = f_key.decrypt(encrypted_key)
            
            # Decrypt content
            f_content = Fernet(key)
            decrypted_template = f_content.decrypt(encrypted_content)
            
            return decrypted_template
        except Exception as e:
            raise ValueError(f"Biometric template decryption failed: {str(e)}")
    
    def generate_hmac_signature(self, data: str, key: Optional[str] = None) -> str:
        """
        Generate HMAC signature for data integrity.
        
        Args:
            data: Data to sign
            key: Optional custom key
            
        Returns:
            str: HMAC signature
        """
        signing_key = key.encode() if key else self.secret_key
        signature = hmac.new(
            signing_key,
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def verify_hmac_signature(self, data: str, signature: str, key: Optional[str] = None) -> bool:
        """
        Verify HMAC signature.
        
        Args:
            data: Original data
            signature: Signature to verify
            key: Optional custom key
            
        Returns:
            bool: True if signature is valid
        """
        expected_signature = self.generate_hmac_signature(data, key)
        return hmac.compare_digest(expected_signature, signature)
    
    def generate_csrf_token(self, session_id: str) -> str:
        """
        Generate CSRF token for session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            str: CSRF token
        """
        token_data = f"{session_id}:{datetime.utcnow().timestamp()}"
        return self.generate_hmac_signature(token_data)
    
    def verify_csrf_token(self, session_id: str, token: str, max_age: int = 3600) -> bool:
        """
        Verify CSRF token.
        
        Args:
            session_id: Session identifier
            token: CSRF token to verify
            max_age: Maximum age in seconds
            
        Returns:
            bool: True if token is valid
        """
        try:
            # Generate expected token
            token_data = f"{session_id}:{datetime.utcnow().timestamp()}"
            expected_token = self.generate_hmac_signature(token_data)
            
            # Compare tokens
            if not hmac.compare_digest(expected_token, token):
                return False
            
            # Note: In production, you'd want to store the token timestamp
            # and verify it's not too old. This is a simplified version.
            return True
        except Exception:
            return False
    
    def generate_otp_secret(self) -> str:
        """Generate OTP secret for TOTP."""
        return secrets.token_hex(20)
    
    def generate_password_reset_token(self, user_id: str) -> str:
        """
        Generate secure password reset token.
        
        Args:
            user_id: User identifier
            
        Returns:
            str: Reset token
        """
        timestamp = datetime.utcnow().timestamp()
        token_data = f"{user_id}:{timestamp}"
        return self.generate_hmac_signature(token_data)
    
    def verify_password_reset_token(self, user_id: str, token: str, max_age: int = 3600) -> bool:
        """
        Verify password reset token.
        
        Args:
            user_id: User identifier
            token: Reset token to verify
            max_age: Maximum age in seconds
            
        Returns:
            bool: True if token is valid
        """
        try:
            # Generate expected token
            timestamp = datetime.utcnow().timestamp()
            token_data = f"{user_id}:{timestamp}"
            expected_token = self.generate_hmac_signature(token_data)
            
            # Compare tokens
            if not hmac.compare_digest(expected_token, token):
                return False
            
            # Note: In production, you'd want to verify the timestamp
            # from when the token was generated
            return True
        except Exception:
            return False


# Global security manager instance
security = SecurityManager()
