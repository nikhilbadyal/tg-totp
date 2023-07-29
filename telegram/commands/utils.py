"""Utility functions."""
from enum import Enum
from typing import Dict, List

import pyotp
from django.utils.translation import gettext as _
from loguru import logger
from telethon import events
from telethon.tl.types import User

from sqlitedb.models import Secret
from telegram.commands.exceptions import InvalidSecret
from telegram.commands.strings import missing_secret_issuer

PAGE_SIZE = 10  # Number of conversations per page


# Define a list of supported commands
class SupportedCommands(Enum):
    """Enum for supported commands."""

    START: str = "/start"
    TEMP: str = "/temp"
    ADD: str = "/add"

    @classmethod
    def get_values(cls) -> List[str]:
        """Returns a list of all the values of the SupportedCommands enum.

        Returns:
            list: A list of all the values of the SupportedCommands enum.
        """
        return [command.value for command in cls]

    def __str__(self) -> str:
        """Returns the string representation of the enum value.

        Returns:
            str: The string representation of the enum value.
        """
        return self.value


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


def get_regex() -> str:
    """Generate a regex pattern that matches any message that is not a
    supported command.

    Returns:
        str: A regex pattern as a string.
    """
    # Exclude any message that starts with one of the supported commands using negative lookahead
    pattern = r"^(?!(%s))[^/].*" % "|".join(SupportedCommands.get_values())
    return pattern


def parse_secret(secret_string: str) -> Dict[str, str]:
    """Parse Secret."""
    # Split the input string into key-value pairs
    key_value_pairs = secret_string.split(",")

    # Initialize a dictionary to store the values
    secret_data = {}

    # Loop through each key-value pair and extract the values
    for pair in key_value_pairs:
        key, value = pair.split("=")
        if key in Secret.objects.possible_inputs():
            secret_data[key.strip()] = value.strip()

    # Check if 'secret' and 'issuer' fields are present in the secret_data
    if "secret" not in secret_data or "issuer" not in secret_data:
        raise ValueError(_(missing_secret_issuer))

    return secret_data


def is_valid_2fa_secret(secret: str) -> bool:
    """Validate if 2fa secret is valid."""
    # noinspection PyBroadException
    try:
        # Attempt to create a TOTP object based on the provided secret
        pyotp.TOTP(secret).now()
        return True
    except Exception:
        raise InvalidSecret()
