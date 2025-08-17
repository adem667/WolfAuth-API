
from datetime import datetime

def is_valid_key(key, correct_key):
    return key == correct_key

def parse_expiration_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None

def is_account_expired(account):
    return datetime.utcnow() > account.expiration_date
