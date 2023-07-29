"""Custom Exception."""
from django.db.utils import IntegrityError


class DuplicateSecret(IntegrityError):
    """Duplicate Secret."""

    pass


class InvalidSecret(ValueError):
    """Invalid Secret."""

    pass


class FileProcessFail(ValueError):
    """Invalid Secret."""

    pass
