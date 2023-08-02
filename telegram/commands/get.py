"""Handle get command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from sqlitedb.models import Secret
from telegram.strings import no_input, no_result

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_get_handlers(client: TelegramClient) -> None:
    """get /get command Event Handler."""
    client.add_event_handler(handle_get_message)

def get_usage() -> str:
    """Return the usage of add command."""
    usage = (
        "/get command expect filter as input to the command.\n"
        "If any URI(s) contain issuer or account name which matches with filter. "
        "It will be returned along with ID and OTP."
    )
    return usage
# Register the function to handle the /get command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.GET.value}(.*)"))  # type: ignore
async def handle_get_message(event: events.NewMessage.Event) -> None:
    """Handle /get command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    try:
        data = event.pattern_match.group(1).strip()
        if not data:
            raise ValueError()
        user = await get_user(event)

        data, size = await Secret.objects.get_secret(user=user, secret_filter=data)
        if size > 0:
            response = f"Here are the TOTP for **{size}** found secrets.\n\n"
            for secret in data:
                response += f"➡️ {Secret.objects.reduced_print(secret)}\n"
            await event.reply(response)
        else:
            await event.reply(no_result)
    except ValueError:
        await event.reply(no_input)
