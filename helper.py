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
