"""Main function."""
from environs import Env
from loguru import logger

from sqlitedb.sqlite import SQLiteDatabase
from telegram.replier import Telegram

project_name = "tg-totp"
env = Env()
env.read_env()
db = SQLiteDatabase()
if __name__ == "__main__":
    if env.str("BOT_TOKEN", None):
        Telegram(project_name).bot_listener()
    else:
        logger.info("No bot token provided.")
