"""Handle temp command."""
# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.exceptions import InvalidSecret
from telegram.strings import invalid_secret, no_input

# Import some helper functions
from telegram.utils import SupportedCommands
from totp.totp import OTP


def add_temp_handlers(client: TelegramClient) -> None:
    """Add /temp command Event Handler."""
    client.add_event_handler(handle_temp_message)


def temp_usage() -> str:
    """Return the usage of add command."""
    usage = (
        "This command help you in getting OTP for a secret **without** saving it.\n"
        "The command expects secret as input to the command."
    )
    return usage


# Register the function to handle the /temp command
@events.register(events.NewMessage(pattern=rf"^{SupportedCommands.TEMP.value}(.*)"))  # type: ignore
async def handle_temp_message(event: events.NewMessage.Event) -> None:
    """Handle /temp command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    try:
        data = event.pattern_match.group(1).strip()
        if not data:
            raise ValueError()
        otp, valid_till, time_left = OTP.now(secret=data)
        response = (
            "`{otp}` is OTP. Valid for {time_left} sec till **{valid_till}**"
        ).format(
            otp=otp,
            time_left=time_left,
            valid_till=valid_till.strftime("%b %d, %Y %I:%M:%S %p"),
        )
        await event.reply(response)
    except InvalidSecret:
        await event.reply(invalid_secret)
    except ValueError:
        # Send an error message if no input was provided
        await event.reply(no_input)
