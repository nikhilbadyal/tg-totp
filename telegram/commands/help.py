"""Handle help command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.strings import command_not_found, docs_not_found

# Import some helper functions
from telegram.utils import SupportedCommands, command_help

help_message = """
Hey there,Welcome to the Help Center. Here you can get TOTP for your 2FA account.

Here's a list of supported commands:

1. `/add`: Add secret (usage: `/add <arguments>`).
2. `/adduri`: Add secret using URI (usage: `/adduri <arguments>`).
3. `/addurifile`: Add secret using URI file (usage: `/addurifile <arguments>`).
4. `/export`: Export secrets (usage: `/export <arguments>`).
5. `/exportqr`: Export secrets as a QR code (usage: `/exportqr <arguments>`).
6. `/get`: Get something (usage: `/get <arguments>`).
7. `/help`: Show available commands and their usage (usage: `/help`).
8. `/list`: List secrets (usage: `/list`).
9. `/reset`: Reset all secrets (usage: `/reset`).
10. `/rm`: Remove some secret (usage: `/rm <arguments>`).
11. `/settings`: Bot settings (usage: `/settings <arguments>`).
12. `/start`: Start using the bot (usage: `/start`).
13. `/temp`: Get otp without saving TOTP (usage: `/temp <arguments>`).
14. `/total`: Get the total count of secrets(usage: `/total`).

For more information on each command, type `/help <command>`.

If you have any questions or need assistance, feel free to ask. Happy botting!
"""


def add_help_handlers(client: TelegramClient) -> None:
    """Add /help command Event Handler."""
    client.add_event_handler(handle_help_message)


def help_usage() -> str:
    """Return the usage of add command."""
    return "Really bro🥸."


# Register the function to handle the /help command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.HELP.value}(.*)"))  # type: ignore[untyped-decorator]
async def handle_help_message(event: events.NewMessage.Event) -> None:
    """Handle /help command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    data = event.pattern_match.group(1).strip()
    if not data:
        await event.reply(help_message)
    elif f"/{data}" not in SupportedCommands.get_values():
        await event.reply(command_not_found)
    else:
        try:
            usage = command_help(data)
            await event.reply(usage)
        except KeyError:
            await event.reply(docs_not_found)
