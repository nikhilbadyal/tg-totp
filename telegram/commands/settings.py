"""Settings command."""

from loguru import logger
from telethon import Button, TelegramClient, events

from telegram.strings import invalid_setting, user_fetch_failed
from telegram.user_settings import modify_page_size
from telegram.utils import SupportedCommands, UserSettings, get_user


def add_settings_handlers(client: TelegramClient) -> None:
    """Add /settings command Event Handler."""
    client.add_event_handler(handle_settings_command)
    client.add_event_handler(handle_settings_list_settings)
    client.add_event_handler(handle_settings_current_settings)


def settings_usage() -> str:
    """Return the usage of add command."""
    usage = (
        "This command help you in listing or modifying settings.\n"
        "To update a setting, use the following command in format:\n"
        "`/settings <setting_name> <value>`\n\n"
        "** For example **:\n`/settings page_size 5`\n\n"
    )
    return usage


@events.register(events.CallbackQuery(pattern="list_settings"))  # type: ignore
async def handle_settings_list_settings(
    event: events.callbackquery.CallbackQuery.Event,
):
    """Event handler for listing available settings.

    Args:
        event (CallbackQuery.Event): The callback query event.
    """
    await event.answer()

    response = "**Available settings**:\n\n"
    for setting in UserSettings:
        response += f"- `{setting.name}`: {setting.description}\n"

    await event.edit(response, parse_mode="markdown")


@events.register(events.CallbackQuery(pattern="current_settings"))  # type: ignore
async def handle_settings_current_settings(
    event: events.callbackquery.CallbackQuery.Event,
):
    """Event handler for listing current settings.

    Args:
        event (CallbackQuery.Event): The callback query event.
    """
    await event.answer()

    response = "**Current settings**:\n\n"
    try:
        user = await get_user(event)
        settings = user.settings
        for setting in settings:
            setting_enum = UserSettings(setting)
            description = setting_enum.description
            response += f"- `{setting_enum} {settings[setting]}`: __{description}__\n"
    except SystemError:
        response = user_fetch_failed

    await event.edit(response, parse_mode="markdown")


@events.register(events.NewMessage(pattern=f"^{SupportedCommands.SETTINGS.value}"))  # type: ignore
async def handle_settings_command(event: events.NewMessage.Event) -> None:
    """Event handler for the /settings command.

    Args:
        event (NewMessage.Event): The new message event.
    """

    # Extract the setting name and new value from the input message
    parts = event.message.text.split()
    if len(parts) < 3:
        response = "To update a setting, use the following command format:\n``/settings <setting_name> <value>`\n\n"
        response += "**For example**:\n`/settings page_size 5`\n\n"
        response += (
            "Click the **List Settings** button below to see available settings."
        )

        buttons = [
            Button.inline("List Settings", data="list_settings"),
            Button.inline("Current Settings", data="current_settings"),
        ]

        await event.reply(response, buttons=buttons, parse_mode="markdown")
        return

    setting_name = parts[1]
    new_value = parts[2]
    logger.debug(f"Received request to modify {setting_name} settings to {new_value}")

    user = await get_user(event)
    user_settings = user.settings

    settings_modification_functions = {
        UserSettings.PAGE_SIZE.value: modify_page_size,
    }

    setting_modification_function = settings_modification_functions.get(
        setting_name.lower()
    )
    if setting_modification_function:
        await setting_modification_function(event, user, user_settings, new_value)
    else:
        await event.reply(
            f"{invalid_setting} `{setting_name}`.",
            parse_mode="markdown",
        )
