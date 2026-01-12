import json
import logging
from datetime import time, datetime, date, timedelta
from helper import ensure_user_list

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

TOKEN = "YOUR-TELEGRAM-TOKEN"
DATA_FILE = "reminders.json"

logging.basicConfig(level=logging.INFO)

# ---------- Persistence ----------
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ---------- Commands ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hi!\n\n"
        "I can send you daily reminders.\n\n"
        "Use:\n"
        "/setdaily HH:MM Your reminder text\n"
        "Example:\n"
        "/setdaily 08:00 Take my medication\n\n"
        "But also one time reminders, use:\n"
        "/set HH:MM Your reminder text\n"
        "Example:\n"
        "/set 15:50 Meeting in 10 minutes"
    )
async def schedule_daily_reminder(context, chat_id, text, hour, minute):
    """Schedules a daily reminder using run_once and reschedules itself."""
    now = datetime.now()
    run_date = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if run_date <= now:
        run_date += timedelta(days=1)

    delay = (run_date - now).total_seconds()

    context.job_queue.run_once(
        callback=daily_job_handler,
        when=delay,
        chat_id=chat_id,
        data={"text": text, "hour": hour, "minute": minute},
    )
    logging.info(f"Daily reminder scheduled in {delay:.1f}s at {run_date}")

async def daily_job_handler(context):
    """Sends the reminder and reschedules itself for tomorrow."""
    job_data = context.job.data
    chat_id = context.job.chat_id
    text = job_data["text"]
    hour = job_data["hour"]
    minute = job_data["minute"]

    # send the message
    await context.bot.send_message(chat_id=chat_id, text=f"⏰ Daily reminder:\n{text}")

    # reschedule for tomorrow
    await schedule_daily_reminder(context, chat_id, text, hour, minute)

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
    ensure_user_list(data, user_id)

    # Store reminder
    data[user_id].append({
        "type": "daily",
        "hour": hour,
        "minute": minute,
        "text": reminder_text,
    })
    save_data(data)

    # Schedule the job
    await schedule_daily_reminder(context, update.effective_chat.id, reminder_text, hour, minute)

    await update.message.reply_text(f"✅ Daily reminder set for {hour:02d}:{minute:02d}\n📝 {reminder_text}")


async def set_once(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
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

    user_id = str(update.effective_user.id)

    data = load_data()
    data.setdefault(user_id, [])
    print(data)
    ensure_user_list(data, user_id)

    data[user_id].append({
        "type": "daily",
        "hour": hour,
        "minute": minute,
        "text": reminder_text,
    })

    save_data(data)

    delay = (run_date - datetime.now()).total_seconds()

    # HARD SAFETY GUARD
    if delay <= 0:
        delay = 5  # seconds

    logging.info(f"Scheduling one-time reminder in {delay} seconds")

    context.job_queue.run_once(
        send_once_reminder,
        when=delay,
        chat_id=update.effective_chat.id,
        data={
            "user_id": user_id,
            "text": reminder_text,
            "run_at": run_date.isoformat(),
        },
    )

    await update.message.reply_text(
        f"✅ One-time reminder set!\n"
        f"🕒 {run_date.strftime('%Y-%m-%d %H:%M')}\n"
        f"📝 {reminder_text}"
    )


# ---------- Job ----------
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"⏰ Reminder:\n{context.job.data}"
    )


async def send_once_reminder(context: ContextTypes.DEFAULT_TYPE):
    logging.info("One-time reminder fired")

    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text=f"⏰ One-time reminder:\n{job.data['text']}"
    )

    user_id = job.data["user_id"]
    run_at = job.data["run_at"]

    data = load_data()
    if user_id in data:
        data[user_id] = [
            r for r in data[user_id]
            if r.get("run_at") != run_at
        ]
        save_data(data)


# ---------- Main ----------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setdaily", set_daily))
    app.add_handler(CommandHandler("set", set_once))

    logging.info(f"JobQueue present: {app.job_queue}")

    app.run_polling()

if __name__ == "__main__":
    main()
