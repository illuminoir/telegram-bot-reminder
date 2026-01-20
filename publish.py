from telegram.ext import ContextTypes

from db_utils import delete_once_reminder


async def send_reminder(context):
    job = context.job
    data = job.data

    text = data["text"]
    reminder_id = data.get("reminder_id")   # only exists for once reminders

    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⏰ Reminder:\n{text}"
    )

    # If this was a one-time reminder → delete it from DB
    if reminder_id is not None:
        delete_once_reminder(reminder_id)