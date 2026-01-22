import logging
from datetime import datetime, time, timezone
from typing import Optional

from db_utils import get_reminders, delete_user_reminder
from helpers import format_time, format_offset, offset_to_timezone


# ---------- Reminder Data ----------
def build_reminder_data(user_id: int, text: str, reminder_id: Optional[int] = None, offset: Optional[int] = None) -> dict:
    """Build a consistent reminder data dictionary."""
    data = {"user_id": user_id, "text": text}
    if reminder_id is not None:
        data["reminder_id"] = reminder_id
    if offset is not None:
        data["offset"] = offset
    return data


# ---------- Reminder Callback ----------
async def send_reminder(context):
    """Callback function that sends a reminder message."""
    job = context.job
    data = job.data

    text = data["text"]
    reminder_id = data.get("reminder_id")

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⏰ Reminder:\n{text}"
    )

    # If this was a one-time reminder, delete it from DB
    if reminder_id is not None and data.get("offset") is None:
        # Only delete if it's a "once" reminder (no offset means it's not daily)
        delete_user_reminder(reminder_id)


# ---------- Scheduling Functions ----------
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


# ---------- Reload from Database ----------
async def reload_all_reminders(app):
    """Reload all active reminders from the database on startup."""
    logging.info("Reloading reminders from database...")

    try:
        rows = get_reminders()
    except Exception as e:
        logging.error(f"Failed to load reminders from database: {e}")
        return

    logging.info(f"Found {len(rows)} active reminders in DB")

    for reminder_id, user_id, rtype, hour, minute, run_at, text, offset in rows:
        chat_id = int(user_id)
        user_tz = offset_to_timezone(offset)

        if rtype == "daily":
            reminder_time = time(hour=hour, minute=minute, tzinfo=user_tz)
            data = build_reminder_data(user_id, text, reminder_id, offset)

            schedule_daily_reminder(
                app.job_queue, chat_id, reminder_time, data, name=f"daily-{reminder_id}"
            )
            logging.info(f"Reloaded DAILY reminder {reminder_id} at {format_time(hour, minute)} {format_offset(offset)}")

        elif rtype == "once":
            now = datetime.now(timezone.utc)
            # Parse run_at string to datetime
            if isinstance(run_at, str):
                run_at = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
            if run_at.tzinfo is None:
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
