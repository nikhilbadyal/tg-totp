"""Handle export command."""

import contextlib
from datetime import UTC, datetime
from pathlib import Path

import aiofiles

# Import necessary libraries and modules
from telethon import TelegramClient, events

from sqlitedb.models import Secret
from telegram.strings import no_export, processing_request

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_export_handlers(client: TelegramClient) -> None:
    """Export /export command Event Handler."""
    client.add_event_handler(handle_export_message)


def export_usage() -> str:
    """Return the usage of add command."""
    return (
        "You can do 2 types of exports.\n"
        "1. If /export command is sent without any input it will export all the uris.\n"
        "2. If /export command is sent with ID the URI will be exported "
        "for that URI. You can get ID from /list or /get "
        "command."
    )


# Register the function to handle the /export command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.EXPORT.value}\\s*(\\d*)$"))  # type: ignore[misc]
async def handle_export_message(event: events.NewMessage.Event) -> None:
    """Handle /export command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    message = await event.reply(processing_request)
    data = event.pattern_match.group(1).strip()
    secret_filter = {"id__in": [int(data)]} if data else {}
    user = await get_user(event)
    data, size = await Secret.objects.export_secrets(user=user, secret_filter=secret_filter)
    if size == 0:
        await event.reply(message=no_export)
    else:
        uris = [Secret.objects.export_print(secret) for secret in data]
        output_file = f"export_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.txt"
        async with aiofiles.open(output_file, mode="w") as file:
            await file.write("\n".join(uris))
        await message.delete()
        await event.reply(message=f"Exported {size} URIs.", file=output_file)
        with contextlib.suppress(FileNotFoundError):
            Path(output_file).unlink()
