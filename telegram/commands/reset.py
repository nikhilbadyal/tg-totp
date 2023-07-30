"""Handle Reset Command."""
from asgiref.sync import sync_to_async
from loguru import logger

# Import necessary libraries and modules
from telethon import Button, TelegramClient, events
from telethon.tl.types import User as TelegramUser

from sqlitedb.models import Secret, User
from telegram.strings import ignore

# Import some helper functions
from telegram.utils import SupportedCommands, get_user

reset_yes_data = b"reset_yes"
reset_yes_description = "Yes!"
reset_no_data = b"reset_no"
reset_no_description = "No!"


def add_reset_handlers(client: TelegramClient) -> None:
    """Add /reset command Event Handler."""
    client.add_event_handler(handle_reset_command)
    client.add_event_handler(handle_reset_confirm_response)


@events.register(events.callbackquery.CallbackQuery(pattern="^reset_(yes|no)$"))  # type: ignore
async def handle_reset_confirm_response(
    event: events.callbackquery.CallbackQuery.Event,
):
    """Handle reset confirmation response.

    This function is registered as an event handler to handle the callback query
    generated when the user clicks one of the buttons in the confirmation message
    after sending the /reset command. If the user clicks the "Hell yes!" button,
    it imports the main function for cleaning up user data and calls it to delete
    all user data. If the user clicks the "Fuck, No!" button, it ignores the request.

    Args:
        event (events.callbackquery.CallbackQuery.Event): The event object associated with the callback query.

    Returns:
        None: This function doesn't return anything.
    """
    await event.answer()
    logger.debug("Received reset callback")
    if event.data == reset_yes_data:
        telegram_user: TelegramUser = await get_user(event)
        user = await sync_to_async(User.objects.get_user)(telegram_user.id)
        size = await sync_to_async(Secret.objects.clear_secret)(user=user)
        await event.reply(f"Deleted {size} secrets.")
    elif event.data == reset_no_data:
        await event.edit(ignore)


# Register the function to handle the /reset command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.RESET.value}$"))  # type: ignore
async def handle_reset_command(event: events.NewMessage.Event) -> None:
    """Handle /reset command Delete all message history for a user.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns:
        None: This function doesn't return anything.
    """

    # Log that a request has been received to delete all user data
    logger.debug("Received request to delete all user secrets.")

    await event.reply(
        "Are you sure you want to delete everything?",
        buttons=[
            [Button.inline(reset_yes_description, data=reset_yes_data)],
            [Button.inline(reset_no_description, data=reset_no_data)],
        ],
    )
