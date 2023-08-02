"""Handle addurifile command."""
import os

# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.exceptions import FileProcessFail
from telegram.strings import file_process_failed, no_input, processing_file

# Import some helper functions
from telegram.utils import (
    SupportedCommands,
    bulk_add_secret_data,
    extract_secret_from_uri,
    get_uri_file_from_message,
    get_user,
    import_failure_output_file,
    process_uri_file,
)


def add_addurifile_handlers(client: TelegramClient) -> None:
    """Add /addurifile command Event Handler."""
    client.add_event_handler(handle_addurifile_message)


def addurifile_usage() -> str:
    """Return the usage of add command."""
    usage = (
        "/addurifile command expects file with the command.\n"
        "You can also reply to the already sent file."
    )
    return usage


# Register the function to handle the /addurifile command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.ADDURIFILE.value}$"))  # type: ignore
async def handle_addurifile_message(event: events.NewMessage.Event) -> None:
    """Handle /addurifile command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """
    message = None
    try:
        uri_file = await get_uri_file_from_message(event)
        message = await event.reply(processing_file)
        uris = process_uri_file(uri_file)
        parsed_secret, parse_failed = extract_secret_from_uri(uris)
        user = await get_user(event)
        import_status, failed_secrets = await bulk_add_secret_data(parsed_secret, user)
        import_status["invalid"] = len(parse_failed["invalid"])
        failed_secrets["invalid"] = parse_failed["invalid"]
        was_failed = False
        if len(parse_failed["invalid"]) > 0:
            was_failed = True
        else:
            for fail_type, count in import_status.items():
                if fail_type != "success" and count > 0:
                    was_failed = True
        await message.edit(f"Done processing with status `{import_status}`")
        if was_failed:
            output_file = import_failure_output_file(failed_secrets)
            await event.reply(file=output_file)
            os.remove(output_file)
    except FileNotFoundError:
        await event.reply(no_input)
    except FileProcessFail as e:
        if message:
            await message.edit(f"Unable to process\n`{e}`.\n{file_process_failed}")
