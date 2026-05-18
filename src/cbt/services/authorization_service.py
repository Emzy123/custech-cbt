"""
Authorization service for role-based access control and permissions.
"""

from typing import Set, Dict, Any, Optional, List
from datetime import datetime, timezone

from ..models.user import User, UserRole, UserRoleAssignment
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
        
        Args:
            user_id: User ID
            permission: Permission to check
            resource_type: Type of resource
            resource_id: Specific resource ID
            
        Returns:
            bool: User has permission
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
            
        except Exception as e:
            # Log error and deny by default
            return False
    
    async def get_user_permissions(self, user_id: str) -> Set[str]:
        """
        Get all permissions for user (cached).
        
        Args:
            user_id: User ID
            
        Returns:
            Set[str]: User permissions
        """
        cache_key = f"user_permissions:{user_id}"
        
        # Try cache first
        cached_permissions = await self.cache.get(cache_key)
        if cached_permissions:
            return set(cached_permissions)
        
        # Build from roles
        permissions = set()
        user_roles = await self.get_user_roles(user_id)
        
        # Define role permissions
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
                "course.read",
                "exam.read",
                "exam.schedule",
                "exam.publish",
                "exam.cancel",
                "grade.read",
                "grade.approve",
                "result.read",
                "result.publish",
                "result.export",
                "system.monitor",
            ],
            "INVIGILATOR": [
                "user.read",
                "student.read",
                "exam.read",
                "exam.invigilate",
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
                "question.encrypt",
                "question.decrypt",
                "question.security.admin",
                "question.security.read",
                "question.security.audit",
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
                "exam.invigilate",
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
                "security.scan",
                "security.read",
                "security.penetration_test",
                "security.harden",
                "security.configure",
                "security.audit",
                "security.remediate",
                "security.acknowledge",
                "security.manage",
                "biometric.register",
                "biometric.verify",
                "biometric.update",
                "biometric.deactivate",
                "biometric.read",
                "biometric.admin",
                "pilot.manage",
                "pilot.read",
                "deployment.manage",
                "deployment.execute",
                "deployment.read",
            ],
            "SUPER_ADMIN": [
                # All permissions
                "*"
            ]
        }
        
        # Collect permissions from all roles
        for role in user_roles:
            role_perms = role_permissions.get(role, [])
            permissions.update(role_perms)
        
        # Cache permissions
        await self.cache.set(cache_key, list(permissions), self.user_cache_ttl)
        
        return permissions
    
    async def get_user_roles(self, user_id: str) -> List[str]:
        """
        Get all active roles for user.

        Args:
            user_id: User ID

        Returns:
            List[str]: User roles
        """
        cache_key = f"user_roles:{user_id}"

        # Try cache first
        cached_roles = await self.cache.get(cache_key)
        if cached_roles:
            return cached_roles

        # Query database for user's role assignments
        now = datetime.now(timezone.utc)
        role_assignments = await UserRoleAssignment.find(
            {"user_id": user_id}
        ).to_list()

        # Filter active roles (not expired)
        roles = []
        for assignment in role_assignments:
            if assignment.expires_at is None or assignment.expires_at > now:
                roles.append(assignment.role.value)

        # Cache roles
        await self.cache.set(cache_key, roles, self.user_cache_ttl)

        return roles
    
    async def invalidate_user_cache(self, user_id: str):
        """
        Invalidate cached user permissions and roles.
        
        Args:
            user_id: User ID
        """
        await self.cache.delete(f"user_permissions:{user_id}")
        await self.cache.delete(f"user_roles:{user_id}")
    
    async def check_role_permission(self, role: str, permission: str) -> bool:
        """
        Check if role has permission.
        
        Args:
            role: Role name
            permission: Permission to check
            
        Returns:
            bool: Role has permission
        """
        # Define role permissions
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
                "user.read", "student.read", "student.import", "course.read",
                "exam.read", "exam.schedule", "exam.publish", "exam.cancel",
                "grade.read", "grade.approve", "result.read", "result.publish", "result.export",
                "system.monitor"
            },
            "INVIGILATOR": {
                "user.read", "student.read", "exam.read", "system.monitor"
            },
            "ADMINISTRATOR": {
                "user.read", "user.create", "user.update",
                "student.read", "student.create", "student.update", "student.import",
                "course.read", "course.create", "course.update",
                "question.read", "question.create", "question.update", "question.delete",
                "question.import", "question.export",
                "exam.read", "exam.create", "exam.update", "exam.delete", "exam.schedule",
                "exam.publish", "exam.cancel",
                "grade.read", "grade.update", "grade.approve",
                "result.read", "result.update", "result.publish", "result.export",
                "system.config", "system.monitor", "system.audit",
                "security.user_roles", "security.permissions", "security.sessions"
            },
            "SUPER_ADMIN": {"*"}
        }
        
        permissions = role_permissions.get(role, set())
        return permission in permissions or "*" in permissions
    
    async def get_accessible_resources(self, user_id: str, resource_type: str,
                                     permission: str) -> List[str]:
        """
        Get list of resources user can access with specific permission.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            permission: Permission required
            
        Returns:
            List[str]: Accessible resource IDs
        """
        # This would query database for resources user can access
        # For now, return empty list
        return []
    
    async def create_custom_policy(self, policy_name: str, description: str,
                                 conditions: List[Dict[str, Any]]) -> bool:
        """
        Create custom authorization policy.
        
        Args:
            policy_name: Policy name
            description: Policy description
            conditions: Policy conditions
            
        Returns:
            bool: Policy creation success
        """
        # This would store custom policies in database
        # For now, return True
        return True
    
    async def evaluate_policy(self, policy_name: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate custom policy against context.
        
        Args:
            policy_name: Policy name
            context: Evaluation context
            
        Returns:
            bool: Policy evaluation result
        """
        # This would evaluate stored policy
        # For now, return True
        return True
    
    async def get_permission_hierarchy(self) -> Dict[str, List[str]]:
        """
        Get permission hierarchy for UI display.
        
        Returns:
            Dict[str, List[str]]: Permission hierarchy
        """
        return {
            "User Management": [
                "user.read", "user.create", "user.update", "user.delete"
            ],
            "Student Management": [
                "student.read", "student.create", "student.update", "student.delete", "student.import"
            ],
            "Course Management": [
                "course.read", "course.create", "course.update", "course.delete"
            ],
            "Question Management": [
                "question.read", "question.create", "question.update", "question.delete",
                "question.import", "question.export", "question.review",
                "question.encrypt", "question.decrypt",
                "question.security.admin", "question.security.read", "question.security.audit",
            ],
            "Examination Management": [
                "exam.read", "exam.create", "exam.update", "exam.delete", "exam.schedule",
                "exam.publish", "exam.cancel", "exam.start", "exam.active", "exam.manage", "exam.invigilate",
            ],
            "Grading Management": [
                "grade.read", "grade.update", "grade.approve"
            ],
            "Result Management": [
                "result.read", "result.update", "result.publish", "result.export"
            ],
            "System Administration": [
                "system.config", "system.monitor", "system.audit", "system.backup"
            ],
            "Security Management": [
                "security.user_roles", "security.permissions", "security.sessions",
                "security.scan", "security.read", "security.penetration_test",
                "security.harden", "security.configure", "security.audit",
                "security.remediate", "security.acknowledge", "security.manage",
                "biometric.register", "biometric.verify", "biometric.update",
                "biometric.deactivate", "biometric.read", "biometric.admin",
            ],
            "Pilot and Deployment": [
                "pilot.manage", "pilot.read",
                "deployment.manage", "deployment.execute", "deployment.read",
            ],
        }

    async def get_role_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get role definitions for UI display.
        
        Returns:
            Dict[str, Dict[str, Any]]: Role definitions
        """
        return {
            "STUDENT": {
                "name": "Student",
                "description": "Regular student with exam-taking capabilities",
                "permissions": [
                    "user.read", "student.read", "course.read", "question.read",
                    "exam.read", "exam.start", "exam.submit", "exam.review", "result.read"
                ]
            },
            "LECTURER": {
                "name": "Lecturer",
                "description": "Course instructor with question and exam management",
                "permissions": [
                    "user.read", "student.read", "course.read", "course.create", "course.update",
                    "question.read", "question.create", "question.update", "question.delete",
                    "exam.read", "exam.create", "exam.update", "exam.delete", "exam.schedule",
                    "grade.read", "grade.update", "result.read", "result.export"
                ]
            },
            "EXAM_OFFICER": {
                "name": "Examination Officer",
                "description": "Exam coordination and administration",
                "permissions": [
                    "user.read", "student.read", "student.import", "course.read",
                    "exam.read", "exam.schedule", "exam.publish", "exam.cancel",
                    "grade.read", "grade.approve", "result.read", "result.publish", "result.export",
                    "system.monitor"
                ]
            },
            "INVIGILATOR": {
                "name": "Invigilator",
                "description": "Exam supervision and proctoring",
                "permissions": [
                    "user.read", "student.read", "exam.read", "exam.invigilate", "system.monitor"
                ]
            },
            "ADMINISTRATOR": {
                "name": "Administrator",
                "description": "System administrator with full access",
                "permissions": [
                    "user.read", "user.create", "user.update", "user.delete",
                    "student.read", "student.create", "student.update", "student.import",
                    "course.read", "course.create", "course.update",
                    "question.read", "question.create", "question.update", "question.delete",
                    "question.import", "question.export", "question.review",
                    "question.encrypt", "question.decrypt",
                    "question.security.admin", "question.security.read", "question.security.audit",
                    "exam.read", "exam.create", "exam.update", "exam.delete", "exam.schedule",
                    "exam.publish", "exam.cancel", "exam.start", "exam.active", "exam.manage", "exam.invigilate",
                    "grade.read", "grade.update", "grade.approve",
                    "result.read", "result.update", "result.publish", "result.export",
                    "system.config", "system.monitor", "system.audit",
                    "security.user_roles", "security.permissions", "security.sessions",
                    "security.scan", "security.read", "security.penetration_test",
                    "security.harden", "security.configure", "security.audit",
                    "security.remediate", "security.acknowledge", "security.manage",
                    "biometric.register", "biometric.verify", "biometric.update",
                    "biometric.deactivate", "biometric.read", "biometric.admin",
                    "pilot.manage", "pilot.read",
                    "deployment.manage", "deployment.execute", "deployment.read",
                ]
            },
            "SUPER_ADMIN": {
                "name": "Super Administrator",
                "description": "Super admin with complete system access",
                "permissions": ["*"]
            }
        }
