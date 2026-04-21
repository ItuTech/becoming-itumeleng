"""Data structures used across the Becoming Itumeleng agent."""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class Goal:
    """A personal goal to track and work towards."""
    name: str
    description: str
    target_date: Optional[str] = None
    status: str = "in_progress"
    progress_notes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Habit:
    """A daily habit to build and maintain."""
    name: str
    description: str
    frequency: str = "daily"
    streak: int = 0
    last_logged: Optional[str] = None
    history: list[str] = field(default_factory=list)


@dataclass
class OutfitRequest:
    """Details for an outfit recommendation."""
    occasion: str
    date: Optional[str] = None
    weather: Optional[str] = None
    mood: Optional[str] = None
    constraints: Optional[str] = None


@dataclass
class BrandRequest:
    """Details for a brand guidance request."""
    platform: str
    content_type: str
    topic: Optional[str] = None
    audience: Optional[str] = None
    tone: Optional[str] = None


@dataclass
class Win:
    """An achievement worth celebrating."""
    description: str
    category: str
    date: str = field(default_factory=lambda: datetime.now().isoformat())

