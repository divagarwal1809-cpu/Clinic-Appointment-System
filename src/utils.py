import datetime

def parse_date(date_str: str) -> datetime.date:
    """Parses date string YYYY-MM-DD to date object."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return datetime.date.today()

def parse_time(time_str: str) -> datetime.time:
    """Parses time string HH:MM to time object."""
    try:
        return datetime.datetime.strptime(time_str, "%H:%M").time()
    except ValueError:
        return datetime.time(9, 0)

def format_datetime(dt: datetime.datetime) -> str:
    """Formats datetime object to standard ISO format."""
    if not dt:
        return ""
    return dt.isoformat()
