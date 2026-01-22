# telegram-bot-reminder

I use reminders to schedule my days, I often schedule messages to myself using Telegram so why not turn it into a bot?

With this bot you can send daily or one-time reminders, for different timezones. It uses a default of UTC+0, make sure to set the timezone for your scheduled reminders.

## Installation

```bash
pip install -r requirements.txt
```

## Setup

1. Create a bot via [@BotFather](https://t.me/botfather) and copy the token
2. Set the `BOT_TOKEN` environment variable:
   ```bash
   export BOT_TOKEN="your_token_here"
   ```
3. Run the bot:
   ```bash
   python main.py
   ```

The database (`reminders.db`) is created automatically on first run.

## Commands

| Command | Description                                                      |
|---------|------------------------------------------------------------------|
| `/help` | Show all commands                                                |
| `/settz <timezone>` | Set your timezone in UTC+N (e.g., `1` for UTC+1, `-2` for UTC-2) |
| `/set HH:MM [message]` | Set a one-time reminder                                          |
| `/setdaily HH:MM [message]` | Set a daily recurring reminder                                   |
| `/list` | View all your active reminders                                   |
| `/delete <id>` | Delete a reminder by its ID                                      |

## Examples

```
/settz 1
/set 09:00 Take medication
/setdaily 08:30 Morning standup meeting
/list
/delete 3
```

## Tech Stack

- Python 3.10+
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) (async)
- SQLite for persistence
