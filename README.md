# TG-TOTP: Telegram TOTP Bot 🔐

A secure, self-hosted Telegram bot for managing Two-Factor Authentication (2FA) TOTP codes. Store your TOTP secrets securely and generate time-based one-time passwords directly through Telegram.

## 🌟 Features

- **Secure TOTP Management**: Store and manage your 2FA secrets securely
- **Multiple Input Methods**: Add secrets via manual input, URI strings, or file uploads
- **QR Code Export**: Generate QR codes for easy backup and transfer
- **Bulk Operations**: Import/export multiple secrets at once
- **User Management**: Individual user data isolation with SQLite database
- **Rich Commands**: Comprehensive set of commands for complete TOTP management
- **Real-time Generation**: Generate TOTP codes with remaining validity time
- **Search & Filter**: Find your secrets quickly with search functionality

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Telegram API credentials (from [my.telegram.org](https://my.telegram.org))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/tg-totp.git
   cd tg-totp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**

   Create a `.env` file in the project root:
   ```env
   # Telegram Bot Configuration
   BOT_TOKEN=your_bot_token_here
   API_ID=your_api_id
   API_HASH=your_api_hash

   # Database Configuration
   DATABASE_URL=sqlite:///./tg_totp.db
   ```

4. **Initialize Database**
   ```bash
   python manage.py migrate
   ```

5. **Run the Bot**
   ```bash
   python main.py
   ```

### Development Mode

For development with auto-restart on file changes:
```bash
python watcher.py
```

## 🔧 Configuration

### Environment Variables

| Variable       | Description                            | Required | Default                  |
|----------------|----------------------------------------|----------|--------------------------|
| `BOT_TOKEN`    | Telegram Bot Token from BotFather      | ✅        | -                        |
| `API_ID`       | Telegram API ID from my.telegram.org   | ✅        | -                        |
| `API_HASH`     | Telegram API Hash from my.telegram.org | ✅        | -                        |
| `DATABASE_URL` | Database connection URL                | ✅        | `sqlite:///./tg_totp.db` |

### Getting Telegram Credentials

1. **Bot Token**:
   - Message [@BotFather](https://t.me/botfather) on Telegram
   - Create a new bot with `/newbot`
   - Copy the provided token

2. **API Credentials**:
   - Visit [my.telegram.org](https://my.telegram.org)
   - Log in with your phone number
   - Go to "API development tools"
   - Create a new application
   - Copy `api_id` and `api_hash`

## 📱 Bot Commands

### Core Commands

| Command  | Description                        | Usage             |
|----------|------------------------------------|-------------------|
| `/start` | Initialize bot and check status    | `/start`          |
| `/help`  | Show help message or command usage | `/help [command]` |

### Secret Management

| Command       | Description                            | Usage                              |
|---------------|----------------------------------------|------------------------------------|
| `/add`        | Add a new TOTP secret manually         | `/add secret=ABC123,issuer=Google` |
| `/adduri`     | Add secret from TOTP URI               | `/adduri otpauth://totp/...`       |
| `/addurifile` | Add secrets from uploaded file         | `/addurifile` (with file)          |
| `/list`       | List all stored secrets                | `/list [page]`                     |
| `/get`        | Get TOTP code for specific service     | `/get google`                      |
| `/rm`         | Remove a secret by ID                  | `/rm 123`                          |
| `/reset`      | Remove all secrets (with confirmation) | `/reset`                           |
| `/total`      | Show total count of stored secrets     | `/total`                           |

### Export & Backup

| Command     | Description                 | Usage            |
|-------------|-----------------------------|------------------|
| `/export`   | Export secrets as text/file | `/export [id]`   |
| `/exportqr` | Export secrets as QR codes  | `/exportqr [id]` |

### Utility Commands

| Command     | Description                  | Usage                             |
|-------------|------------------------------|-----------------------------------|
| `/temp`     | Generate TOTP without saving | `/temp secret=ABC123,issuer=Test` |
| `/settings` | Manage bot settings          | `/settings page_size=20`          |

## 🔐 Usage Examples

### Adding a Secret

**Method 1: Manual Entry**
```
/add secret=JBSWY3DPEHPK3PXP,issuer=Google,name=john@gmail.com
```

**Method 2: URI Format**
```
/adduri otpauth://totp/Google:john@gmail.com?secret=JBSWY3DPEHPK3PXP&issuer=Google
```

**Method 3: File Upload**
1. Send `/addurifile` command
2. Upload a text file containing TOTP URIs (one per line)

### Advanced Add Options

```bash
# With custom settings
/add secret=JBSWY3DPEHPK3PXP,issuer=GitHub,name=myaccount,digits=8,period=60,algorithm=SHA256

# Supported parameters:
# - secret: (Required) Base32 encoded secret
# - issuer: (Required) Service name
# - name: Account identifier
# - digits: OTP length (6-8, default: 6)
# - period: Validity period in seconds (15-120, default: 30)
# - algorithm: Hash algorithm (SHA1/SHA256/SHA512, default: SHA1)
```

### Getting TOTP Codes

```bash
# Search by service name
/get google

# Search by account name
/get john@gmail.com

# Response includes:
# - Service name and account
# - Current TOTP code
# - Time remaining until next code
# - Secret ID for management
```

### Export Options

```bash
# Export all secrets as text
/export

# Export specific secret by ID
/export 123

# Export all as QR codes (ZIP file)
/exportqr

# Export specific secret as QR code
/exportqr 123
```

## 🗄️ Database Schema

The bot uses SQLite with Django ORM:

### User Table
- `id`: Auto-increment primary key
- `name`: User's display name
- `telegram_id`: Unique Telegram user ID
- `status`: Account status (active/suspended/banned)
- `settings`: JSON field for user preferences
- `joining_date`: Account creation timestamp
- `last_updated`: Last modification timestamp

### Secret Table
- `id`: Auto-increment primary key
- `user`: Foreign key to User
- `secret`: Encrypted TOTP secret (unique)
- `issuer`: Service provider name
- `account_id`: Account identifier
- `digits`: OTP digit count (default: 6)
- `period`: Time period in seconds (default: 30)
- `algorithm`: Hash algorithm (default: SHA1)
- `joining_date`: Secret creation timestamp
- `last_updated`: Last modification timestamp

## 🔒 Security Features

- **Data Encryption**: All secrets are stored securely in the database
- **User Isolation**: Each user's data is completely isolated
- **Unique Constraints**: Prevents duplicate secret storage
- **Input Validation**: Comprehensive validation of all inputs
- **Error Handling**: Secure error messages without data leakage

## 🛠️ Development

### Project Structure

```
tg-totp/
├── main.py                 # Application entry point
├── manage.py              # Django management
├── watcher.py             # Development auto-reload
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
├── sqlitedb/             # Database models and utilities
│   ├── models.py         # Django models
│   ├── migrations/       # Database migrations
│   └── utils.py          # Database utilities
├── telegram/             # Telegram bot implementation
│   ├── commands/         # Bot command handlers
│   ├── replier.py        # Main bot class
│   ├── utils.py          # Telegram utilities
│   └── strings.py        # Bot messages
└── totp/                 # TOTP generation logic
    └── totp.py           # TOTP implementation
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-django pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=.
```

### Code Quality

The project uses several tools for code quality:

```bash
# Install pre-commit hooks
pre-commit install

# Run linting
pre-commit run --all-files

# Manual linting
ruff check .
black .
mypy .
```

### Adding New Commands

1. Create a new file in `telegram/commands/`
2. Implement the command handler
3. Add the handler to `telegram/replier.py`
4. Update the help system in `telegram/commands/help.py`

## 📦 Deployment

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py migrate

CMD ["python", "main.py"]
```

### Systemd Service

Create `/etc/systemd/system/tg-totp.service`:

```ini
[Unit]
Description=Telegram TOTP Bot
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/tg-totp
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10
Environment=PATH=/usr/bin:/usr/local/bin
EnvironmentFile=/path/to/tg-totp/.env

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable tg-totp
sudo systemctl start tg-totp
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Security Notice

- Keep your `.env` file secure and never commit it to version control
- Regularly backup your database
- Use strong, unique passwords for your Telegram account
- Consider running the bot on a secure, private server
- Monitor bot logs for any suspicious activity

## 🆘 Troubleshooting

### Common Issues

**Bot not responding:**
- Check if `BOT_TOKEN` is correct
- Verify bot is not blocked by Telegram
- Check network connectivity

**Database errors:**
- Run `python manage.py migrate`
- Check database file permissions
- Verify `DATABASE_URL` format

**Import/Export issues:**
- Ensure file format is correct (one URI per line)
- Check file encoding (UTF-8 recommended)
- Verify TOTP URI format

### Getting Help

- Check the `/help` command in the bot
- Review error messages in bot logs
- Open an issue on GitHub with detailed error information

---

**Live Bot**: You can check the progress [here](https://t.me/tgtotpbot)

Made with ❤️ for secure 2FA management
