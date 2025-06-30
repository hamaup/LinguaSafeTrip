"""
Date and time utilities for schemas.
Common datetime-related functionality and mixins.
"""

from typing import Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field

class TimestampMixin(BaseModel):
    """Mixin for models that need creation and update timestamps."""
    
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="作成日時"
    )
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="更新日時"
    )
    
    def touch(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

class ExpiryMixin(BaseModel):
    """Mixin for models that can expire."""
    
    expires_at: Optional[datetime] = Field(
        None,
        description="有効期限"
    )
    
    def is_expired(self) -> bool:
        """Check if the model has expired."""
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at
    
    def set_expiry(self, hours: int) -> None:
        """Set expiry time from now."""
        from datetime import timedelta
        self.expires_at = datetime.now(timezone.utc) + timedelta(hours=hours)

def utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.now(timezone.utc)

def iso_format(dt: datetime) -> str:
    """Format datetime to ISO string."""
    return dt.isoformat()

def parse_iso(iso_string: str) -> datetime:
    """Parse ISO string to datetime."""
    return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))