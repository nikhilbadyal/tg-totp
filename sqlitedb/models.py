"""Models."""
from typing import Any, List, Union

from django.db import models
from loguru import logger
from telethon.tl.types import User as TelegramUser

from manage import init_django
from sqlitedb.utils import ErrorCodes, UserStatus, paginate_queryset
from telegram.commands.exceptions import DuplicateSecret

init_django()


class UserManager(models.Manager):  # type: ignore
    """Manager for the User model."""

    def get_user(self, telegram_id: int) -> Union["User", ErrorCodes]:
        """Retrieve a User object from the database for a given user_id. If the
        user does not exist, create a new user.

        Args:
            telegram_id (int): The ID of the user to retrieve or create.

        Returns:
            Union[User, int]: The User object corresponding to the specified user ID, or -1 if an error occurs.
        """
        try:
            user: User
            user, created = User.objects.get_or_create(
                telegram_id=telegram_id, defaults={"name": f"User {telegram_id}"}
            )
        except IndexError as e:
            logger.error(
                f"Unable to get or create user: {e} because of {type(e).__name__}"
            )
            return ErrorCodes.exceptions
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

    def create_secret(self, telegram_user: TelegramUser, **kwargs: Any) -> "Secret":
        """Add secret."""
        user = User.objects.get_user(telegram_user.id)
        secret, created = self.get_or_create(user=user, **kwargs)
        if not created:
            raise DuplicateSecret()
        return secret  # type: ignore

    def possible_inputs(self) -> List[str]:
        """Possible input."""
        return ["secret", "issuer", "account_id", "digits", "period", "algorithm"]

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
            f"Secret [{self.secret}](spoiler) for {self.issuer} with ID {self.id} added on"
            f" {self.joining_date.strftime('%b %d, %Y %I:%M:%S %p')}"
        )
