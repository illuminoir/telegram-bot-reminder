import json

DATA_FILE = "reminders.json"

def ensure_user_list(data, user_id):
    """
    Migrates old single-reminder dict format to list format.
    """
    if user_id not in data:
        data[user_id] = []

    # Old format → migrate
    if isinstance(data[user_id], dict):
        old = data[user_id]
        data[user_id] = [{
            "type": "daily",
            "hour": old["hour"],
            "minute": old["minute"],
            "text": old["text"],
        }]


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


def save_user_data(data, user_id, type, hour, minute, reminder_text):
    ensure_user_list(data, user_id)

    # Store reminder
    data[user_id].append({
       "type": type,
        "hour": hour,
        "minute": minute,
        "text": reminder_text,
    })
    save_data(data)