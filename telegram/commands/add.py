"""Handle add command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.commands.strings import no_input

# Import some helper functions
from telegram.commands.utils import SupportedCommands, add_secret_data, parse_secret


def add_add_handlers(client: TelegramClient) -> None:
    """Add /add command Event Handler."""
    client.add_event_handler(handle_add_message)


# Register the function to handle the /add command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.ADD.value}(?!uri)"))  # type: ignore
async def handle_add_message(event: events.NewMessage.Event) -> None:
    """Handle /add command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Define a prefix for the image URL
    prefix = f"{SupportedCommands.ADD.value}"
    # Pad by 1 to consider the space after command
    prefix = prefix.ljust(len(prefix) + 1)

    # Extract the image query from the message text
    prefix_len = len(prefix)
    secret_data = event.message.text[prefix_len:]
    try:
        secret_data = parse_secret(secret_data)
        response = await add_secret_data(secret_data, event)
        await event.reply(response)
    except ValueError:
        await event.reply(no_input)
