"""Custom exceptions for the Becoming Itumeleng agent."""


class BecomingItumelengError(Exception):
    """Base exception for the agent."""
    pass


class GoalNotFoundError(BecomingItumelengError):
    """Raised when a goal cannot be found by name."""
    pass


class HabitNotFoundError(BecomingItumelengError):
    """Raised when a habit cannot be found by name."""
    pass


class DataFileError(BecomingItumelengError):
    """Raised when a data file cannot be read or written."""
    pass


class WardrobeEmptyError(BecomingItumelengError):
    """Raised when the wardrobe inventory has no items."""
    pass

