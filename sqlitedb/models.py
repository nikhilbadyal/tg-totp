"""Models."""
import operator
from functools import reduce
from typing import Any, Dict, Tuple

from django.db import models
from django.db.models import Field, Q
from loguru import logger

from manage import init_django
from sqlitedb.lookups import Like
from sqlitedb.utils import UserStatus, paginate_queryset
from telegram.exceptions import DuplicateSecret

init_django()

Field.register_lookup(Like)


class UserManager(models.Manager):  # type: ignore
    """Manager for the User model."""

    def get_user(self, telegram_id: int) -> "User":
        """Retrieve a User object from the database for a given user_id. If the
        user does not exist, create a new user.

        Args:
            telegram_id (int): The ID of the user to retrieve or create.

        Returns:
            User: The User object corresponding to the specified user ID
        """
        try:
            user: User
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id, defaults={"name": f"User {telegram_id}"}
            )
        except IndexError:
            raise SystemError()
        else:
            if created:
                logger.info(f"Created new user {user}")
            else:
                logger.info(f"Retrieved existing {user}")
        return user


class User(models.Model):
    """Model for storing user data.

    Attributes:
        id (int): The unique ID of the user.
        name (str or None): The name of the user, or None if no name was provided.
        telegram_id (int): The ID of the user.
        status (str): The current status of the user's account (active, suspended, or temporarily banned).
        joining_date (datetime): The date and time when the user was added to the database.
        last_updated (datetime): The date and time when the user's details were last updated.

    Managers:
        objects (UserManager): The custom manager for this model.

    Meta:
        db_table (str): The name of the database table used to store this model's data.

    Raises:
        IntegrityError: If the user's Telegram ID is not unique.
    """

    # User ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # User name, max length of 255, can be null
    name = models.CharField(max_length=255, blank=True)

    # User Telegram ID, integer
    telegram_id = models.IntegerField(unique=True)

    # State of the user
    status = models.CharField(
        max_length=20,
        choices=[(status.value, status.name) for status in UserStatus],
        default=UserStatus.ACTIVE.value,
    )

    # Date and time when the user was added to the database, auto-generated
    joining_date = models.DateTimeField(auto_now_add=True)

    # Date and time when the user details was modified , auto-generated
    last_updated = models.DateTimeField(auto_now=True)

    # Conversation settings, stored as a JSON object
    settings = models.JSONField(default=dict)

    # Use custom manager for this model
    objects = UserManager()

    class Meta:
        # Database table name
        db_table = "user"

    def __str__(self) -> str:
        """Return a string representation of the user object."""
        return f"User(id={self.id}, name={self.name}, telegram_id={self.telegram_id}, status={self.status})"


class SecretManager(models.Manager):  # type: ignore
    """Manager for the User model."""

    def create_secret(self, user: User, **kwargs: Any) -> "Secret":
        """Add secret."""
        if self.filter(user=user, secret=kwargs["secret"]).exists():
            raise DuplicateSecret()
        secret = self.create(user=user, **kwargs)
        return secret  # type: ignore

    def possible_inputs(self) -> Dict[str, str]:
        """Possible input."""
        inputs = {
            "secret": "secret",
            "issuer": "issuer",
            "digits": "digits",
            "name": "account_id",
            "period": "period",
            "algorithm": "algorithm",
        }
        return inputs

    def get_secrets(self, user: User, page: int, per_page: int) -> Any:
        """Return a paginated list of secrets for a given user.

        Args:
            user (User): User.
            page (int): The current page number.
            per_page (int): The number of conversations to display per page.

        Returns:
            dict: A dictionary containing the paginated conversations and pagination details.
        """
        # Retrieve the conversations for the given user
        data = (
            self.only("id", "issuer", "account_id", "secret", "joining_date")
            .filter(user=user)
            .order_by("-last_updated")
        )

        # Use the helper function to paginate the queryset
        return paginate_queryset(data, page, per_page)

    def get_secret(self, user: User, secret_filter: str) -> Tuple[Any, int]:
        """Return a paginated list of secrets for a given user.

        Args:
            user (User): User.
            secret_filter (str): The current page number.

        Returns:
            tuple: Data and the no of records in it
        """
        # Retrieve the conversations for the given user
        filter_kwargs = {
            "account_id__icontains": secret_filter,
            "issuer__icontains": secret_filter,
        }
        or_filters = [Q(**{key: val}) for key, val in filter_kwargs.items()]
        # noinspection PyTypeChecker
        data = (
            self.only("issuer", "account_id", "secret")
            .filter(user=user)
            .filter(reduce(operator.or_, or_filters))
            .order_by("issuer")
        )
        size = len(data)
        return data, size

    def export_secrets(self, user: User) -> Tuple[Any, int]:
        """Return all secrets for a given user.

        Args:
            user (User): User.

        Returns:
            tuple: Data and the no of records in it
        """
        # Retrieve the conversations for the given user
        # noinspection PyTypeChecker
        data = self.filter(user=user)
        size = len(data)
        return data, size

    def reduced_print(self, secret: "Secret") -> Any:
        """Print Secret with minial details.

        Returns:
            str: String repr of secret.
        """
        from totp.totp import OTP

        return "`{otp}` is OTP for account **{account}** issued by **{issuer}**".format(
            otp=OTP.now(secret=secret.secret),
            account=secret.account_id,
            issuer=secret.issuer,
        )

    def export_print(self, secret: "Secret") -> Any:
        """Print Secret with minial details.

        Returns:
            str: String repr of secret.
        """
        return (
            "otpauth://totp/{issuer}%3A{account}?period={period}&digits={digits}&"
            "algorithm={algorithm}&secret={secret}&issuer={issuer}"
        ).format(
            issuer=secret.issuer.strip(),
            account=secret.account_id.strip(),
            period=secret.period,
            digits=secret.digits,
            algorithm=secret.algorithm.strip(),
            secret=secret.secret.strip(),
        )

    def clear_secret(self, user: User) -> int:
        """Clear all secret for a given user."""
        deleted, _ = self.filter(user=user).delete()
        return deleted


#


class Secret(models.Model):
    """Model to store secrets."""

    # Secret ID, auto-generated primary key
    id = models.AutoField(primary_key=True)

    # Foreign Key to user
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    # Actual Secret
    secret = models.TextField(unique=True)

    # Issue of the secret
    issuer = models.CharField(max_length=256)

    # Account/Email-id  used
    account_id = models.CharField(max_length=256, blank=True)

    # Digit in output OTP
    digits = models.IntegerField(default=6)

    # Period of the secret
    period = models.IntegerField(default=30)

    # Algorithm used
    algorithm = models.CharField(max_length=256, default="SHA1")

    # Date and time when the secret was added to the database, auto-generated
    joining_date = models.DateTimeField(auto_now_add=True)

    # Date and time when the secret was modified , auto-generated
    last_updated = models.DateTimeField(auto_now=True)

    # Use custom manager for this model
    objects = SecretManager()

    class Meta:
        # Database table name
        db_table = "secret"

    def __str__(self) -> str:
        """Return a string representation of the user object."""
        return (
            f"Secret [{self.secret}](spoiler) issued by {self.issuer} for {self.account_id} added on"
            f" {self.joining_date.strftime('%b %d, %Y %I:%M:%S %p')}"
        )
