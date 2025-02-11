"""Database errors module."""

class DatabaseError(Exception):
    """Base class for database errors."""
    pass

class UserAlreadyExistsError(DatabaseError):
    """Raised when attempting to create a user that already exists."""
    pass

class UserNotFoundError(DatabaseError):
    """Raised when a user is not found."""
    pass

class InvalidCredentialsError(DatabaseError):
    """Raised when invalid credentials are provided."""
    pass

class SessionNotFoundError(DatabaseError):
    """Raised when a session is not found."""
    pass

class RoleNotFoundError(DatabaseError):
    """Raised when a role is not found."""
    pass

class PermissionNotFoundError(DatabaseError):
    """Raised when a permission is not found."""
    pass

class TaskNotFoundError(DatabaseError):
    """Raised when a task is not found."""
    pass

class WorkflowNotFoundError(DatabaseError):
    """Raised when a workflow is not found."""
    pass

class InvalidStatusTransitionError(DatabaseError):
    """Raised when an invalid status transition is attempted."""
    pass

class InvalidPriorityError(DatabaseError):
    """Raised when an invalid priority is provided."""
    pass

class InvalidCategoryError(DatabaseError):
    """Raised when an invalid category is provided."""
    pass
