"""Handle start command."""
# Import necessary libraries and modules
from telethon import TelegramClient, events

# Import some helper functions
from telegram.commands.utils import SupportedCommands


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
    result = "Hello there"
    await event.respond(result)
