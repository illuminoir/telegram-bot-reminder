import logging
from datetime import datetime, time

from telegram import Update
from telegram.ext import ContextTypes

from config import MIN_UTC_OFFSET, MAX_UTC_OFFSET
from db_utils import set_user_timezone, save_daily_reminder, save_once_reminder
from helpers import (
    reply_error,
    reply_success,
    format_time,
    format_offset,
    parse_time,
    parse_date,
    is_date_string,
    get_user_tz,
    validate_offset,
    create_datetime_with_tz,
)
from scheduler import build_reminder_data, schedule_daily_reminder, schedule_once_reminder


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
