from datetime import datetime, date, timezone, timedelta
from telegram import Update

from config import MIN_UTC_OFFSET, MAX_UTC_OFFSET
from db_utils import get_user_timezone


# ---------- Reply Helpers ----------
async def reply_error(update: Update, message: str):
    """Send an error reply to the user."""
    await update.message.reply_text(f"❌ {message}")


async def reply_success(update: Update, message: str):
    """Send a success reply to the user."""
    await update.message.reply_text(f"✅ {message}")


# ---------- Formatting Helpers ----------
def format_time(hour: int, minute: int) -> str:
    """Format hour and minute as HH:MM string."""
    return f"{hour:02d}:{minute:02d}"


def format_offset(offset: int) -> str:
    """Format timezone offset as UTC+N or UTC-N."""
    sign = "+" if offset >= 0 else ""
    return f"UTC{sign}{offset}"


# ---------- Parsing Helpers ----------
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


# ---------- Timezone Helpers ----------
def get_user_tz(user_id: int) -> timezone:
    """Get timezone object for a user."""
    offset = get_user_timezone(user_id)
    return timezone(timedelta(hours=offset))


def offset_to_timezone(offset: int) -> timezone:
    """Convert an offset integer to a timezone object."""
    return timezone(timedelta(hours=offset))


def validate_offset(offset: int) -> bool:
    """Check if timezone offset is within valid range."""
    return MIN_UTC_OFFSET <= offset <= MAX_UTC_OFFSET


# ---------- DateTime Helpers ----------
def create_datetime_with_tz(d: date, hour: int, minute: int, tz: timezone) -> datetime:
    """Create a timezone-aware datetime from date and time components."""
    return datetime(d.year, d.month, d.day, hour, minute, tzinfo=tz)
