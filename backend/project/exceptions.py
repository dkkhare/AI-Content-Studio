from __future__ import annotations


class ProjectError(Exception):
    """
    Base exception for all project-related errors.
    """

    pass


# --------------------------------------------------
# Project Lifecycle
# --------------------------------------------------

class ProjectExistsError(ProjectError):
    """
    Raised when attempting to create a project
    that already exists.
    """

    pass


class ProjectNotFoundError(ProjectError):
    """
    Raised when a project cannot be found.
    """

    pass


class ProjectClosedError(ProjectError):
    """
    Raised when an operation requires an open
    project but none is available.
    """

    pass


# --------------------------------------------------
# Serialization
# --------------------------------------------------

class ProjectSerializationError(ProjectError):
    """
    Raised when a project cannot be saved,
    loaded, restored or backed up.
    """

    pass


# --------------------------------------------------
# Validation
# --------------------------------------------------

class ProjectValidationError(ProjectError):
    """
    Raised when project validation fails.
    """

    pass


class InvalidProjectError(ProjectValidationError):
    """Compatibility error for invalid project metadata or structure."""

    pass


# --------------------------------------------------
# Assets
# --------------------------------------------------

class AssetNotFoundError(ProjectError):
    """
    Raised when a required generated asset
    cannot be found.
    """

    pass


class InvalidAssetError(ProjectError):
    """
    Raised when an asset type or asset path
    is invalid.
    """

    pass


# --------------------------------------------------
# Processing
# --------------------------------------------------

class ProjectBusyError(ProjectError):
    """
    Raised when another processing task is
    already running.
    """

    pass


class ProjectCancelledError(ProjectError):
    """
    Raised when a running project task is
    cancelled.
    """

    pass