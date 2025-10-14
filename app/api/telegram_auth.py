from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app import schemas
from app.crud import UserCRUD
from app.database import get_db
from app.config import settings
from app.utils.telegram import extract_telegram_init_data, verify_telegram_webapp_data

router = APIRouter(prefix="/telegram/mini-app", tags=["telegram"])


@router.post("/auth")
def telegram_mini_app_auth(
        authorization: Optional[str] = Header(None),
        db: Session = Depends(get_db)
):
    """
    Authenticate Telegram Mini App user
    """
    # Get the init data from Authorization header or request body
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

            return {
                "success": True,
                "data": existing_user,
                "message": "User authenticated successfully"
            }
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
            return {
                "success": True,
                "data": new_user,
                "message": "User created and authenticated successfully"
            }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in telegram auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication"
        )
