import logging
import psycopg
from datetime import datetime, date, time, timezone, timedelta
from typing import Optional

from db_utils import get_conn, get_user_timezone, set_user_timezone, init_db, save_daily_reminder, save_once_reminder
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
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)

# Constants
MIN_UTC_OFFSET = -12
MAX_UTC_OFFSET = 14


# ---------- Reply Helpers ----------
async def reply_error(update: Update, message: str):
    """Send an error reply to the user."""
    await update.message.reply_text(f"❌ {message}")


async def reply_success(update: Update, message: str):
    """Send a success reply to the user."""
    await update.message.reply_text(f"✅ {message}")


# ---------- Time/Timezone Helpers ----------
def format_time(hour: int, minute: int) -> str:
    """Format hour and minute as HH:MM string."""
    return f"{hour:02d}:{minute:02d}"


def format_offset(offset: int) -> str:
    """Format timezone offset as UTC+N or UTC-N."""
    sign = "+" if offset >= 0 else ""
    return f"UTC{sign}{offset}"


def parse_time(time_str: str) -> tuple[int, int]:
    """Parse HH:MM string and validate hour/minute ranges."""
    hour, minute = map(int, time_str.split(":"))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("Invalid hour or minute")
    return hour, minute


def parse_date(date_str: str) -> date:
    """Parse YYYY-MM-DD string into a date object."""
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def is_date_string(s: str) -> bool:
    """Check if string looks like a date (YYYY-MM-DD)."""
    return len(s) == 10 and s.count("-") == 2


def get_user_tz(user_id: int) -> timezone:
    """Get timezone object for a user."""
    offset = get_user_timezone(user_id=user_id)
    return timezone(timedelta(hours=offset))


def validate_offset(offset: int) -> bool:
    """Check if timezone offset is within valid range."""
    return MIN_UTC_OFFSET <= offset <= MAX_UTC_OFFSET


# ---------- Reminder Helpers ----------
def build_reminder_data(user_id: int, text: str, reminder_id: Optional[int] = None, offset: Optional[int] = None) -> dict:
    """Build a consistent reminder data dictionary."""
    data = {"user_id": user_id, "text": text}
    if reminder_id is not None:
        data["reminder_id"] = reminder_id
    if offset is not None:
        data["offset"] = offset
    return data


def schedule_daily_reminder(job_queue, chat_id: int, run_time: time, data: dict, name: Optional[str] = None):
    """Schedule a daily recurring reminder."""
    job_queue.run_daily(
        callback=send_reminder,
        time=run_time,
        chat_id=chat_id,
        data=data,
        name=name,
    )


def schedule_once_reminder(job_queue, chat_id: int, delay_seconds: float, data: dict, name: Optional[str] = None):
    """Schedule a one-time reminder."""
    job_queue.run_once(
        callback=send_reminder,
        when=delay_seconds,
        chat_id=chat_id,
        data=data,
        name=name,
    )


def create_datetime_with_tz(d: date, hour: int, minute: int, tz: timezone) -> datetime:
    """Create a timezone-aware datetime from date and time components."""
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)


# ---------- Commands ----------
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    await update.message.reply_text(
        "Hi!\n\n"
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
    """Set user's timezone offset."""
    if not context.args:
        await reply_error(
            update,
            "Usage: /settz <UTC offset>\n\n"
            "Examples:\n"
            "/settz 0   (UTC)\n"
            "/settz 1   (France, Germany)\n"
            "/settz -5  (New York)\n"
            "/settz 9   (Japan)"
        )
        return

    try:
        offset = int(context.args[0])
        if not validate_offset(offset):
            raise ValueError
    except ValueError:
        await reply_error(update, f"Offset must be a number between {MIN_UTC_OFFSET} and +{MAX_UTC_OFFSET}.")
        return

    user_id = update.effective_user.id
    set_user_timezone(user_id, offset)

    formatted_offset = format_offset(offset)
    await reply_success(update, f"Timezone set to {formatted_offset}\n\nAll future reminders will use this timezone.")
    logging.info(f"User {user_id} set timezone to {formatted_offset}")

async def set_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to set a daily reminder."""
    if len(context.args) < 2:
        await reply_error(update, "Usage: /setdaily HH:MM reminder text")
        return

    try:
        hour, minute = parse_time(context.args[0])
        reminder_text = " ".join(context.args[1:])
    except ValueError:
        await reply_error(update, "Time format must be HH:MM (00-23:00-59)")
        return

    user_id = update.effective_user.id
    user_tz = get_user_tz(user_id)
    run_time = time(hour=hour, minute=minute, tzinfo=user_tz)
    data = build_reminder_data(user_id, reminder_text)

    save_daily_reminder(user_id, hour, minute, reminder_text)

    schedule_daily_reminder(context.job_queue, update.effective_chat.id, run_time, data)

    await reply_success(update, f"Daily reminder set for {format_time(hour, minute)}\n{reminder_text}")


async def set_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to set a one-time reminder."""
    try:
        if len(context.args) < 2:
            raise ValueError("Not enough arguments")

        user_id = update.effective_user.id
        user_tz = get_user_tz(user_id)

        # Case 1: date + time provided (YYYY-MM-DD HH:MM)
        if is_date_string(context.args[0]):
            reminder_date = parse_date(context.args[0])
            hour, minute = parse_time(context.args[1])
            reminder_text = " ".join(context.args[2:])

            if not reminder_text:
                raise ValueError("Missing reminder text")

            run_date = create_datetime_with_tz(reminder_date, hour, minute, user_tz)

        # Case 2: only time provided -> use today
        else:
            hour, minute = parse_time(context.args[0])
            reminder_text = " ".join(context.args[1:])
            today = datetime.now(user_tz).date()
            run_date = create_datetime_with_tz(today, hour, minute, user_tz)

    except ValueError:
        await reply_error(update, "Usage:\n/set HH:MM reminder\n/set YYYY-MM-DD HH:MM reminder")
        return

    now = datetime.now(user_tz)
    if run_date <= now:
        await reply_error(update, "Time must be in the future.")
        return

    delay = (run_date - now).total_seconds()

    reminder_id = save_once_reminder(user_id, run_date, reminder_text)

    data = build_reminder_data(user_id, reminder_text, reminder_id)

    schedule_once_reminder(context.job_queue, update.effective_chat.id, delay, data)

    logging.info(f"Scheduling one-time reminder in {delay:.1f} seconds")
    await reply_success(
        update,
        f"One-time reminder set!\n"
        f"Time: {run_date.strftime('%Y-%m-%d %H:%M')}\n"
        f"{reminder_text}"
    )


async def reload_all_reminders(app):
    """Reload all active reminders from the database on startup."""
    logging.info("Reloading reminders from database...")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT r.id, r.user_id, r.type, r.hour, r.minute, r.run_at, r.text,
                           u.timezone_offset
                    FROM reminders r
                    JOIN users u ON u.id = r.user_id
                    WHERE r.active = TRUE
                    """
                )
                rows = cur.fetchall()
    except Exception as e:
        logging.error(f"Failed to load reminders from database: {e}")
        return

    logging.info(f"Found {len(rows)} active reminders in DB")

    for reminder_id, user_id, rtype, hour, minute, run_at, text, offset in rows:
        chat_id = int(user_id)
        user_tz = timezone(timedelta(hours=offset))

        if rtype == "daily":
            reminder_time = time(hour=hour, minute=minute, tzinfo=user_tz)
            data = build_reminder_data(user_id, text, reminder_id, offset)

            schedule_daily_reminder(
                app.job_queue, chat_id, reminder_time, data, name=f"daily-{reminder_id}"
            )
            logging.info(f"Reloaded DAILY reminder {reminder_id} at {format_time(hour, minute)} {format_offset(offset)}")

        elif rtype == "once":
            now = datetime.now(timezone.utc)
            run_at = run_at.replace(tzinfo=timezone.utc)
            delay = (run_at - now).total_seconds()

            if delay > 0:
                data = build_reminder_data(user_id, text, reminder_id)
                schedule_once_reminder(
                    app.job_queue, chat_id, delay, data, name=f"once-{reminder_id}"
                )
                logging.info(f"Reloaded ONCE reminder {reminder_id} in {delay:.1f}s")
            else:
                logging.info(f"Skipping expired one-time reminder {reminder_id}")

    logging.info("Reminder reload complete")

async def post_init(app):
    await reload_all_reminders(app)


async def get_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM users ")
        rows = cur.fetchall()
        print(rows)
        await reply_success(update, rows)



# ---------- Main ----------
def main():

    init_db()

    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("setdaily", set_daily))
    app.add_handler(CommandHandler("set", set_once))
    app.add_handler(CommandHandler("settz", set_timezone))
    #DEBUG TODO
    app.add_handler(CommandHandler("gettz", get_timezone))

    app.run_polling()

if __name__ == "__main__":
    main()
