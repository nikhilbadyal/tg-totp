"""Handle start command."""
from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import User

# Import some helper functions
from telegram.commands.utils import SupportedCommands, get_user


def add_start_handlers(client: TelegramClient) -> None:
    """Add /start command Event Handler."""
    client.add_event_handler(handle_start_message)


# Register the function to handle the /start command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.START.value}$"))  # type: ignore
async def handle_start_message(event: events.NewMessage.Event) -> None:
    """Handle /start command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Get the user associated with the message
    telegram_user: TelegramUser = await get_user(event)
    await sync_to_async(User.objects.get_user)(telegram_user.id)
    result = f"Hii👋, {telegram_user.first_name} {telegram_user.last_name}"
    await event.respond(result)
