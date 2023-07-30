"""Handle export command."""
from datetime import datetime
import os

from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import Secret, User

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_export_handlers(client: TelegramClient) -> None:
    """export /export command Event Handler."""
    client.add_event_handler(handle_export_message)


# Register the function to handle the /export command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.EXPORT.value}"))  # type: ignore
async def handle_export_message(event: events.NewMessage.Event) -> None:
    """Handle /export command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    telegram_user: TelegramUser = await get_user(event)
    user = await sync_to_async(User.objects.get_user)(telegram_user.id)
    data, size = await sync_to_async(Secret.objects.export_secrets)(user=user)
    uris = []
    for secret in data:
        uris.append(Secret.objects.export_print(secret))
    output_file = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, "w", encoding="utf-8") as file:
        file.write("\n".join(uris))
    await event.reply(message=f"Exported {size} URIs.", file=output_file)
    try:
        os.remove(output_file)
    except FileNotFoundError:
        pass
