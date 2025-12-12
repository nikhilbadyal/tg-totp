"""Handle adduri command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.exceptions import DuplicateSecretError, InvalidSecretError
from telegram.strings import duplicate_secret, invalid_secret, no_input

# Import some helper functions
from telegram.utils import SupportedCommands, add_secret_data, get_user
from totp.totp import OTP


def add_adduri_handlers(client: TelegramClient) -> None:
    """Add /adduri command Event Handler."""
    client.add_event_handler(handle_adduri_message)


def adduri_usage() -> str:
    """Return the usage of add command."""
    return (
        "/adduri command expect `Key-URI` as input to the command.\n"
        "You can check the format "
        "[here](https://docs.yubico.com/yesdk/users-manual/application-oath/uri-string-format.html)"
    )


# Register the function to handle the /adduri command
@events.register(events.NewMessage(pattern=rf"^{SupportedCommands.ADDURI.value}(?!file)(.*)"))  # type: ignore[untyped-decorator]
async def handle_adduri_message(event: events.NewMessage.Event) -> None:
    """Handle /adduri command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    try:
        data = event.pattern_match.group(1).strip()
        if not data:
            raise ValueError
        secret_data = OTP.parse_uri(data)
        user = await get_user(event)
        response = await add_secret_data(secret_data, user)
        await event.reply(response)
    except InvalidSecretError:
        await event.reply(invalid_secret)
    except DuplicateSecretError:
        await event.reply(duplicate_secret)
    except ValueError:
        await event.reply(no_input)
