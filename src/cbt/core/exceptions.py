"""Custom exceptions for the CBT application."""

class CBTException(Exception):
    """Base exception for CBT application."""
    pass

class ValidationError(CBTException):
    """Raised when validation fails."""
    pass

class AuthenticationError(CBTException):
    """Raised when authentication fails."""
    pass

class AuthorizationError(CBTException):
    """Raised when authorization fails."""
    pass


class SecurityError(CBTException):
    """Raised when question or data security constraints are violated."""
    pass


class NotFoundError(CBTException):
    """Raised when a resource is not found."""
    pass

class ConflictError(CBTException):
    """Raised when there's a conflict in data."""
    pass

class BiometricVerificationError(CBTException):
    """Raised when biometric verification fails."""
    pass
