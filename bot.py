import logging
from datetime import datetime, date, time, timezone, timedelta
from helper import save_user_data, load_data
from publish import send_reminder

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from dotenv import load_dotenv
import os

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")

logging.basicConfig(level=logging.INFO)

tmp_offset_no_bd = 0

# ---------- Commands ----------
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi!\n\n"
        "I can send you daily reminders.\n\n"
        "Use:\n"
        "/settz N To set your timezone to UTC+N (default timezone is UTC+0)\n\n"
        "/setdaily HH:MM Your reminder text\n"
        "Example:\n"
        "/setdaily 08:00 Take my medication\n\n"
        "But also one time reminders, use:\n"
        "/set HH:MM Your reminder text\n"
        "Example:\n"
        "/set 15:50 Meeting in 10 minutes"
    )

async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Usage: /settz <UTC offset>\n\n"
            "Examples:\n"
            "/settz 0   (UTC)\n"
            "/settz 1   (France, Germany)\n"
            "/settz -5  (New York)\n"
            "/settz 9   (Japan)"
        )
        return

    try:
        offset = int(context.args[0])
        if offset < -12 or offset > 14:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Offset must be a number between -12 and +14.")
        return

    user_id = str(update.effective_user.id)

    sign = "+" if offset >= 0 else ""
    await update.message.reply_text(
        f"✅ Timezone set to UTC{sign}{offset}\n\n"
        "All future reminders will use this timezone."
    )

    global tmp_offset_no_bd
    tmp_offset_no_bd = offset

    logging.info(f"User {user_id} set timezone to UTC{sign}{offset}")


async def set_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to set a daily reminder."""
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: /setdaily HH:MM reminder text")
        return

    try:
        hour, minute = map(int, context.args[0].split(":"))
        reminder_text = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ Time format must be HH:MM")
        return

    user_id = str(update.effective_user.id)
    data = load_data()
    save_user_data(data, user_id, "daily", hour, minute, reminder_text)

    user_tz = timezone(timedelta(hours=tmp_offset_no_bd))
    run_date = time(hour=hour, minute=minute, tzinfo=user_tz)

    context.job_queue.run_daily(
        callback=send_reminder,
        time=run_date,
        chat_id=update.effective_chat.id,
        data=reminder_text,
    )

    await update.message.reply_text(f"✅ Daily reminder set for {hour:02d}:{minute:02d}\n📝 {reminder_text}")

async def set_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            raise ValueError
        # Case 1: date + time provided
        if len(context.args[0]) == 10 and context.args[0].count("-") == 2:
            date_str = context.args[0]
            time_str = context.args[1]
            reminder_text = " ".join(context.args[2:])

            run_date = datetime.strptime(
                f"{date_str} {time_str}", "%Y-%m-%d %H:%M"
            )

        # Case 2: only time provided → use today
        else:
            time_str = context.args[0]
            reminder_text = " ".join(context.args[1:])

            today = date.today()
            hour, minute = map(int, time_str.split(":"))

            run_date = datetime(
                today.year,
                today.month,
                today.day,
                hour,
                minute
            )

    except ValueError:
        await update.message.reply_text(
            "❌ Usage:\n"
            "/set HH:MM reminder\n"
            "/set YYYY-MM-DD HH:MM reminder"
        )
        return

    if run_date <= datetime.now():
        await update.message.reply_text("❌ Time must be in the future.")
        return

    delay = (run_date - datetime.now()).total_seconds()

    logging.info(f"Scheduling one-time reminder in {delay} seconds")

    context.job_queue.run_once(
        send_reminder,
        when=delay,
        chat_id=update.effective_chat.id,
        data=reminder_text
    )

    await update.message.reply_text(
        f"✅ One-time reminder set!\n"
        f"🕒 {run_date.strftime('%Y-%m-%d %H:%M')}\n"
        f"📝 {reminder_text}"
    )


# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("setdaily", set_daily))
    app.add_handler(CommandHandler("set", set_once))
    app.add_handler(CommandHandler("settz", set_timezone))

    app.run_polling()

if __name__ == "__main__":
    main()
