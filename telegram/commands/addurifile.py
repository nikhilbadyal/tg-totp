"""Handle addurifile command."""
import os

from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import User
from telegram.exceptions import FileProcessFail
from telegram.strings import file_process_failed, processing_file

# Import some helper functions
from telegram.utils import (
    SupportedCommands,
    bulk_add_secret_data,
    extract_secret_from_uri,
    get_uri_file_from_message,
    get_user,
    import_failure_output_file,
    process_uri_file,
)


def add_addurifile_handlers(client: TelegramClient) -> None:
    """Add /addurifile command Event Handler."""
    client.add_event_handler(handle_addurifile_message)


# Register the function to handle the /addurifile command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.ADDURIFILE.value}"))  # type: ignore
async def handle_addurifile_message(event: events.NewMessage.Event) -> None:
    """Handle /addurifile command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Define a prefix for the image URL
    message = await event.reply(processing_file)

    try:
        uri_file = await get_uri_file_from_message(event)
        uris = process_uri_file(uri_file)
        secrets = extract_secret_from_uri(uris)
        telegram_user: TelegramUser = await get_user(event)
        user = await sync_to_async(User.objects.get_user)(telegram_user.id)
        import_status, import_failures = await bulk_add_secret_data(secrets, user)
        output_file = import_failure_output_file(import_failures)
        await message.edit(f"Done processing with status `{import_status}`")
        await event.respond(file=output_file)
        os.remove(output_file)
    except (FileNotFoundError, FileProcessFail):
        await message.edit(file_process_failed)
