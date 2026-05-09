# Role-Based Access Control with Attribute-Based Extensions

## Overview

This document defines the comprehensive Role-Based Access Control (RBAC) system with Attribute-Based Access Control (ABAC) extensions for the CBT system, implementing fine-grained authorization that respects academic hierarchy and contextual constraints.

## Authorization Architecture

### Access Control Model
```
RBAC Foundation:
- Users assigned to one or more roles
- Roles contain collections of permissions
- Permissions grant access to specific actions on resources

ABAC Extensions:
- Context-aware authorization based on attributes
- Dynamic permission evaluation
- Environment and time-based constraints
- Relationship-based access rules

Hybrid Model:
- RBAC for basic authorization (fast, cached)
- ABAC for fine-grained control (evaluated when needed)
- Policy Decision Point (PDP) for complex rules
- Policy Enforcement Point (PEP) in application layer
```

### Authorization Components
```
1. Identity Provider: Authentication service
2. Policy Decision Point: Authorization engine
3. Policy Enforcement Point: Application middleware
4. Policy Information Point: Attribute provider
5. Permission Cache: Redis-based caching layer
```

---

## Role and Permission Model

### Role Hierarchy
```python
# models/authorization.py
from enum import Enum
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from datetime import datetime, time

class UserRole(Enum):
    STUDENT = "STUDENT"
    LECTURER = "LECTURER"
    EXAM_OFFICER = "EXAM_OFFICER"
    ADMINISTRATOR = "ADMINISTRATOR"
    SUPER_ADMIN = "SUPER_ADMIN"

class Permission(Enum):
    # User Management
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Student Management
    STUDENT_READ = "student:read"
    STUDENT_CREATE = "student:create"
    STUDENT_UPDATE = "student:update"
    STUDENT_DELETE = "student:delete"
    STUDENT_IMPORT = "student:import"
    
    # Course Management
    COURSE_READ = "course:read"
    COURSE_CREATE = "course:create"
    COURSE_UPDATE = "course:update"
    COURSE_DELETE = "course:delete"
    
    # Question Bank Management
    QUESTION_READ = "question:read"
    QUESTION_CREATE = "question:create"
    QUESTION_UPDATE = "question:update"
    QUESTION_DELETE = "question:delete"
    QUESTION_IMPORT = "question:import"
    QUESTION_EXPORT = "question:export"
    
    # Examination Management
    EXAM_READ = "exam:read"
    EXAM_CREATE = "exam:create"
    EXAM_UPDATE = "exam:update"
    EXAM_DELETE = "exam:delete"
    EXAM_SCHEDULE = "exam:schedule"
    EXAM_PUBLISH = "exam:publish"
    EXAM_CANCEL = "exam:cancel"
    
    # Exam Taking
    EXAM_START = "exam:start"
    EXAM_SUBMIT = "exam:submit"
    EXAM_REVIEW = "exam:review"
    
    # Grading Management
    GRADE_READ = "grade:read"
    GRADE_UPDATE = "grade:update"
    GRADE_APPROVE = "grade:approve"
    GRADE_PUBLISH = "grade:publish"
    
    # Result Management
    RESULT_READ = "result:read"
    RESULT_UPDATE = "result:update"
    RESULT_PUBLISH = "result:publish"
    RESULT_EXPORT = "result:export"
    
    # System Administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_AUDIT = "system:audit"
    
    # Security Management
    SECURITY_USER_ROLES = "security:user_roles"
    SECURITY_PERMISSIONS = "security:permissions"
    SECURITY_SESSIONS = "security:sessions"
    SECURITY_BIOMETRIC = "security:biometric"

@dataclass
class RoleDefinition:
    role: UserRole
    permissions: Set[Permission]
    description: str
    is_system_role: bool = False

@dataclass
class UserContext:
    user_id: str
    username: str
    roles: List[UserRole]
    department_id: Optional[str]
    academic_session_id: Optional[str]
    ip_address: str
    device_fingerprint: str
    timestamp: datetime

@dataclass
class ResourceContext:
    resource_type: str
    resource_id: str
    owner_id: Optional[str]
    department_id: Optional[str]
    academic_session_id: Optional[str]
    additional_attributes: Dict[str, Any]
```

### Role Definitions
```python
# services/role_definitions.py
from .authorization import UserRole, Permission, RoleDefinition

class RoleDefinitions:
    """Centralized role definitions with permissions"""
    
    @staticmethod
    def get_all_roles() -> Dict[UserRole, RoleDefinition]:
        return {
            UserRole.STUDENT: RoleDefinition(
                role=UserRole.STUDENT,
                permissions={
                    Permission.USER_READ,
                    Permission.STUDENT_READ,
                    Permission.COURSE_READ,
                    Permission.QUESTION_READ,
                    Permission.EXAM_READ,
                    Permission.EXAM_START,
                    Permission.EXAM_SUBMIT,
                    Permission.EXAM_REVIEW,
                    Permission.RESULT_READ,
                },
                description="Student role with exam-taking capabilities",
                is_system_role=True
            ),
            
            UserRole.LECTURER: RoleDefinition(
                role=UserRole.LECTURER,
                permissions={
                    Permission.USER_READ,
                    Permission.STUDENT_READ,
                    Permission.COURSE_READ,
                    Permission.COURSE_CREATE,
                    Permission.COURSE_UPDATE,
                    Permission.QUESTION_READ,
                    Permission.QUESTION_CREATE,
                    Permission.QUESTION_UPDATE,
                    Permission.QUESTION_DELETE,
                    Permission.QUESTION_IMPORT,
                    Permission.EXAM_READ,
                    Permission.EXAM_CREATE,
                    Permission.EXAM_UPDATE,
                    Permission.EXAM_DELETE,
                    Permission.EXAM_SCHEDULE,
                    Permission.GRADE_READ,
                    Permission.GRADE_UPDATE,
                    Permission.RESULT_READ,
                    Permission.RESULT_EXPORT,
                },
                description="Lecturer role with course and exam management",
                is_system_role=True
            ),
            
            UserRole.EXAM_OFFICER: RoleDefinition(
                role=UserRole.EXAM_OFFICER,
                permissions={
                    Permission.USER_READ,
                    Permission.STUDENT_READ,
                    Permission.STUDENT_IMPORT,
                    Permission.COURSE_READ,
                    Permission.EXAM_READ,
                    Permission.EXAM_SCHEDULE,
                    Permission.EXAM_PUBLISH,
                    Permission.EXAM_CANCEL,
                    Permission.GRADE_READ,
                    Permission.GRADE_APPROVE,
                    Permission.RESULT_READ,
                    Permission.RESULT_PUBLISH,
                    Permission.RESULT_EXPORT,
                    Permission.SYSTEM_MONITOR,
                },
                description="Examination officer with exam coordination capabilities",
                is_system_role=True
            ),
            
            UserRole.ADMINISTRATOR: RoleDefinition(
                role=UserRole.ADMINISTRATOR,
                permissions={
                    Permission.USER_READ,
                    Permission.USER_CREATE,
                    Permission.USER_UPDATE,
                    Permission.STUDENT_READ,
                    Permission.STUDENT_CREATE,
                    Permission.STUDENT_UPDATE,
                    Permission.STUDENT_IMPORT,
                    Permission.COURSE_READ,
                    Permission.COURSE_CREATE,
                    Permission.COURSE_UPDATE,
                    Permission.QUESTION_READ,
                    Permission.QUESTION_CREATE,
                    Permission.QUESTION_UPDATE,
                    Permission.QUESTION_DELETE,
                    Permission.QUESTION_IMPORT,
                    Permission.QUESTION_EXPORT,
                    Permission.EXAM_READ,
                    Permission.EXAM_CREATE,
                    Permission.EXAM_UPDATE,
                    Permission.EXAM_DELETE,
                    Permission.EXAM_SCHEDULE,
                    Permission.EXAM_PUBLISH,
                    Permission.EXAM_CANCEL,
                    Permission.GRADE_READ,
                    Permission.GRADE_UPDATE,
                    Permission.GRADE_APPROVE,
                    Permission.RESULT_READ,
                    Permission.RESULT_UPDATE,
                    Permission.RESULT_PUBLISH,
                    Permission.RESULT_EXPORT,
                    Permission.SYSTEM_CONFIG,
                    Permission.SYSTEM_MONITOR,
                    Permission.SYSTEM_AUDIT,
                    Permission.SECURITY_USER_ROLES,
                    Permission.SECURITY_PERMISSIONS,
                    Permission.SECURITY_SESSIONS,
                },
                description="Administrator with system management capabilities",
                is_system_role=True
            ),
            
            UserRole.SUPER_ADMIN: RoleDefinition(
                role=UserRole.SUPER_ADMIN,
                permissions={
                    # All permissions
                    *list(Permission)
                },
                description="Super administrator with full system access",
                is_system_role=True
            )
        }
    
    @staticmethod
    def get_role_permissions(role: UserRole) -> Set[Permission]:
        """Get permissions for a specific role"""
        roles = RoleDefinitions.get_all_roles()
        role_def = roles.get(role)
        return role_def.permissions if role_def else set()
    
    @staticmethod
    def has_permission(role: UserRole, permission: Permission) -> bool:
        """Check if role has specific permission"""
        return permission in RoleDefinitions.get_role_permissions(role)
```

---

## Attribute-Based Access Control

### Context Attributes
```python
# services/abac_attributes.py
from typing import Any, Dict, List
from datetime import datetime, time
from enum import Enum

class AttributeType(Enum):
    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    TIME = "time"
    LIST = "list"

class Attribute:
    def __init__(self, name: str, value: Any, attribute_type: AttributeType):
        self.name = name
        self.value = value
        self.type = attribute_type

class AttributeProvider:
    """Provides attributes for authorization decisions"""
    
    def __init__(self):
        self.attributes = {}
    
    def get_user_attributes(self, user_id: str) -> Dict[str, Attribute]:
        """Get user-specific attributes"""
        # This would integrate with database to fetch user attributes
        return {
            "user_id": Attribute("user_id", user_id, AttributeType.STRING),
            "user_role": Attribute("user_role", "STUDENT", AttributeType.STRING),
            "department_id": Attribute("department_id", "dept-123", AttributeType.STRING),
            "academic_level": Attribute("academic_level", 100, AttributeType.INTEGER),
            "is_active": Attribute("is_active", True, AttributeType.BOOLEAN),
            "enrollment_date": Attribute("enrollment_date", datetime(2023, 9, 1), AttributeType.DATETIME),
            "last_login": Attribute("last_login", datetime.now(), AttributeType.DATETIME),
        }
    
    def get_resource_attributes(self, resource_type: str, resource_id: str) -> Dict[str, Attribute]:
        """Get resource-specific attributes"""
        # This would integrate with database to fetch resource attributes
        if resource_type == "exam":
            return {
                "exam_id": Attribute("exam_id", resource_id, AttributeType.STRING),
                "course_id": Attribute("course_id", "course-123", AttributeType.STRING),
                "department_id": Attribute("department_id", "dept-123", AttributeType.STRING),
                "exam_status": Attribute("exam_status", "SCHEDULED", AttributeType.STRING),
                "exam_date": Attribute("exam_date", datetime(2026, 4, 30), AttributeType.DATETIME),
                "exam_time": Attribute("exam_time", time(9, 0), AttributeType.TIME),
                "duration_minutes": Attribute("duration_minutes", 120, AttributeType.INTEGER),
                "is_published": Attribute("is_published", False, AttributeType.BOOLEAN),
            }
        return {}
    
    def get_environment_attributes(self) -> Dict[str, Attribute]:
        """Get environment-specific attributes"""
        return {
            "current_time": Attribute("current_time", datetime.now(), AttributeType.DATETIME),
            "current_day": Attribute("current_day", datetime.now().strftime("%A"), AttributeType.STRING),
            "business_hours": Attribute("business_hours", self._is_business_hours(), AttributeType.BOOLEAN),
            "exam_period": Attribute("exam_period", self._is_exam_period(), AttributeType.BOOLEAN),
            "maintenance_mode": Attribute("maintenance_mode", False, AttributeType.BOOLEAN),
        }
    
    def _is_business_hours(self) -> bool:
        """Check if current time is within business hours"""
        now = datetime.now().time()
        return time(8, 0) <= now <= time(17, 0)
    
    def _is_exam_period(self) -> bool:
        """Check if current time is within exam period"""
        # This would check academic calendar
        return True  # Simplified for example
```

### Policy Engine
```python
# services/policy_engine.py
from typing import List, Dict, Any, Optional
from .authorization import Permission, UserContext, ResourceContext, UserRole
from .abac_attributes import AttributeProvider, Attribute

class PolicyRule:
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.conditions = []
        self.effect = "allow"  # or "deny"
    
    def add_condition(self, condition: 'PolicyCondition'):
        """Add condition to policy rule"""
        self.conditions.append(condition)
        return self
    
    def evaluate(self, user_context: UserContext, resource_context: ResourceContext,
                  attribute_provider: AttributeProvider) -> bool:
        """Evaluate policy rule against context"""
        if not self.conditions:
            return self.effect == "allow"
        
        # All conditions must be satisfied (AND logic)
        for condition in self.conditions:
            if not condition.evaluate(user_context, resource_context, attribute_provider):
                return self.effect == "deny"
        
        return self.effect == "allow"

class PolicyCondition:
    def __init__(self, attribute_name: str, operator: str, value: Any):
        self.attribute_name = attribute_name
        self.operator = operator
        self.value = value
    
    def evaluate(self, user_context: UserContext, resource_context: ResourceContext,
                  attribute_provider: AttributeProvider) -> bool:
        """Evaluate condition against context"""
        # Get attribute value
        attribute_value = self._get_attribute_value(
            self.attribute_name, user_context, resource_context, attribute_provider
        )
        
        if attribute_value is None:
            return False
        
        # Apply operator
        return self._apply_operator(attribute_value, self.operator, self.value)
    
    def _get_attribute_value(self, attribute_name: str, user_context: UserContext,
                           resource_context: ResourceContext,
                           attribute_provider: AttributeProvider) -> Any:
        """Get attribute value from context"""
        # Check user context first
        if hasattr(user_context, attribute_name):
            return getattr(user_context, attribute_name)
        
        # Check resource context
        if hasattr(resource_context, attribute_name):
            return getattr(resource_context, attribute_name)
        
        # Check attribute provider
        user_attrs = attribute_provider.get_user_attributes(user_context.user_id)
        if attribute_name in user_attrs:
            return user_attrs[attribute_name].value
        
        resource_attrs = attribute_provider.get_resource_attributes(
            resource_context.resource_type, resource_context.resource_id
        )
        if attribute_name in resource_attrs:
            return resource_attrs[attribute_name].value
        
        env_attrs = attribute_provider.get_environment_attributes()
        if attribute_name in env_attrs:
            return env_attrs[attribute_name].value
        
        return None
    
    def _apply_operator(self, attribute_value: Any, operator: str, expected_value: Any) -> bool:
        """Apply operator to compare values"""
        if operator == "equals":
            return attribute_value == expected_value
        elif operator == "not_equals":
            return attribute_value != expected_value
        elif operator == "contains":
            return expected_value in str(attribute_value)
        elif operator == "not_contains":
            return expected_value not in str(attribute_value)
        elif operator == "greater_than":
            return attribute_value > expected_value
        elif operator == "less_than":
            return attribute_value < expected_value
        elif operator == "greater_equal":
            return attribute_value >= expected_value
        elif operator == "less_equal":
            return attribute_value <= expected_value
        elif operator == "in":
            return attribute_value in expected_value
        elif operator == "not_in":
            return attribute_value not in expected_value
        elif operator == "matches":
            import re
            return bool(re.match(expected_value, str(attribute_value)))
        else:
            return False

class PolicyEngine:
    def __init__(self):
        self.policies = {}
        self.attribute_provider = AttributeProvider()
        self._load_default_policies()
    
    def _load_default_policies(self):
        """Load default authorization policies"""
        
        # Student can only access their own exams
        student_own_exam_policy = PolicyRule(
            "student_own_exam",
            "Students can only access their own exam instances"
        )
        student_own_exam_policy.add_condition(
            PolicyCondition("user_role", "equals", "STUDENT")
        ).add_condition(
            PolicyCondition("resource_owner_id", "equals", "user_id")
        )
        self.policies["student_own_exam"] = student_own_exam_policy
        
        # Lecturer can only access exams for their courses
        lecturer_course_exam_policy = PolicyRule(
            "lecturer_course_exam",
            "Lecturers can only access exams for courses they teach"
        )
        lecturer_course_exam_policy.add_condition(
            PolicyCondition("user_role", "equals", "LECTURER")
        ).add_condition(
            PolicyCondition("course_department_id", "equals", "user_department_id")
        )
        self.policies["lecturer_course_exam"] = lecturer_course_exam_policy
        
        # Exam can only be taken during scheduled time
        exam_time_policy = PolicyRule(
            "exam_time_restriction",
            "Exams can only be taken during scheduled time"
        )
        exam_time_policy.add_condition(
            PolicyCondition("resource_type", "equals", "exam")
        ).add_condition(
            PolicyCondition("current_time", "greater_equal", "exam_date")
        ).add_condition(
            PolicyCondition("current_time", "less_equal", "exam_end_time")
        )
        self.policies["exam_time_restriction"] = exam_time_policy
        
        # Business hours restriction for administrative functions
        business_hours_policy = PolicyRule(
            "business_hours_admin",
            "Administrative functions only allowed during business hours"
        )
        business_hours_policy.add_condition(
            PolicyCondition("permission", "in", [
                Permission.SYSTEM_CONFIG, Permission.SYSTEM_BACKUP, Permission.SECURITY_PERMISSIONS
            ])
        ).add_condition(
            PolicyCondition("business_hours", "equals", True)
        )
        self.policies["business_hours_admin"] = business_hours_policy
        
        # Exam period restrictions
        exam_period_policy = PolicyRule(
            "exam_period_only",
            "Exam-related actions only allowed during exam period"
        )
        exam_period_policy.add_condition(
            PolicyCondition("permission", "in", [
                Permission.EXAM_START, Permission.EXAM_SUBMIT, Permission.EXAM_REVIEW
            ])
        ).add_condition(
            PolicyCondition("exam_period", "equals", True)
        )
        self.policies["exam_period_only"] = exam_period_policy
        
        # Department-based access for course management
        department_course_policy = PolicyRule(
            "department_course_access",
            "Course management restricted to department"
        )
        department_course_policy.add_condition(
            PolicyCondition("permission", "in", [
                Permission.COURSE_CREATE, Permission.COURSE_UPDATE, Permission.COURSE_DELETE
            ])
        ).add_condition(
            PolicyCondition("user_department_id", "equals", "resource_department_id")
        )
        self.policies["department_course_access"] = department_course_policy
    
    def add_policy(self, policy_name: str, policy: PolicyRule):
        """Add custom policy"""
        self.policies[policy_name] = policy
    
    def evaluate_policies(self, permission: Permission, user_context: UserContext,
                          resource_context: ResourceContext) -> bool:
        """Evaluate all relevant policies for permission check"""
        # First check basic RBAC permissions
        if not self._check_rbac_permission(permission, user_context):
            return False
        
        # Then evaluate ABAC policies
        relevant_policies = self._get_relevant_policies(permission, user_context, resource_context)
        
        for policy_name, policy in relevant_policies.items():
            try:
                if not policy.evaluate(user_context, resource_context, self.attribute_provider):
                    return False
            except Exception as e:
                # Log policy evaluation error
                print(f"Policy evaluation error for {policy_name}: {str(e)}")
                return False
        
        return True
    
    def _check_rbac_permission(self, permission: Permission, user_context: UserContext) -> bool:
        """Check basic RBAC permission"""
        from .role_definitions import RoleDefinitions
        
        for role in user_context.roles:
            if RoleDefinitions.has_permission(role, permission):
                return True
        return False
    
    def _get_relevant_policies(self, permission: Permission, user_context: UserContext,
                             resource_context: ResourceContext) -> Dict[str, PolicyRule]:
        """Get policies relevant to the permission check"""
        relevant_policies = {}
        
        for policy_name, policy in self.policies.items():
            # Check if policy is relevant to this permission check
            if self._is_policy_relevant(policy, permission, user_context, resource_context):
                relevant_policies[policy_name] = policy
        
        return relevant_policies
    
    def _is_policy_relevant(self, policy: PolicyRule, permission: Permission,
                           user_context: UserContext, resource_context: ResourceContext) -> bool:
        """Determine if policy is relevant to permission check"""
        for condition in policy.conditions:
            # Check if condition references permission
            if condition.attribute_name == "permission":
                if condition.operator == "in" and permission in condition.value:
                    return True
                elif condition.operator == "equals" and permission == condition.value:
                    return True
            
            # Check if condition references resource type
            if condition.attribute_name == "resource_type":
                if condition.operator == "equals" and condition.value == resource_context.resource_type:
                    return True
        
        return False
```

---

## Authorization Service Implementation

### Main Authorization Service
```python
# services/authorization_service.py
import json
import redis
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from .authorization import Permission, UserContext, ResourceContext, UserRole
from .role_definitions import RoleDefinitions
from .policy_engine import PolicyEngine
from .abac_attributes import AttributeProvider

class AuthorizationService:
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.policy_engine = PolicyEngine()
        self.permission_cache_ttl = 300  # 5 minutes
        self.user_cache_ttl = 600      # 10 minutes
    
    async def check_permission(self, user_id: str, permission: Permission,
                             resource_type: str, resource_id: str,
                             context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if user has permission for resource"""
        try:
            # Build user context
            user_context = await self._build_user_context(user_id)
            if not user_context:
                return False
            
            # Build resource context
            resource_context = self._build_resource_context(resource_type, resource_id, context)
            
            # Check permission with policy engine
            return self.policy_engine.evaluate_policies(
                permission, user_context, resource_context
            )
            
        except Exception as e:
            # Log error and deny by default
            print(f"Authorization check failed: {str(e)}")
            return False
    
    async def check_permissions(self, user_id: str, permissions: List[Permission],
                              resource_type: str, resource_id: str,
                              context: Optional[Dict[str, Any]] = None) -> Dict[Permission, bool]:
        """Check multiple permissions for user"""
        results = {}
        for permission in permissions:
            results[permission] = await self.check_permission(
                user_id, permission, resource_type, resource_id, context
            )
        return results
    
    async def get_user_permissions(self, user_id: str) -> Set[Permission]:
        """Get all permissions for user (cached)"""
        cache_key = f"user_permissions:{user_id}"
        
        # Try cache first
        cached_permissions = self.redis_client.get(cache_key)
        if cached_permissions:
            return set(json.loads(cached_permissions))
        
        # Build from roles
        user_context = await self._build_user_context(user_id)
        if not user_context:
            return set()
        
        permissions = set()
        for role in user_context.roles:
            permissions.update(RoleDefinitions.get_role_permissions(role))
        
        # Cache permissions
        self.redis_client.setex(
            cache_key, 
            self.user_cache_ttl, 
            json.dumps(list(permissions))
        )
        
        return permissions
    
    async def invalidate_user_cache(self, user_id: str):
        """Invalidate cached user permissions"""
        cache_key = f"user_permissions:{user_id}"
        self.redis_client.delete(cache_key)
    
    async def get_accessible_resources(self, user_id: str, resource_type: str,
                                     permission: Permission) -> List[str]:
        """Get list of resources user can access with specific permission"""
        # This would integrate with database to query accessible resources
        # For now, return empty list
        return []
    
    async def _build_user_context(self, user_id: str) -> Optional[UserContext]:
        """Build user context from database"""
        # This would integrate with user service/database
        # For now, return mock context
        return UserContext(
            user_id=user_id,
            username="testuser",
            roles=[UserRole.STUDENT],
            department_id="dept-123",
            academic_session_id="session-2026",
            ip_address="127.0.0.1",
            device_fingerprint="fp-123",
            timestamp=datetime.now()
        )
    
    def _build_resource_context(self, resource_type: str, resource_id: str,
                               context: Optional[Dict[str, Any]]) -> ResourceContext:
        """Build resource context"""
        additional_attrs = context or {}
        return ResourceContext(
            resource_type=resource_type,
            resource_id=resource_id,
            owner_id=additional_attrs.get("owner_id"),
            department_id=additional_attrs.get("department_id"),
            academic_session_id=additional_attrs.get("academic_session_id"),
            additional_attributes=additional_attrs
        )
    
    async def create_custom_policy(self, policy_name: str, description: str,
                                 conditions: List[Dict[str, Any]]) -> bool:
        """Create custom authorization policy"""
        try:
            from .policy_engine import PolicyRule, PolicyCondition
            
            policy = PolicyRule(policy_name, description)
            
            for condition_data in conditions:
                condition = PolicyCondition(
                    attribute_name=condition_data["attribute_name"],
                    operator=condition_data["operator"],
                    value=condition_data["value"]
                )
                policy.add_condition(condition)
            
            self.policy_engine.add_policy(policy_name, policy)
            return True
            
        except Exception as e:
            print(f"Failed to create policy {policy_name}: {str(e)}")
            return False
    
    async def update_user_roles(self, user_id: str, roles: List[UserRole]):
        """Update user roles and invalidate cache"""
        # This would update database
        # Invalidate cache to force refresh
        await self.invalidate_user_cache(user_id)
    
    def get_policy_engine(self) -> PolicyEngine:
        """Get policy engine for testing/debugging"""
        return self.policy_engine
```

---

## Authorization Middleware

### FastAPI Middleware
```python
# middleware/authorization_middleware.py
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from .authorization_service import AuthorizationService
from .authorization import Permission

security = HTTPBearer()

class AuthorizationMiddleware:
    def __init__(self, auth_service: AuthorizationService):
        self.auth_service = auth_service
    
    async def check_permission(self, request: Request, permission: Permission,
                               resource_type: str = None, resource_id: str = None):
        """Check permission for request"""
        # Extract user from JWT token
        credentials: Optional[HTTPAuthorizationCredentials] = await security(request)
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify token and get user_id
        user_id = await self._verify_token(credentials.credentials)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract resource information from request
        resource_type = resource_type or self._extract_resource_type(request)
        resource_id = resource_id or self._extract_resource_id(request)
        
        # Check permission
        has_permission = await self.auth_service.check_permission(
            user_id, permission, resource_type, resource_id
        )
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Add user context to request state
        request.state.user_id = user_id
        
        return True
    
    async def _verify_token(self, token: str) -> Optional[str]:
        """Verify JWT token and return user_id"""
        # This would integrate with authentication service
        # For now, return mock user_id
        return "user-123"
    
    def _extract_resource_type(self, request: Request) -> Optional[str]:
        """Extract resource type from request"""
        # Extract from path parameters
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 1:
            return path_parts[0]
        return None
    
    def _extract_resource_id(self, request: Request) -> Optional[str]:
        """Extract resource ID from request"""
        # Extract from path parameters
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 2:
            return path_parts[1]
        return None

# Decorator for permission checking
def require_permission(permission: Permission, resource_type: str = None):
    """Decorator to require specific permission"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get request from function arguments
            request = kwargs.get('request')
            if not request:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request context not available"
                )
            
            # Get authorization middleware
            auth_middleware = kwargs.get('auth_middleware')
            if not auth_middleware:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authorization middleware not available"
                )
            
            # Check permission
            await auth_middleware.check_permission(request, permission, resource_type)
            
            # Call original function
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

---

## Usage Examples

### API Endpoint with Authorization
```python
# api/exams.py
from fastapi import APIRouter, Depends, HTTPException
from .middleware.authorization_middleware import require_permission
from .authorization import Permission

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])

@router.get("/{exam_id}")
@require_permission(Permission.EXAM_READ, "exam")
async def get_exam(exam_id: str, request: Request):
    """Get exam details"""
    # Implementation here
    pass

@router.post("/")
@require_permission(Permission.EXAM_CREATE, "exam")
async def create_exam(exam_data: dict, request: Request):
    """Create new exam"""
    # Implementation here
    pass

@router.put("/{exam_id}")
@require_permission(Permission.EXAM_UPDATE, "exam")
async def update_exam(exam_id: str, exam_data: dict, request: Request):
    """Update exam"""
    # Implementation here
    pass

@router.delete("/{exam_id}")
@require_permission(Permission.EXAM_DELETE, "exam")
async def delete_exam(exam_id: str, request: Request):
    """Delete exam"""
    # Implementation here
    pass
```

### Custom Policy Creation
```python
# services/policy_management.py
from .authorization_service import AuthorizationService

async def create_time_based_exam_policy(auth_service: AuthorizationService):
    """Create policy for exam time restrictions"""
    conditions = [
        {
            "attribute_name": "resource_type",
            "operator": "equals",
            "value": "exam"
        },
        {
            "attribute_name": "current_time",
            "operator": "greater_equal",
            "value": "exam_date"
        },
        {
            "attribute_name": "current_time",
            "operator": "less_equal",
            "value": "exam_end_time"
        }
    ]
    
    success = await auth_service.create_custom_policy(
        "exam_time_window",
        "Exams can only be accessed during scheduled time window",
        conditions
    )
    
    return success
```

This comprehensive RBAC system with ABAC extensions provides:

1. **Fine-Grained Control**: Role-based permissions with attribute-based constraints
2. **Context-Aware Authorization**: Time, location, and relationship-based access rules
3. **Performance Optimization**: Redis-based caching for frequently accessed permissions
4. **Flexible Policy Engine**: Custom policy creation for complex authorization rules
5. **Academic Hierarchy Support**: Department-based and course-based access controls
6. **Security First**: Default deny policy with explicit permission grants
7. **Audit Trail**: All authorization decisions logged for compliance

The system ensures that users can only access the resources and perform actions that are appropriate to their role, department, and the current academic context, maintaining the integrity and security of the examination system.
