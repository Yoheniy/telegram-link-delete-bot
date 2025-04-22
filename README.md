# Telegram Link Delete Bot

A Telegram bot that automatically detects and deletes messages containing links in a group chat. The bot ignores messages from group administrators and can be configured to whitelist specific domains.

## Features

- Automatic detection and deletion of messages containing URLs
- Whitelist support for specific domains
- Admin commands to toggle bot functionality
- Rate limiting to prevent API abuse
- Logging of all deletion actions
- Temporary notification messages
- Support for all types of messages (text, captions)

## Setup

1. Create a new bot with BotFather:
   - Open Telegram and search for @BotFather
   - Send `/newbot` command
   - Follow the instructions to create your bot
   - Save the bot token provided by BotFather

2. Clone this repository:
   ```bash
   git clone [repository-url]
   cd telegramlinkdeletebot
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

## Deployment

1. Make sure your bot has the following permissions in the group:
   - Delete messages
   - Send messages
   - Read messages

2. Add the bot to your group as an administrator with the above permissions.

3. Run the bot:
   ```bash
   python bot.py
   ```

For production deployment, you may want to use a process manager like `systemd` or `supervisor`.

### Example systemd Service

Create a file `/etc/systemd/system/telegrambot.service`:
```ini
[Unit]
Description=Telegram Link Delete Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/bot
Environment=PYTHONUNBUFFERED=1
ExecStart=/path/to/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:
```bash
sudo systemctl enable telegrambot
sudo systemctl start telegrambot
```

## Admin Commands

- `/start` - Display bot information
- `/toggle` - Toggle link deletion on/off
- `/status` - Check bot status and configuration

## Logs

The bot logs all actions to `bot.log` in the project directory. Monitor this file for deletion actions and errors:
```bash
tail -f bot.log
```

## Customization

To modify the whitelist of allowed domains, edit the `WHITELISTED_DOMAINS` set in `bot.py`. 