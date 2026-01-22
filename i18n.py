MESSAGES = {
    "en": {
        "help": (
            "Hi!\n\n"
            "I can send you daily reminders.\n\n"
            "Use:\n"
            "/settz N To set your timezone to UTC+N (default is UTC+0)\n"
            "/setdaily HH:MM Your reminder text\n"
            "Example:\n"
            "/setdaily 08:00 Take my medication\n\n"
            "But also one time reminders, use:\n"
            "/set HH:MM Your reminder text\n"
            "Example:\n"
            "/set 15:50 Meeting in 10 minutes\n\n"
            "To change language, use: /setlang <language>\n"
            "Supported languages: {languages}"
        ),
        "timezone_set_success": "Timezone set to {formatted_offset}\n\nAll future reminders will use this timezone.",
        "timezone_set_usage": (
            "Usage: /settz <UTC offset>\n\n"
            "Examples:\n"
            "/settz 0   (UTC)\n"
            "/settz 1   (France, Germany)\n"
            "/settz -5  (New York)\n"
            "/settz 9   (Japan)"
        ),
        "timezone_set_error": "Offset must be a number between {MIN_UTC_OFFSET} and +{MAX_UTC_OFFSET}.",
        "set_daily_reminder_usage": "Usage: /setdaily HH:MM reminder text",
        "set_daily_reminder_success": "Daily reminder set for {time}\n{text}",
        "set_once_reminder_usage": "Usage:\n/set HH:MM reminder\n/set YYYY-MM-DD HH:MM reminder",
        "set_once_reminder_success": "Reminder set for {time}\n{text}",
        "invalid_time": "Time format must be HH:MM (00-23:00-59)",
        "time_not_in_future": "Time must be in the future.",
        "no_reminders": "No reminders.",
        "reminder_list_header": "📋 Reminders:",
        "reminder_list_item": "Reminder n°{id} | Set to run at: {time} | Text: {text}",
        "reminder_does_not_exist": "Reminder number {number} does not exist.",
        "set_language_usage": "Usage: /setlang <language>\nSupported: {languages}",
        "unsupported_language": "Unsupported language.\nSupported: {languages}",
        "set_language_success": "Language set to {language}",
    },

    "fr": {
        "help": (
            "Salut !\n\n"
            "Je peux t'envoyer des rappels quotidiens.\n\n"
            "Utilisation :\n"
            "/settz N Pour définir ton fuseau horaire en UTC+N (par défaut UTC+0)\n"
            "/setdaily HH:MM Ton texte de rappel\n"
            "Exemple :\n"
            "/setdaily 08:00 Prendre mon médicament\n\n"
            "Tu peux aussi définir un rappel unique avec :\n"
            "/set HH:MM Ton texte de rappel\n"
            "Exemple :\n"
            "/set 15:50 Réunion dans 10 minutes\n\n"
            "Pour changer de langue, utilise : /setlang <langue>\n"
            "Langues disponibles : {languages}"
        ),

        "timezone_set_success": (
            "Fuseau horaire défini sur {formatted_offset}\n\n"
            "Tous les futurs rappels utiliseront ce fuseau horaire."
        ),
        "timezone_set_usage": (
            "Utilisation : /settz <décalage UTC>\n\n"
            "Exemples :\n"
            "/settz 0   (UTC)\n"
            "/settz 1   (France, Allemagne)\n"
            "/settz -5  (New York)\n"
            "/settz 9   (Japon)"
        ),
        "timezone_set_error": "Le décalage doit être un nombre entre {MIN_UTC_OFFSET} et +{MAX_UTC_OFFSET}.",
        "set_daily_reminder_usage": "Utilisation : /setdaily HH:MM texte du rappel",
        "set_daily_reminder_success": "Rappel quotidien défini pour {time}\n{text}",
        "set_once_reminder_usage": "Utilisation :\n/set HH:MM rappel\n/set YYYY-MM-DD HH:MM rappel",
        "set_once_reminder_success": "Rappel défini pour {time}\n{text}",
        "invalid_time": "Le format de l'heure doit être HH:MM (00-23:00-59)",
        "time_not_in_future": "L'heure doit être dans le futur.",
        "no_reminders": "Aucun rappel.",
        "reminder_list_header": "📋 Rappels :",
        "reminder_list_item": "Rappel n°{id} | Exécution prévue à : {time} | Texte : {text}",
        "reminder_does_not_exist": "Le rappel numéro {number} n'existe pas.",
        "set_language_usage": "Utilisation : /setlang <langue>\nLangues disponibles : {languages}",
        "unsupported_language": "Langue non supportée.\nLangues disponibles : {languages}",
        "set_language_success": "Langue définie sur {language}",
    }
}

SUPPORTED_LANGUAGES = set(MESSAGES.keys())
