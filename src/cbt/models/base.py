"""
Base model class for all database models using Beanie (MongoDB).
"""

from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
import uuid

class BaseDocument(Document):
    """Base document with common fields."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True

    async def save(self, *args, **kwargs):
        """Override save to update `updated_at`."""
        self.updated_at = datetime.now(timezone.utc)
        return await super().save(*args, **kwargs)

    async def set(self, expression, *args, **kwargs):
        """Override set to also update `updated_at`."""
        if isinstance(expression, dict):
            expression['updated_at'] = datetime.now(timezone.utc)
        return await super().set(expression, *args, **kwargs)

    class Settings:
        use_state_management = True
