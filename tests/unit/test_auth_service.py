"""
Unit tests for authentication service.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

from src.cbt.services.auth_service import AuthService
from src.cbt.models.user import User
from src.cbt.core.security import security
from src.cbt.core.exceptions import AuthenticationError, AuthorizationError


@pytest.mark.unit
class TestAuthService:
    """Test cases for AuthService."""
    
    @pytest.fixture
    def auth_service(self, test_session):
        """Create AuthService instance for testing."""
        return AuthService(test_session)
    
    @pytest.fixture
    def mock_user(self):
        """Create mock user for testing."""
        user = Mock(spec=User)
        user.id = "test-user-id"
        user.email = "test@example.com"
        user.full_name = "Test User"
        user.role = "student"
        user.is_active = True
        user.password_hash = "$2b$12$hashed_password_here"
        user.created_at = datetime.utcnow()
        user.last_login = None
        return user
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, sample_user_data):
        """Test successful user registration."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # User doesn't exist
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(security, 'hash_password', return_value='hashed_password'):
                with patch.object(auth_service, '_create_user_record') as mock_create:
                    mock_create.return_value = Mock(id='user-id')
                    
                    result = await auth_service.register_user(sample_user_data)
                    
                    assert result['email'] == sample_user_data['email']
                    assert result['full_name'] == sample_user_data['full_name']
                    assert result['role'] == sample_user_data['role']
                    mock_create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, auth_service, sample_user_data, mock_user):
        """Test registration with existing email."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user  # User exists
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with pytest.raises(AuthenticationError, match="Email already registered"):
                await auth_service.register_user(sample_user_data)
    
    @pytest.mark.asyncio
    async def test_register_user_invalid_email(self, auth_service, sample_user_data):
        """Test registration with invalid email."""
        sample_user_data['email'] = 'invalid-email'
        
        with pytest.raises(AuthenticationError, match="Invalid email format"):
            await auth_service.register_user(sample_user_data)
    
    @pytest.mark.asyncio
    async def test_register_user_weak_password(self, auth_service, sample_user_data):
        """Test registration with weak password."""
        sample_user_data['password'] = 'weak'
        
        with pytest.raises(AuthenticationError, match="Password does not meet security requirements"):
            await auth_service.register_user(sample_user_data)
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_user):
        """Test successful user authentication."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(security, 'verify_password', return_value=True):
                with patch.object(auth_service, '_update_last_login'):
                    result = await auth_service.authenticate_user('test@example.com', 'password')
                    
                    assert result['user_id'] == mock_user.id
                    assert result['email'] == mock_user.email
                    assert result['role'] == mock_user.role
                    assert 'access_token' in result
                    assert 'refresh_token' in result
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_email(self, auth_service):
        """Test authentication with invalid email."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None  # User not found
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with pytest.raises(AuthenticationError, match="Invalid credentials"):
                await auth_service.authenticate_user('nonexistent@example.com', 'password')
    
    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service, mock_user):
        """Test authentication with invalid password."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(security, 'verify_password', return_value=False):
                with pytest.raises(AuthenticationError, match="Invalid credentials"):
                    await auth_service.authenticate_user('test@example.com', 'wrong_password')
    
    @pytest.mark.asyncio
    async def test_authenticate_user_inactive(self, auth_service, mock_user):
        """Test authentication with inactive user."""
        mock_user.is_active = False
        
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with pytest.raises(AuthenticationError, match="Account is deactivated"):
                await auth_service.authenticate_user('test@example.com', 'password')
    
    @pytest.mark.asyncio
    async def test_refresh_token_success(self, auth_service, mock_user):
        """Test successful token refresh."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(security, 'verify_token', return_value={'sub': mock_user.id}):
                with patch.object(security, 'create_access_token', return_value='new_access_token'):
                    result = await auth_service.refresh_token('valid_refresh_token')
                    
                    assert result['access_token'] == 'new_access_token'
                    assert result['token_type'] == 'bearer'
    
    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, auth_service):
        """Test token refresh with invalid token."""
        with patch.object(security, 'verify_token', side_effect=jwt.InvalidTokenError):
            with pytest.raises(AuthenticationError, match="Invalid refresh token"):
                await auth_service.refresh_token('invalid_token')
    
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_user):
        """Test successful password change."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(security, 'verify_password', return_value=True):
                with patch.object(security, 'hash_password', return_value='new_hashed_password'):
                    with patch.object(auth_service, '_update_user_password'):
                        result = await auth_service.change_password(
                            mock_user.id, 'old_password', 'new_password'
                        )
                        
                        assert result['success'] is True
                        assert result['message'] == "Password changed successfully"
    
    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, auth_service, mock_user):
        """Test password change with wrong current password."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(security, 'verify_password', return_value=False):
                with pytest.raises(AuthenticationError, match="Current password is incorrect"):
                    await auth_service.change_password(
                        mock_user.id, 'wrong_password', 'new_password'
                    )
    
    @pytest.mark.asyncio
    async def test_reset_password_request(self, auth_service, mock_user):
        """Test password reset request."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(auth_service, '_generate_reset_token', return_value='reset_token'):
                with patch.object(auth_service, '_send_reset_email'):
                    result = await auth_service.reset_password_request('test@example.com')
                    
                    assert result['success'] is True
                    assert result['message'] == "Password reset email sent"
    
    @pytest.mark.asyncio
    async def test_reset_password_confirm(self, auth_service, mock_user):
        """Test password reset confirmation."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(auth_service, '_verify_reset_token', return_value=True):
                with patch.object(security, 'hash_password', return_value='new_hashed_password'):
                    with patch.object(auth_service, '_update_user_password'):
                        result = await auth_service.reset_password_confirm(
                            'reset_token', 'new_password'
                        )
                        
                        assert result['success'] is True
                        assert result['message'] == "Password reset successfully"
    
    @pytest.mark.asyncio
    async def test_logout_user(self, auth_service, mock_user):
        """Test user logout."""
        with patch.object(auth_service, '_invalidate_token'):
            result = await auth_service.logout_user('access_token')
            
            assert result['success'] is True
            assert result['message'] == "Logged out successfully"
    
    @pytest.mark.asyncio
    async def test_validate_token_success(self, auth_service, mock_user):
        """Test successful token validation."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(security, 'verify_token', return_value={'sub': mock_user.id}):
                result = await auth_service.validate_token('valid_token')
                
                assert result['valid'] is True
                assert result['user_id'] == mock_user.id
                assert result['email'] == mock_user.email
    
    @pytest.mark.asyncio
    async def test_validate_token_invalid(self, auth_service):
        """Test token validation with invalid token."""
        with patch.object(security, 'verify_token', side_effect=jwt.InvalidTokenError):
            result = await auth_service.validate_token('invalid_token')
            
            assert result['valid'] is False
            assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_check_permission_success(self, auth_service, mock_user):
        """Test successful permission check."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(auth_service, '_user_has_permission', return_value=True):
                result = await auth_service.check_permission(mock_user.id, 'exam.read')
                
                assert result['authorized'] is True
    
    @pytest.mark.asyncio
    async def test_check_permission_denied(self, auth_service, mock_user):
        """Test permission check when denied."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(auth_service, '_user_has_permission', return_value=False):
                with pytest.raises(AuthorizationError, match="Insufficient permissions"):
                    await auth_service.check_permission(mock_user.id, 'admin.access')
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, auth_service, mock_user):
        """Test getting user profile."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            result = await auth_service.get_user_profile(mock_user.id)
            
            assert result['id'] == mock_user.id
            assert result['email'] == mock_user.email
            assert result['full_name'] == mock_user.full_name
            assert result['role'] == mock_user.role
    
    @pytest.mark.asyncio
    async def test_update_user_profile(self, auth_service, mock_user):
        """Test updating user profile."""
        update_data = {
            'full_name': 'Updated Name',
            'department': 'Updated Department'
        }
        
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(auth_service, '_update_user_record'):
                result = await auth_service.update_user_profile(mock_user.id, update_data)
                
                assert result['success'] is True
                assert result['message'] == "Profile updated successfully"
    
    @pytest.mark.asyncio
    async def test_deactivate_user(self, auth_service, mock_user):
        """Test user deactivation."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(auth_service, '_update_user_status'):
                result = await auth_service.deactivate_user(mock_user.id)
                
                assert result['success'] is True
                assert result['message'] == "User deactivated successfully"
    
    @pytest.mark.asyncio
    async def test_activate_user(self, auth_service, mock_user):
        """Test user activation."""
        mock_user.is_active = False
        
        # Mock database operations
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = mock_user
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            with patch.object(auth_service, '_update_user_status'):
                result = await auth_service.activate_user(mock_user.id)
                
                assert result['success'] is True
                assert result['message'] == "User activated successfully"
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, auth_service, mock_user):
        """Test getting user sessions."""
        # Mock database operations
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = [mock_user]
        
        with patch.object(auth_service.db, 'execute', return_value=mock_result):
            result = await auth_service.get_user_sessions(mock_user.id)
            
            assert isinstance(result, list)
            assert len(result) >= 0
    
    @pytest.mark.asyncio
    async def test_revoke_user_sessions(self, auth_service, mock_user):
        """Test revoking user sessions."""
        with patch.object(auth_service, '_invalidate_all_user_tokens'):
            result = await auth_service.revoke_user_sessions(mock_user.id)
            
            assert result['success'] is True
            assert result['message'] == "All sessions revoked successfully"
    
    # Helper method tests
    
    @pytest.mark.asyncio
    async def test_create_user_record(self, auth_service, sample_user_data):
        """Test creating user record."""
        with patch.object(auth_service.db, 'add') as mock_add:
            with patch.object(auth_service.db, 'commit') as mock_commit:
                user = await auth_service._create_user_record(sample_user_data, 'hashed_password')
                
                mock_add.assert_called_once()
                mock_commit.assert_called_once()
                assert user.email == sample_user_data['email']
                assert user.full_name == sample_user_data['full_name']
    
    @pytest.mark.asyncio
    async def test_update_user_password(self, auth_service, mock_user):
        """Test updating user password."""
        with patch.object(auth_service.db, 'commit') as mock_commit:
            await auth_service._update_user_password(mock_user.id, 'new_hashed_password')
            
            mock_commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_last_login(self, auth_service, mock_user):
        """Test updating last login."""
        with patch.object(auth_service.db, 'commit') as mock_commit:
            await auth_service._update_last_login(mock_user.id)
            
            mock_commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_reset_token(self, auth_service, mock_user):
        """Test generating reset token."""
        with patch.object(security, 'create_reset_token', return_value='reset_token'):
            token = await auth_service._generate_reset_token(mock_user.email)
            
            assert token == 'reset_token'
    
    @pytest.mark.asyncio
    async def test_verify_reset_token(self, auth_service):
        """Test verifying reset token."""
        with patch.object(security, 'verify_reset_token', return_value='test@example.com'):
            result = await auth_service._verify_reset_token('valid_token')
            
            assert result == 'test@example.com'
    
    @pytest.mark.asyncio
    async def test_send_reset_email(self, auth_service):
        """Test sending reset email."""
        with patch.object(auth_service, '_send_email') as mock_send:
            await auth_service._send_reset_email('test@example.com', 'reset_token')
            
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_invalidate_token(self, auth_service):
        """Test token invalidation."""
        with patch.object(auth_service, '_add_token_to_blacklist'):
            await auth_service._invalidate_token('access_token')
    
    @pytest.mark.asyncio
    async def test_user_has_permission(self, auth_service, mock_user):
        """Test user permission check."""
        # Test admin permissions
        mock_user.role = 'admin'
        assert await auth_service._user_has_permission(mock_user.id, 'admin.access') is True
        
        # Test student permissions
        mock_user.role = 'student'
        assert await auth_service._user_has_permission(mock_user.id, 'exam.read') is True
        assert await auth_service._user_has_permission(mock_user.id, 'admin.access') is False
