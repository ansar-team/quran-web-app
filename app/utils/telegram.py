import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs, unquote
from fastapi import HTTPException, status, Header
from typing import Optional


def extract_telegram_init_data(authorization: Optional[str] = Header(None)):
    """
    Extract Telegram init data from Authorization header
    """
    if not authorization:
        return None

    # Check what format we're receiving
    if authorization.startswith("tma "):
        init_data = authorization[4:]
    elif authorization.startswith("Bearer "):
        init_data = authorization[7:]
    else:
        # Assume it's raw init data
        init_data = authorization

    return init_data

def verify_telegram_webapp_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Verify Telegram WebApp init data signature using HMAC-SHA256.
    Returns parsed user data if valid, otherwise None.
    """
    try:
        parsed_data = parse_qs(init_data)
        received_hash = parsed_data.get("hash", [None])[0]
        if not received_hash:
            return None
        # Build the data check string
        data_check_string_parts = [
            f"{key}={value}"
            for key, values in parsed_data.items()
            if key != "hash"
            for value in values
        ]
        data_check_string_parts.sort()
        data_check_string = "\n".join(data_check_string_parts)

        # Create secret key
        secret_key = hmac.new(
            b"WebAppData",
            bot_token.encode(),
            hashlib.sha256
        ).digest()

        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        # Check auth_date freshness (24 hours)
        auth_date = int(parsed_data.get("auth_date", [0])[0])
        if int(time.time()) - auth_date > 86400:
            return None

        # Extract user data
        user_data_str = parsed_data.get("user", [None])[0]
        if not user_data_str:
            return None

        return json.loads(unquote(user_data_str))

    except Exception as e:
        print(f"[verify_telegram_webapp_data] Error: {e}")
        return None
