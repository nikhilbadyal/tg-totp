"""Utility class."""
from enum import Enum

from loguru import logger
from telethon import events
from telethon.tl.types import User


class UserStatus(Enum):
    """User Status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TEMP_BANNED = "temporarily banned"


async def get_user(event: events.NewMessage.Event) -> User:
    """Get the user associated with a message event in Telegram.

    Args:
        event (events.NewMessage.Event): The message event.

    Returns:
        User: The User entity associated with the message event.
    """
    try:
        # Get the user entity from the peer ID of the message event, Uses cache
        user: User = await event.client.get_entity(event.peer_id)
    except (ValueError, AttributeError):
        logger.debug("Invalid Peer ID")
        user = await event.get_sender()
    return user


class ErrorCodes(Enum):
    """List of error codes."""

    exceptions = -1
