"""Handle add command."""

# Import necessary libraries and modules
from telethon import TelegramClient, events

from telegram.exceptions import DuplicateSecretError, InvalidSecretError
from telegram.strings import duplicate_secret, invalid_secret, no_input

# Import some helper functions
from telegram.utils import SupportedCommands, add_secret_data, get_user, parse_secret


def add_add_handlers(client: TelegramClient) -> None:
    """Add /add command Event Handler."""
    client.add_event_handler(handle_add_message)


def add_usage() -> str:
    """Return the usage of add command."""
    return """
    Use the `/add` command to add a new account for Two-Factor
    Authentication (2FA) and store its secret key securely in the bot.\n

    Command Syntax:

    `/add secret=<SECRET_KEY>,issuer=<ISSUER_NAME>[,key=value[,key1=value1[,...]]]`

    \nArguments:

    - `secret`: (Mandatory) The secret key used for Two-Factor Authentication. It
    must be a base32 encoded string and is provided by the service you're setting up 2FA for.

    - `issuer`: (Mandatory) The name of the issuer or service for which the 2FA
    is being set up. For example, "Google" or "GitHub".

    \nOptional Arguments:

    - `digits`: The number of digits for the one-time passcode (OTP).
    It must be an integer between 6 and 8. (Default is 6 if not specified)

    - `name`: A custom name to identify the account. This can be useful
    if you have multiple accounts for the same service.

    - `period`: The time period in seconds for which the OTP is valid.
    It must be an integer between 15 and 120. (Default is 30 seconds if not specified)

    - `algorithm`: The algorithm used for generating OTPs.
    Supported values are "SHA1", "SHA256", and "SHA512". (Default is SHA1 if not specified)

    \nExamples:

    1. Add a new 2FA account for Google with the default settings:
       `
       /add secret=ABCDE12345FGHIJ,issuer=Google
       `
    2. Add a GitHub account with a custom name and 8-digit OTP:
       `
       /add secret=FGHIJ6789KLMNO,issuer=GitHub,name=MyGitHubAccount,digits=8
       `
    3. Add a 2FA account for Example Service with a longer OTP validity (60 seconds) and SHA256 algorithm:
       `
       /add secret=UVWXY1234567890,issuer=ExampleService,period=60,algorithm=SHA256
       `
    \nNotes:

    - Make sure to separate each argument with a comma (,).
    - The `secret` and `issuer` arguments are mandatory and must be provided.
    - Other arguments are optional and can be included as needed.
    - The `/add` command stores the secret key securely in the bot's database. For
    generating OTPs later using the `/get` command.
    """


# Register the function to handle the /add command
@events.register(events.NewMessage(pattern=rf"^{SupportedCommands.ADD.value}(?!uri)(.*)"))  # type: ignore[misc]
async def handle_add_message(event: events.NewMessage.Event) -> None:
    """Handle /add command.

    Args:
        event (events.NewMessage.Event): A new message event.

    Returns
    -------
        None: This function doesn't return anything.
    """
    try:
        data = event.pattern_match.group(1).strip()
        if not data:
            raise ValueError
        secret_data = parse_secret(data)
        user = await get_user(event)
        response = await add_secret_data(secret_data, user)
        await event.reply(response)
    except InvalidSecretError:
        await event.reply(invalid_secret)
    except DuplicateSecretError:
        await event.reply(duplicate_secret)
    except ValueError:
        await event.reply(no_input)
