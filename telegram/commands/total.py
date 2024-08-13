"""Handle total command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from sqlitedb.models import Secret

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_total_handlers(client: TelegramClient) -> None:
    """Get /total command Event Handler."""
    client.add_event_handler(handle_total_message)


def total_usage() -> str:
    """Return the usage of add command."""
    return (
        "This command help you in getting count of total no of secret.\n"
        "The command doesn't expects any argument as input."
    )


# Register the function to handle the /total command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.TOTAL.value}$"))  # type: ignore[misc]
async def handle_total_message(event: events.NewMessage.Event) -> None:
    """Handle /total command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    user = await get_user(event)
    size = await Secret.objects.total_secrets(user=user)  # type: ignore[misc]
    await event.reply(f"There are {size} secrets in total.")
