"""Handle temp command."""
# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.commands.strings import no_input

# Import some helper functions
from telegram.commands.utils import SupportedCommands
from totp.totp import OTP


def add_temp_handlers(client: TelegramClient) -> None:
    """Add /temp command Event Handler."""
    client.add_event_handler(handle_temp_message)


# Register the function to handle the /temp command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.TEMP.value}"))  # type: ignore
async def handle_temp_message(event: events.NewMessage.Event) -> None:
    """Handle /temp command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    # Define a prefix for the image URL
    prefix = f"{SupportedCommands.TEMP.value}"
    # Pad by 1 to consider the space after command
    prefix = prefix.ljust(len(prefix) + 1)

    # Extract the image query from the message text
    prefix_len = len(prefix)
    totp = event.message.text[prefix_len:]
    if totp:
        await event.respond(OTP.now(secret=totp))
    else:
        # Send an error message if no input was provided
        await event.respond(no_input)
