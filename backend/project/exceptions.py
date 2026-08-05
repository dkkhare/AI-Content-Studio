class ProjectError(Exception):
    """
    Base exception for project subsystem.
    """
    pass


class InvalidProjectError(ProjectError):
    """
    Raised when a project is invalid or corrupted.
    """
    pass


class ProjectExistsError(ProjectError):
    """
    Raised when attempting to create a project
    that already exists.
    """
    pass