"""Handle adduri command."""
from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import User
from telegram.commands.exceptions import DuplicateSecret, InvalidSecret
from telegram.commands.strings import duplicate_secret, invalid_secret, no_input

# Import some helper functions
from telegram.commands.utils import SupportedCommands, add_secret_data, get_user
from totp.totp import OTP


def add_adduri_handlers(client: TelegramClient) -> None:
    """Add /adduri command Event Handler."""
    client.add_event_handler(handle_adduri_message)


# Register the function to handle the /adduri command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.ADDURI.value}(?!file)"))  # type: ignore
async def handle_adduri_message(event: events.NewMessage.Event) -> None:
    """Handle /adduri command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Define a prefix for the image URL
    prefix = f"{SupportedCommands.ADDURI.value}"
    # Pad by 1 to consider the space after command
    prefix = prefix.ljust(len(prefix) + 1)

    # Extract the image query from the message text
    prefix_len = len(prefix)
    secret_data = event.message.text[prefix_len:]
    try:
        secret_data = OTP.parse_uri(secret_data)
        telegram_user: TelegramUser = await get_user(event)
        user = await sync_to_async(User.objects.get_user)(telegram_user.id)
        response = await add_secret_data(secret_data, user)
        await event.reply(response)
    except InvalidSecret:
        await event.reply(invalid_secret)
    except DuplicateSecret:
        await event.reply(duplicate_secret)
    except ValueError:
        await event.reply(no_input)