import datetime

def utc_now() -> datetime.datetime:
    """Returns current UTC datetime as a timezone-naive datetime object (standard for SQLite & PostgreSQL storage)"""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
