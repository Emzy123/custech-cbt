"""
Authorization service for role-based access control and permissions.
"""

from typing import Set, Dict, Any, Optional, List
from datetime import datetime, timezone

from ..models.user import User
from ..core.redis import cache_manager
from ..core.config import settings


class AuthorizationService:
    """Authorization service for RBAC and permissions."""
    
    def __init__(self, cache):
        self.cache = cache
        self.permission_cache_ttl = 300  # 5 minutes
        self.user_cache_ttl = 600  # 10 minutes
    
    async def check_permission(self, user_id: str, permission: str,
                             resource_type: str, resource_id: Optional[str] = None) -> bool:
        """
        Check if user has permission for resource.
        """
        try:
            # Get user permissions (cached)
            user_permissions = await self.get_user_permissions(user_id)
            
            # Check direct permission
            if permission in user_permissions:
                return True
            
            # Check wildcard permissions
            if f"{resource_type}.*" in user_permissions:
                return True
            
            # Check admin permissions
            if "system.admin" in user_permissions:
                return True
            
            # Check super admin wildcard (all permissions)
            if "*" in user_permissions:
                return True
            
            return False
            
        except Exception:
            return False
    
    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        Get all permissions for user (cached).
        """
        cache_key = f"user_permissions:{user_id}"
        
        cached_permissions = await self.cache.get(cache_key)
        if cached_permissions:
            return set(cached_permissions)
        
        permissions = set()
        user_roles = await self.get_user_roles(user_id)
        
        role_permissions = {
            "STUDENT": [
                "user.read",
                "student.read",
                "course.read",
                "question.read",
                "exam.read",
                "exam.start",
                "exam.submit",
                "exam.review",
                "result.read",
            ],
            "LECTURER": [
                "user.read",
                "student.read",
                "course.read",
                "course.create",
                "course.update",
                "question.read",
                "question.create",
                "question.update",
                "question.delete",
                "exam.read",
                "exam.create",
                "exam.update",
                "exam.delete",
                "exam.schedule",
                "grade.read",
                "grade.update",
                "result.read",
                "result.export",
            ],
            "EXAM_OFFICER": [
                "user.read",
                "student.read",
                "student.import",
                "student.create",
                "student.update",
                "student.delete",
                "academic.read",
                "course.read",
                "exam.read",
                "exam.create",
                "exam.update",
                "exam.schedule",
                "exam.publish",
                "exam.cancel",
                "exam.manage",
                "grade.read",
                "grade.approve",
                "result.read",
                "result.publish",
                "result.export",
                "system.monitor",
            ],
            "ADMINISTRATOR": [
                "user.read",
                "user.create",
                "user.update",
                "user.delete",
                "student.read",
                "student.create",
                "student.update",
                "student.delete",
                "student.import",
                "course.read",
                "course.create",
                "course.update",
                "question.read",
                "question.create",
                "question.update",
                "question.delete",
                "question.import",
                "question.export",
                "question.review",
                "exam.read",
                "exam.create",
                "exam.update",
                "exam.delete",
                "exam.schedule",
                "exam.publish",
                "exam.cancel",
                "exam.start",
                "exam.active",
                "exam.manage",
                "academic.read",
                "academic.create",
                "academic.update",
                "grade.read",
                "grade.update",
                "grade.approve",
                "result.read",
                "result.update",
                "result.publish",
                "result.export",
                "system.config",
                "system.monitor",
                "system.audit",
                "security.user_roles",
                "security.permissions",
                "security.sessions",
                "security.read",
            ],
            "SUPER_ADMIN": [
                "*"
            ]
        }
        
        for role in user_roles:
            role_perms = role_permissions.get(role.upper(), [])
            permissions.update(role_perms)
        
        await self.cache.set(cache_key, list(permissions), self.user_cache_ttl)
        
        return permissions
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all active roles for user directly from User document.
        """
        cache_key = f"user_roles:{user_id}"

        cached_roles = await self.cache.get(cache_key)
        if cached_roles:
            return cached_roles

        user = await User.find_one(User.id == user_id)
        if not user or not user.is_active:
            return []

        # Map simplified "admin" role to full administrator privileges to preserve compatibility
        mapped_role = user.role.upper()
        if mapped_role == "ADMIN":
            roles = ["ADMINISTRATOR", "SUPER_ADMIN", "EXAM_OFFICER"]
        else:
            roles = [mapped_role]

        await self.cache.set(cache_key, roles, self.user_cache_ttl)

        return roles
    
    async def invalidate_user_cache(self, user_id: str):
        """
        Invalidate cached user permissions and roles.
        """
        await self.cache.delete(f"user_permissions:{user_id}")
        await self.cache.delete(f"user_roles:{user_id}")
    
    async def check_role_permission(self, role: str, permission: str) -> bool:
        """
        Check if role has permission.
        """
        role_permissions = {
            "STUDENT": {
                "user.read", "student.read", "course.read", "question.read",
                "exam.read", "exam.start", "exam.submit", "exam.review", "result.read"
            },
            "LECTURER": {
                "user.read", "student.read", "course.read", "course.create", "course.update",
                "question.read", "question.create", "question.update", "question.delete",
                "exam.read", "exam.create", "exam.update", "exam.delete", "exam.schedule",
                "grade.read", "grade.update", "result.read", "result.export"
            },
            "EXAM_OFFICER": {
                "user.read", "student.read", "student.import", "student.create", "student.update", "student.delete", "academic.read",
                "course.read", "exam.read", "exam.create", "exam.update",
                "exam.schedule", "exam.publish", "exam.cancel", "exam.manage",
                "grade.read", "grade.approve", "result.read", "result.publish",
                "result.export", "system.monitor"
            },
            "ADMINISTRATOR": {
                "*"
            },
            "SUPER_ADMIN": {
                "*"
            }
        }
        
        role_perms = role_permissions.get(role.upper(), set())
        if "*" in role_perms:
            return True
            
        return permission in role_perms or f"{permission.split('.')[0]}.*" in role_perms
