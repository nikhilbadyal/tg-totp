"""Handle add command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.exceptions import DuplicateSecret, InvalidSecret
from telegram.strings import duplicate_secret, invalid_secret, no_input

# Import some helper functions
from telegram.utils import SupportedCommands, add_secret_data, get_user, parse_secret


def add_add_handlers(client: TelegramClient) -> None:
    """Add /add command Event Handler."""
    client.add_event_handler(handle_add_message)


# Register the function to handle the /add command
@events.register(events.NewMessage(pattern=rf"^{SupportedCommands.ADD.value}(?!uri)(.*)"))  # type: ignore
async def handle_add_message(event: events.NewMessage.Event) -> None:
    """Handle /add command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    try:
        data = event.pattern_match.group(1).strip()
        if not data:
            raise ValueError()
        secret_data = parse_secret(data)
        user = await get_user(event)
        response = await add_secret_data(secret_data, user)
        await event.reply(response)
    except InvalidSecret:
        await event.reply(invalid_secret)
    except DuplicateSecret:
        await event.reply(duplicate_secret)
    except ValueError:
        await event.reply(no_input)
