from telegram.ext import ContextTypes

async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"⏰ Reminder:\n{context.job.data}"
    )
    '''
    user_id = context.job.data["user_id"]
    run_at = context.job.data["run_at"]

    data = load_data()
    if user_id in data:
        data[user_id] = [
            r for r in data[user_id]
            if r.get("run_at") != run_at
        ]
        save_data(data)
    '''