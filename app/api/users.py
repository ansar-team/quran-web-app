from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import current_user

from app.database import get_db
from app.models import User
from app.schemas import UserSchema
from app.crud import UserCRUD, LessonProgressCRUD
# from app.api.dependencies import get_current_user
from app.utils.session_store import get_current_user

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


@router.get("/progress", response_model=dict)
async def get_current_user_info(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get lesson progress information"""
    lessons = LessonProgressCRUD.get_lessons_progresses(db, current_user.id)
    total_lessons = len(lessons)
    completed_lessons = 0
    total_words = 0
    words_due_for_review = 0
    for lesson in lessons:
        total_words += lesson.words_learned
        words_due_for_review += lesson.words_to_review
        if lesson.is_completed:
            completed_lessons += 1
    return {
        "total_words": total_words,
        "completed_lessons": completed_lessons,
        "total_lessons": total_lessons,
        "words_due_for_review": words_due_for_review
    }

