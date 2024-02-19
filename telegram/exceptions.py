"""Custom Exception."""

from django.db.utils import IntegrityError


class TGOtpError(Exception):
    """Base Project Error."""


class DuplicateSecretError(IntegrityError):
    """Duplicate Secret."""


class InvalidSecretError(ValueError):
    """Invalid Secret."""


class FileProcessFailError(ValueError):
    """Invalid Secret."""
