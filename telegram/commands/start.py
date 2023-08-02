"""Handle start command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_start_handlers(client: TelegramClient) -> None:
    """Add /start command Event Handler."""
    client.add_event_handler(handle_start_message)


def start_usage() -> str:
    """Return the usage of add command."""
    usage = "It can be used to check if bot is alive or dead.\n"
    return usage


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
    user = await get_user(event)
    result = f"Hii👋, {user.name}"
    await event.reply(result)
