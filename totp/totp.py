"""TOTP generator."""
import traceback
from typing import Dict

import pyotp
from loguru import logger

from sqlitedb.models import Secret
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

    @staticmethod
    def parse_uri(secret_uri: str) -> Dict[str, str]:
        """Generate TOTP."""
        try:
            otp = pyotp.parse_uri(secret_uri)
            data_points = Secret.objects.possible_inputs()
            secret_data = {}
            for data in data_points:
                if getattr(otp, data, None):
                    secret_data.update({data: str(getattr(otp, data))})
            return secret_data
        except IndexError:
            logger.error(f"Failed to parse {secret_uri}")
            raise InvalidSecret()
