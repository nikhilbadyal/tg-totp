"""List User Conversation."""
from typing import List, Tuple

from asgiref.sync import sync_to_async
from loguru import logger
from telethon import Button, TelegramClient, events

from sqlitedb.models import Secret, User
from telegram.utils import PAGE_SIZE, SupportedCommands, get_user


def add_list_handlers(client: TelegramClient) -> None:
    """Add /list command Event Handler."""
    client.add_event_handler(handle_list_command)
    client.add_event_handler(navigate_pages)


@events.register(events.CallbackQuery(pattern=r"(next|prev)_page:(\d+)"))  # type: ignore
async def navigate_pages(event: events.callbackquery.CallbackQuery.Event):
    """Event handler to navigate between pages of records.

    Args:
        event (CallbackQuery.Event): The callback query event.
    """
    _, page = event.data.decode("utf-8").split(":")
    page = int(page)

    await event.answer()
    user = await get_user(event)
    response, buttons = await send_paginated_records(user, page)
    await event.edit(response, buttons=buttons, parse_mode="markdown")


async def send_paginated_records(
    user: User, page: int
) -> Tuple[str, List[List[Button]] | None]:
    """Fetch and send paginated records for the given user.

    Args:
        user (User): The Telegram ID of the user.
        page (int): The current page number.

    Returns:
        Tuple[str, List]: A tuple containing the response message and the list of buttons.
    """
    user_settings = user.settings

    page_size = user_settings.get("page_size", PAGE_SIZE)

    result = await sync_to_async(Secret.objects.get_secrets)(user, page, page_size)

    response = "**Secrets**:\n"
    for secret in result["data"]:
        response += f"- {secret}\n"

    response += f"\nPage {result['current_page']} of {result['total_pages']}"
    response += f"\n[Total records {result['total_data']}](spoiler)"

    buttons: List[List[Button]] = []
    main_button = []
    if result["has_previous"]:
        main_button.append(Button.inline("Previous", data=f"prev_page:{page - 1}"))
    if result["has_next"]:
        main_button.append(Button.inline("Next", data=f"next_page:{page + 1}"))
    buttons.append(main_button)
    extra = []
    if page != 1:
        extra.append(Button.inline("First Page", data="next_page:1"))
    if page != result["total_pages"]:
        last_page = result["total_pages"]
        extra.append(Button.inline("Last Page", data=f"next_page:{last_page}"))
    buttons.append(extra)

    if not buttons:
        buttons = None  # type: ignore

    return response, buttons


# Register the function to handle the /list command
@events.register(events.NewMessage(pattern=f"^{SupportedCommands.LIST.value}$"))  # type: ignore
async def handle_list_command(event: events.NewMessage.Event) -> None:
    """Event handler for the /list command.

    Args:
        event (NewMessage.Event): The new message event.
    """
    # Log that a request has been received to delete all user data
    logger.debug("Received request to list all secrets")
    page = 1
    user = await get_user(event)
    response, buttons = await send_paginated_records(user, page)
    await event.reply(response, buttons=buttons)
