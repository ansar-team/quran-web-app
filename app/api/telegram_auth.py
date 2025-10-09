from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Optional
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qs, unquote

from app import crud, schemas
from app.database import get_db
from app.config import settings

router = APIRouter()


def verify_telegram_webapp_data(init_data: str, bot_token: str) -> Optional[dict]:
    """
    Verify Telegram WebApp init data signature
    """
    try:
        # Parse the init data
        parsed_data = parse_qs(init_data)

        # Extract hash from data
        received_hash = parsed_data.get('hash', [None])[0]
        if not received_hash:
            return None

        # Remove hash from data for verification
        data_check_string_parts = []
        for key, values in parsed_data.items():
            if key != 'hash':
                for value in values:
                    data_check_string_parts.append(f"{key}={value}")

        # Sort the parts
        data_check_string_parts.sort()
        data_check_string = '\n'.join(data_check_string_parts)

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

        # Verify hash
        if not hmac.compare_digest(calculated_hash, received_hash):
            return None

        # Check auth_date (should be within 24 hours)
        auth_date = int(parsed_data.get('auth_date', [0])[0])
        current_time = int(time.time())
        if current_time - auth_date > 86400:  # 24 hours
            return None

        # Parse user data
        user_data_str = parsed_data.get('user', [None])[0]
        if user_data_str:
            user_data = json.loads(unquote(user_data_str))
            return user_data

        return None

    except Exception as e:
        print(f"Error verifying Telegram data: {e}")
        return None


@router.post("/telegram/mini-app/auth")
def telegram_mini_app_auth(
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Authenticate Telegram Mini App user
    """
    try:
        # Get the init data from Authorization header or request body
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            init_data = auth_header[7:]  # Remove "Bearer " prefix
        else:
            # Try to get from request body
            body = request.json()
            init_data = body.get("init_data", "")

        if not init_data:
            raise HTTPException(status_code=400, detail="Missing init_data")

        # Verify the Telegram WebApp data
        user_data = verify_telegram_webapp_data(init_data, settings.TELEGRAM_BOT_TOKEN)

        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram WebApp data")

        # Extract user information
        telegram_id = user_data.get("id")
        username = user_data.get("username")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        if not telegram_id:
            raise HTTPException(status_code=400, detail="Missing user ID in Telegram data")

        # Check if user already exists
        existing_user = crud.get_user_by_telegram_id(db, telegram_id)

        if existing_user:
            # Update user info if needed
            if username != existing_user.username:
                existing_user.username = username
                db.commit()
                db.refresh(existing_user)

            return {
                "success": True,
                "data": schemas.UserResponse.model_validate(existing_user),
                "message": "User authenticated successfully"
            }
        else:
            # Create new user
            user_create = schemas.UserCreate(
                telegram_id=telegram_id,
                username=username
            )

            new_user = crud.create_user(db, user_create)

            return {
                "success": True,
                "data": schemas.UserResponse.model_validate(new_user),
                "message": "User created and authenticated successfully"
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in telegram auth: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during authentication")


@router.get("/telegram/mini-app/me")
def get_current_user(
        request: Request,
        db: Session = Depends(get_db)
):
    """
    Get current authenticated user information
    """
    try:
        # Get the init data from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

        init_data = auth_header[7:]  # Remove "Bearer " prefix

        # Verify the Telegram WebApp data
        user_data = verify_telegram_webapp_data(init_data, settings.TELEGRAM_BOT_TOKEN)

        if not user_data:
            raise HTTPException(status_code=401, detail="Invalid Telegram WebApp data")

        # Get user from database
        telegram_id = user_data.get("id")
        user = crud.get_user_by_telegram_id(db, telegram_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "data": schemas.UserResponse.model_validate(user),
            "message": "User information retrieved successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting current user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
