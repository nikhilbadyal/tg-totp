"""Handle add command."""
from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events
from telethon.tl.types import User

from sqlitedb.models import Secret
from telegram.commands.exceptions import DuplicateSecret, InvalidSecret
from telegram.commands.strings import (
    added_secret,
    duplicate_secret,
    invalid_secret,
    no_input,
)

# Import some helper functions
from telegram.commands.utils import (
    SupportedCommands,
    get_user,
    is_valid_2fa_secret,
    parse_secret,
)


def add_add_handlers(client: TelegramClient) -> None:
    """Add /add command Event Handler."""
    client.add_event_handler(handle_add_message)


# Register the function to handle the /add command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.ADD.value}"))  # type: ignore
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
        is_valid_2fa_secret(secret_data["secret"])
        # Get the user associated with the message
        telegram_user: User = await get_user(event)
        await sync_to_async(Secret.objects.create_secret)(
            telegram_user=telegram_user, **secret_data
        )
        await event.reply(added_secret)
    except InvalidSecret:
        await event.reply(invalid_secret)
    except ValueError:
        await event.reply(no_input)
    except DuplicateSecret:
        await event.reply(duplicate_secret)
