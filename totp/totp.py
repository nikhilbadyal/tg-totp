"""TOTP generator."""
import datetime
import traceback
from typing import Dict

import pyotp
from loguru import logger

from sqlitedb.models import Secret
from telegram.exceptions import InvalidSecret
from telegram.strings import invalid_secret
from telegram.utils import is_valid_2fa_secret


class OTP(object):
    """Base class for OTP handlers."""

    @staticmethod
    def now(secret: str) -> tuple[str, datetime.datetime, int]:
        """Generate TOTP."""
        try:
            is_valid_2fa_secret(secret)
            totp = pyotp.TOTP(secret)
            otp = str(totp.now())
            curr_time = datetime.datetime.now()
            time_left = int(totp.interval - curr_time.timestamp() % totp.interval)
            time_remaining = datetime.timedelta(seconds=time_left)
            return otp, curr_time + time_remaining, time_left
        except InvalidSecret:
            totp = invalid_secret
        except ValueError:
            totp = invalid_secret
            logger.error(f"Failed to generate TOTP for {secret}")
        except Exception as exc:
            totp = invalid_secret
            logger.error(f"Failed to generate TOTP for {secret}")
            traceback.print_exception(exc)
        return str(totp), datetime.datetime.now(), 0

    @staticmethod
    def parse_uri(secret_uri: str) -> Dict[str, str]:
        """Generate TOTP."""
        try:
            otp = pyotp.parse_uri(secret_uri)
            data_points = Secret.objects.possible_inputs()
            secret_data = {}
            for data, my_data in data_points.items():
                if getattr(otp, data, None):
                    secret_data.update({my_data: str(getattr(otp, data))})
            return secret_data
        except ValueError as e:
            raise InvalidSecret(e)
