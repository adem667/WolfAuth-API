from datetime import datetime

def is_valid_key(provided, real):
    return provided == real

def parse_expiration_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None

def is_account_expired(account):
    return datetime.utcnow() > account.expiration_date
