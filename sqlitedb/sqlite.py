"""SQLite database to store messages."""

from typing import TypeVar

from django.db.models import Model

T = TypeVar("T", bound=Model)
