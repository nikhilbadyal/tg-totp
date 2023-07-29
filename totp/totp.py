"""TOTP generator."""
import traceback

import pyotp
from loguru import logger

from telegram.commands.exceptions import InvalidSecret
from telegram.commands.strings import invalid_secret
from telegram.commands.utils import is_valid_2fa_secret


class OTP(object):
    """Base class for OTP handlers."""

    @staticmethod
    def now(secret: str) -> str:
        """Generate TOTP."""
        try:
            is_valid_2fa_secret(secret)
            return str(pyotp.TOTP(secret).now())
        except InvalidSecret:
            totp = invalid_secret
        except ValueError:
            totp = invalid_secret
            logger.error(f"Failed to generate TOTP for {secret}")
        except Exception as exc:
            totp = invalid_secret
            logger.error(f"Failed to generate TOTP for {secret}")
            traceback.print_exception(exc)
        return totp
