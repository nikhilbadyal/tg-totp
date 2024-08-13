"""Handle exportqr command."""

import contextlib
from pathlib import Path
from urllib.parse import quote_plus

# Import necessary libraries and modules
from telethon import TelegramClient, events

from sqlitedb.models import Secret
from telegram.strings import no_export, processing_request

# Import some helper functions
from telegram.utils import SupportedCommands, all_files, create_qr, get_user


def add_exportqr_handlers(client: TelegramClient) -> None:
    """Add /exportqr command Event Handler."""
    client.add_event_handler(handle_exportqr_message)


def exportqr_usage() -> str:
    """Return the usage of add command."""
    return (
        "You can do 2 types of QR exports.\n"
        "1. If /exportqr command is sent without any input it will export all the QR code images in a zip file.\n"
        "2. If /exportqr command is sent with ID the QR code will be sent directly"
        "for that ID. You can get ID from /list or /get command."
    )


# Register the function to handle the /exportqr command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.EXPORTQR.value}\\s*(\\d*)$"))  # type: ignore[misc]
async def handle_exportqr_message(event: events.NewMessage.Event) -> None:
    """Handle /exportqr command.

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
    data, size = await Secret.objects.export_secrets(user=user, secret_filter=secret_filter)  # type: ignore[misc]
    if size == 0:
        await event.reply(message=no_export)
    else:
        qr_meta = {}
        for secret in data:
            uri = Secret.objects.export_print(secret)  # type: ignore[misc]
            qr_meta[uri] = secret
        zip_file_name = f"{user.id}_{quote_plus(user.name)}"
        os_path = create_qr(qr_meta, zip_file_name)
        await message.delete()
        await event.reply(
            message=f"Exported {len(qr_meta)} qr images.",
            file=str(os_path),
        )
        if Path(os_path).is_dir():
            all_files(os_path)
        else:
            with contextlib.suppress(FileNotFoundError):
                Path(os_path).unlink()
