"""Reply to messages."""

from loguru import logger
from telethon import TelegramClient

from telegram.commands.add import add_add_handlers
from telegram.commands.adduri import add_adduri_handlers
from telegram.commands.addurifile import add_addurifile_handlers
from telegram.commands.export import add_export_handlers
from telegram.commands.exportqr import add_exportqr_handlers
from telegram.commands.general import add_general_handlers
from telegram.commands.get import add_get_handlers
from telegram.commands.help import add_help_handlers
from telegram.commands.list import add_list_handlers
from telegram.commands.reset import add_reset_handlers
from telegram.commands.rm import add_rm_handlers
from telegram.commands.settings import add_settings_handlers
from telegram.commands.start import add_start_handlers
from telegram.commands.temp import add_temp_handlers
from telegram.commands.total import add_total_handlers
from telegram.utils import CustomMarkdown


class Telegram(object):
    """A class representing a Telegram bot."""

    def __init__(self, session_file: str):
        """Create a new Telegram object and connect to the Telegram API using
        the given session file.

        Args:
            session_file (str): The path to the session file to use for connecting to the Telegram API.
        """
        from main import env

        # Create a new TelegramClient instance with the given session file and API credentials
        self.client: TelegramClient = TelegramClient(
            session_file,
            env.int("API_ID"),
            env.str("API_HASH"),
            sequential_updates=True,
        )
        # Connect to the Telegram API using bot authentication
        logger.debug("Trying to connect using bot token")
        self.client.start(bot_token=env.str("BOT_TOKEN"))
        # Check if the connection was successful
        if self.client.is_connected():
            self.client.parse_mode = CustomMarkdown()
            logger.info("Connected to Telegram")
            logger.info("Using bot authentication. Only bot messages are recognized.")
        else:
            logger.info("Unable to connect with Telegram exiting.")
            exit(1)

    def bot_listener(self) -> None:
        """Listen for incoming bot messages and handle them based on the
        command."""

        # Register event handlers for each command the bot can handle
        add_start_handlers(self.client)
        add_temp_handlers(self.client)
        add_add_handlers(self.client)
        add_list_handlers(self.client)
        add_settings_handlers(self.client)
        add_get_handlers(self.client)
        add_adduri_handlers(self.client)
        add_addurifile_handlers(self.client)
        add_export_handlers(self.client)
        add_reset_handlers(self.client)
        add_total_handlers(self.client)
        add_rm_handlers(self.client)
        add_general_handlers(self.client)
        add_exportqr_handlers(self.client)
        add_help_handlers(self.client)

        # Start listening for incoming bot messages
        self.client.run_until_disconnected()

        # Log a message when the bot stops running
        logger.info("Stopped!")
