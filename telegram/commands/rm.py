"""Handle rm command."""
from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events

from sqlitedb.models import Secret
from telegram.strings import no_input

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_rm_handlers(client: TelegramClient) -> None:
    """Get /rm command Event Handler."""
    client.add_event_handler(handle_rm_message)


# Register the function to handle the /rm command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.RM.value}"))  # type: ignore
async def handle_rm_message(event: events.NewMessage.Event) -> None:
    """Handle /rm command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Define a prefix for the image URL
    prefix = f"{SupportedCommands.RM.value}"
    # Pad by 1 to consider the space after command
    prefix = prefix.ljust(len(prefix) + 1)

    # Extract the image query from the message text
    prefix_len = len(prefix)
    secret_id = event.message.text[prefix_len:]
    if not secret_id:
        await event.reply(no_input)
        return
    try:
        secret_id = int(secret_id)
    except ValueError:
        await event.reply(no_input)
        return
    user = await get_user(event)

    size = await sync_to_async(Secret.objects.rm_user_secret)(
        user=user, secret_id=secret_id
    )
    await event.reply(f"Delete {size} secret.")