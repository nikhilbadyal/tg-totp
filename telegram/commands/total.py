"""Handle total command."""
from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events

from sqlitedb.models import Secret

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_total_handlers(client: TelegramClient) -> None:
    """Get /total command Event Handler."""
    client.add_event_handler(handle_total_message)


# Register the function to handle the /total command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.TOTAL.value}"))  # type: ignore
async def handle_total_message(event: events.NewMessage.Event) -> None:
    """Handle /total command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    user = await get_user(event)

    size = await sync_to_async(Secret.objects.total_secrets)(user=user)
    await event.reply(f"There are {size} secrets in total.")