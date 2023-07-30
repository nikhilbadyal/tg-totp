"""Handle total command."""
from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import Secret, User

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
    telegram_user: TelegramUser = await get_user(event)
    user = await sync_to_async(User.objects.get_user)(telegram_user.id)

    size = await sync_to_async(Secret.objects.total_secrets)(user=user)
    await event.reply(f"There are {size} secrets in total.")
