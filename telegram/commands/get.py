"""Handle get command."""
from asgiref.sync import sync_to_async

# Import necessary libraries and modules
from telethon import TelegramClient, events
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import Secret, User
from telegram.strings import no_input, no_result

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_get_handlers(client: TelegramClient) -> None:
    """get /get command Event Handler."""
    client.add_event_handler(handle_get_message)


# Register the function to handle the /get command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.GET.value}"))  # type: ignore
async def handle_get_message(event: events.NewMessage.Event) -> None:
    """Handle /get command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Define a prefix for the image URL
    prefix = f"{SupportedCommands.GET.value}"
    # Pad by 1 to consider the space after command
    prefix = prefix.ljust(len(prefix) + 1)

    # Extract the image query from the message text
    prefix_len = len(prefix)
    secret_filter = event.message.text[prefix_len:]
    if not secret_filter:
        await event.reply(no_input)
        return
    telegram_user: TelegramUser = await get_user(event)
    user = await sync_to_async(User.objects.get_user)(telegram_user.id)

    data, size = await sync_to_async(Secret.objects.get_secret)(
        user=user, secret_filter=secret_filter
    )
    if size > 0:
        response = f"Here are the TOTP for **{size}** found secrets.\n\n"
        for secret in data:
            response += f"{Secret.objects.reduced_print(secret)}\n"
        await event.reply(response)
    else:
        await event.reply(no_result)
