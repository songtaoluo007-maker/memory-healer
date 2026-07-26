"""Compatibility exports while persistence models move behind repositories."""

from backend.models.save import SaveSlot
from backend.persistence.models import User, UserSession

__all__ = ["SaveSlot", "User", "UserSession"]
