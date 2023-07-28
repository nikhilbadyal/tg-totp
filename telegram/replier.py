"""Reply to messages."""

from loguru import logger
from telethon import TelegramClient

from telegram.commands.start import add_start_handlers


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

        # Start listening for incoming bot messages
        self.client.run_until_disconnected()

        # Log a message when the bot stops running
        logger.info("Stopped!")
