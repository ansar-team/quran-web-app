from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.schemas import User as UserSchema
from app.crud import UserCRUD
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserSchema)
async def get_current_user_info(
        current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user


@router.put("/me", response_model=UserSchema)
async def update_user_info(
        username: str = None,
        first_name: str = None,
        last_name: str = None,
        language_code: str = None,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update current user information"""
    update_data = {}
    if username is not None:
        update_data["username"] = username
    if first_name is not None:
        update_data["first_name"] = first_name
    if last_name is not None:
        update_data["last_name"] = last_name
    if language_code is not None:
        update_data["language_code"] = language_code

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No update data provided"
        )

    updated_user = UserCRUD.update_user(db, current_user.id, **update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return updated_user
