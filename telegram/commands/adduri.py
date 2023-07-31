"""Handle adduri command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.exceptions import DuplicateSecret, InvalidSecret
from telegram.strings import duplicate_secret, invalid_secret, no_input

# Import some helper functions
from telegram.utils import SupportedCommands, add_secret_data, get_user
from totp.totp import OTP


def add_adduri_handlers(client: TelegramClient) -> None:
    """Add /adduri command Event Handler."""
    client.add_event_handler(handle_adduri_message)


# Register the function to handle the /adduri command
@events.register(events.NewMessage(pattern=rf"^{SupportedCommands.ADDURI.value}(?!file) (\w+)"))  # type: ignore
async def handle_adduri_message(event: events.NewMessage.Event) -> None:
    """Handle /adduri command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    secret_data = event.pattern_match.group(1)
    try:
        secret_data = OTP.parse_uri(secret_data)
        user = await get_user(event)
        response = await add_secret_data(secret_data, user)
        await event.reply(response)
    except InvalidSecret:
        await event.reply(invalid_secret)
    except DuplicateSecret:
        await event.reply(duplicate_secret)
    except ValueError:
        await event.reply(no_input)
