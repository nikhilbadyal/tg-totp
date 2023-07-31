"""Handle any other commands."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

# Import some helper functions
from telegram.strings import command_not_found
from telegram.utils import get_regex


def add_general_handlers(client: TelegramClient) -> None:
    """Add /add command Event Handler."""
    client.add_event_handler(handle_any_message)


# Register the function to handle any new message that matches the specified pattern
@events.register(events.NewMessage(pattern=get_regex()))  # type: ignore
async def handle_any_message(event: events.NewMessage.Event) -> None:
    """Handle any new message.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    await event.reply(command_not_found)
