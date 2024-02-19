"""Models."""

from typing import Any, Self
from urllib.parse import quote

from django.db import IntegrityError, models
from django.db.models import Field
from telethon.tl.types import User as TelegramUser

from manage import init_django
from sqlitedb.lookups import ILike
from sqlitedb.utils import UserStatus, paginate_queryset
from telegram.exceptions import DuplicateSecretError

init_django()

Field.register_lookup(ILike)


class UserManager(models.Manager):  # type: ignore[type-arg]
    """Manager for the User model."""

    async def get_user(self: Self, telegram_user: TelegramUser) -> "User":
        """Retrieve a User object from the database for a given user_id. If the user does not exist, create a new user.

        Args:
            telegram_user (TelegramUser): The ID of the user to retrieve or create.

        Returns
        -------
            User: The User object corresponding to the specified user ID
        """
        try:
            user: User = await self.filter(telegram_id=telegram_user.id).aget()
        except self.model.DoesNotExist:
            user_dict = {
                "telegram_id": telegram_user.id,
                "name": f"{telegram_user.first_name} {telegram_user.last_name}",
            }
            user = await User.objects.acreate(**user_dict)

        return user


class User(models.Model):
    """Model for storing user data.

    Attributes
    ----------
        id (int): The unique ID of the user.
        name (str or None): The name of the user, or None if no name was provided.
        telegram_id (int): The ID of the user.
        status (str): The current status of the user's account (active, suspended, or temporarily banned).
        joining_date (datetime): The date and time when the user was added to the database.
        last_updated (datetime): The date and time when the user's details were last updated.

    Raises
    ------
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
        """Database table name."""

        db_table = "user"

    def __str__(self: Self) -> str:
        """Return a string representation of the user object."""
        return f"User(id={self.id}, name={self.name}, telegram_id={self.telegram_id}, status={self.status})"


class SecretManager(models.Manager):  # type: ignore[type-arg]
    """Manager for the User model."""

    async def create_secret(self: Self, user: User, **kwargs: Any) -> "Secret":
        """Add secret."""
        try:
            obj = await self.acreate(user=user, **kwargs)
            if isinstance(obj, Secret):
                return obj
            raise IntegrityError
        except IntegrityError as e:
            raise DuplicateSecretError from e

    def possible_inputs(self: Self) -> dict[str, str]:
        """Possible input."""
        return {
            "secret": "secret",
            "issuer": "issuer",
            "digits": "digits",
            "name": "account_id",
            "period": "period",
            "algorithm": "algorithm",
        }

    def get_secrets(self: Self, user: User, page: int, per_page: int) -> Any:
        """Return a paginated list of secrets for a given user.

        Args:
            user (User): User.
            page (int): The current page number.
            per_page (int): The number of records to display per page.

        Returns
        -------
            dict: A dictionary containing the paginated records and pagination details.
        """
        from telegram.utils import or_filters, prepare_user_filter

        user_filter = prepare_user_filter(user)
        combined_filter = or_filters(user_filter)
        data = (
            self.only("id", "issuer", "account_id", "secret", "joining_date")
            .filter(combined_filter)
            .order_by("-last_updated")
        )

        # Use the helper function to paginate the queryset
        return paginate_queryset(data, page, per_page)

    async def get_secret(self: Self, user: User, secret_filter: str) -> tuple[Any, int]:
        """Return a paginated list of secrets for a given user.

        Args:
            user (User): User.
            secret_filter (str): The current page number.

        Returns
        -------
            tuple: Data and the no of records in it
        """
        # Retrieve the records for the given user
        try:
            filter_kwargs = {
                "account_id__icontains": secret_filter,
                "issuer__icontains": secret_filter,
            }
            return await self.export_secrets(user, filter_kwargs)
        except self.model.DoesNotExist:
            return [], 0

    async def export_secrets(self: Self, user: User, secret_filter: dict[str, Any]) -> tuple[Any, int]:
        """Return all secrets for a given user.

        Args:
            user (User): User.
            secret_filter (Dict[str, str]): Filter Criteria.

        Returns
        -------
            tuple: Data and the no of records in it
        """
        from telegram.utils import or_filters, prepare_user_filter

        # noinspection PyTypeChecker
        try:
            user_filter = prepare_user_filter(user)
            combined_filter = or_filters(secret_filter)
            data = self.filter(**user_filter)
            if combined_filter:
                data = data.filter(combined_filter)
            result = list(data)
            return result, len(result)
        except self.model.DoesNotExist:
            return [], 0

    async def total_secrets(self: Self, user: User) -> int:
        """Return count of all secrets for a given user.

        Args:
            user (User): User.

        Returns
        -------
            int:no of records
        """
        # Retrieve the records for the given user
        # noinspection PyTypeChecker
        return await self.filter(user=user).acount()

    def reduced_print(self: Self, secret: "Secret") -> Any:
        """Print Secret with minial details.

        Returns
        -------
            str: String repr of secret.
        """
        from totp.totp import OTP

        otp, valid_till, time_left = OTP.now(secret=secret.secret)

        return (
            "`{otp}` is OTP for account **{account}** issued by **{issuer}**.(ID - `{id}`)."
            "Valid for {time_left} sec till **{valid_till}**"
        ).format(
            otp=otp,
            account=secret.account_id,
            issuer=secret.issuer,
            id=secret.id,
            time_left=time_left,
            valid_till=valid_till.strftime("%b %d, %Y %I:%M:%S %p"),
        )

    def export_print(self: Self, secret: "Secret") -> str:
        """Print Secret with minial details.

        Returns
        -------
            str: String repr of secret.
        """
        return (
            "otpauth://totp/{issuer}%3A{account}?period={period}&digits={digits}&"
            "algorithm={algorithm}&secret={secret}&issuer={issuer}"
        ).format(
            issuer=quote(secret.issuer.strip()),
            account=quote(secret.account_id.strip()),
            period=secret.period,
            digits=secret.digits,
            algorithm=secret.algorithm.strip(),
            secret=secret.secret.strip(),
        )

    async def clear_user_secrets(self: Self, user: User) -> int:
        """Clear all secret for a given user."""
        deleted, _ = await self.filter(user=user).adelete()
        return deleted

    async def rm_user_secret(self: Self, user: User, secret_id: int) -> int:
        """Clear secret with given id."""
        deleted, _ = await self.filter(user=user, id=secret_id).adelete()
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
        """Database table name."""

        db_table = "secret"

    def __str__(self: Self) -> str:
        """Return a string representation of the user object."""
        return (
            f"Secret [{self.secret}](spoiler) "
            f"with ID `{self.id}` "
            f"issued by **{self.issuer}** "
            f"for account **{self.account_id}** "
            f"added on **{self.joining_date.strftime('%b %d, %Y %I:%M:%S %p')}**"
        )
