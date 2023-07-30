"""Utility class."""
from enum import Enum
from typing import Any, Dict, TypeVar

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Model, QuerySet
from loguru import logger

T = TypeVar("T", bound=Model)


class UserStatus(Enum):
    """User Status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TEMP_BANNED = "temporarily banned"


class ErrorCodes(Enum):
    """List of error codes."""

    exceptions = -1


def paginate_queryset(
    queryset: QuerySet[T], page: int, per_page: int
) -> Dict[str, Any]:
    """Helper function to paginate a given queryset.

    Args:
        queryset (QuerySet[T]): The queryset to be paginated.
        page (int): The current page number.
        per_page (int): The number of items to display per page.

    Returns:
        dict: A dictionary containing the paginated data and pagination details.
    """
    paginator = Paginator(queryset, per_page)

    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        logger.debug(f"{page} is not a valid page number")
        paginated_data = paginator.page(1)
    except EmptyPage:
        logger.debug(f"Empty {page} current page")
        paginated_data = paginator.page(paginator.num_pages)
    #Don't remove this. It is to force evaluate the queryset
    logger.info(f"Got {len(paginated_data)} records")
    return {
        "data": paginated_data,
        "total_data": paginator.count,
        "total_pages": paginator.num_pages,
        "current_page": paginated_data.number,
        "has_previous": paginated_data.has_previous(),
        "has_next": paginated_data.has_next(),
    }
