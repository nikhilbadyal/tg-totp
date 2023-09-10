"""TOTP generator."""
import datetime
from typing import Dict

import pyotp

from sqlitedb.models import Secret
from telegram.exceptions import InvalidSecretError
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
            utc = datetime.timezone.utc
            curr_time = datetime.datetime.now(utc)
            time_left = int(totp.interval - curr_time.timestamp() % totp.interval)
            time_remaining = datetime.timedelta(seconds=time_left)
            return otp, curr_time + time_remaining, time_left
        except ValueError as e:
            raise InvalidSecretError from e

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
        except ValueError as e:
            raise InvalidSecretError(e) from e
        else:
            return secret_data
