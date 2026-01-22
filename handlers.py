import logging
from datetime import datetime, time

from telegram import Update
from telegram.ext import ContextTypes

from config import MIN_UTC_OFFSET, MAX_UTC_OFFSET
from db_utils import set_user_timezone, save_daily_reminder, save_once_reminder, get_reminders_for_user, \
    delete_user_reminder, check_reminder_exists, set_user_language, ensure_user_exists
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
    create_datetime_with_tz, t,
)
from i18n import SUPPORTED_LANGUAGES
from scheduler import build_reminder_data, schedule_daily_reminder, schedule_once_reminder


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    user_id = update.effective_user.id
    await update.message.reply_text(t(user_id, "help", languages=(', '.join(SUPPORTED_LANGUAGES))))


async def set_timezone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set user's timezone offset."""
    user_id = update.effective_user.id
    ensure_user_exists(user_id, update.effective_user.language_code)
    if not context.args:
        await reply_error(update, t(user_id, "timezone_set_usage"))
        return

    try:
        offset = int(context.args[0])
        if not validate_offset(offset):
            raise ValueError
    except ValueError:
        await reply_error(
            update,
            t(
                user_id,
                "timezone_set_error",
                MIN_UTC_OFFSET=MIN_UTC_OFFSET,
                MAX_UTC_OFFSET=MAX_UTC_OFFSET,
            )
        )
        return

    set_user_timezone(user_id, offset)
    formatted_offset = format_offset(offset)
    await reply_success(update, t(user_id, "timezone_set_success", formatted_offset=formatted_offset))
    logging.info(f"User {user_id} set timezone to {formatted_offset}")


async def set_daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to set a daily reminder."""
    user_id = update.effective_user.id
    ensure_user_exists(user_id, update.effective_user.language_code)

    if len(context.args) < 2:
        await reply_error(update, t(user_id, "set_daily_reminder_usage"))
        return

    try:
        hour, minute = parse_time(context.args[0])
        reminder_text = " ".join(context.args[1:])
    except ValueError:
        await reply_error(update, t(user_id, "invalid_time"))
        return

    user_tz = get_user_tz(user_id)
    run_time = time(hour=hour, minute=minute, tzinfo=user_tz)
    data = build_reminder_data(user_id, reminder_text)

    save_daily_reminder(user_id, hour, minute, reminder_text)
    schedule_daily_reminder(context.job_queue, update.effective_chat.id, run_time, data)

    await reply_success(update, t(user_id, "set_daily_reminder_success", time=format_time(hour, minute), text=reminder_text))


async def set_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command to set a one-time reminder."""

    user_id = update.effective_user.id
    ensure_user_exists(user_id, update.effective_user.language_code)
    try:
        if len(context.args) < 2:
            raise ValueError("ERR:ARGS")

        user_tz = get_user_tz(user_id)

        # Case 1: date + time provided (YYYY-MM-DD HH:MM)
        if is_date_string(context.args[0]):
            reminder_date = parse_date(context.args[0])
            hour, minute = parse_time(context.args[1])
            reminder_text = " ".join(context.args[2:])

            if not reminder_text:
                raise ValueError("ERR:NO_TEXT")

            run_date = create_datetime_with_tz(reminder_date, hour, minute, user_tz)

        # Case 2: only time provided -> use today
        else:
            hour, minute = parse_time(context.args[0])
            reminder_text = " ".join(context.args[1:])
            today = datetime.now(user_tz).date()
            run_date = create_datetime_with_tz(today, hour, minute, user_tz)

    except ValueError:
        await reply_error(update, t(user_id, "set_once_reminder_usage"))
        return

    now = datetime.now(user_tz)
    if run_date <= now:
        await reply_error(update, t(user_id,"time_not_in_future"))
        return

    delay = (run_date - now).total_seconds()

    reminder_id = save_once_reminder(user_id, run_date, reminder_text)
    data = build_reminder_data(user_id, reminder_text, reminder_id)

    schedule_once_reminder(context.job_queue, update.effective_chat.id, delay, data)

    logging.info(f"Scheduling one-time reminder in {delay:.1f} seconds")
    await reply_success(
        update, t(user_id, "set_once_reminder_success",
                  time=run_date.strftime('%Y-%m-%d %H:%M'),
                  text=reminder_text)
    )

async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id, update.effective_user.language_code)
    reminders = get_reminders_for_user(user_id)

    if not reminders:
        await reply_success(update, t(user_id, "no_reminders"))
        return

    lines = [t(user_id, "reminder_list_header")]
    for reminder_id, run_at, text in reminders:
        run_at_str = run_at.replace("+01:00", "")
        lines.append(t(user_id, "reminder_list_item", id=reminder_id, time=run_at_str, text=text))

    message = "\n".join(lines)
    await reply_success(update, message)

async def delete_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    ensure_user_exists(user_id, update.effective_user.language_code)
    try:
        if len(context.args) < 1:
            raise ValueError("ERR:ARGS")
        reminder_number = context.args[0]
        #TODO check int
        if not check_reminder_exists(reminder_number):
            await reply_error(update, t(user_id, "reminder_does_not_exist", number=reminder_number))
            return
        delete_user_reminder(reminder_number)
    except ValueError:
        await reply_error(update, "Usage:\n/delete reminder_number")
        return

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user_exists(user_id, update.effective_user.language_code)
    if not context.args:
        await reply_error(
            update,
            t(user_id, "set_language_usage", languages=(', '.join(sorted(SUPPORTED_LANGUAGES))))
        )
        return

    lang = context.args[0]

    if lang not in SUPPORTED_LANGUAGES:
        await reply_error(
            update,
            t(user_id, "unsupported_language", languages=(', '.join(sorted(SUPPORTED_LANGUAGES))))
        )
        return

    set_user_language(user_id, lang)

    await reply_success(update, t(user_id, "set_language_success", language=lang))

