"""Handle export command."""
import os
from datetime import datetime

# Import necessary libraries and modules
from telethon import TelegramClient, events

from sqlitedb.models import Secret
from telegram.strings import no_export

# Import some helper functions
from telegram.utils import SupportedCommands, get_user


def add_export_handlers(client: TelegramClient) -> None:
    """export /export command Event Handler."""
    client.add_event_handler(handle_export_message)


# Register the function to handle the /export command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.EXPORT.value}\\s*(\\d*)$"))  # type: ignore
async def handle_export_message(event: events.NewMessage.Event) -> None:
    """Handle /export command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    data = event.pattern_match.group(1).strip()
    secret_filter = {}
    if data:
        secret_filter = {"id__in": [int(data)]}
    user = await get_user(event)
    data, size = await Secret.objects.export_secrets(
        user=user, secret_filter=secret_filter
    )
    if size == 0:
        await event.reply(message=no_export)
    else:
        uris = []
        for secret in data:
            uris.append(Secret.objects.export_print(secret))
        output_file = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, "w", encoding="utf-8") as file:
            file.write("\n".join(uris))
        await event.reply(message=f"Exported {size} URIs.", file=output_file)
        try:
            os.remove(output_file)
        except FileNotFoundError:
            pass
