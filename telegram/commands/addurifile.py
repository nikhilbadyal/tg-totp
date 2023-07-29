"""Handle addurifile command."""


# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.commands.exceptions import FileProcessFail
from telegram.commands.strings import file_process_failed

# Import some helper functions
from telegram.commands.utils import (
    SupportedCommands,
    bulk_add_secret_data,
    extract_secret_from_uri,
    get_uri_file_from_message,
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

    try:
        uri_file = await get_uri_file_from_message(event)
        uris = process_uri_file(uri_file)
        secrets = extract_secret_from_uri(uris)
        response = await bulk_add_secret_data(secrets, event)
        if response:
            await event.reply(f"Failed to insert {response} secrets.")
        else:
            await event.reply(f"Done processing {len(secrets)} URIs.")
    except (FileNotFoundError, FileProcessFail):
        await event.reply(file_process_failed)
