from telegram.ext import ApplicationBuilder, CommandHandler

from config import TOKEN
from db_utils import init_db
from handlers import help_command, set_timezone, set_daily, set_once
from scheduler import reload_all_reminders


async def post_init(app):
    """Called after the application is initialized."""
    await reload_all_reminders(app)


def main():
    init_db()

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("start", help_command))
    app.add_handler(CommandHandler("setdaily", set_daily))
    app.add_handler(CommandHandler("set", set_once))
    app.add_handler(CommandHandler("settz", set_timezone))

    app.run_polling()


if __name__ == "__main__":
    main()
