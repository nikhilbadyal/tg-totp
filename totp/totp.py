"""TOTP generator."""
import traceback

import pyotp
from loguru import logger

from telegram.commands.strings import invalid_secret


class OTP(object):
    """Base class for OTP handlers."""

    @staticmethod
    def now(secret: str) -> str:
        """Generate TOTP."""
        try:
            totp = str(pyotp.TOTP(secret).now())
        except Exception as exc:
            totp = invalid_secret
            logger.error(f"Failed to generate TOTP for {secret}")
            traceback.print_exception(exc)
        return totp
