from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app import schemas
from app.crud import UserCRUD
from app.database import get_db
from app.config import settings
from app.models import User
from app.utils.telegram import extract_telegram_init_data, verify_telegram_webapp_data

security = HTTPBearer()


def get_current_user(
        authorization: Optional[str] = Header(None),
        # init_data: str = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    Get current user from Telegram WebApp init data
    """
    # Extract init data from Authorization header
    init_data = extract_telegram_init_data(authorization)
    try:
        # Verify the Telegram WebApp data
        user_data = verify_telegram_webapp_data(init_data, settings.telegram_bot_token)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram WebApp data"
            )

        # Extract user information
        telegram_id = user_data.get("id")
        username = user_data.get("username")

        if not telegram_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing user ID in Telegram data"
            )

        # Check if user already exists
        existing_user = UserCRUD.get_user_by_telegram_id(db, telegram_id)

        if existing_user:
            # Update user info if needed
            if username != existing_user.username:
                existing_user.username = username
                db.commit()
                db.refresh(existing_user)

            return existing_user
        else:
            # Create new user
            user_create = schemas.UserCreate(
                telegram_id=telegram_id,
                username=username,
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                language_code=user_data.get("language_code", "en")
            )

            new_user = UserCRUD.create_user(db, user_create)
            return new_user

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in telegram auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )
