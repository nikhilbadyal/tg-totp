"""Utility functions."""
import json
import operator
import os
from enum import Enum
from functools import reduce
from pathlib import Path
from shutil import rmtree
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus
from zipfile import ZipFile

import pyotp
import qrcode
from django.db.models import Q
from django.utils.translation import gettext as _
from loguru import logger
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.colormasks import VerticalGradiantColorMask
from qrcode.image.styles.moduledrawers import HorizontalBarsDrawer
from telethon import events, types
from telethon.extensions import markdown
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import Secret, User
from telegram.exceptions import DuplicateSecret, FileProcessFail, InvalidSecret
from telegram.strings import added_secret, no_input

# Number of records per page
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
    RESET: str = "/reset"
    TOTAL: str = "/total"
    RM: str = "/rm"
    EXPORTQR: str = "/exportqr"
    HELP: str = "/help"

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


async def get_telegram_user(event: events.NewMessage.Event) -> TelegramUser:
    """Get the user associated with a message event in Telegram.

    Args:
        event (events.NewMessage.Event): The message event.

    Returns:
        User: The User entity associated with the message event.
    """
    try:
        # Get the user entity from the peer ID of the message event, Uses cache
        user: TelegramUser = await event.client.get_entity(event.peer_id)
    except (ValueError, AttributeError):
        logger.debug("Couldn't get user from cache. Invalid Peer ID")
        user = await event.get_sender()
    return user


def get_regex() -> str:
    """Generate a regex pattern that matches any message that is not a
    supported command.

    Returns:
        str: A regex pattern as a string.
    """
    # Exclude any message that starts with one of the supported commands using negative lookahead
    pattern = r"^(?!(%s))[/].*" % "|".join(SupportedCommands.get_values())
    return pattern


class UserSettings(Enum):
    """User Settings."""

    PAGE_SIZE = "page_size", "The number of records displayed per page."

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
    await Secret.objects.create_secret(user=user, **secret_data)
    return added_secret


async def bulk_add_secret_data(
    secrets: List[Dict[str, str]], user: User
) -> Tuple[Dict[str, int], Dict[str, List[Dict[str, str]]]]:
    """Add secret data."""
    import_status = {"invalid": 0, "duplicate": 0, "success": 0}
    failed_secrets: Dict[str, List[Dict[str, str]]] = {"invalid": [], "duplicate": []}
    for secret_data in secrets:
        try:
            await add_secret_data(secret_data, user)
            import_status["success"] += 1
        except DuplicateSecret:
            import_status["duplicate"] += 1
            failed_secrets["duplicate"].append(secret_data)
    return import_status, failed_secrets


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


def extract_secret_from_uri(
    uris: List[str],
) -> Tuple[List[Dict[str, str]], Dict[str, List[Dict[str, str]]]]:
    """Extract secrets from URI."""
    from totp.totp import OTP

    secrets = []
    failed: Dict[str, List[Dict[str, str]]] = {"invalid": []}
    for uri in uris:
        try:
            secret_data = OTP.parse_uri(uri)
            secrets.append(secret_data)
        except InvalidSecret as e:
            failed["invalid"].append({"uri": uri, "reason": str(e)})
    return secrets, failed


def import_failure_output_file(import_failures: Dict[str, List[Dict[str, str]]]) -> str:
    """Prepare failed record file."""
    output_file = "output-data.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(import_failures, f, ensure_ascii=False, indent=2)
    return output_file


async def get_user(event: events.NewMessage.Event) -> User:
    """Get out user from telegram user."""
    telegram_user: TelegramUser = await get_telegram_user(event)
    user = await User.objects.get_user(telegram_user=telegram_user)
    return user


def or_filters(filters: Dict[str, Any]) -> List[Any]:
    """Prepare queryset fileter from dict."""
    try:
        filtered_or = [Q(**{key: val}) for key, val in filters.items()]
        return reduce(operator.or_, filtered_or)  # type: ignore
    except TypeError:
        return []


def prepare_user_filter(user: User) -> Dict[str, Any]:
    """Prepare queryset fileter for user."""
    queryset_filters = {"user__in": [user]}
    return queryset_filters


def create_qr(uris: Dict[str, Secret], zip_file_name: str) -> Path:
    """Create qr image from uris list."""
    folder_name = "qrexports/"
    for uri, secret in uris.items():
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(uri)
        qr_code = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=HorizontalBarsDrawer(),
            color_mask=VerticalGradiantColorMask(),
        )
        file_name = f"{secret.id}_{quote_plus(secret.issuer)}_{quote_plus(secret.account_id)}.png"
        qr_code.save(
            f"{folder_name}/{file_name}",
        )
    if len(uris) < 1:
        visible_files = [
            file
            for file in Path(folder_name).iterdir()
            if not file.name.startswith(".")
        ]
        return visible_files[0]
    zip_name = f"{zip_file_name}.zip"
    # Create object of ZipFile
    with ZipFile(zip_name, "w") as zip_object:
        # Traverse all files in directory
        for folder_name, sub_folders, file_names in os.walk(folder_name):
            for filename in file_names:
                file_path = os.path.join(folder_name, filename)
                zip_object.write(file_path, os.path.basename(file_path))
    all_files(Path(folder_name))
    return Path(zip_name)


def all_files(folder_name: Path) -> None:
    """Delete all files from given folder."""
    for path in Path(folder_name).glob("**/*"):
        if path.is_file() and path.name != "README.md":
            path.unlink()
        elif path.is_dir():
            rmtree(path)


def command_help(command: str) -> str:
    """Return func for command helper."""
    from telegram.commands.add import add_usage
    from telegram.commands.adduri import adduri_usage
    from telegram.commands.addurifile import addurifile_usage
    from telegram.commands.export import export_usage
    from telegram.commands.exportqr import exportqr_usage
    from telegram.commands.help import help_usage
    from telegram.commands.list import list_usage
    from telegram.commands.reset import reset_usage
    from telegram.commands.rm import rm_usage
    from telegram.commands.settings import settings_usage
    from telegram.commands.start import start_usage

    mapper = {
        "add": add_usage(),
        "adduri": adduri_usage(),
        "addurifile": addurifile_usage(),
        "export": export_usage(),
        "exportqr": exportqr_usage(),
        "help": help_usage(),
        "list": list_usage(),
        "reset": reset_usage(),
        "rm": rm_usage(),
        "settings": settings_usage(),
        "start": start_usage(),
    }
    return mapper[command]
