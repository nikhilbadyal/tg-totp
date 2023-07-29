"""Utility functions."""
import json
import os
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import pyotp
from asgiref.sync import sync_to_async
from django.utils.translation import gettext as _
from loguru import logger
from telethon import events, types
from telethon.extensions import markdown
from telethon.tl.types import User

from sqlitedb.models import Secret
from telegram.exceptions import DuplicateSecret, FileProcessFail, InvalidSecret
from telegram.strings import added_secret, no_input

# Number of conversations per page
PAGE_SIZE = 10


class CustomMarkdown:
    """Custom Markdown parser."""

    @staticmethod
    def parse(text: str) -> Any:
        """Parse."""
        text, entities = markdown.parse(text)
        for i, e in enumerate(entities):
            if isinstance(e, types.MessageEntityTextUrl):
                if e.url == "spoiler":
                    entities[i] = types.MessageEntitySpoiler(e.offset, e.length)
                elif e.url.startswith("emoji/"):
                    entities[i] = types.MessageEntityCustomEmoji(
                        e.offset, e.length, int(e.url.split("/")[1])
                    )
        return text, entities

    @staticmethod
    def unparse(text: str, entities: Any) -> Any:
        """Unparse."""
        for i, e in enumerate(entities or []):
            if isinstance(e, types.MessageEntityCustomEmoji):
                entities[i] = types.MessageEntityTextUrl(
                    e.offset, e.length, f"emoji/{e.document_id}"
                )
            if isinstance(e, types.MessageEntitySpoiler):
                entities[i] = types.MessageEntityTextUrl(e.offset, e.length, "spoiler")
        return markdown.unparse(text, entities)


# Define a list of supported commands
class SupportedCommands(Enum):
    """Enum for supported commands."""

    START: str = "/start"
    TEMP: str = "/temp"
    ADD: str = "/add"
    LIST: str = "/list"
    SETTINGS: str = "/settings"
    GET: str = "/get"
    ADDURI: str = "/adduri"
    ADDURIFILE: str = "/addurifile"
    EXPORT: str = "/export"

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


class UserSettings(Enum):
    """User Settings."""

    PAGE_SIZE = "page_size", "The number of conversations displayed per page."

    def __new__(cls, *args: Any, **kwds: Any) -> "UserSettings":
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    # ignore the first param since it's already set by __new__
    def __init__(self, _: str, description: Optional[str] = None):
        self._description_ = description

    def __str__(self) -> str:
        return str(self.value)

    @property
    def description(self) -> Optional[str]:
        """Returns the description of the setting.

        Returns:
            Optional[str]: The description of the setting.
        """
        return self._description_


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
        raise ValueError(_(no_input))

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


async def add_secret_data(secret_data: Dict[str, str], user: User) -> str:
    """Add secret data."""
    is_valid_2fa_secret(secret_data["secret"])
    # Get the user associated with the message
    await sync_to_async(Secret.objects.create_secret)(user=user, **secret_data)
    return added_secret


async def bulk_add_secret_data(
    secrets: List[Dict[str, str]], user: User
) -> Tuple[Dict[str, int], Dict[str, List[Dict[str, str]]]]:
    """Add secret data."""
    status = {"invalid": 0, "duplicate": 0, "success": 0}
    failed_secrets: Dict[str, List[Dict[str, str]]] = {"invalid": [], "duplicate": []}
    for secret_data in secrets:
        try:
            await add_secret_data(secret_data, user)
            status["success"] += 1
        except InvalidSecret:
            status["invalid"] += 1
            failed_secrets["invalid"].append(secret_data)
        except DuplicateSecret:
            status["duplicate"] += 1
            failed_secrets["duplicate"].append(secret_data)
    return status, failed_secrets


async def get_uri_file_from_message(event: events.NewMessage.Event) -> str:
    """Get file from message."""
    # Define a prefix for the image URL
    temp_file = await event.message.download_media()
    if not temp_file and event.message.is_reply:
        logger.debug("Checking replied message for file.")
        replied_msg = await event.message.get_reply_message()
        temp_file = await replied_msg.download_media()
    if not temp_file:
        raise FileNotFoundError()
    return temp_file  # type: ignore


def process_uri_file(temp_file: str) -> List[str]:
    """Process URI file."""
    uris = []
    try:
        with open(temp_file) as uri_file:
            for uri in uri_file:
                uris.append(uri.strip())
        return uris
    except Exception:
        raise FileProcessFail()
    finally:
        os.remove(temp_file)


def extract_secret_from_uri(uris: List[str]) -> List[Dict[str, str]]:
    """Extract secrets from URI."""
    from totp.totp import OTP

    secrets = []
    for uri in uris:
        try:
            secret_data = OTP.parse_uri(uri)
            secrets.append(secret_data)
        except InvalidSecret:
            raise FileProcessFail(uri)
    return secrets


def import_failure_output_file(import_failures: Dict[str, List[Dict[str, str]]]) -> str:
    """Prepare failed record file."""
    output_file = "output-data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(import_failures, f, ensure_ascii=False, indent=4)
    return output_file
